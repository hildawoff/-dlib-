<template>
  <div class="recognize-page">
    <section class="page-shell">
      <div class="page-head">
        <span class="eyebrow">Face Match</span>
        <h2>人脸识别</h2>
        <p>上传一张清晰的人脸照片，系统会与已登记人员进行特征比对。</p>
      </div>

      <div class="recognize-grid">
        <el-card class="panel-card" shadow="never">
          <div class="panel-title">上传照片</div>

          <label class="upload-box" for="face-file">
            <input id="face-file" type="file" accept="image/*" @change="handleFile" />
            <template v-if="previewUrl">
              <img :src="previewUrl" alt="人脸预览" />
            </template>
            <template v-else>
              <div class="upload-icon">+</div>
              <div class="upload-text">选择人脸图片</div>
              <div class="upload-tip">支持 jpg、png 等常见图片格式</div>
            </template>
          </label>

          <div class="button-row">
            <el-button type="primary" :disabled="!file || loading" @click="recognize">
              {{ loading ? '识别中...' : '开始识别' }}
            </el-button>
            <el-button @click="$router.push('/register')">返回登记</el-button>
          </div>
        </el-card>

        <el-card class="panel-card result-card" shadow="never">
          <div class="panel-title">识别结果</div>
          <div v-if="result" :class="['result-box', result.name ? 'success' : 'unknown']">
            <div class="result-status">{{ result.message }}</div>
            <div v-if="result.name" class="person-name">{{ result.name }}</div>
            <div v-if="result.similarity" class="similarity">
              相似度 {{ formatSimilarity(result.similarity) }}
            </div>
          </div>
          <div v-else class="empty-result">
            <div class="empty-dot"></div>
            <p>等待上传图片并开始识别</p>
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

const file = ref(null)
const result = ref(null)
const previewUrl = ref('')
const loading = ref(false)

const clearPreview = () => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = ''
}

const handleFile = (e) => {
  const selected = e.target.files?.[0]
  if (!selected) return
  file.value = selected
  result.value = null
  clearPreview()
  previewUrl.value = URL.createObjectURL(selected)
}

const recognize = async () => {
  if (!file.value) {
    ElMessage.warning('请先选择一张人脸图片')
    return
  }

  const formData = new FormData()
  formData.append('file', file.value)

  loading.value = true
  try {
    const res = await request.post('/recognize', formData)
    result.value = res.data
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '识别失败，请换一张清晰照片重试')
  } finally {
    loading.value = false
  }
}

const formatSimilarity = (value) => `${(Number(value) * 100).toFixed(1)}%`

onUnmounted(() => {
  clearPreview()
})
</script>

<style scoped>
.recognize-page {
  max-width: 980px;
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

.recognize-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(280px, 0.95fr);
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

.upload-box {
  min-height: 280px;
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
  height: 280px;
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

.button-row {
  display: flex;
  gap: 12px;
  margin-top: 18px;
}

.result-card :deep(.el-card__body) {
  height: 100%;
}

.result-box,
.empty-result {
  min-height: 280px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 24px;
}

.result-box.success {
  background: #effaf3;
  border: 1px solid #9ed8b2;
}

.result-box.unknown {
  background: #fff8ed;
  border: 1px solid #edc887;
}

.result-status {
  color: #52616b;
  font-size: 14px;
}

.person-name {
  color: #1e3245;
  font-size: 32px;
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

.empty-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #9fb1bc;
  margin-bottom: 12px;
}

@media (max-width: 760px) {
  .page-shell {
    padding: 20px;
  }

  .recognize-grid {
    grid-template-columns: 1fr;
  }

  .button-row {
    flex-wrap: wrap;
  }
}
</style>
