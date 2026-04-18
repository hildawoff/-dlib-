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
      <!-- 原有内容保持不变 -->
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
      <!-- 原有内容保持不变 -->
      <div class="charts-grid">
        <div class="panel chart-panel">
          <h3 class="panel-title">今日出勤率</h3>
          <div ref="rateChartRef" class="chart-box" />
        </div>
        <div class="panel chart-panel">
          <h3 class="panel-title">近 7 天出勤趋势</h3>
          <div ref="trendChartRef" class="chart-box" />
        </div>
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
      <!-- 原有内容保持不变 -->
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
        <p class="tip">在此管理人员的考勤参与状态和基本信息。</p>
        <el-table :data="attendanceUsers">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="employee_id" label="工号" width="100" />
          <el-table-column prop="name" label="姓名" width="100" />
          <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
          <el-table-column prop="department" label="部门" width="120" />
          <el-table-column label="考勤状态" width="100">
            <template #default="s">
              <el-switch
                :model-value="s.row.join_attendance"
                @change="toggleAttendance(s.row)"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="s">
              <el-button size="small" type="primary" @click="openEditEmployee(s.row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-dialog v-model="showEditDialog" title="编辑员工信息" width="400px">
        <el-form :model="editForm" label-width="80px">
          <el-form-item label="工号">
            <el-input v-model="editForm.employee_id" />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="editForm.name" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="editForm.email" />
          </el-form-item>
          <el-form-item label="部门">
            <el-input v-model="editForm.department" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="saveEmployee">保存</el-button>
        </template>
      </el-dialog>
    </div>

    <!-- ══════════════════════════════════════════
         Tab 5：全局参数设置
    ══════════════════════════════════════════ -->
    <div v-if="activeTab === 'settings'" class="tab-content">
      <!-- 原有内容保持不变 -->
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

    <!-- ══════════════════════════════════════════
         Tab 6：记录导出（按日期筛选并导出 CSV）
    ══════════════════════════════════════════ -->
    <div v-if="activeTab === 'export'" class="tab-content">
      <div class="panel">
        <h3 class="panel-title">📤 考勤记录导出</h3>

        <div class="export-mode-bar">
          <el-radio-group v-model="exportMode" size="small">
            <el-radio-button value="daily">日报</el-radio-button>
            <el-radio-button value="monthly">月报</el-radio-button>
          </el-radio-group>
        </div>

        <div class="export-filter">
          <template v-if="exportMode === 'daily'">
            <span class="filter-label">日期范围：</span>
            <el-date-picker
              v-model="exportDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD DD"
              value-format="YYYY-MM-DD"
              style="width: 300px;"
            />
          </template>
          <template v-else>
            <span class="filter-label">年份：</span>
            <el-input-number v-model="exportYear" :min="2020" :max="2030" :controls="false" style="width: 90px;" />
            <span class="filter-label" style="margin-left: 16px;">月份：</span>
            <el-select v-model="exportMonth" placeholder="全年" clearable style="width: 100px;">
              <el-option v-for="m in 12" :key="m" :label="m + '月'" :value="m" />
            </el-select>
          </template>

          <span class="filter-label" style="margin-left: 16px;">人员：</span>
          <el-select v-model="exportUserId" placeholder="全部成员" clearable style="width: 140px;">
            <el-option v-for="u in allUsers" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>

          <button class="btn btn-blue" style="margin-left: 12px;" @click="fetchExportData">查询</button>
          <button class="btn btn-green" @click="handleExport" :disabled="!exportData.length">导出 CSV</button>
        </div>

        <template v-if="exportMode === 'daily'">
          <el-table :data="exportData" size="small" style="width: 100%; margin-top: 16px;" max-height="400">
            <el-table-column prop="date" label="日期" width="100" />
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
            <el-table-column prop="check_in_time" label="签到时间" width="140">
              <template #default="scope">
                {{ scope.row.check_in_time ? formatTime(scope.row.check_in_time) : '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="check_out_time" label="签退时间" width="140">
              <template #default="scope">
                {{ scope.row.check_out_time ? formatTime(scope.row.check_out_time) : '--' }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'on_time' ? 'success' : 'danger'" size="small">
                  {{ scope.row.status === 'on_time' ? '准时' : scope.row.status === 'late' ? `迟到${scope.row.late_minutes}分` : scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="late_minutes" label="迟到(分)" width="80" />
          </el-table>
          <div v-if="exportData.length === 0 && hasSearched" style="text-align: center; color: #999; padding: 20px;">
            暂无考勤记录
          </div>
        </template>

        <template v-else>
          <el-table :data="exportData" size="small" style="width: 100%; margin-top: 16px;">
            <el-table-column prop="name" label="姓名" width="100" />
            <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
            <el-table-column prop="total_days" label="应到天数" width="90" />
            <el-table-column prop="check_in_count" label="签到天数" width="90" />
            <el-table-column prop="on_time_count" label="准时天数" width="90" />
            <el-table-column prop="late_count" label="迟到天数" width="90" />
            <el-table-column prop="total_late_minutes" label="迟到总(分)" width="90" />
            <el-table-column prop="attendance_rate" label="出勤率" width="90">
              <template #default="scope">
                <span :style="{ color: scope.row.attendance_rate >= 90 ? '#27ae60' : scope.row.attendance_rate >= 60 ? '#e67e22' : '#e74c3c' }">
                  {{ scope.row.attendance_rate }}%
                </span>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="exportData.length === 0 && hasSearched" style="text-align: center; color: #999; padding: 20px;">
            暂无考勤记录
          </div>
        </template>
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
  { key: 'settings', label: '🛠️ 全局参数设置' },
  { key: 'export',  label: '📤 记录导出' }  // 新增导出标签
]
const activeTab = ref('today')

// ── 摄像头相关 ────────────────────────────────────────────
const videoRef = ref(null)
const canvasRef = ref(null)
const checkinResult = ref(null)
const isCameraActive = ref(false)
let stream = null
let captureTimer = null

const startCamera = async () => {
  if (isCameraActive.value) return
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    videoRef.value.srcObject = stream
    isCameraActive.value = true
    await new Promise(resolve => setTimeout(resolve, 500))
    captureLoop()
  } catch {
    alert('无法启动摄像头，请检查权限')
  }
}

const stopCamera = () => {
  isCameraActive.value = false
  clearTimeout(captureTimer)
  if (stream) stream.getTracks().forEach(t => t.stop())
  stream = null
}

const captureLoop = () => {
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
      const res = await request.post('/attendance/checkin', form, {
        timeout: 5000,
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      const data = res.data
      if (['check_in', 'check_out'].includes(data.action)) {
        checkinResult.value = data
        setTimeout(() => { checkinResult.value = null }, 3000)
        fetchTodayRecords()
      } else {
        console.log('打卡忽略:', data.message)
      }
    } catch (e) {
      handleCheckinError(e)
    } finally {
      if (isCameraActive.value) {
        captureTimer = setTimeout(captureLoop, 2000)
      }
    }
  }, 'image/jpeg', 0.85)
}

const handleCheckinError = (error) => {
  const status = error.response?.status
  const detail = error.response?.data?.detail
  let message = '系统异常，请稍后重试'
  let code = ERROR_CODE.SYSTEM
  if (typeof detail === 'object' && detail.message) {
    message = detail.message
    code = detail.code
  } else if (typeof detail === 'string') {
    message = detail
  }
  switch (code) {
    case ERROR_CODE.NO_FACE:
      console.warn('未检测到人脸')
      break
    case ERROR_CODE.UNKNOWN_USER:
      showWarningBubble('未识别身份', message)
      break
    default:
      showWarningBubble('系统提示', message)
      if (!status || status >= 500) {
        console.log('服务器异常，延长重试时间...')
        captureTimer = setTimeout(captureLoop, 5000)
      }
      break
  }
}

const showWarningBubble = (title, msg) => {
  checkinResult.value = {
    action: 'error',
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

const showEditDialog = ref(false)
const editForm = ref({
  id: null,
  employee_id: '',
  name: '',
  email: '',
  department: ''
})

const openEditEmployee = (user) => {
  editForm.value = {
    id: user.id,
    employee_id: user.employee_id || '',
    name: user.name || '',
    email: user.email || '',
    department: user.department || ''
  }
  showEditDialog.value = true
}

const saveEmployee = async () => {
  try {
    await request.put(`/employees/${editForm.value.id}`, {
      employee_id: editForm.value.employee_id || null,
      name: editForm.value.name,
      email: editForm.value.email,
      department: editForm.value.department || null
    })
    ElMessage.success('保存成功')
    showEditDialog.value = false
    fetchAttendanceUsers()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  }
}

// ── 全局配置 ──────────────────────────────────────────────
const globalConfig = ref({
  checkin_debounce_seconds: 60,
  face_similarity_threshold: 0.6
})

const fetchConfig = async () => {
  const res = await request.get('/attendance/config')
  res.data.forEach(item => {
    if (globalConfig.value.hasOwnProperty(item.key)) {
      if (item.key === 'face_similarity_threshold') {
        globalConfig.value[item.key] = parseFloat(item.value)
      } else {
        globalConfig.value[item.key] = parseInt(item.value)
      }
    }
  })
}

const saveGlobalConfig = async () => {
  for (const key in globalConfig.value) {
    await request.put(`/attendance/config/${key}`, {
      value: String(globalConfig.value[key])
    })
  }
  ElMessage.success('参数已更新')
}

// ═══════════════════════════════════════════════════════════
// 记录导出相关
// ═══════════════════════════════════════════════════════════
const exportMode = ref('daily')
const exportDateRange = ref([])
const exportYear = ref(new Date().getFullYear())
const exportMonth = ref(null)
const exportUserId = ref(null)
const exportData = ref([])
const hasSearched = ref(false)
const allUsers = ref([])

const fetchAllUsers = async () => {
  const res = await request.get('/attendance/users')
  allUsers.value = res.data
}

const fetchExportData = async () => {
  hasSearched.value = true
  try {
    if (exportMode.value === 'daily') {
      const [start, end] = exportDateRange.value || []
      const res = await request.get('/attendance/records/export', {
        params: { start_date: start, end_date: end, user_id: exportUserId.value }
      })
      exportData.value = res.data
    } else {
      const res = await request.get('/attendance/records/monthly', {
        params: {
          year: exportYear.value,
          month: exportMonth.value,
          user_id: exportUserId.value
        }
      })
      exportData.value = res.data
    }
    if (exportData.value.length === 0) {
      ElMessage.info('暂无考勤记录')
    }
  } catch (err) {
    ElMessage.error('查询失败：' + (err.response?.data?.detail || err.message))
  }
}

const formatDateTime = (t) => {
  if (!t) return ''
  return t.replace('T', ' ').substring(0, 19)
}

const handleExport = () => {
  if (!exportData.value.length) return

  let headers, rows, filename

  if (exportMode.value === 'daily') {
    headers = [
      { label: '日期', key: 'date' },
      { label: '姓名', key: 'name' },
      { label: '邮箱', key: 'email' },
      { label: '签到时间', key: 'check_in_time' },
      { label: '签退时间', key: 'check_out_time' },
      { label: '状态', key: 'status' },
      { label: '迟到分钟', key: 'late_minutes' }
    ]
    rows = exportData.value.map(record => {
      return headers.map(h => {
        let value = record[h.key]
        if (h.key === 'status') {
          value = value === 'on_time' ? '准时' : value === 'late' ? `迟到${record.late_minutes}分钟` : value
        }
        if (value && (h.key === 'check_in_time' || h.key === 'check_out_time')) {
          value = formatDateTime(value)
        }
        if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
          value = `"${value.replace(/"/g, '""')}"`
        }
        return value !== undefined && value !== null ? value : ''
      }).join(',')
    })
    filename = `考勤日报_${exportDateRange.value?.[0] || '全部'}`
  } else {
    headers = [
      { label: '姓名', key: 'name' },
      { label: '邮箱', key: 'email' },
      { label: '应到天数', key: 'total_days' },
      { label: '签到天数', key: 'check_in_count' },
      { label: '准时天数', key: 'on_time_count' },
      { label: '迟到天数', key: 'late_count' },
      { label: '迟到总分钟', key: 'total_late_minutes' },
      { label: '出勤率', key: 'attendance_rate' }
    ]
    rows = exportData.value.map(record => {
      return headers.map(h => {
        let value = record[h.key]
        if (h.key === 'attendance_rate') {
          value = value + '%'
        }
        if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
          value = `"${value.replace(/"/g, '""')}"`
        }
        return value !== undefined && value !== null ? value : ''
      }).join(',')
    })
    filename = exportMonth.value
      ? `考勤月报_${exportYear.value}_${exportMonth.value}月`
      : `考勤年报_${exportYear.value}`
  }

  const csvContent = [
    headers.map(h => h.label).join(','),
    ...rows
  ].join('\n')

  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${filename}.csv`
  
  URL.revokeObjectURL(link.href)
}

// ── 生命周期 ──────────────────────────────────────────────
onMounted(() => {
  fetchTodayRecords()
  fetchRules()
  fetchAttendanceUsers()
  fetchConfig()
  fetchAllUsers()
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
/* 原有样式保持不变，新增部分已在上面内联，无需额外样式 */
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

.result-bubble.error {
  background: #fff0f0;
  border: 1.5px solid #ff4d4f;
}
.result-bubble.error .result-name {
  color: #ff4d4f;
}

/* ── 导出功能样式 ── */
.export-mode-bar {
  margin-bottom: 16px;
}
.export-filter {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}
.filter-label {
  font-size: 13px;
  color: #666;
}
</style>