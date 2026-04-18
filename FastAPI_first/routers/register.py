from fastapi import Depends, UploadFile, File, HTTPException, Form,APIRouter
from sqlalchemy.orm import Session
from services import face_service
from models import models
from core.get_current_user import get_current_user
from core.database import get_db
from pydantic import BaseModel



router = APIRouter(
    # prefix="/register",
    tags=["register"],
)


class EmployeeUpdate(BaseModel):
    employee_id: str | None = None
    name: str | None = None
    email: str | None = None
    department: str | None = None


@router.post("/register")
def register_face(
    name: str = Form(...),
    email: str = Form(...),
    employee_id: str = Form(None),
    department: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):

    image_bytes = file.file.read()
    encoding = face_service.get_face_encoding(image_bytes)

    if encoding is None:
        raise HTTPException(status_code=400, detail="未检测到人脸")

    face_user = models.FaceUser(
        employee_id=employee_id,
        name=name,
        email=email,
        department=department,
        face_encoding=encoding.tobytes()
    )

    db.add(face_user)
    db.commit()
    db.refresh(face_user)

    return {"message": "注册成功", "id": face_user.id}


@router.put("/employees/{user_id}")
def update_employee(
    user_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """更新员工基本信息"""
    user = db.query(models.FaceUser).filter(models.FaceUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="员工不存在")

    if data.employee_id is not None:
        user.employee_id = data.employee_id
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        user.email = data.email
    if data.department is not None:
        user.department = data.department

    db.commit()
    db.refresh(user)
    return {"message": "更新成功", "data": {
        "id": user.id,
        "employee_id": user.employee_id,
        "name": user.name,
        "email": user.email,
        "department": user.department
    }}


@router.get("/employees")
def get_employees(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取所有员工列表（包含工号、部门）"""
    users = db.query(models.FaceUser).filter(
        models.FaceUser.is_unknown == False
    ).all()
    return [
        {
            "id": u.id,
            "employee_id": u.employee_id,
            "name": u.name,
            "email": u.email,
            "department": u.department,
            "join_attendance": u.join_attendance,
            "image_path": u.image_path,
        }
        for u in users
    ]