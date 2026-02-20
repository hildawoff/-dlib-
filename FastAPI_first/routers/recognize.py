from models import models
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, APIRouter
from core.database import get_db
from core.get_current_user import get_current_user
import numpy as np
from services import face_service

router = APIRouter(
    # prefix="/recognize",
    tags=["recognize"],
)


@router.post("/recognize")
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