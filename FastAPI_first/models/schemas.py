# Pydantic 数据模型
from pydantic import BaseModel

class AdminLogin(BaseModel):
    username: str
    password: str


class FaceUserCreate(BaseModel):
    name: str
    email: str
