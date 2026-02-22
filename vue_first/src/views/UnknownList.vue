<template>
  <el-card>
    <h2>陌生人列表</h2>

    <el-table :data="users">
      <el-table-column prop="id" label="ID" />

      <el-table-column label="照片">
        <template #default="scope">
          <img
            :src="`http://127.0.0.1:8000/${scope.row.image_path}`"
            width="80"
          />
        </template>
      </el-table-column>

      <el-table-column label="填写信息">
        <template #default="scope">
          <el-input
            v-model="scope.row.temp_name"
            placeholder="姓名"
          />
          <el-input
            v-model="scope.row.temp_email"
            placeholder="邮箱"
          />
          <el-button
            type="success"
            @click="save(scope.row)"
          >
            保存
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request'

const users = ref([])

const fetchData = async () => {
  const res = await request.get('/unknown-users')
  users.value = res.data.map(u => ({
    ...u,
    temp_name: '',
    temp_email: ''
  }))
}

const save = async (row) => {
  await request.put(`/users/${row.id}`, {
    name: row.temp_name,
    email: row.temp_email
  })
  fetchData()
}

onMounted(fetchData)
</script>