# 数据库模型
from sqlalchemy import Column, Integer, String, LargeBinary
from core.database import Base

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True)
    password = Column(String(200))


class FaceUser(Base):
    __tablename__ = "face_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    email = Column(String(100))
    face_encoding = Column(LargeBinary)  # 存储128维特征
