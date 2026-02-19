<template>
  <el-card>
    <h2>识别记录</h2>
    <el-table :data="logs">
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="similarity" label="相似度" />
      <el-table-column prop="status" label="状态" />
      <el-table-column prop="created_at" label="时间" />
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request'

const logs = ref([])

onMounted(async () => {
  const res = await request.get('/logs')
  logs.value = res.data
})
</script>
