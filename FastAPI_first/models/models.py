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
    name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    face_encoding = Column(LargeBinary)
    is_unknown = Column(Boolean, default=True)
    image_path = Column(String(200), nullable=True)
    join_attendance = Column(Boolean, default=True)


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
    user_id = Column(Integer, ForeignKey("face_users.id"), nullable=False)
    date = Column(Date, nullable=False)                    # 考勤日期
    check_in_time = Column(DateTime, nullable=True)        # 签到时间
    check_out_time = Column(DateTime, nullable=True)       # 签退时间
    status = Column(String(20))                            # on_time / late / absent
    late_minutes = Column(Integer, default=0)              # 迟到分钟数
    checkin_email_sent = Column(Boolean, default=False)    # 签到邮件是否已发
    checkout_email_sent = Column(Boolean, default=False)   # 签退邮件是否已发
    created_at = Column(DateTime, default=datetime.utcnow)