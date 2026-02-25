# Pydantic 数据模型
from pydantic import BaseModel
from typing import Optional
from datetime import time, date, datetime


class AdminLogin(BaseModel):
    username: str
    password: str


class FaceUserCreate(BaseModel):
    name: str
    email: str


# ===================== 考勤规则 Schema =====================

class AttendanceRuleCreate(BaseModel):
    """创建考勤规则"""
    name: str
    work_start: time          # e.g. "09:00:00"
    work_end: time            # e.g. "18:00:00"
    late_threshold_minutes: int = 10

    class Config:
        json_encoders = {time: lambda v: v.strftime("%H:%M:%S")}


class AttendanceRuleUpdate(BaseModel):
    """更新考勤规则（所有字段可选）"""
    name: Optional[str] = None
    work_start: Optional[time] = None
    work_end: Optional[time] = None
    late_threshold_minutes: Optional[int] = None
    is_active: Optional[bool] = None

    class Config:
        json_encoders = {time: lambda v: v.strftime("%H:%M:%S")}


class AttendanceRuleOut(BaseModel):
    """返回考勤规则"""
    id: int
    name: str
    work_start: time
    work_end: time
    late_threshold_minutes: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {time: lambda v: v.strftime("%H:%M:%S")}


# ===================== 考勤记录 Schema =====================

class AttendanceRecordOut(BaseModel):
    """返回考勤记录"""
    id: int
    user_id: int
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: Optional[str] = None
    late_minutes: int
    checkin_email_sent: bool
    checkout_email_sent: bool
    created_at: datetime
    # 关联用户信息（通过联表查询补充）
    name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True

# ===================== 系统配置 Schema =====================

class SystemConfigCreate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class SystemConfigOut(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class SystemConfigUpdate(BaseModel):
    value: str
    description: Optional[str] = None