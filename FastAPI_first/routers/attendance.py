# 考勤路由模块
# 所有接口统一前缀 /attendance，方便与其他接口区分
import numpy as np
from datetime import datetime, date
from calendar import monthrange
from typing import Optional, List

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

import logging  # 导入日志模块
from fastapi import status  # 导入状态码常量

from core.database import get_db
from core.get_current_user import get_current_user
from models import models
from models.schemas import (
    AttendanceRuleCreate, AttendanceRuleUpdate, AttendanceRuleOut,
    AttendanceRecordOut,SystemConfigCreate, SystemConfigOut, SystemConfigUpdate
)
from services import face_service, attendance_service, email_service
from core.config import MAIL_USERNAME  # 管理员邮箱（用作迟到抄送）
import numpy as np

# 【新增】定义错误码常量，方便前端判断
ERROR_NO_FACE = "NO_FACE_DETECTED"
ERROR_UNKNOWN_USER = "UNKNOWN_USER"
ERROR_SYSTEM = "SYSTEM_ERROR"

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 直接定义阈值
SIMILARITY_THRESHOLD = 0.6

router = APIRouter(
    prefix="/attendance",
    tags=["attendance"],
)


# ╔══════════════════════════════════════════════════════════╗
# ║                  考勤打卡接口                            ║
# ╚══════════════════════════════════════════════════════════╝

@router.post("/checkin")
async def attendance_checkin(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    摄像头考勤打卡接口。
    - 上传人脸图像，系统自动识别并判断签到 / 签退。
    - 陌生人（is_unknown=True）不参与考勤。
    - 同一人 60 秒内不重复打卡（防抖）。
    - 打卡后异步发送邮件通知。
    """
    try:
        # 1. 文件格式校验
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": ERROR_SYSTEM, "message": "请上传有效的图片格式"}
            )

        # 2. 文件大小校验 (防止上传过大文件导致内存溢出)
        image_bytes = await file.read()
        max_size = 5 * 1024 * 1024  # 5MB
        if len(image_bytes) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={"code": ERROR_SYSTEM, "message": "图片大小不能超过5MB"}
            )

        # 3. 人脸编码处理 (捕获底层 dlib/face_recognition 库可能的崩溃)
        try:
            encoding = face_service.get_face_encoding(image_bytes)
        except Exception as e:
            logger.error(f"人脸编码库错误: {e}")
            # 这里的错误可能是图片损坏、dlib崩溃等，不应暴露给用户具体堆栈
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": ERROR_SYSTEM, "message": "图像处理失败，请确保照片清晰且光线充足"}
            )

        # 4. 人脸检测结果判断
        if encoding is None:
            # 返回特定的错误码，前端据此判断是否需要重试
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": ERROR_NO_FACE, "message": "未检测到人脸，请正对摄像头"}
            )

        # 5. 只匹配参与考勤的已知用户
        users = (
            db.query(models.FaceUser)
            .filter(
                models.FaceUser.is_unknown == False,
                models.FaceUser.join_attendance == True,
            )
            .all()
        )

        if not users:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": ERROR_SYSTEM, "message": "系统无考勤人员，请先在人员管理中开启考勤"}
            )

        # 3. 【核心优化】构建特征矩阵 & 向量化计算距离
        # 将数据库中的二进制编码转换为 NumPy 矩阵
        # 形状: (用户数 N, 128)
        known_encodings = np.array([
            np.frombuffer(user.face_encoding) for user in users
        ])

        # 将当前人脸编码转换为 (1, 128) 以便广播计算
        current_encoding = np.array([encoding])

        # 一次性计算所有距离 (利用广播机制)
        # 结果形状: (用户数 N, )
        # 计算公式: 欧氏距离
        distances = np.linalg.norm(known_encodings - current_encoding, axis=1)

        # 找到最小距离的索引
        min_index = np.argmin(distances)
        min_dist = distances[min_index]

        # 4. 阈值判断
        if min_dist >= SIMILARITY_THRESHOLD:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": ERROR_UNKNOWN_USER, "message": f"未匹配到考勤人员 (距离: {min_dist:.2f})"}
            )

        best_match = users[min_index]
        similarity = round(1 - min_dist, 4)

        # 4. 执行考勤业务逻辑
        try:
            result = attendance_service.process_attendance(db, best_match)
        except Exception as e:
            logger.error(f"数据库操作失败: {e}")
            # 数据库错误是严重错误，需要回滚（service层处理）并提示用户
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": ERROR_SYSTEM, "message": "考勤记录保存失败，请稍后重试"}
            )

        action = result["action"]

        # 5. 防抖直接返回
        if action == "debounce":
            return {
                "message": result["message"],
                "name": best_match.name,
                "similarity": similarity,
            }

        if action == "already_complete":
            return {
                "message": result["message"],
                "name": best_match.name,
                "similarity": similarity,
            }

        record: models.AttendanceRecord = result["record"]

        # 6. 异步发送邮件（不阻塞响应）
        user_email = best_match.email
        if user_email:
            if action == "check_in":
                check_in_str = record.check_in_time.strftime("%Y-%m-%d %H:%M:%S")
                if result["status"] == "on_time":
                    background_tasks.add_task(
                        email_service.send_checkin_ontime_email,
                        best_match.name, user_email, check_in_str,
                    )
                else:
                    background_tasks.add_task(
                        email_service.send_checkin_late_email,
                        best_match.name, user_email, check_in_str,
                        result["late_minutes"], MAIL_USERNAME,  # 管理员邮箱抄送
                    )
                # 标记邮件已发送
                record.checkin_email_sent = True
                db.commit()

            elif action == "check_out":
                check_out_str = record.check_out_time.strftime("%Y-%m-%d %H:%M:%S")
                work_hours = result.get("work_hours", 0)
                background_tasks.add_task(
                    email_service.send_checkout_email,
                    best_match.name, user_email, check_out_str, work_hours,
                )
                record.checkout_email_sent = True
                db.commit()

        # 7. 构建响应
        response = {
            "message": result["message"],
            "name": best_match.name,
            "similarity": similarity,
            "action": action,
            "record_id": record.id,
        }
        if action == "check_in":
            response["status"] = result["status"]
            response["late_minutes"] = result["late_minutes"]
            response["check_in_time"] = record.check_in_time.strftime("%H:%M:%S")
        elif action == "check_out":
            response["work_hours"] = result.get("work_hours", 0)
            response["check_out_time"] = record.check_out_time.strftime("%H:%M:%S")

        return response
    except HTTPException:
        raise  # 抛出我们手动设定的异常
    except Exception as e:
        logger.exception("未知系统错误")  # 记录完整堆栈
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": ERROR_SYSTEM, "message": "系统繁忙，请稍后再试"}
        )


# ╔══════════════════════════════════════════════════════════╗
# ║                  考勤记录查询接口                        ║
# ╚══════════════════════════════════════════════════════════╝

@router.get("/records", response_model=List[AttendanceRecordOut])
def get_attendance_records(
    query_date: Optional[date] = Query(None, description="按日期筛选 e.g. 2024-06-01"),
    user_id: Optional[int] = Query(None, description="按人员ID筛选"),
    status: Optional[str] = Query(None, description="按状态筛选: on_time / late / absent"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """获取考勤记录列表，支持多条件筛选分页"""
    q = (
        db.query(
            models.AttendanceRecord,
            models.FaceUser.name,
            models.FaceUser.email,
        )
        .join(models.FaceUser, models.AttendanceRecord.user_id == models.FaceUser.id)
    )

    if query_date:
        q = q.filter(models.AttendanceRecord.date == query_date)
    if user_id:
        q = q.filter(models.AttendanceRecord.user_id == user_id)
    if status:
        q = q.filter(models.AttendanceRecord.status == status)

    rows = (
        q.order_by(models.AttendanceRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = []
    for record, name, email in rows:
        item = AttendanceRecordOut.model_validate(record)
        item.name = name
        item.email = email
        result.append(item)
    return result


@router.get("/records/export")
def get_records_for_export(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    user_id: Optional[int] = Query(None, description="按人员ID筛选(空则查全部)"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """考勤记录导出接口，支持日期范围和人员筛选"""
    q = (
        db.query(
            models.AttendanceRecord,
            models.FaceUser.name,
            models.FaceUser.email,
        )
        .join(models.FaceUser, models.AttendanceRecord.user_id == models.FaceUser.id)
    )

    if start_date:
        q = q.filter(models.AttendanceRecord.date >= start_date)
    if end_date:
        q = q.filter(models.AttendanceRecord.date <= end_date)
    if user_id:
        q = q.filter(models.AttendanceRecord.user_id == user_id)

    rows = q.order_by(models.AttendanceRecord.date.desc(), models.FaceUser.name).all()

    result = []
    for record, name, email in rows:
        result.append({
            "id": record.id,
            "user_id": record.user_id,
            "name": name,
            "email": email,
            "date": str(record.date),
            "check_in_time": record.check_in_time.strftime("%Y-%m-%d %H:%M:%S") if record.check_in_time else None,
            "check_out_time": record.check_out_time.strftime("%Y-%m-%d %H:%M:%S") if record.check_out_time else None,
            "status": record.status,
            "late_minutes": record.late_minutes,
        })
    return result


@router.get("/records/monthly")
def get_monthly_stats(
    year: int = Query(None, description="年份 e.g. 2024"),
    month: Optional[int] = Query(None, description="月份 1-12 (空则查全年)"),
    user_id: Optional[int] = Query(None, description="人员ID (空则查全部)"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """月报/年报统计，支持按人员筛选"""
    if month:
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

    base_query = db.query(models.AttendanceRecord).join(
        models.FaceUser, models.AttendanceRecord.user_id == models.FaceUser.id
    ).filter(
        models.AttendanceRecord.date >= start_date,
        models.AttendanceRecord.date <= end_date,
    )

    if user_id:
        base_query = base_query.filter(models.AttendanceRecord.user_id == user_id)

    records = base_query.all()

    user_stats = {}
    for rec in records:
        uid = rec.user_id
        if uid not in user_stats:
            user_stats[uid] = {
                "user_id": uid,
                "name": "",
                "total_days": set(),
                "check_in_count": 0,
                "check_out_count": 0,
                "on_time_count": 0,
                "late_count": 0,
                "absent_count": 0,
                "total_late_minutes": 0,
            }

        user_stats[uid]["total_days"].add(rec.date)
        if rec.check_in_time:
            user_stats[uid]["check_in_count"] += 1
            if rec.status == "on_time":
                user_stats[uid]["on_time_count"] += 1
            elif rec.status == "late":
                user_stats[uid]["late_count"] += 1
                user_stats[uid]["total_late_minutes"] += rec.late_minutes

        if rec.check_out_time:
            user_stats[uid]["check_out_count"] += 1

    user_ids = list(user_stats.keys())
    if user_ids:
        users = db.query(models.FaceUser).filter(
            models.FaceUser.id.in_(user_ids)
        ).all()
        for u in users:
            if u.id in user_stats:
                user_stats[u.id]["name"] = u.name
                user_stats[u.id]["email"] = u.email

    total_work_days = len(user_stats[list(user_ids)[0]]["total_days"]) if user_ids else 0

    result = []
    for uid, stat in user_stats.items():
        total_days = len(stat["total_days"])
        result.append({
            "user_id": uid,
            "name": stat["name"],
            "email": stat.get("email", ""),
            "total_days": total_days,
            "check_in_count": stat["check_in_count"],
            "check_out_count": stat["check_out_count"],
            "on_time_count": stat["on_time_count"],
            "late_count": stat["late_count"],
            "absent_count": stat["absent_count"],
            "total_late_minutes": stat["total_late_minutes"],
            "attendance_rate": round(stat["check_in_count"] / total_days * 100, 1) if total_days > 0 else 0,
        })

    result.sort(key=lambda x: x["name"])
    return result


@router.get("/records/today")
def get_today_records(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """获取今日所有考勤记录（含用户信息）"""
    today = datetime.now().date()
    rows = (
        db.query(
            models.AttendanceRecord,
            models.FaceUser.name,
            models.FaceUser.email,
        )
        .join(models.FaceUser, models.AttendanceRecord.user_id == models.FaceUser.id)
        .filter(models.AttendanceRecord.date == today)
        .order_by(models.AttendanceRecord.check_in_time.asc())
        .all()
    )

    return [
        {
            "id": rec.id,
            "user_id": rec.user_id,
            "name": name,
            "email": email,
            "date": str(rec.date),
            "check_in_time": rec.check_in_time.strftime("%H:%M:%S") if rec.check_in_time else None,
            "check_out_time": rec.check_out_time.strftime("%H:%M:%S") if rec.check_out_time else None,
            "status": rec.status,
            "late_minutes": rec.late_minutes,
        }
        for rec, name, email in rows
    ]


# ╔══════════════════════════════════════════════════════════╗
# ║               考勤规则管理接口（管理员）                  ║
# ╚══════════════════════════════════════════════════════════╝

@router.get("/rules", response_model=List[AttendanceRuleOut])
def get_rules(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """获取所有考勤规则"""
    return db.query(models.AttendanceRule).order_by(models.AttendanceRule.id).all()


@router.post("/rules", response_model=AttendanceRuleOut)
def create_rule(
    data: AttendanceRuleCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    新建考勤规则。
    新建时默认不激活，需手动调用激活接口。
    """
    rule = models.AttendanceRule(**data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=AttendanceRuleOut)
def update_rule(
    rule_id: int,
    data: AttendanceRuleUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """更新考勤规则（部分更新）"""
    rule = db.query(models.AttendanceRule).filter(
        models.AttendanceRule.id == rule_id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    updates = data.model_dump(exclude_unset=True)

    # 如果要激活此规则，先停用其他所有规则
    if updates.get("is_active") is True:
        db.query(models.AttendanceRule).filter(
            models.AttendanceRule.id != rule_id
        ).update({"is_active": False})

    for key, value in updates.items():
        setattr(rule, key, value)

    rule.updated_at = datetime.now()
    db.commit()
    db.refresh(rule)
    return rule


@router.post("/rules/{rule_id}/activate", response_model=AttendanceRuleOut)
def activate_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """激活指定规则（同时停用其他所有规则，保证只有一条生效）"""
    rule = db.query(models.AttendanceRule).filter(
        models.AttendanceRule.id == rule_id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    # 停用其他规则
    db.query(models.AttendanceRule).filter(
        models.AttendanceRule.id != rule_id
    ).update({"is_active": False})

    rule.is_active = True
    rule.updated_at = datetime.now()
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """删除考勤规则（已激活的规则不允许删除）"""
    rule = db.query(models.AttendanceRule).filter(
        models.AttendanceRule.id == rule_id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    if rule.is_active:
        raise HTTPException(status_code=400, detail="不能删除当前生效的规则，请先激活其他规则")

    db.delete(rule)
    db.commit()
    return {"message": "规则已删除"}


# ╔══════════════════════════════════════════════════════════╗
# ║               人员考勤状态管理接口                       ║
# ╚══════════════════════════════════════════════════════════╝

@router.put("/users/{user_id}/toggle-attendance")
def toggle_user_attendance(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """开启 / 关闭指定人员的考勤参与（陌生人始终不可开启）"""
    user = db.query(models.FaceUser).filter(models.FaceUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.is_unknown:
        raise HTTPException(status_code=400, detail="陌生人不可参与考勤")

    user.join_attendance = not user.join_attendance
    db.commit()
    return {
        "user_id": user.id,
        "name": user.name,
        "join_attendance": user.join_attendance,
        "message": f"{'已开启' if user.join_attendance else '已关闭'}考勤",
    }


@router.get("/users")
def get_attendance_users(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """获取所有已知人员及其考勤状态（供管理员管理）"""
    users = (
        db.query(models.FaceUser)
        .filter(models.FaceUser.is_unknown == False)
        .all()
    )
    return [
        {
            "id": u.id,
            "employee_id": u.employee_id,
            "name": u.name,
            "email": u.email,
            "department": u.department,
            "join_attendance": u.join_attendance,
            "image_path": u.image_path,
        }
        for u in users
    ]


# ╔══════════════════════════════════════════════════════════╗
# ║               统计数据接口（为大屏准备）                  ║
# ╚══════════════════════════════════════════════════════════╝

@router.get("/stats/today")
def stats_today(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """今日考勤统计：总人数 / 已签到 / 迟到 / 未签到"""
    today = datetime.now().date()

    total = db.query(models.FaceUser).filter(
        models.FaceUser.is_unknown == False,
        models.FaceUser.join_attendance == True,
    ).count()

    checked_in = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.date == today
    ).count()

    late = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.date == today,
        models.AttendanceRecord.status == "late",
    ).count()

    return {
        "total": total,
        "checked_in": checked_in,
        "on_time": checked_in - late,
        "late": late,
        "absent": max(total - checked_in, 0),
        "attendance_rate": round(checked_in / total * 100, 1) if total > 0 else 0,
    }


@router.get("/stats/weekly")
def stats_weekly(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """近 7 天每日签到人数（折线图数据）"""
    from datetime import timedelta
    today = datetime.now().date()
    result = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.date == day
        ).count()
        late_count = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.date == day,
            models.AttendanceRecord.status == "late",
        ).count()
        result.append({
            "date": str(day),
            "checked_in": count,
            "late": late_count,
            "on_time": count - late_count,
        })
    return result


# ╔══════════════════════════════════════════════════════════╗
# ║               系统配置管理接口 (管理员)                  ║
# ╚══════════════════════════════════════════════════════════╝

@router.get("/config", response_model=List[SystemConfigOut])
def get_configs(
        db: Session = Depends(get_db),
        current_user: str = Depends(get_current_user),
):
    """获取所有系统配置"""
    return db.query(models.SystemConfig).all()


@router.put("/config/{config_key}")
def update_config(
        config_key: str,
        data: SystemConfigUpdate,
        db: Session = Depends(get_db),
        current_user: str = Depends(get_current_user),
):
    """更新系统配置（如防抖时间、相似度阈值）"""
    config = db.query(models.SystemConfig).filter(
        models.SystemConfig.key == config_key
    ).first()
    if not config:
        # 如果不存在则创建
        config = models.SystemConfig(key=config_key, value=data.value, description=data.description)
        db.add(config)
    else:
        config.value = data.value
        if data.description:
            config.description = data.description

    db.commit()
    db.refresh(config)
    return {"message": "配置更新成功", "data": config}