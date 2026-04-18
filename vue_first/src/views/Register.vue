<template>
  <div class="register-container">
    <el-card class="register-card">
      <h2>注册人脸</h2>

      <el-form label-width="80px">
        <el-form-item label="工号">
          <el-input v-model="employee_id" placeholder="可选" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="name" placeholder="必填" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="email" placeholder="必填" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="department" placeholder="可选" />
        </el-form-item>
      </el-form>

      <div class="face-source-section">
        <div class="section-title">人脸采集方式</div>
        <el-radio-group v-model="faceSource" size="small" class="source-tabs">
          <el-radio-button value="upload">上传图片</el-radio-button>
          <el-radio-button value="camera">摄像头拍照</el-radio-button>
        </el-radio-group>

        <div v-if="faceSource === 'upload'" class="upload-section">
          <input type="file" @change="handleFile" accept="image/*" class="file-input" />
          <div v-if="previewUrl" class="preview-box">
            <img :src="previewUrl" alt="预览" />
          </div>
        </div>

        <div v-else class="camera-section">
          <div class="camera-wrapper">
            <video ref="videoRef" autoplay class="camera-video" />
            <canvas ref="canvasRef" style="display: none" />
          </div>
          <div class="camera-controls">
            <el-button v-if="!cameraActive" type="primary" @click="startCamera">启动摄像头</el-button>
            <el-button v-else type="warning" @click="capturePhoto">拍照采集</el-button>
            <el-button v-if="cameraActive" @click="stopCamera">关闭摄像头</el-button>
          </div>
          <div v-if="capturedPhoto" class="preview-box">
            <img :src="capturedPhoto" alt="已拍照" />
            <div class="tip">已采集人脸照片</div>
          </div>
        </div>
      </div>

      <div class="action-buttons">
        <el-button type="success" @click="submit" :disabled="!canSubmit">提交注册</el-button>
        <el-button @click="$router.push('/recognize')">去识别页面</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import request from '../api/request'
import { ElMessage } from 'element-plus'

const employee_id = ref('')
const name = ref('')
const email = ref('')
const department = ref('')
const faceSource = ref('upload')
const file = ref(null)
const previewUrl = ref('')

const videoRef = ref(null)
const canvasRef = ref(null)
const cameraActive = ref(false)
const capturedPhoto = ref(null)
let stream = null

const canSubmit = computed(() => {
  if (!name.value || !email.value) return false
  if (faceSource.value === 'upload') return file.value
  return capturedPhoto.value
})

const handleFile = (e) => {
  const f = e.target.files[0]
  if (f) {
    file.value = f
    previewUrl.value = URL.createObjectURL(f)
    capturedPhoto.value = null
  }
}

const startCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    videoRef.value.srcObject = stream
    cameraActive.value = true
    capturedPhoto.value = null
  } catch {
    ElMessage.error('无法启动摄像头，请检查权限')
  }
}

const stopCamera = () => {
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }
  cameraActive.value = false
}

const capturePhoto = () => {
  if (!videoRef.value || !canvasRef.value) return

  const video = videoRef.value
  const canvas = canvasRef.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0)

  canvas.toBlob((blob) => {
    if (blob) {
      capturedPhoto.value = URL.createObjectURL(blob)
      file.value = new File([blob], 'capture.jpg', { type: 'image/jpeg' })
      previewUrl.value = null
      stopCamera()
      ElMessage.success('人脸照片已采集')
    }
  }, 'image/jpeg', 0.9)
}

const submit = async () => {
  if (!name.value || !email.value) {
    ElMessage.warning('姓名和邮箱为必填项')
    return
  }
  if (!file.value) {
    ElMessage.warning('请先采集人脸照片')
    return
  }

  const formData = new FormData()
  formData.append('employee_id', employee_id.value)
  formData.append('name', name.value)
  formData.append('email', email.value)
  formData.append('department', department.value)
  formData.append('file', file.value)

  try {
    await request.post('/register', formData)
    ElMessage.success('注册成功')
    employee_id.value = ''
    name.value = ''
    email.value = ''
    department.value = ''
    file.value = null
    previewUrl.value = ''
    capturedPhoto.value = ''
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '注册失败')
  }
}

onUnmounted(() => {
  stopCamera()
})
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  padding: 40px 20px;
}

.register-card {
  width: 100%;
  max-width: 500px;
}

.register-card h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #303133;
}

.face-source-section {
  margin: 20px 0;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.section-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}

.source-tabs {
  margin-bottom: 16px;
}

.upload-section {
  text-align: center;
}

.file-input {
  margin-bottom: 12px;
}

.camera-section {
  text-align: center;
}

.camera-wrapper {
  width: 100%;
  max-width: 320px;
  margin: 0 auto 12px;
  border-radius: 8px;
  overflow: hidden;
  background: #000;
}

.camera-video {
  width: 100%;
  display: block;
}

.camera-controls {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-bottom: 12px;
}

.preview-box {
  max-width: 200px;
  margin: 12px auto 0;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 8px;
}

.preview-box img {
  width: 100%;
  display: block;
  border-radius: 4px;
}

.preview-box .tip {
  text-align: center;
  font-size: 12px;
  color: #67c23a;
  margin-top: 8px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 24px;
}
</style>