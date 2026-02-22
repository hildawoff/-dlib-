from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import user

from core.database import engine
from fastapi.staticfiles import StaticFiles  # 导入静态文件服务
import os

from core.database import Base
from models import models
import fastapi_cdn_host
from fastapi.middleware.cors import CORSMiddleware


from core.get_current_user import get_current_user
from core.database import get_db
from routers.login import router as login_router
from routers.recognize import router as recognize_router
from routers.register import router as register_router
from routers.camera import router as camera_router


Base.metadata.create_all(bind=engine)

app = FastAPI()

# uvicorn main:app --reload

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],  # 前端运行地址（精确匹配）
    # allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有请求方法（GET/POST等）
    allow_headers=["*"],  # 允许所有请求头（包括Authorization）
)

fastapi_cdn_host.patch_docs(app)



# ========== 核心配置：映射 /uploads 路径到本地 uploads 文件夹 ==========
# 获取项目根目录（确保路径正确，避免相对路径问题）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# 挂载静态文件：访问 /uploads/xxx.jpg 时，读取本地 UPLOAD_DIR 下的 xxx.jpg
app.mount(
    "/uploads",  # 前端访问的 URL 路径前缀
    StaticFiles(directory=UPLOAD_DIR),  # 本地文件目录
    name="uploads"  # 路由名称（自定义）
)



# 管理员注册
# 管理员登录
app.include_router(login_router)


# 注册人脸
app.include_router(register_router)


# 人脸识别
app.include_router(recognize_router)

# 摄像头专用识别
app.include_router(camera_router)

@app.get("/logs")
def get_logs(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    logs = db.query(models.RecognitionLog).order_by(
        models.RecognitionLog.created_at.desc()
    ).all()

    return logs


@app.get("/unknown-users")
def get_unknown_users(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    users = db.query(models.FaceUser).filter(
        models.FaceUser.is_unknown == True
    ).all()

    return [
        {
            "id": user.id,
            "image_path": user.image_path,
        }
        for user in users
    ]

from pydantic import BaseModel
class UpdateUserInfo(BaseModel):
    name: str
    email: str

@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: UpdateUserInfo,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(models.FaceUser).filter(
        models.FaceUser.id == user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.name = data.name
    user.email = data.email
    user.is_unknown = False

    db.commit()

    return {"message": "信息更新成功"}