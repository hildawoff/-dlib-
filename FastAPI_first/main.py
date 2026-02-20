from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from core.database import engine


from core.database import Base
from models import models
import fastapi_cdn_host
from fastapi.middleware.cors import CORSMiddleware


from core.get_current_user import get_current_user
from core.database import get_db
from routers.login import router as login_router
from routers.recognize import router as recognize_router
from routers.register import router as register_router


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



# 管理员注册
# 管理员登录
app.include_router(login_router)


# 注册人脸
app.include_router(register_router)


# 人脸识别
app.include_router(recognize_router)



@app.get("/logs")
def get_logs(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    logs = db.query(models.RecognitionLog).order_by(
        models.RecognitionLog.created_at.desc()
    ).all()

    return logs