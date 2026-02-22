# 数据库模型
from sqlalchemy import Column, Integer, String, LargeBinary
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


class RecognitionLog(Base):
    __tablename__ = "recognition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("face_users.id"), nullable=True)
    name = Column(String(50))
    similarity = Column(Float)
    status = Column(String(20))  # success / unknown
    created_at = Column(DateTime, default=datetime.utcnow)