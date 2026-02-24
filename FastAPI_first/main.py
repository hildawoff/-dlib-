from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import user

from core.database import engine
from fastapi.staticfiles import StaticFiles
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
from routers.attendance import router as attendance_router


Base.metadata.create_all(bind=engine)

app = FastAPI()

# uvicorn main:app --reload

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_cdn_host.patch_docs(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads"
)

# ── 原有路由（保留，后续可废弃）──────────────────────────
app.include_router(login_router)
app.include_router(register_router)
app.include_router(recognize_router)
app.include_router(camera_router)

# ── 考勤模块路由（/attendance/*）─────────────────────────
app.include_router(attendance_router)


# ── 以下为原有接口（保留兼容，建议后续迁移到独立路由文件）──

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
        {"id": user.id, "image_path": user.image_path}
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