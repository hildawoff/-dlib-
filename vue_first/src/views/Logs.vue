<template>
  <div class="logs-page">
    <section class="page-shell">
      <div class="page-head">
        <span class="eyebrow">Recognition Logs</span>
        <h2>识别记录</h2>
        <p>按时间查看系统识别结果，包括匹配人员、相似度和识别状态。</p>
      </div>

      <el-card class="panel-card" shadow="never">
        <div class="panel-toolbar">
          <div>
            <div class="panel-title">识别日志</div>
            <div class="panel-subtitle">共 {{ logs.length }} 条记录</div>
          </div>
          <el-button type="primary" @click="fetchLogs">刷新</el-button>
        </div>

        <el-table :data="logs" empty-text="暂无识别记录">
          <el-table-column prop="name" label="姓名" min-width="120">
            <template #default="scope">
              <span :class="['name-text', scope.row.status === 'unknown' ? 'muted' : '']">
                {{ scope.row.name || 'unknown' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="相似度" width="120">
            <template #default="scope">
              {{ formatSimilarity(scope.row.similarity) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.status === 'success' ? 'success' : 'warning'" size="small">
                {{ scope.row.status === 'success' ? '识别成功' : '未匹配' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="时间" min-width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.created_at) }}
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

const logs = ref([])

const fetchLogs = async () => {
  try {
    const res = await request.get('/logs')
    logs.value = res.data
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '获取识别记录失败')
  }
}

const formatSimilarity = (value) => {
  const num = Number(value)
  if (!Number.isFinite(num) || num <= 0) return '--'
  return `${(num * 100).toFixed(1)}%`
}

const formatDateTime = (value) => {
  if (!value) return '--'
  return value.replace('T', ' ').slice(0, 19)
}

onMounted(fetchLogs)
</script>

<style scoped>
.logs-page {
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

.name-text {
  color: #1e3245;
  font-weight: 700;
}

.name-text.muted {
  color: #8a8274;
  font-weight: 600;
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

:deep(.el-table .el-table__cell) {
  padding: 10px 0;
}

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
}
</style>
