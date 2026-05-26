<template>
  <div class="home-page">
    <section class="hero-panel">
      <div>
        <span class="eyebrow">FaceID Dashboard</span>
        <h1>人脸识别考勤管理系统</h1>
        <p>集成人脸登记、实时识别、考勤打卡、数据统计与记录导出，帮助管理员快速完成日常考勤管理。</p>
        <div class="hero-actions">
          <el-button type="primary" @click="$router.push('/attendance')">进入考勤管理</el-button>
          <el-button @click="$router.push('/register')">登记新人脸</el-button>
        </div>
      </div>
      <div class="status-card">
        <div class="status-label">今日日期</div>
        <div class="status-date">{{ todayText }}</div>
        <div class="login-state">{{ userStore.isLoggedIn ? '管理员已登录' : '管理员未登录' }}</div>
      </div>
    </section>

    <section class="stats-grid">
      <div v-for="item in statCards" :key="item.label" :class="['stat-card', item.tone]">
        <div class="stat-value">{{ item.value }}</div>
        <div class="stat-label">{{ item.label }}</div>
      </div>
    </section>

    <section class="content-grid">
      <el-card class="panel-card" shadow="never">
        <div class="panel-title">快捷入口</div>
        <div class="quick-grid">
          <button v-for="item in quickLinks" :key="item.path" class="quick-card" @click="$router.push(item.path)">
            <span class="quick-icon">{{ item.icon }}</span>
            <span class="quick-title">{{ item.title }}</span>
            <span class="quick-desc">{{ item.desc }}</span>
          </button>
        </div>
      </el-card>

      <el-card class="panel-card" shadow="never">
        <div class="panel-title">最近识别记录</div>
        <div v-if="recentLogs.length" class="log-list">
          <div v-for="log in recentLogs" :key="log.id" class="log-item">
            <div>
              <div class="log-name">{{ log.name || 'unknown' }}</div>
              <div class="log-time">{{ formatDateTime(log.created_at) }}</div>
            </div>
            <el-tag :type="log.status === 'success' ? 'success' : 'warning'" size="small">
              {{ log.status === 'success' ? formatSimilarity(log.similarity) : '未匹配' }}
            </el-tag>
          </div>
        </div>
        <div v-else class="empty-box">暂无识别记录</div>
      </el-card>
    </section>

    <section class="flow-panel">
      <div class="panel-title">系统使用流程</div>
      <div class="flow-steps">
        <div v-for="(step, index) in flowSteps" :key="step" class="flow-step">
          <span class="step-num">{{ index + 1 }}</span>
          <span>{{ step }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import request from '../api/request'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

const todayStats = ref({
  total: 0,
  checked_in: 0,
  late: 0,
  absent: 0,
})
const recentLogs = ref([])

const todayText = computed(() => {
  return new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  })
})

const statCards = computed(() => [
  { label: '应到人数', value: todayStats.value.total ?? 0, tone: 'blue' },
  { label: '已签到', value: todayStats.value.checked_in ?? 0, tone: 'green' },
  { label: '迟到人数', value: todayStats.value.late ?? 0, tone: 'orange' },
  { label: '未签到', value: todayStats.value.absent ?? 0, tone: 'red' },
])

const quickLinks = [
  { icon: '录', title: '人脸登记', desc: '录入人员与人脸照片', path: '/register' },
  { icon: '识', title: '摄像头识别', desc: '实时检测并记录身份', path: '/camera' },
  { icon: '勤', title: '考勤管理', desc: '打卡、统计与规则配置', path: '/attendance' },
  { icon: '陌', title: '陌生人记录', desc: '补充未知人员信息', path: '/unknown-users' },
  { icon: '记', title: '识别记录', desc: '查看历史识别日志', path: '/logs' },
  { icon: '表', title: '报表导出', desc: '进入考勤页导出数据', path: '/attendance' },
]

const flowSteps = ['录入人员', '采集人脸', '摄像头识别', '自动考勤', '统计导出']

const fetchDashboard = async () => {
  try {
    const [statsRes, logsRes] = await Promise.all([
      request.get('/attendance/stats/today'),
      request.get('/logs'),
    ])
    todayStats.value = statsRes.data
    recentLogs.value = logsRes.data.slice(0, 5)
  } catch {
    recentLogs.value = []
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

onMounted(() => {
  userStore.init()
  fetchDashboard()
})
</script>

<style scoped>
.home-page {
  max-width: 1160px;
  margin: 0 auto;
}

.hero-panel,
.flow-panel,
.panel-card {
  border-radius: 8px;
  border: 1px solid rgba(37, 53, 68, 0.12);
  box-shadow: 0 10px 30px rgba(31, 46, 59, 0.08);
}

.hero-panel {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 24px;
  padding: 30px;
  background:
    linear-gradient(135deg, rgba(90,154,184,0.12), rgba(255,255,255,0.64)),
    rgba(255,255,255,0.62);
}

.eyebrow {
  color: #5a9ab8;
  font-family: 'Oswald', sans-serif;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

h1 {
  margin: 8px 0 10px;
  color: #1e3245;
  font-size: 32px;
}

.hero-panel p {
  max-width: 680px;
  color: #60717d;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.status-card {
  align-self: stretch;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 22px;
  border-radius: 8px;
  background: #1e3245;
  color: #fff;
}

.status-label {
  color: #9fc5d8;
  font-size: 13px;
}

.status-date {
  margin: 8px 0 14px;
  font-size: 22px;
  font-weight: 800;
}

.login-state {
  display: inline-flex;
  width: fit-content;
  border-radius: 999px;
  padding: 5px 12px;
  color: #dff1f8;
  background: rgba(255,255,255,0.12);
  font-size: 13px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin: 18px 0;
}

.stat-card {
  padding: 18px;
  border-radius: 8px;
  color: #fff;
  box-shadow: 0 8px 22px rgba(31, 46, 59, 0.12);
}

.stat-card.blue { background: linear-gradient(180deg, #3c86ad, #286985); }
.stat-card.green { background: linear-gradient(180deg, #35a66a, #267a4e); }
.stat-card.orange { background: linear-gradient(180deg, #e9983c, #c26b24); }
.stat-card.red { background: linear-gradient(180deg, #df665f, #b9443d); }

.stat-value {
  font-size: 30px;
  font-weight: 800;
  line-height: 1;
}

.stat-label {
  margin-top: 8px;
  font-size: 13px;
  opacity: .9;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(320px, .75fr);
  gap: 18px;
}

.panel-card {
  background: rgba(255,255,255,0.68);
}

.panel-title {
  color: #1e3245;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.quick-card {
  min-height: 118px;
  padding: 16px;
  border: 1px solid rgba(37, 53, 68, 0.1);
  border-radius: 8px;
  background: #f7f8f6;
  text-align: left;
  cursor: pointer;
  transition: transform .16s, border-color .16s, background .16s;
}

.quick-card:hover {
  transform: translateY(-2px);
  border-color: #5a9ab8;
  background: #f2f7f9;
}

.quick-icon {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #fff;
  background: #2f5268;
  font-weight: 800;
}

.quick-title {
  display: block;
  margin-top: 12px;
  color: #1e3245;
  font-weight: 800;
}

.quick-desc {
  display: block;
  margin-top: 5px;
  color: #7c8790;
  font-size: 12px;
}

.log-list {
  display: grid;
  gap: 10px;
}

.log-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  background: #f7f8f6;
  border: 1px solid rgba(37, 53, 68, 0.08);
}

.log-name {
  color: #1e3245;
  font-weight: 800;
}

.log-time {
  color: #8a969c;
  font-size: 12px;
  margin-top: 4px;
}

.empty-box {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #f6f4ef;
  border: 1px dashed #c9c2b2;
  color: #8a8274;
}

.flow-panel {
  margin-top: 18px;
  padding: 22px;
  background: rgba(255,255,255,0.62);
}

.flow-steps {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.flow-step {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 8px;
  background: #f7f8f6;
  color: #1e3245;
  font-weight: 700;
}

.step-num {
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #fff;
  background: #5a9ab8;
  font-size: 12px;
}

:deep(.el-button) {
  border-radius: 6px;
}

@media (max-width: 900px) {
  .hero-panel,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid,
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .flow-steps {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .hero-panel {
    padding: 22px;
  }

  h1 {
    font-size: 26px;
  }

  .stats-grid,
  .quick-grid {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    flex-wrap: wrap;
  }
}
</style>
