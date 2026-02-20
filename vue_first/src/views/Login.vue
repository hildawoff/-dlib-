<template>
  <div class="container">
    <el-card>
      <h2>管理员登录</h2>
      <el-input v-model="username" placeholder="用户名" />
      <el-input v-model="password" type="password" placeholder="密码" />
      <el-button type="primary" @click="login">登录</el-button>
    </el-card>
    <el-button type="text" @click="$router.push('/admin/register')">
  没有账号？去注册
    </el-button>
    <el-button @click="logout">退出登录</el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import request from '../api/request'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')

const login = async () => {
  try {
    const res = await request.post('/login', {
      username: username.value,
      password: password.value
    })

    localStorage.setItem('token', res.data.access_token)
    router.push('/register')
  } catch (error) {
    alert('登录失败')
  }
}
const logout = () => {
  localStorage.removeItem('token')
  router.push('/')
}
</script>
