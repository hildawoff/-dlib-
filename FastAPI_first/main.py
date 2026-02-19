from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from core.database import SessionLocal, engine

from models import schemas
from core import auth
from services import face_service
import numpy as np
from core.database import Base
from models import models
import fastapi_cdn_host
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()
fastapi_cdn_host.patch_docs(app)
# uvicorn main:app --reload

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],  # 前端运行地址（精确匹配）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有请求方法（GET/POST等）
    allow_headers=["*"],  # 允许所有请求头（包括Authorization）
)


# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 管理员登录
@app.post("/login")
def login(admin: schemas.AdminLogin, db: Session = Depends(get_db)):
    user = db.query(models.Admin).filter(
        models.Admin.username == admin.username
    ).first()

    if not user or not auth.verify_password(admin.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token}


# 注册人脸
@app.post("/register")
def register_face(
    name: str,
    email: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    image_bytes = file.file.read()
    encoding = face_service.get_face_encoding(image_bytes)

    if encoding is None:
        raise HTTPException(status_code=400, detail="未检测到人脸")

    face_user = models.FaceUser(
        name=name,
        email=email,
        face_encoding=encoding.tobytes()
    )

    db.add(face_user)
    db.commit()
    db.refresh(face_user)

    return {"message": "注册成功", "id": face_user.id}


# 人脸识别
@app.post("/recognize")
def recognize_face(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    image_bytes = file.file.read()
    encoding = face_service.get_face_encoding(image_bytes)

    if encoding is None:
        raise HTTPException(status_code=400, detail="未检测到人脸")

    users = db.query(models.FaceUser).all()

    for user in users:
        stored_encoding = np.frombuffer(user.face_encoding)
        dist = np.linalg.norm(stored_encoding - encoding)

        if dist < 0.6:
            return {
                "message": "识别成功",
                "name": user.name,
                "similarity": float(1 - dist)
            }

    return {"message": "未识别到匹配人员"}
