<template>
  <div class="container">
    <el-card>
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

const employee_id = ref('')
const name = ref('')
const email = ref('')
const department = ref('')
const file = ref(null)

const handleFile = (e) => {
  file.value = e.target.files[0]
}

const submit = async () => {
  if (!name.value || !email.value) {
    alert('姓名和邮箱为必填项')
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
    alert('注册成功')
  } catch {
    alert('注册失败')
  }
}
</script>
