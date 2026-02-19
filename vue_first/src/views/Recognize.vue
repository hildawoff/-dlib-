<template>
  <div class="container">
    <el-card>
      <h2>人脸识别</h2>

      <input type="file" @change="handleFile" />
      <el-button type="primary" @click="recognize">
        开始识别
      </el-button>

      <div v-if="result">
        <p>{{ result.message }}</p>
        <p v-if="result.name">姓名：{{ result.name }}</p>
        <p v-if="result.similarity">
          相似度：{{ result.similarity }}
        </p>
      </div>

      <el-button @click="$router.push('/register')">
        返回注册
      </el-button>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import request from '../api/request'

const file = ref(null)
const result = ref(null)

const handleFile = (e) => {
  file.value = e.target.files[0]
}

const recognize = async () => {
  const formData = new FormData()
  formData.append('file', file.value)

  try {
    const res = await request.post('/recognize', formData)
    result.value = res.data
  } catch {
    alert('识别失败')
  }
}
</script>
