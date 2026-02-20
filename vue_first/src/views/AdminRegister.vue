<template>
  <div class="container">
    <el-card style="width:400px;margin:auto;margin-top:100px">
      <h2>管理员注册</h2>

      <el-input v-model="username" placeholder="用户名" />
      <el-input
        v-model="password"
        type="password"
        placeholder="密码"
      />

      <el-button type="primary" @click="register">
        注册
      </el-button>

      <el-button type="text" @click="$router.push('/')">
        返回登录
      </el-button>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import request from '../api/request'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')

const register = async () => {
  try {
    await request.post('/admin/register', {
      username: username.value,
      password: password.value
    })

    alert('注册成功，请登录')
    router.push('/')
  } catch (error) {
    alert(error.response?.data?.detail || '注册失败')
  }
}
</script>