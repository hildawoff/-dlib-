<template>
  <div class="container">
    <el-card>
      <h2>注册人脸</h2>

      <el-input v-model="name" placeholder="姓名" />
      <el-input v-model="email" placeholder="邮箱" />

      <input type="file" @change="handleFile" />

      <el-button type="success" @click="submit">提交注册</el-button>

      <el-button @click="$router.push('/recognize')">
        去识别页面
      </el-button>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import request from '../api/request'

const name = ref('')
const email = ref('')
const file = ref(null)

const handleFile = (e) => {
  file.value = e.target.files[0]
}

const submit = async () => {
  const formData = new FormData()
  formData.append('name', name.value)
  formData.append('email', email.value)
  formData.append('file', file.value)

  try {
    await request.post('/register', formData)
    alert('注册成功')
  } catch {
    alert('注册失败')
  }
}
</script>
