<template>
  <div class="camera-page">
    <section class="page-shell">
      <div class="page-head">
        <span class="eyebrow">Live Camera</span>
        <h2>实时摄像头识别</h2>
        <p>启动摄像头后，系统会定时采集画面并返回当前识别结果。</p>
      </div>

      <div class="camera-grid">
        <el-card class="panel-card" shadow="never">
          <div class="video-frame">
            <video ref="video" autoplay muted playsinline></video>
            <div v-if="!cameraActive" class="video-placeholder">
              <div class="lens-mark"></div>
              <span>摄像头未启动</span>
            </div>
            <canvas ref="canvas" style="display:none;"></canvas>
          </div>

          <div class="camera-actions">
            <el-button type="primary" :disabled="cameraActive" @click="startCamera">
              启动摄像头
            </el-button>
            <el-button type="danger" :disabled="!cameraActive" @click="stopCamera">
              停止识别
            </el-button>
          </div>
        </el-card>

        <el-card class="panel-card result-panel" shadow="never">
          <div class="panel-title">实时结果</div>
          <div v-if="result" :class="['result-box', result.is_unknown ? 'unknown' : 'success']">
            <div class="status-pill">{{ result.is_unknown ? '陌生人' : '已匹配' }}</div>
            <div class="result-message">{{ result.message }}</div>
            <div v-if="result.name" class="person-name">{{ result.name }}</div>
            <div v-if="result.similarity" class="similarity">
              相似度 {{ formatSimilarity(result.similarity) }}
            </div>
          </div>
          <div v-else class="empty-result">
            <div class="pulse-dot"></div>
            <p>{{ cameraActive ? '正在等待识别结果' : '启动摄像头后显示识别结果' }}</p>
          </div>
        </el-card>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import request from '../api/request'
import { ElMessage } from 'element-plus'

const video = ref(null)
const canvas = ref(null)
const result = ref(null)
const cameraActive = ref(false)
let interval = null
let stream = null

const startCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    video.value.srcObject = stream
    cameraActive.value = true
    result.value = null
    clearInterval(interval)
    interval = setInterval(captureFrame, 1200)
  } catch {
    ElMessage.error('无法启动摄像头，请检查浏览器权限')
  }
}

const stopCamera = () => {
  clearInterval(interval)
  interval = null
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  cameraActive.value = false
}

const captureFrame = async () => {
  if (!video.value || !canvas.value || !cameraActive.value) return
  if (!video.value.videoWidth || !video.value.videoHeight) return

  const ctx = canvas.value.getContext('2d')
  canvas.value.width = video.value.videoWidth
  canvas.value.height = video.value.videoHeight
  ctx.drawImage(video.value, 0, 0)

  canvas.value.toBlob(async (blob) => {
    if (!blob) return
    const formData = new FormData()
    formData.append('file', blob, 'camera-frame.jpg')

    try {
      const res = await request.post('/camera_recognize', formData)
      result.value = res.data
    } catch (error) {
      console.error(error)
    }
  }, 'image/jpeg', 0.86)
}

const formatSimilarity = (value) => `${(Number(value) * 100).toFixed(1)}%`

onUnmounted(() => {
  stopCamera()
})
</script>

<style scoped>
.camera-page {
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

.camera-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
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

.video-frame {
  position: relative;
  aspect-ratio: 16 / 10;
  border-radius: 8px;
  overflow: hidden;
  background: #101820;
  border: 1px solid #223545;
}

.video-frame video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.video-placeholder {
  position: absolute;
  inset: 0;
  color: #aebbc5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.04) 25%, transparent 25%) 0 0 / 20px 20px,
    #101820;
}

.lens-mark {
  width: 62px;
  height: 62px;
  border-radius: 50%;
  border: 2px solid #5a9ab8;
  box-shadow: inset 0 0 0 8px rgba(90, 154, 184, 0.15);
  margin-bottom: 12px;
}

.camera-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.result-box,
.empty-result {
  min-height: 300px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 22px;
}

.result-box.success {
  background: #effaf3;
  border: 1px solid #9ed8b2;
}

.result-box.unknown {
  background: #fff3f0;
  border: 1px solid #efb2a8;
}

.status-pill {
  border-radius: 999px;
  padding: 4px 12px;
  background: rgba(30, 50, 69, 0.08);
  color: #52616b;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 12px;
}

.result-message {
  color: #52616b;
  font-size: 14px;
}

.person-name {
  color: #1e3245;
  font-size: 30px;
  font-weight: 800;
  margin: 10px 0;
}

.similarity {
  color: #2d7a4f;
  font-size: 14px;
  font-weight: 700;
}

.empty-result {
  background: #f6f4ef;
  border: 1px dashed #c9c2b2;
  color: #8a8274;
}

.pulse-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #5a9ab8;
  box-shadow: 0 0 0 8px rgba(90, 154, 184, 0.16);
  margin-bottom: 14px;
}

@media (max-width: 820px) {
  .page-shell {
    padding: 20px;
  }

  .camera-grid {
    grid-template-columns: 1fr;
  }

  .camera-actions {
    flex-wrap: wrap;
  }
}
</style>
