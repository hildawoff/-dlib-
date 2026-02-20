# 管理员登录与注册
from core import auth
from models import models
from models import schemas
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Form, APIRouter
from core.database import get_db
from core.auth import hash_password

router = APIRouter(
    # prefix="/login",
    tags=["login"],
)


# 管理员登录
@router.post("/login")
def login(admin: schemas.AdminLogin, db: Session = Depends(get_db)):
    user = db.query(models.Admin).filter(
        models.Admin.username == admin.username
    ).first()

    if not user or not auth.verify_password(admin.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token}



# 管理员注册
@router.post("/admin/register")
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
