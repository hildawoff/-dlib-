<template>
  <div class="container">
    <el-card>
      <h2>实时摄像头识别</h2>

      <video ref="video" width="400" autoplay></video>
      <canvas ref="canvas" style="display:none;"></canvas>

      <el-button type="primary" @click="startCamera">
        启动摄像头
      </el-button>

      <el-button type="danger" @click="stopCamera">
        停止摄像头
      </el-button>

      <div v-if="result">
        <p>{{ result.message }}</p>
        <p v-if="result.name">姓名：{{ result.name }}</p>
        <p v-if="result.similarity">
          相似度：{{ result.similarity }}
        </p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import request from '../api/request'

const video = ref(null)
const canvas = ref(null)
const result = ref(null)
let interval = null
let stream = null

const startCamera = async () => {
  stream = await navigator.mediaDevices.getUserMedia({ video: true })
  video.value.srcObject = stream

  interval = setInterval(captureFrame, 1000)
}

const stopCamera = () => {
  clearInterval(interval)
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
  }
}

const captureFrame = async () => {
  const ctx = canvas.value.getContext('2d')
  canvas.value.width = video.value.videoWidth
  canvas.value.height = video.value.videoHeight
  ctx.drawImage(video.value, 0, 0)

  canvas.value.toBlob(async (blob) => {
    const formData = new FormData()
    formData.append('file', blob)

    try {
      const res = await request.post('/recognize', formData)
      result.value = res.data
    } catch (error) {
      console.error(error)
    }
  }, 'image/jpeg')
}

onUnmounted(() => {
  stopCamera()
})
</script>
