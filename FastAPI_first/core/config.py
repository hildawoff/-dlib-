DATABASE_URL = "mysql+pymysql://root:07210721@localhost:3306/face_system"

# 生成和验证令牌（Token）的密钥
SECRET_KEY = "9d8%7a6$8s9&7k8@5z2#9d8%7a6$8s9&7k8@5z2#9d8%7a"
# 指定生成 Token 的加密算法
ALGORITHM = "HS256"
# 指定 Token 的有效期，单位是分钟
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ===================== QQ邮箱 SMTP 配置 =====================
# 填写你的 QQ 邮箱地址
MAIL_USERNAME = "2134801282@qq.com"
# QQ邮箱授权码（非登录密码）：QQ邮箱 → 设置 → 账户 → SMTP服务 → 生成授权码
MAIL_PASSWORD = "izjoiisffweneagj"
# 发件人显示名和邮箱
MAIL_FROM = "HildaWoff@qq.com"
MAIL_FROM_NAME = "人脸考勤系统"
# QQ 邮箱 SMTP 服务器配置
MAIL_SERVER = "smtp.qq.com"
MAIL_PORT = 465
MAIL_SSL_TLS = True       # QQ邮箱使用 SSL
MAIL_STARTTLS = False     # 与 SSL_TLS 互斥，不能同时为 True

# 打卡防抖间隔（秒）：同一人在此时间内重复出现不重复打卡
CHECKIN_DEBOUNCE_SECONDS = 60
