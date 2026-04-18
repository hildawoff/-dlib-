# 数据库模型
from sqlalchemy import Column, Integer, String, LargeBinary, Time, Date
from core.database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from datetime import datetime


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True)
    password = Column(String(200))


class FaceUser(Base):
    __tablename__ = "face_users"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), nullable=True, index=True)  # 工号
    name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)  # 所属部门
    face_encoding = Column(LargeBinary)
    is_unknown = Column(Boolean, default=False, index=True)
    image_path = Column(String(200), nullable=True)
    join_attendance = Column(Boolean, default=True, index=True)


class RecognitionLog(Base):
    __tablename__ = "recognition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("face_users.id"), nullable=True)
    name = Column(String(50))
    similarity = Column(Float)
    status = Column(String(20))  # success / unknown
    created_at = Column(DateTime, default=datetime.utcnow)


class AttendanceRule(Base):
    """考勤规则表（管理员可配置）"""
    __tablename__ = "attendance_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), default="默认规则")          # 规则名称
    work_start = Column(Time, nullable=False)               # 上班时间 e.g. 09:00:00
    work_end = Column(Time, nullable=False)                 # 下班时间 e.g. 18:00:00
    late_threshold_minutes = Column(Integer, default=10)    # 迟到容忍分钟数
    is_active = Column(Boolean, default=False)              # 是否为当前生效规则（只能一条生效）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AttendanceRecord(Base):
    """考勤记录表"""
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("face_users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)                    # 考勤日期
    check_in_time = Column(DateTime, nullable=True, index=True)        # 签到时间
    check_out_time = Column(DateTime, nullable=True)       # 签退时间
    status = Column(String(20))                            # on_time / late / absent
    late_minutes = Column(Integer, default=0)              # 迟到分钟数
    checkin_email_sent = Column(Boolean, default=False)    # 签到邮件是否已发
    checkout_email_sent = Column(Boolean, default=False)   # 签退邮件是否已发
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemConfig(Base):
    """系统全局配置表"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)         # 配置键
    value = Column(String(200), nullable=False)                   # 配置值
    description = Column(String(200), nullable=True)              # 配置说明
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AwayLog(Base):
    """离岗记录表"""
    __tablename__ = "away_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("face_users.id"), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)                 # 离岗开始时间
    end_time = Column(DateTime, nullable=True)                    # 离岗结束时间（若为空表示仍在离岗）
    duration_minutes = Column(Integer, default=0)                 # 离岗时长（分钟）
    reason = Column(String(200), nullable=True)                   # 离岗原因（可选）
    created_at = Column(DateTime, default=datetime.utcnow)