from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import user

from core.database import engine
from fastapi.staticfiles import StaticFiles
import os

from core.database import Base
from models import models
import fastapi_cdn_host  # 优化 Swagger 文档的 CDN 资源加载
from fastapi.middleware.cors import CORSMiddleware

from core.get_current_user import get_current_user  # 依赖：获取当前登录用户
from core.database import get_db  # 依赖：获取数据库会话
from routers.login import router as login_router  # 登录相关路由
from routers.recognize import router as recognize_router  # 人脸识别路由
from routers.register import router as register_router  # 注册路由
from routers.camera import router as camera_router  # 摄像头管理路由
from routers.attendance import router as attendance_router  # 考勤模块路由

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler  # 后台定时任务调度器
from core.database import SessionLocal
from services.attendance_service import perform_auto_checkout  # 自动签退业务逻辑

# ══════════════ 定时任务配置 ══════════════
# 创建后台调度器实例
scheduler = BackgroundScheduler()

def scheduled_auto_checkout():
    """定时任务包装器：在独立线程中执行自动签退检查"""
    db = SessionLocal()  # 创建新的数据库会话（避免与请求生命周期耦合）
    try:
        print(f"[定时任务] 开始执行自动签退检查... {datetime.now()}")
        perform_auto_checkout(db)  # 调用服务层函数，处理所有应签退的考勤记录
    except Exception as e:
        print(f"[定时任务] 执行出错: {e}")
    finally:
        db.close()  # 确保会话关闭，释放连接

# 每10分钟执行一次自动签退检查（可根据业务需求调整间隔）
scheduler.add_job(scheduled_auto_checkout, 'interval', minutes=10)
scheduler.start()  # 启动调度器

# 程序退出时关闭调度器，避免后台线程残留
import atexit
atexit.register(lambda: scheduler.shutdown())


# 创建所有数据库表（如果表不存在则创建）
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用实例
app = FastAPI()

# uvicorn main:app --reload  # 开发启动命令参考

# ── 跨域中间件配置 ──
# 允许前端开发服务器（Vite 默认端口 5173）访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 优化 Swagger 文档的 CDN 资源，避免国内访问慢的问题
fastapi_cdn_host.patch_docs(app)

# ── 静态文件服务配置 ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")  # 存放上传的人脸图片

# 将 /uploads 路径映射到本地 uploads 目录，供前端访问图片资源
app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads"
)

# ── 路由注册 ──────────────────────────────────
app.include_router(login_router)       # 登录接口
app.include_router(register_router)    # 注册接口
app.include_router(recognize_router)   # 人脸识别接口
app.include_router(camera_router)      # 摄像头管理接口

# 考勤模块路由（/attendance/*）
app.include_router(attendance_router)

# ── 以下为原有接口（保留兼容，建议后续迁移到独立路由文件）──

@app.get("/logs")
def get_logs(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)  # 需要登录才能访问
):
    """获取所有人脸识别日志，按时间倒序排列"""
    logs = db.query(models.RecognitionLog).order_by(
        models.RecognitionLog.created_at.desc()
    ).all()
    return logs


@app.get("/unknown-users")
def get_unknown_users(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取所有标记为“未知”的人脸记录（未关联到具体用户）"""
    users = db.query(models.FaceUser).filter(
        models.FaceUser.is_unknown == True
    ).all()
    return [
        {"id": user.id, "image_path": user.image_path}
        for user in users
    ]


from pydantic import BaseModel

class UpdateUserInfo(BaseModel):
    """更新用户信息请求体模型"""
    name: str
    email: str

@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: UpdateUserInfo,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """更新用户信息（姓名、邮箱），并将该用户标记为非未知用户"""
    user = db.query(models.FaceUser).filter(
        models.FaceUser.id == user_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.name = data.name
    user.email = data.email
    user.is_unknown = False  # 从“未知”状态变为已知用户
    db.commit()
    return {"message": "信息更新成功"}