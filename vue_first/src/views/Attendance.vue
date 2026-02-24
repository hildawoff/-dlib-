<template>
  <div class="attendance-wrap">

    <!-- ── 顶部 Tab 切换 ── -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- ══════════════════════════════════════════
         Tab 1：今日考勤 + 摄像头打卡
    ══════════════════════════════════════════ -->
    <div v-if="activeTab === 'today'" class="tab-content">
      <div class="two-col">

        <!-- 左栏：摄像头打卡 -->
        <div class="panel">
          <h3 class="panel-title">📷 摄像头打卡</h3>
          <video ref="videoRef" width="100%" autoplay class="video-box" />
          <canvas ref="canvasRef" style="display:none" />

          <div class="btn-row">
            <button class="btn btn-green" @click="startCamera">启动摄像头</button>
            <button class="btn btn-red" @click="stopCamera">停止</button>
          </div>

          <!-- 打卡结果气泡 -->
          <transition name="fade">
            <div v-if="checkinResult" :class="['result-bubble', checkinResult.action]">
              <div class="result-name">{{ checkinResult.name }}</div>
              <div class="result-msg">{{ checkinResult.message }}</div>
              <div class="result-detail" v-if="checkinResult.action === 'check_in'">
                签到时间：{{ checkinResult.check_in_time }}
                <span v-if="checkinResult.status === 'late'" class="late-badge">
                  迟到 {{ checkinResult.late_minutes }} 分钟
                </span>
              </div>
              <div class="result-detail" v-if="checkinResult.action === 'check_out'">
                签退时间：{{ checkinResult.check_out_time }} ｜
                在岗 {{ checkinResult.work_hours }} 小时
              </div>
              <div class="similarity">相似度：{{ (checkinResult.similarity * 100).toFixed(1) }}%</div>
            </div>
          </transition>
        </div>

        <!-- 右栏：今日签到列表 -->
        <div class="panel">
          <h3 class="panel-title">
            📋 今日签到记录
            <button class="refresh-btn" @click="fetchTodayRecords">刷新</button>
          </h3>
          <!-- 今日统计卡片 -->
          <div class="stat-cards" v-if="todayStats">
            <div class="stat-card blue">
              <div class="stat-num">{{ todayStats.total }}</div>
              <div class="stat-label">应到</div>
            </div>
            <div class="stat-card green">
              <div class="stat-num">{{ todayStats.checked_in }}</div>
              <div class="stat-label">已到</div>
            </div>
            <div class="stat-card orange">
              <div class="stat-num">{{ todayStats.late }}</div>
              <div class="stat-label">迟到</div>
            </div>
            <div class="stat-card red">
              <div class="stat-num">{{ todayStats.absent }}</div>
              <div class="stat-label">未到</div>
            </div>
          </div>

          <el-table :data="todayRecords" size="small" style="margin-top:12px">
            <el-table-column prop="name" label="姓名" width="80" />
            <el-table-column prop="check_in_time" label="签到" width="72" />
            <el-table-column prop="check_out_time" label="签退" width="72" />
            <el-table-column prop="status" label="状态" width="70">
              <template #default="s">
                <el-tag
                  :type="s.row.status === 'on_time' ? 'success' : 'danger'"
                  size="small"
                >
                  {{ s.row.status === 'on_time' ? '准时' : `迟到${s.row.late_minutes}分` }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════
         Tab 2：数据概览（ECharts）
    ══════════════════════════════════════════ -->
    <div v-if="activeTab === 'stats'" class="tab-content">
      <div class="charts-grid">

        <!-- 今日出勤率 环形图 -->
        <div class="panel chart-panel">
          <h3 class="panel-title">今日出勤率</h3>
          <div ref="rateChartRef" class="chart-box" />
        </div>

        <!-- 近7天趋势 折线图 -->
        <div class="panel chart-panel">
          <h3 class="panel-title">近 7 天出勤趋势</h3>
          <div ref="trendChartRef" class="chart-box" />
        </div>

        <!-- 近7天迟到统计 柱状图 -->
        <div class="panel chart-panel">
          <h3 class="panel-title">近 7 天迟到统计</h3>
          <div ref="lateChartRef" class="chart-box" />
        </div>

      </div>
    </div>

    <!-- ══════════════════════════════════════════
         Tab 3：考勤规则管理
    ══════════════════════════════════════════ -->
    <div v-if="activeTab === 'rules'" class="tab-content">
      <div class="panel">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <h3 class="panel-title" style="margin:0">⚙️ 考勤规则</h3>
          <button class="btn btn-blue" @click="showRuleForm = true">+ 新建规则</button>
        </div>

        <el-table :data="rules" style="margin-top:16px">
          <el-table-column prop="name" label="规则名称" />
          <el-table-column label="上班时间" width="100">
            <template #default="s">{{ formatTime(s.row.work_start) }}</template>
          </el-table-column>
          <el-table-column label="下班时间" width="100">
            <template #default="s">{{ formatTime(s.row.work_end) }}</template>
          </el-table-column>
          <el-table-column prop="late_threshold_minutes" label="迟到容忍(分)" width="110" />
          <el-table-column label="状态" width="90">
            <template #default="s">
              <el-tag :type="s.row.is_active ? 'success' : 'info'" size="small">
                {{ s.row.is_active ? '生效中' : '未激活' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="s">
              <el-button
                v-if="!s.row.is_active"
                size="small" type="success"
                @click="activateRule(s.row.id)"
              >激活</el-button>
              <el-button
                size="small" type="primary"
                @click="openEditRule(s.row)"
              >编辑</el-button>
              <el-button
                v-if="!s.row.is_active"
                size="small" type="danger"
                @click="deleteRule(s.row.id)"
              >删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 新建/编辑规则弹窗 -->
      <el-dialog
        v-model="showRuleForm"
        :title="editingRule ? '编辑规则' : '新建规则'"
        width="400px"
      >
        <el-form :model="ruleForm" label-width="110px">
          <el-form-item label="规则名称">
            <el-input v-model="ruleForm.name" />
          </el-form-item>
          <el-form-item label="上班时间">
            <el-time-picker
              v-model="ruleForm.work_start"
              format="HH:mm"
              value-format="HH:mm:ss"
              style="width:100%"
            />
          </el-form-item>
          <el-form-item label="下班时间">
            <el-time-picker
              v-model="ruleForm.work_end"
              format="HH:mm"
              value-format="HH:mm:ss"
              style="width:100%"
            />
          </el-form-item>
          <el-form-item label="迟到容忍(分钟)">
            <el-input-number v-model="ruleForm.late_threshold_minutes" :min="0" :max="120" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showRuleForm = false">取消</el-button>
          <el-button type="primary" @click="saveRule">保存</el-button>
        </template>
      </el-dialog>
    </div>

    <!-- ══════════════════════════════════════════
         Tab 4：人员考勤开关
    ══════════════════════════════════════════ -->
    <div v-if="activeTab === 'members'" class="tab-content">
      <div class="panel">
        <h3 class="panel-title">👥 考勤人员管理</h3>
        <p class="tip">在此开启或关闭人员的考勤参与状态。陌生人不可参与考勤。</p>
        <el-table :data="attendanceUsers">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column label="考勤状态" width="100">
            <template #default="s">
              <el-switch
                :model-value="s.row.join_attendance"
                @change="toggleAttendance(s.row)"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import request from '../api/request'

// ── Tab 配置 ─────────────────────────────────────────────
const tabs = [
  { key: 'today',   label: '📷 今日打卡' },
  { key: 'stats',   label: '📊 数据概览' },
  { key: 'rules',   label: '⚙️ 考勤规则' },
  { key: 'members', label: '👥 人员管理' },
]
const activeTab = ref('today')

// ── 摄像头相关 ────────────────────────────────────────────
const videoRef = ref(null)
const canvasRef = ref(null)
const checkinResult = ref(null)
let stream = null
let captureTimer = null

const startCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    videoRef.value.srcObject = stream
    captureTimer = setInterval(captureAndCheckin, 2000) // 每2秒识别一次
  } catch {
    alert('无法启动摄像头，请检查权限')
  }
}

const stopCamera = () => {
  clearInterval(captureTimer)
  if (stream) stream.getTracks().forEach(t => t.stop())
  stream = null
}

const captureAndCheckin = () => {
  if (!videoRef.value || !canvasRef.value) return
  const ctx = canvasRef.value.getContext('2d')
  canvasRef.value.width  = videoRef.value.videoWidth
  canvasRef.value.height = videoRef.value.videoHeight
  ctx.drawImage(videoRef.value, 0, 0)

  canvasRef.value.toBlob(async (blob) => {
    const form = new FormData()
    form.append('file', blob, 'frame.jpg')
    try {
      const res = await request.post('/attendance/checkin', form)
      // 只在有实际打卡动作时显示气泡（防抖/已完成不弹出）
      if (['check_in', 'check_out'].includes(res.data.action)) {
        checkinResult.value = res.data
        setTimeout(() => { checkinResult.value = null }, 5000)
        fetchTodayRecords()
      }
    } catch (e) {
      // 未识别到人脸时不弹出，静默处理
      console.debug('checkin:', e.response?.data?.detail)
    }
  }, 'image/jpeg', 0.8)
}

// ── 今日记录 & 统计 ───────────────────────────────────────
const todayRecords = ref([])
const todayStats   = ref(null)

const fetchTodayRecords = async () => {
  const [recRes, statRes] = await Promise.all([
    request.get('/attendance/records/today'),
    request.get('/attendance/stats/today'),
  ])
  todayRecords.value = recRes.data
  todayStats.value   = statRes.data
}

// ── ECharts ───────────────────────────────────────────────
const rateChartRef  = ref(null)
const trendChartRef = ref(null)
const lateChartRef  = ref(null)
let rateChart, trendChart, lateChart

const initCharts = async () => {
  await nextTick()
  const [statRes, weekRes] = await Promise.all([
    request.get('/attendance/stats/today'),
    request.get('/attendance/stats/weekly'),
  ])
  const stat = statRes.data
  const week = weekRes.data

  // 环形图 - 今日出勤率
  rateChart = echarts.init(rateChartRef.value)
  rateChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['50%', '70%'],
      label: { formatter: '{b}\n{c}人' },
      data: [
        { value: stat.on_time,    name: '准时',  itemStyle: { color: '#27ae60' } },
        { value: stat.late,       name: '迟到',  itemStyle: { color: '#e67e22' } },
        { value: stat.absent,     name: '未到',  itemStyle: { color: '#e74c3c' } },
      ]
    }]
  })

  // 折线图 - 近7天趋势
  trendChart = echarts.init(trendChartRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['已签到', '准时', '迟到'] },
    xAxis: { type: 'category', data: week.map(d => d.date.slice(5)) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '已签到', type: 'line', smooth: true, data: week.map(d => d.checked_in),
        itemStyle: { color: '#2980b9' }, areaStyle: { opacity: 0.1 } },
      { name: '准时',  type: 'line', smooth: true, data: week.map(d => d.on_time),
        itemStyle: { color: '#27ae60' } },
      { name: '迟到',  type: 'line', smooth: true, data: week.map(d => d.late),
        itemStyle: { color: '#e67e22' } },
    ]
  })

  // 柱状图 - 近7天迟到
  lateChart = echarts.init(lateChartRef.value)
  lateChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: week.map(d => d.date.slice(5)) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      name: '迟到人数', type: 'bar',
      data: week.map(d => d.late),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#e67e22' },
          { offset: 1, color: '#f39c12' },
        ])
      },
      barMaxWidth: 40,
    }]
  })
}

// ── 规则管理 ──────────────────────────────────────────────
const rules       = ref([])
const showRuleForm = ref(false)
const editingRule  = ref(null)
const ruleForm    = ref({
  name: '', work_start: '09:00:00', work_end: '18:00:00',
  late_threshold_minutes: 10,
})

const fetchRules = async () => {
  const res = await request.get('/attendance/rules')
  rules.value = res.data
}

const openEditRule = (rule) => {
  editingRule.value = rule
  ruleForm.value = {
    name: rule.name,
    work_start: rule.work_start,
    work_end: rule.work_end,
    late_threshold_minutes: rule.late_threshold_minutes,
  }
  showRuleForm.value = true
}

const saveRule = async () => {
  try {
    if (editingRule.value) {
      await request.put(`/attendance/rules/${editingRule.value.id}`, ruleForm.value)
    } else {
      await request.post('/attendance/rules', ruleForm.value)
    }
    showRuleForm.value = false
    editingRule.value = null
    ruleForm.value = { name: '', work_start: '09:00:00', work_end: '18:00:00', late_threshold_minutes: 10 }
    await fetchRules()
  } catch (e) {
    alert(e.response?.data?.detail || '保存失败')
  }
}

const activateRule = async (id) => {
  await request.post(`/attendance/rules/${id}/activate`)
  await fetchRules()
}

const deleteRule = async (id) => {
  if (!confirm('确认删除此规则？')) return
  await request.delete(`/attendance/rules/${id}`)
  await fetchRules()
}

const formatTime = (t) => t ? t.slice(0, 5) : '--'

// ── 人员管理 ──────────────────────────────────────────────
const attendanceUsers = ref([])

const fetchAttendanceUsers = async () => {
  const res = await request.get('/attendance/users')
  attendanceUsers.value = res.data
}

const toggleAttendance = async (user) => {
  await request.put(`/attendance/users/${user.id}/toggle-attendance`)
  await fetchAttendanceUsers()
}

// ── 生命周期 ──────────────────────────────────────────────
onMounted(() => {
  fetchTodayRecords()
  fetchRules()
  fetchAttendanceUsers()
})

watch(activeTab, (val) => {
  if (val === 'stats') initCharts()
})

onUnmounted(() => {
  stopCamera()
  rateChart?.dispose()
  trendChart?.dispose()
  lateChart?.dispose()
})
</script>

<style scoped>
.attendance-wrap {
  max-width: 1100px;
  margin: 0 auto;
}

/* ── Tab bar ── */
.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  border-bottom: 2px solid #d8d4c8;
  padding-bottom: 0;
}
.tab-btn {
  padding: 8px 20px;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  cursor: pointer;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  color: #666;
  transition: all .2s;
}
.tab-btn.active {
  color: #1e3a5f;
  border-bottom-color: #1e3a5f;
  font-weight: 700;
}
.tab-btn:hover { color: #1e3a5f; }

/* ── Panel ── */
.panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.07);
}
.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: #1e3a5f;
  margin: 0 0 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

/* ── Camera ── */
.video-box {
  border-radius: 6px;
  background: #111;
  display: block;
  width: 100%;
}
.btn-row { display: flex; gap: 10px; margin-top: 12px; }
.btn {
  padding: 8px 18px;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 600;
  transition: opacity .15s;
}
.btn:hover { opacity: .85; }
.btn-green { background: #27ae60; color: #fff; }
.btn-red   { background: #e74c3c; color: #fff; }
.btn-blue  { background: #2980b9; color: #fff; }

/* ── Result bubble ── */
.result-bubble {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 8px;
  font-size: 14px;
}
.result-bubble.check_in  { background: #f0fff4; border: 1.5px solid #27ae60; }
.result-bubble.check_out { background: #eaf4fb; border: 1.5px solid #2980b9; }
.result-name { font-weight: 700; font-size: 16px; color: #1e3a5f; }
.result-msg  { margin: 4px 0; color: #444; }
.result-detail { color: #666; font-size: 13px; }
.late-badge {
  background: #e74c3c; color: #fff;
  padding: 2px 8px; border-radius: 3px;
  font-size: 12px; margin-left: 6px;
}
.similarity { color: #999; font-size: 12px; margin-top: 4px; }

/* ── Stat cards ── */
.stat-cards { display: flex; gap: 10px; margin-bottom: 12px; }
.stat-card {
  flex: 1; text-align: center; padding: 10px;
  border-radius: 6px; color: #fff;
}
.stat-card.blue   { background: #2980b9; }
.stat-card.green  { background: #27ae60; }
.stat-card.orange { background: #e67e22; }
.stat-card.red    { background: #e74c3c; }
.stat-num   { font-size: 24px; font-weight: 700; line-height: 1; }
.stat-label { font-size: 12px; opacity: .85; margin-top: 4px; }

/* ── Charts ── */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
}
.chart-panel { min-height: 300px; }
.chart-box { width: 100%; height: 240px; }

/* ── Misc ── */
.refresh-btn {
  margin-left: auto;
  background: none; border: 1px solid #2980b9;
  color: #2980b9; font-size: 12px;
  padding: 2px 10px; border-radius: 3px; cursor: pointer;
}
.tip { color: #888; font-size: 13px; margin-bottom: 12px; }

/* ── Transitions ── */
.fade-enter-active, .fade-leave-active { transition: opacity .4s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>