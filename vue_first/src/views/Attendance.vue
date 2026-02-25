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

    <div v-if="activeTab === 'settings'" class="tab-content">
      <!-- 新增：全局设置面板 -->
    <div class="panel" style="margin-top: 20px;">
      <h3 class="panel-title">🛠️ 全局参数设置</h3>
      <el-form label-width="150px" style="max-width: 500px;">
        <el-form-item label="防抖时间(秒)">
          <el-input-number v-model="globalConfig.checkin_debounce_seconds" @change="saveGlobalConfig" />
          <div class="tip">同一人连续打卡的最小间隔，防止刷屏</div>
        </el-form-item>
        <el-form-item label="识别相似度阈值">
          <el-slider v-model="globalConfig.face_similarity_threshold" :min="0" :max="1" :step="0.01" show-input @change="saveGlobalConfig" />
          <div class="tip">值越高识别越严格，建议 0.6-0.8 之间</div>
        </el-form-item>
      </el-form>
    </div>
    </div>




  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import request from '../api/request'
import { ElMessage } from 'element-plus'

// 定义错误码，与后端保持一致
const ERROR_CODE = {
  NO_FACE: 'NO_FACE_DETECTED',
  UNKNOWN_USER: 'UNKNOWN_USER',
  SYSTEM: 'SYSTEM_ERROR'
}


// ── Tab 配置 ─────────────────────────────────────────────
const tabs = [
  { key: 'today',   label: '📷 今日打卡' },
  { key: 'stats',   label: '📊 数据概览' },
  { key: 'rules',   label: '⚙️ 考勤规则' },
  { key: 'members', label: '👥 人员管理' },
  { key: 'settings',   label: '🛠️ 全局参数设置'}
]
const activeTab = ref('today')

// ── 摄像头相关 ────────────────────────────────────────────
const videoRef = ref(null)
const canvasRef = ref(null)
const checkinResult = ref(null)
const isCameraActive = ref(false) // 新增：摄像头状态锁
let stream = null
let captureTimer = null  // 注意：这里不再是 interval ID，而是 timeout ID

// 启动摄像头
const startCamera = async () => {
  if (isCameraActive.value) return // 防止重复启动

  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    videoRef.value.srcObject = stream
    isCameraActive.value = true

    // 等待视频流加载
    await new Promise(resolve => setTimeout(resolve, 500))

    // 开始识别循环
    captureLoop()
  } catch {
    alert('无法启动摄像头，请检查权限')
  }
}

const stopCamera = () => {
  isCameraActive.value = false
  clearTimeout(captureTimer) // 清除 setTimeout
  if (stream) stream.getTracks().forEach(t => t.stop())
  stream = null
}

// 【核心修改】递归循环识别，替代 setInterval
const captureLoop = () => {
  // 如果摄像头已停止，不再继续循环
  if (!isCameraActive.value) return

  captureAndCheckin()
}

const captureAndCheckin = async () => {
  if (!videoRef.value || !canvasRef.value || !isCameraActive.value) return

  const ctx = canvasRef.value.getContext('2d')
  canvasRef.value.width = videoRef.value.videoWidth
  canvasRef.value.height = videoRef.value.videoHeight
  ctx.drawImage(videoRef.value, 0, 0)

  canvasRef.value.toBlob(async (blob) => {
    if (!blob) return

    const form = new FormData()
    form.append('file', blob, 'frame.jpg')

    try {
      // 1. 设置请求超时 (5秒)
      const res = await request.post('/attendance/checkin', form, {
        timeout: 5000,
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      const data = res.data

      // 2. 处理成功打卡
      if (['check_in', 'check_out'].includes(data.action)) {
        checkinResult.value = data
        // playSound('success') // 如果有音效可开启

        // 3秒后自动隐藏气泡
        setTimeout(() => { checkinResult.value = null }, 3000)
        fetchTodayRecords()
      } else {
        // 处理防抖或已完成情况 (静默提示)
        console.log('打卡忽略:', data.message)
      }

    } catch (e) {
      // 3. 【核心修改】使用专门的错误处理函数
      handleCheckinError(e)
    } finally {
      // 无论成功失败，继续下一轮循环
      if (isCameraActive.value) {
        captureTimer = setTimeout(captureLoop, 2000)
      }
    }
  }, 'image/jpeg', 0.85)
}

// 核心改进：精细化错误处理函数
const handleCheckinError = (error) => {
  const status = error.response?.status
  const detail = error.response?.data?.detail

  // 定义默认错误信息
  let message = '系统异常，请稍后重试'
  let code = ERROR_CODE.SYSTEM

  // 如果后端返回了标准 detail 对象
  if (typeof detail === 'object' && detail.message) {
    message = detail.message
    code = detail.code
  } else if (typeof detail === 'string') {
    message = detail
  }

  // 根据不同类型进行反馈
  switch (code) {
    case ERROR_CODE.NO_FACE:
      // 未检测到人脸：通常是因为人在动或侧脸，静默处理，避免频繁打扰
      console.warn('未检测到人脸')
      break

    case ERROR_CODE.UNKNOWN_USER:
      // 陌生人：弹出警告气泡
      showWarningBubble('未识别身份', message)
      // playSound('fail') // 如果有音效可开启
      break

    default:
      // 其他错误：网络错误、服务器错误等
      showWarningBubble('系统提示', message)
      // playSound('fail')

      // 如果是网络超时或服务器错误，增加间隔重试
      if (!status || status >= 500) {
        console.log('服务器异常，延长重试时间...')
        captureTimer = setTimeout(captureLoop, 5000) // 延长到5秒
      }
      break
  }
}

// 辅助函数：显示错误气泡
const showWarningBubble = (title, msg) => {
  checkinResult.value = {
    action: 'error', // 错误状态
    name: title,
    message: msg
  }
  setTimeout(() => { checkinResult.value = null }, 3000)
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


// 新增：全局配置状态
const globalConfig = ref({
  checkin_debounce_seconds: 60,
  face_similarity_threshold: 0.6
})

// 获取配置
const fetchConfig = async () => {
  const res = await request.get('/attendance/config')
  res.data.forEach(item => {
    if (globalConfig.value.hasOwnProperty(item.key)) {
      // 根据类型转换值
      if (item.key === 'face_similarity_threshold') {
        globalConfig.value[item.key] = parseFloat(item.value)
      } else {
        globalConfig.value[item.key] = parseInt(item.value)
      }
    }
  })
}

// 保存配置
const saveGlobalConfig = async () => {
  for (const key in globalConfig.value) {
    await request.put(`/attendance/config/${key}`, {
      value: String(globalConfig.value[key])
    })
  }
  ElMessage.success('参数已更新')
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

/* 新增：错误气泡样式 */
.result-bubble.error {
  background: #fff0f0;
  border: 1.5px solid #ff4d4f;
}
.result-bubble.error .result-name {
  color: #ff4d4f;
}

</style>