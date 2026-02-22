import os
import uuid
from models import models
from sqlalchemy.orm import Session
from fastapi import Depends, UploadFile, File, HTTPException
from core.database import get_db
from core.get_current_user import get_current_user
from fastapi import APIRouter
from services import face_service
import numpy as np

router = APIRouter()



UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/camera_recognize")
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

    THRESHOLD = 0.6

    # ========= 匹配成功 =========
    if best_match and min_dist < THRESHOLD:
        return {
            "message": "识别成功",
            "user_id": best_match.id,
            "name": best_match.name,
            "is_unknown": best_match.is_unknown,
            "similarity": float(1 - min_dist)
        }

    # ========= 自动注册陌生人 =========
    filename = f"{uuid.uuid4()}.jpg"
    image_path = os.path.join(UPLOAD_DIR, filename)

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    new_user = models.FaceUser(
        name=None,
        email=None,
        face_encoding=encoding.tobytes(),
        is_unknown=True,
        image_path=f"uploads/{filename}"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "检测到陌生人，已自动注册",
        "user_id": new_user.id,
        "is_unknown": True
    }