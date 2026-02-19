DATABASE_URL = "mysql+pymysql://root:07210721@localhost:3306/face_system"

# 生成和验证令牌（Token）的密钥
SECRET_KEY = "9d8%7a6$8s9&7k8@5z2#9d8%7a6$8s9&7k8@5z2#9d8%7a"
# 指定生成 Token 的加密算法
ALGORITHM = "HS256"
# 指定 Token 的有效期，单位是分钟
ACCESS_TOKEN_EXPIRE_MINUTES = 60
