<template>
  <div class="unknown-page">
    <section class="page-shell">
      <div class="page-head">
        <span class="eyebrow">Unknown Faces</span>
        <h2>陌生人记录</h2>
        <p>查看摄像头自动记录的陌生人照片，并补充身份信息转为正式人员。</p>
      </div>

      <el-card class="panel-card" shadow="never">
        <div class="panel-toolbar">
          <div>
            <div class="panel-title">待确认人员</div>
            <div class="panel-subtitle">共 {{ users.length }} 条记录</div>
          </div>
          <el-button type="primary" @click="fetchData">刷新</el-button>
        </div>

        <el-table :data="users" empty-text="暂无陌生人记录">
          <el-table-column prop="id" label="ID" width="80" />

          <el-table-column label="照片" width="140">
            <template #default="scope">
              <div class="face-photo">
                <img :src="`http://127.0.0.1:8000/${scope.row.image_path}`" alt="陌生人照片" />
              </div>
            </template>
          </el-table-column>

          <el-table-column label="补充信息">
            <template #default="scope">
              <div class="inline-form">
                <el-input v-model="scope.row.temp_name" placeholder="姓名" />
                <el-input v-model="scope.row.temp_email" placeholder="邮箱" />
                <el-button type="success" :disabled="!scope.row.temp_name || !scope.row.temp_email" @click="save(scope.row)">
                  保存
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '../api/request'
import { ElMessage } from 'element-plus'

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
  try {
    await request.put(`/users/${row.id}`, {
      name: row.temp_name,
      email: row.temp_email
    })
    ElMessage.success('信息已保存')
    fetchData()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  }
}

onMounted(fetchData)
</script>

<style scoped>
.unknown-page {
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

.panel-card {
  border-radius: 8px;
  border: 1px solid rgba(37, 53, 68, 0.1);
}

.panel-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.panel-title {
  color: #1e3245;
  font-size: 16px;
  font-weight: 700;
}

.panel-subtitle {
  color: #7c8790;
  font-size: 13px;
  margin-top: 4px;
}

.face-photo {
  width: 84px;
  height: 84px;
  border-radius: 8px;
  overflow: hidden;
  background: #101820;
  border: 1px solid #d8dee2;
}

.face-photo img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.inline-form {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) minmax(180px, 1.4fr) auto;
  gap: 10px;
  align-items: center;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
  --el-table-header-bg-color: #f0f4f6;
  --el-table-header-text-color: #1e3245;
  --el-table-row-hover-bg-color: #f2f7f9;
}

:deep(.el-table th.el-table__cell) {
  font-weight: 700;
}

:deep(.el-input__wrapper),
:deep(.el-button) {
  border-radius: 6px;
}

@media (max-width: 720px) {
  .page-shell {
    padding: 20px;
  }

  .panel-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .inline-form {
    grid-template-columns: 1fr;
  }
}
</style>
