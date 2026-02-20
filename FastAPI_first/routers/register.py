from fastapi import Depends, UploadFile, File, HTTPException, Form,APIRouter
from sqlalchemy.orm import Session
from services import face_service
from models import models
from core.get_current_user import get_current_user
from core.database import get_db



router = APIRouter(
    # prefix="/register",
    tags=["register"],
)


@router.post("/register")
def register_face(
    name: str = Form(...),
    email: str = Form(...),
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