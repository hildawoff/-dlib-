# 考勤业务逻辑服务
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from models import models
from core.config import CHECKIN_DEBOUNCE_SECONDS


def get_active_rule(db: Session) -> models.AttendanceRule | None:
    """获取当前生效的考勤规则"""
    return db.query(models.AttendanceRule).filter(
        models.AttendanceRule.is_active == True
    ).first()


def process_attendance(db: Session, user: models.FaceUser) -> dict:
    """
    核心打卡处理逻辑。
    返回 dict：
      action  : "check_in" | "check_out" | "debounce" | "already_complete"
      status  : "on_time" | "late"（仅 check_in 时有）
      late_minutes : int
      record  : AttendanceRecord ORM 对象
      message : str（人类可读提示）
    """
    now = datetime.now()
    today = now.date()

    # ── 防抖：60 秒内同一人不重复触发 ──────────────────────
    recent_threshold = now - timedelta(seconds=CHECKIN_DEBOUNCE_SECONDS)
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
            "message": f"请勿频繁打卡，{CHECKIN_DEBOUNCE_SECONDS} 秒内只记录一次",
        }

    # ── 查询今日记录 ────────────────────────────────────────
    today_record = (
        db.query(models.AttendanceRecord)
        .filter(
            models.AttendanceRecord.user_id == user.id,
            models.AttendanceRecord.date == today,
        )
        .first()
    )

    rule = get_active_rule(db)

    # ══ 情况 1：今日尚未签到 → 执行签到 ═══════════════════
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
            user_id=user.id,
            date=today,
            check_in_time=now,
            status=status,
            late_minutes=late_minutes,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        msg = f"签到成功（{'准时' if status == 'on_time' else f'迟到 {late_minutes} 分钟'}）"
        return {
            "action": "check_in",
            "status": status,
            "late_minutes": late_minutes,
            "record": record,
            "message": msg,
        }

    # ══ 情况 2：已签到但未签退 → 执行签退 ════════════════
    if today_record.check_out_time is None:
        today_record.check_out_time = now
        # 计算在岗时长（小时）
        work_seconds = (now - today_record.check_in_time).total_seconds()
        work_hours = work_seconds / 3600
        db.commit()
        db.refresh(today_record)

        return {
            "action": "check_out",
            "record": today_record,
            "work_hours": round(work_hours, 2),
            "message": f"签退成功，今日在岗 {work_hours:.1f} 小时",
        }

    # ══ 情况 3：今日已完成签到和签退 ═══════════════════════
    return {
        "action": "already_complete",
        "record": today_record,
        "message": "今日已完成签到和签退",
    }