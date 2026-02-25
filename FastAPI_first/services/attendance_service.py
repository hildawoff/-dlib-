from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from models import models
from typing import Optional


# 移除硬编码的导入：from core.config import CHECKIN_DEBOUNCE_SECONDS

# ── 辅助函数：从数据库读取配置 ────────────────────────────────
def get_config_value(db: Session, key: str, default_val: str = None) -> str:
    """获取系统配置值"""
    config = db.query(models.SystemConfig).filter(
        models.SystemConfig.key == key
    ).first()
    if config:
        return config.value
    return default_val


def get_config_int(db: Session, key: str, default_val: int) -> int:
    """获取整数类型配置"""
    val = get_config_value(db, key)
    try:
        return int(val) if val else default_val
    except ValueError:
        return default_val


# ── 核心打卡逻辑（修改版）────────────────────────────────────
def get_active_rule(db: Session) -> models.AttendanceRule | None:
    return db.query(models.AttendanceRule).filter(
        models.AttendanceRule.is_active == True
    ).first()


def process_attendance(db: Session, user: models.FaceUser) -> dict:
    now = datetime.now()
    today = now.date()

    # 【优化】从数据库读取防抖时间，默认60秒
    debounce_seconds = get_config_int(db, "checkin_debounce_seconds", 60)

    # ── 防抖逻辑 ──────────────────────────────────────────────
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

    # ... 中间签到/签退逻辑保持不变 ...
    today_record = (
        db.query(models.AttendanceRecord)
        .filter(
            models.AttendanceRecord.user_id == user.id,
            models.AttendanceRecord.date == today,
        )
        .first()
    )
    rule = get_active_rule(db)

    # 情况 1：签到
    if today_record is None:
        status = "on_time"
        late_minutes = 0
        if rule:
            work_start_dt = datetime.combine(today, rule.work_start)
            threshold_dt = work_start_dt + timedelta(minutes=rule.late_threshold_minutes)
            if now > threshold_dt:
                status = "late"
                late_minutes = int((now - work_start_dt).total_seconds() / 60)

        record = models.AttendanceRecord(
            user_id=user.id, date=today, check_in_time=now,
            status=status, late_minutes=late_minutes
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {
            "action": "check_in", "status": status,
            "late_minutes": late_minutes, "record": record,
            "message": f"签到成功（{'准时' if status == 'on_time' else f'迟到 {late_minutes} 分钟'}）"
        }

    # 情况 2：签退
    if today_record.check_out_time is None:
        today_record.check_out_time = now
        work_seconds = (now - today_record.check_in_time).total_seconds()
        work_hours = work_seconds / 3600
        db.commit()
        db.refresh(today_record)
        return {
            "action": "check_out", "record": today_record,
            "work_hours": round(work_hours, 2),
            "message": f"签退成功，今日在岗 {work_hours:.1f} 小时"
        }

    # 情况 3：已完成
    return {
        "action": "already_complete", "record": today_record,
        "message": "今日已完成签到和签退"
    }


# ╔══════════════════════════════════════════════════════════╗
# ║           新增：自动签退逻辑（定时任务调用）             ║
# ╚══════════════════════════════════════════════════════════╝

def perform_auto_checkout(db: Session):
    """
    自动签退执行函数：
    1. 获取当前生效的规则
    2. 检查是否超过了下班时间 + 容忍时间
    3. 查找所有今日已签到但未签退的记录
    4. 执行自动签退并更新状态
    """
    now = datetime.now()
    today = now.date()
    rule = get_active_rule(db)

    if not rule:
        return  # 无规则则不处理

    # 计算自动签退触发时间（下班后30分钟）
    auto_trigger_time = datetime.combine(today, rule.work_end) + timedelta(minutes=30)

    if now < auto_trigger_time:
        return  # 还没到自动签退时间

    # 查找未签退记录
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

    # 执行自动签退
    for record in unfinished_records:
        # 设定签退时间为下班时间（视为准时下班）或当前时间
        # 这里策略可以选择：设为下班时间，这样不算加班，也不算早退
        record.check_out_time = datetime.combine(today, rule.work_end)
        record.status = record.status or "auto_checkout"  # 可以新增一种状态

        # 发送邮件通知（这里需要异步调用，但在定时任务中可以直接调用 await 或同步发送）
        # 简化版：打印日志，实际项目建议集成到后台任务队列
        print(f"[自动签退] 用户 {record.user_id} 已自动签退")

    db.commit()
