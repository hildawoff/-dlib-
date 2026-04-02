# 配置读取：从数据库动态获取系统参数（如防抖时间、考勤规则），避免硬编码。
# 考勤处理：核心函数 process_attendance 处理用户的签到/签退请求，包括防抖、迟到判定、工作时长计算等。
# 自动签退：perform_auto_checkout 用于定时任务，在指定时间（下班后 30 分钟）自动为未签退用户签退，并记录状态。
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from models import models
from typing import Optional


# ── 辅助函数：从数据库读取配置 ────────────────────────────────

def get_config_value(db: Session, key: str, default_val: str = None) -> str:
    """
    根据键名从 SystemConfig 表中获取配置值。
    若不存在，则返回默认值。
    """
    config = db.query(models.SystemConfig).filter(
        models.SystemConfig.key == key
    ).first()
    if config:
        return config.value
    return default_val


def get_config_int(db: Session, key: str, default_val: int) -> int:
    """
    获取整数类型的配置值。
    如果值无法转换为整数，则返回默认值。
    """
    val = get_config_value(db, key)
    try:
        return int(val) if val else default_val
    except ValueError:
        return default_val


# ── 核心打卡逻辑 ─────────────────────────────────────────────

def get_active_rule(db: Session) -> models.AttendanceRule | None:
    """
    获取当前生效的考勤规则（is_active = True）。
    通常只有一个规则生效。
    """
    return db.query(models.AttendanceRule).filter(
        models.AttendanceRule.is_active == True
    ).first()


def process_attendance(db: Session, user: models.FaceUser) -> dict:
    """
    处理单个用户的考勤操作（签到或签退）。
    返回包含操作类型、状态、消息的字典。
    """
    now = datetime.now()
    today = now.date()

    # 从数据库读取防抖间隔（秒），默认 60 秒
    debounce_seconds = get_config_int(db, "checkin_debounce_seconds", 60)

    # ── 防抖逻辑：限制短时间内重复打卡 ─────────────────────────
    recent_threshold = now - timedelta(seconds=debounce_seconds)
    recent = (
        db.query(models.AttendanceRecord)
        .filter(
            models.AttendanceRecord.user_id == user.id,
            models.AttendanceRecord.check_in_time >= recent_threshold,
        )
        .first()
    )
    if recent:
        return {
            "action": "debounce",
            "message": f"请勿频繁打卡，{debounce_seconds} 秒内只记录一次",
        }

    # 查询今日是否已有考勤记录
    today_record = (
        db.query(models.AttendanceRecord)
        .filter(
            models.AttendanceRecord.user_id == user.id,
            models.AttendanceRecord.date == today,
        )
        .first()
    )
    rule = get_active_rule(db)  # 获取生效的考勤规则

    # ── 情况 1：签到（今日无记录）──────────────────────────────
    if today_record is None:
        # 迟到判定：基于规则中的上班时间和迟到阈值
        status = "on_time"
        late_minutes = 0
        if rule:
            work_start_dt = datetime.combine(today, rule.work_start)
            threshold_dt = work_start_dt + timedelta(minutes=rule.late_threshold_minutes)
            if now > threshold_dt:
                status = "late"
                late_minutes = int((now - work_start_dt).total_seconds() / 60)

        # 创建新考勤记录，只填写签到时间
        record = models.AttendanceRecord(
            user_id=user.id,
            date=today,
            check_in_time=now,
            status=status,
            late_minutes=late_minutes
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "action": "check_in",
            "status": status,
            "late_minutes": late_minutes,
            "record": record,
            "message": f"签到成功（{'准时' if status == 'on_time' else f'迟到 {late_minutes} 分钟'}）"
        }

    # ── 情况 2：签退（已有签到但未签退）─────────────────────────
    if today_record.check_out_time is None:
        today_record.check_out_time = now
        # 计算工作时长（小时）
        work_seconds = (now - today_record.check_in_time).total_seconds()
        work_hours = work_seconds / 3600
        db.commit()
        db.refresh(today_record)

        return {
            "action": "check_out",
            "record": today_record,
            "work_hours": round(work_hours, 2),
            "message": f"签退成功，今日在岗 {work_hours:.1f} 小时"
        }

    # ── 情况 3：今日已完成签到和签退 ───────────────────────────
    return {
        "action": "already_complete",
        "record": today_record,
        "message": "今日已完成签到和签退"
    }


# ═══════════════════════════════════════════════════════════
# 自动签退逻辑（供定时任务调用）
# ═══════════════════════════════════════════════════════════

def perform_auto_checkout(db: Session):
    """
    定时任务调用的自动签退函数。
    逻辑：
      1. 获取当前生效的考勤规则。
      2. 计算自动签退触发时间（下班时间 + 30分钟）。
      3. 若当前时间未到触发时间，则返回。
      4. 查询今日所有已签到但未签退的记录。
      5. 将这些记录的签退时间设为当天的下班时间，并提交数据库。
      6. 记录日志（实际项目中可发送通知）。
    """
    now = datetime.now()
    today = now.date()
    rule = get_active_rule(db)

    if not rule:
        return  # 没有考勤规则，无法进行自动签退

    # 自动签退触发时间：下班后 30 分钟（可配置化，这里固定）
    auto_trigger_time = datetime.combine(today, rule.work_end) + timedelta(minutes=30)

    if now < auto_trigger_time:
        return  # 还未到自动签退时间

    # 查询未签退记录
    unfinished_records = (
        db.query(models.AttendanceRecord)
        .filter(
            models.AttendanceRecord.date == today,
            models.AttendanceRecord.check_out_time == None
        )
        .all()
    )

    if not unfinished_records:
        return

    # 批量处理自动签退
    for record in unfinished_records:
        # 将签退时间设置为当天下班时间（视为正常下班）
        record.check_out_time = datetime.combine(today, rule.work_end)
        # 状态可标记为自动签退（可选）
        record.status = record.status or "auto_checkout"

        # 实际项目中可在此发送邮件或推送通知
        print(f"[自动签退] 用户 {record.user_id} 已自动签退")

    db.commit()