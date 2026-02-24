# 邮件服务模块（fastapi-mail + QQ SMTP）
# 安装依赖：pip install fastapi-mail

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from core.config import (
    MAIL_USERNAME, MAIL_PASSWORD, MAIL_FROM,
    MAIL_FROM_NAME, MAIL_SERVER, MAIL_PORT,
    MAIL_SSL_TLS, MAIL_STARTTLS
)

# ── SMTP 连接配置 ──────────────────────────────────────────
conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_SSL_TLS=MAIL_SSL_TLS,
    MAIL_STARTTLS=MAIL_STARTTLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

fm = FastMail(conf)


# ── 公共发送函数 ───────────────────────────────────────────
async def _send(to: str, subject: str, html: str):
    """底层发送，调用方负责异常处理"""
    message = MessageSchema(
        subject=subject,
        recipients=[to],
        body=html,
        subtype=MessageType.html,
    )
    await fm.send_message(message)


# ── 1. 签到成功 - 准时 ─────────────────────────────────────
async def send_checkin_ontime_email(name: str, email: str, check_in_time: str):
    subject = "✅ 签到成功 - 考勤通知"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;
                border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
      <div style="background:#1e3a5f;padding:20px 28px;">
        <h2 style="color:#fff;margin:0;font-size:20px;">📋 考勤签到通知</h2>
      </div>
      <div style="padding:28px;">
        <p style="font-size:15px;">你好，<strong>{name}</strong>，</p>
        <p style="font-size:15px;">您已于 <strong style="color:#27ae60;">{check_in_time}</strong>
           成功完成今日签到。</p>
        <div style="background:#f0fff4;border-left:4px solid #27ae60;
                    padding:12px 16px;border-radius:4px;margin:16px 0;">
          <span style="color:#27ae60;font-weight:bold;">状态：准时 ✅</span>
        </div>
        <p style="color:#999;font-size:13px;margin-top:24px;">此邮件由系统自动发送，请勿回复。</p>
      </div>
    </div>
    """
    try:
        await _send(email, subject, html)
    except Exception as e:
        print(f"[邮件] 签到邮件发送失败 ({email}): {e}")


# ── 2. 签到成功 - 迟到 ─────────────────────────────────────
async def send_checkin_late_email(name: str, email: str,
                                  check_in_time: str, late_minutes: int,
                                  admin_email: str = None):
    subject = "⚠️ 迟到提醒 - 考勤通知"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;
                border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
      <div style="background:#c0392b;padding:20px 28px;">
        <h2 style="color:#fff;margin:0;font-size:20px;">⚠️ 迟到提醒</h2>
      </div>
      <div style="padding:28px;">
        <p style="font-size:15px;">你好，<strong>{name}</strong>，</p>
        <p style="font-size:15px;">您于 <strong style="color:#c0392b;">{check_in_time}</strong>
           完成签到，今日迟到 <strong style="color:#c0392b;">{late_minutes} 分钟</strong>。</p>
        <div style="background:#fff5f5;border-left:4px solid #c0392b;
                    padding:12px 16px;border-radius:4px;margin:16px 0;">
          <span style="color:#c0392b;font-weight:bold;">状态：迟到 ⚠️ ({late_minutes} 分钟)</span>
        </div>
        <p style="color:#999;font-size:13px;margin-top:24px;">此邮件由系统自动发送，请勿回复。</p>
      </div>
    </div>
    """
    try:
        await _send(email, subject, html)
    except Exception as e:
        print(f"[邮件] 迟到邮件发送失败 ({email}): {e}")

    # 同时通知管理员
    if admin_email:
        admin_subject = f"⚠️ 迟到提醒 - {name} 今日迟到 {late_minutes} 分钟"
        admin_html = f"""
        <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;
                    border:1px solid #f0c0c0;border-radius:8px;padding:24px;">
          <h3 style="color:#c0392b;">员工迟到提醒</h3>
          <p><strong>姓名：</strong>{name}</p>
          <p><strong>签到时间：</strong>{check_in_time}</p>
          <p><strong>迟到时长：</strong>{late_minutes} 分钟</p>
        </div>
        """
        try:
            await _send(admin_email, admin_subject, admin_html)
        except Exception as e:
            print(f"[邮件] 管理员迟到通知发送失败: {e}")


# ── 3. 签退成功 ───────────────────────────────────────────
async def send_checkout_email(name: str, email: str,
                               check_out_time: str, work_hours: float):
    subject = "👋 签退成功 - 考勤通知"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;
                border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
      <div style="background:#2471a3;padding:20px 28px;">
        <h2 style="color:#fff;margin:0;font-size:20px;">📋 考勤签退通知</h2>
      </div>
      <div style="padding:28px;">
        <p style="font-size:15px;">你好，<strong>{name}</strong>，</p>
        <p style="font-size:15px;">您已于 <strong style="color:#2471a3;">{check_out_time}</strong>
           成功完成今日签退。</p>
        <div style="background:#eaf4fb;border-left:4px solid #2471a3;
                    padding:12px 16px;border-radius:4px;margin:16px 0;">
          <span style="color:#2471a3;font-weight:bold;">
            今日在岗时长：{work_hours:.1f} 小时 ⏱️
          </span>
        </div>
        <p style="color:#999;font-size:13px;margin-top:24px;">此邮件由系统自动发送，请勿回复。</p>
      </div>
    </div>
    """
    try:
        await _send(email, subject, html)
    except Exception as e:
        print(f"[邮件] 签退邮件发送失败 ({email}): {e}")