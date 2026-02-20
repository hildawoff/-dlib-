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

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from core.config import  SECRET_KEY, ALGORITHM
from fastapi import status

from core.auth import hash_password

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


# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败"
        )



@app.post("/admin/register")
def register_admin(admin: schemas.AdminLogin, db: Session = Depends(get_db)):
    existing = db.query(models.Admin).filter(
        models.Admin.username == admin.username
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    new_admin = models.Admin(
        username=admin.username,
        password=hash_password(admin.password)
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {"message": "管理员注册成功"}



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
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    image_bytes = file.file.read()
    encoding = face_service.get_face_encoding(image_bytes)

    if encoding is None:
        raise HTTPException(status_code=400, detail="未检测到人脸")

    users = db.query(models.FaceUser).all()

    best_match = None
    min_dist = 999

    for user in users:
        stored_encoding = np.frombuffer(user.face_encoding)
        dist = np.linalg.norm(stored_encoding - encoding)

        if dist < min_dist:
            min_dist = dist
            best_match = user

    if min_dist < 0.6:
        log = models.RecognitionLog(
            user_id=best_match.id,
            name=best_match.name,
            similarity=float(1 - min_dist),
            status="success"
        )
        db.add(log)
        db.commit()

        return {
            "message": "识别成功",
            "name": best_match.name,
            "similarity": float(1 - min_dist)
        }

    else:
        log = models.RecognitionLog(
            name="unknown",
            similarity=0,
            status="unknown"
        )
        db.add(log)
        db.commit()

        return {"message": "未识别到匹配人员"}


@app.get("/logs")
def get_logs(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    logs = db.query(models.RecognitionLog).order_by(
        models.RecognitionLog.created_at.desc()
    ).all()

    return logs


