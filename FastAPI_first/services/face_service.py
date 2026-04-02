# 人脸识别服务
import dlib
import cv2
import numpy as np

# ── 加载预训练模型（需要提前下载对应的 .dat 文件）─────────────────
# 1. 人脸检测器：基于 HOG + 线性分类器，快速检测人脸位置
face_detector = dlib.get_frontal_face_detector()

# 2. 68点人脸关键点检测器：用于定位眼睛、鼻子、嘴巴等位置
shape_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# 3. 人脸识别模型：ResNet 网络，输出 128 维人脸嵌入向量
face_rec_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")


def get_face_encoding(image_bytes: bytes) -> np.ndarray | None:
    """
    从图像二进制数据中提取人脸特征向量（128维嵌入）。

    参数:
        image_bytes: 图像的原始字节数据（如通过 requests 读取的文件内容）

    返回:
        成功则返回 numpy 数组 (128,)，否则返回 None（未检测到人脸或出错）
    """
    # 将字节数据转换为 OpenCV 可处理的 numpy 数组
    np_arr = np.frombuffer(image_bytes, np.uint8)
    # 解码为彩色图像（BGR 格式）
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # 检测图像中的人脸（返回人脸矩形框列表）
    faces = face_detector(img)

    # 未检测到人脸，返回 None
    if len(faces) == 0:
        return None

    # 仅使用检测到的第一张人脸（可根据需求调整）
    # 获取 68 个关键点坐标
    shape = shape_predictor(img, faces[0])
    # 计算 128 维人脸嵌入向量
    face_descriptor = face_rec_model.compute_face_descriptor(img, shape)

    # 转换为 numpy 数组并返回
    return np.array(face_descriptor)