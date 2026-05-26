<template>
  <div class="register-page">
    <section class="page-shell">
      <div class="page-head">
        <span class="eyebrow">Face Enrollment</span>
        <h2>人脸登记</h2>
        <p>录入员工基础信息，并采集一张清晰正脸照片作为后续识别和考勤依据。</p>
      </div>

      <div class="register-grid">
        <el-card class="panel-card" shadow="never">
          <div class="panel-title">员工信息</div>
          <el-form label-width="78px" class="info-form">
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

          <div class="action-buttons">
            <el-button type="success" :disabled="!canSubmit" @click="submit">提交登记</el-button>
            <el-button @click="$router.push('/recognize')">去识别页面</el-button>
          </div>
        </el-card>

        <el-card class="panel-card capture-card" shadow="never">
          <div class="panel-title">人脸采集</div>
          <el-radio-group v-model="faceSource" size="small" class="source-tabs">
            <el-radio-button value="upload">上传图片</el-radio-button>
            <el-radio-button value="camera">摄像头拍照</el-radio-button>
          </el-radio-group>

          <div v-if="faceSource === 'upload'" class="capture-section">
            <label class="upload-box" for="register-face-file">
              <input id="register-face-file" type="file" accept="image/*" @change="handleFile" />
              <template v-if="previewUrl">
                <img :src="previewUrl" alt="人脸预览" />
              </template>
              <template v-else>
                <div class="upload-icon">+</div>
                <div class="upload-text">选择人脸照片</div>
                <div class="upload-tip">建议使用光线充足、无遮挡的正脸照片</div>
              </template>
            </label>
          </div>

          <div v-else class="capture-section">
            <div class="camera-wrapper">
              <video ref="videoRef" autoplay muted playsinline class="camera-video" />
              <div v-if="!cameraActive" class="camera-placeholder">摄像头未启动</div>
              <canvas ref="canvasRef" style="display: none" />
            </div>
            <div class="camera-controls">
              <el-button v-if="!cameraActive" type="primary" @click="startCamera">启动摄像头</el-button>
              <el-button v-else type="warning" @click="capturePhoto">拍照采集</el-button>
              <el-button v-if="cameraActive" @click="stopCamera">关闭摄像头</el-button>
            </div>
          </div>

          <div v-if="capturedPhoto" class="preview-strip">
            <img :src="capturedPhoto" alt="已拍照" />
            <span>已采集人脸照片</span>
          </div>
        </el-card>
      </div>
    </section>
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

const clearObjectUrl = (url) => {
  if (url) URL.revokeObjectURL(url)
}

const handleFile = (e) => {
  const f = e.target.files?.[0]
  if (f) {
    clearObjectUrl(previewUrl.value)
    clearObjectUrl(capturedPhoto.value)
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
    clearObjectUrl(capturedPhoto.value)
    capturedPhoto.value = null
  } catch {
    ElMessage.error('无法启动摄像头，请检查浏览器权限')
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
      clearObjectUrl(capturedPhoto.value)
      capturedPhoto.value = URL.createObjectURL(blob)
      file.value = new File([blob], 'capture.jpg', { type: 'image/jpeg' })
      clearObjectUrl(previewUrl.value)
      previewUrl.value = ''
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
    ElMessage.success('登记成功')
    employee_id.value = ''
    name.value = ''
    email.value = ''
    department.value = ''
    file.value = null
    clearObjectUrl(previewUrl.value)
    clearObjectUrl(capturedPhoto.value)
    previewUrl.value = ''
    capturedPhoto.value = ''
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '登记失败')
  }
}

onUnmounted(() => {
  stopCamera()
  clearObjectUrl(previewUrl.value)
  clearObjectUrl(capturedPhoto.value)
})
</script>

<style scoped>
.register-page {
  max-width: 1040px;
  margin: 0 auto;
}

.page-shell {
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(37, 53, 68, 0.12);
  border-radius: 8px;
  padding: 28px;
  box-shadow: 0 10px 30px rgba(31, 46, 59, 0.08);
}

.page-head {
  margin-bottom: 22px;
}

.eyebrow {
  color: #5a9ab8;
  font-family: 'Oswald', sans-serif;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.page-head h2 {
  margin: 6px 0 8px;
  color: #1e3245;
  font-size: 26px;
}

.page-head p {
  color: #667582;
  font-size: 14px;
}

.register-grid {
  display: grid;
  grid-template-columns: minmax(300px, 0.82fr) minmax(0, 1.18fr);
  gap: 20px;
}

.panel-card {
  border-radius: 8px;
  border: 1px solid rgba(37, 53, 68, 0.1);
}

.panel-title {
  color: #1e3245;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 14px;
}

.info-form {
  padding-top: 4px;
}

.source-tabs {
  margin-bottom: 16px;
}

.capture-section {
  min-height: 310px;
}

.upload-box {
  min-height: 310px;
  border: 2px dashed #b8c3c9;
  border-radius: 8px;
  background: #f7f8f6;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
  transition: border-color .18s, background .18s;
}

.upload-box:hover {
  border-color: #5a9ab8;
  background: #f2f7f9;
}

.upload-box input {
  display: none;
}

.upload-box img {
  width: 100%;
  height: 310px;
  object-fit: contain;
  background: #101820;
}

.upload-icon {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  border: 1px solid #9fb1bc;
  color: #5a7d90;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30px;
  margin-bottom: 12px;
}

.upload-text {
  color: #1e3245;
  font-weight: 700;
}

.upload-tip {
  color: #8a969c;
  font-size: 12px;
  margin-top: 6px;
}

.camera-wrapper {
  position: relative;
  aspect-ratio: 16 / 10;
  border-radius: 8px;
  overflow: hidden;
  background: #101820;
  border: 1px solid #223545;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.camera-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #aebbc5;
  background: #101820;
}

.camera-controls,
.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.preview-strip {
  margin-top: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  background: #effaf3;
  border: 1px solid #9ed8b2;
  color: #2d7a4f;
  font-size: 13px;
  font-weight: 700;
}

.preview-strip img {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  object-fit: cover;
}

@media (max-width: 820px) {
  .page-shell {
    padding: 20px;
  }

  .register-grid {
    grid-template-columns: 1fr;
  }
}
</style>
