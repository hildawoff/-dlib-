# 人脸识别服务
import dlib
import cv2
import numpy as np

# 加载模型（你需要下载dlib模型文件）
face_detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
face_rec_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")


def get_face_encoding(image_bytes):
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    faces = face_detector(img)

    if len(faces) == 0:
        return None

    shape = shape_predictor(img, faces[0])
    face_descriptor = face_rec_model.compute_face_descriptor(img, shape)

    return np.array(face_descriptor)
