<template>
  <div class="monitor-container">
    <!-- 状态卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff">
              <el-icon :size="30"><DataLine /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ metrics.currentEpisode || 0 }}</div>
              <div class="stat-label">当前轮次</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a">
              <el-icon :size="30"><SuccessFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ metrics.successCount || 0 }}</div>
              <div class="stat-label">成功次数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c">
              <el-icon :size="30"><WarningFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ metrics.violationCount || 0 }}</div>
              <div class="stat-label">违规次数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #e6a23c">
              <el-icon :size="30"><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(metrics.averageReward) }}</div>
              <div class="stat-label">平均奖励</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 进度和控制 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>实验进度</span>
              <el-tag :type="statusType">{{ statusText }}</el-tag>
            </div>
          </template>
          <el-progress
            :percentage="progress"
            :status="progressStatus"
            :stroke-width="20"
          />
          <div class="progress-info">
            <span>{{ metrics.currentEpisode || 0 }} / {{ metrics.totalEpisodes || 0 }}</span>
            <span>{{ progress.toFixed(1) }}%</span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <span>实验控制</span>
          </template>
          <div class="control-buttons">
            <el-button
              v-if="experimentStatus === 'RUNNING'"
              type="warning"
              :icon="VideoPause"
              @click="pauseExperiment"
            >
              暂停
            </el-button>
            <el-button
              v-if="experimentStatus === 'PAUSED'"
              type="success"
              :icon="VideoPlay"
              @click="resumeExperiment"
            >
              继续
            </el-button>
            <el-button
              type="danger"
              :icon="CircleClose"
              @click="stopExperiment"
            >
              停止
            </el-button>
            <el-button
              type="info"
              :icon="Refresh"
              @click="resetExperiment"
            >
              重置
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时事件 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>实时事件</span>
              <el-button size="small" text @click="clearEvents">清空</el-button>
            </div>
          </template>
          <div class="events-container">
            <div v-for="(event, index) in events" :key="index" class="event-item">
              <el-tag :type="event.type" size="small">{{ event.time }}</el-tag>
              <span>{{ event.message }}</span>
            </div>
            <div v-if="events.length === 0" class="no-events">暂无事件</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>防御统计</span>
          </template>
          <div v-if="defenseStats" class="defense-stats">
            <div class="stat-row">
              <span class="label">总审查:</span>
              <span class="value">{{ defenseStats.totalReviews }}</span>
            </div>
            <div class="stat-row">
              <span class="label">拦截:</span>
              <span class="value danger">{{ defenseStats.blockedCount }}</span>
              <span class="percent">({{ (defenseStats.blockRate * 100).toFixed(1) }}%)</span>
            </div>
            <div class="stat-row">
              <span class="label">警告:</span>
              <span class="value warning">{{ defenseStats.warningCount }}</span>
              <span class="percent">({{ (defenseStats.warningRate * 100).toFixed(1) }}%)</span>
            </div>
            <div class="stat-row">
              <span class="label">修正:</span>
              <span class="value success">{{ defenseStats.autoCorrectCount }}</span>
              <span class="percent">({{ (defenseStats.correctRate * 100).toFixed(1) }}%)</span>
            </div>
          </div>
          <div v-else class="no-data">暂无防御数据</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  VideoPlay,
  VideoPause,
  CircleClose,
  Refresh,
  DataLine,
  SuccessFilled,
  WarningFilled,
  TrendCharts
} from '@element-plus/icons-vue'
import {
  getExperimentStatus,
  getExperimentMetrics,
  pauseExperiment,
  resumeExperiment,
  stopExperiment,
  resetExperiment
} from '@/api/experiment'
import { getDefenseStatistics } from '@/api/defense'

const route = useRoute()
const experimentUuid = ref(route.query.experimentUuid || '')

// 调试：打印初始值
console.log('初始化 - route.query.experimentUuid:', route.query.experimentUuid)
console.log('初始化 - experimentUuid.value:', experimentUuid.value)
console.log('初始化 - experimentUuid.value类型:', typeof experimentUuid.value)

const metrics = reactive({
  currentEpisode: 0,
  totalEpisodes: 0,
  successCount: 0,
  violationCount: 0,
  averageReward: 0
})

const experimentStatus = ref('')
const defenseStats = ref(null)
const events = ref([])

let pollingTimer = null
let ws = null

// 计算属性
const progress = computed(() => {
  if (!metrics.totalEpisodes) return 0
  return (metrics.currentEpisode / metrics.totalEpisodes) * 100
})

const progressStatus = computed(() => {
  if (progress.value >= 100) return 'success'
  if (experimentStatus.value === 'RUNNING') return undefined
  return 'exception'
})

const statusType = computed(() => {
  const statusMap = {
    RUNNING: 'success',
    PAUSED: 'warning',
    COMPLETED: 'info',
    FAILED: 'danger'
  }
  return statusMap[experimentStatus.value] || 'info'
})

const statusText = computed(() => {
  const textMap = {
    RUNNING: '运行中',
    PAUSED: '已暂停',
    COMPLETED: '已完成',
    FAILED: '已失败'
  }
  return textMap[experimentStatus.value] || '未知'
})

// 格式化数字
const formatNumber = (num) => {
  if (num === null || num === undefined) return '0.00'
  return Number(num).toFixed(2)
}

// 添加事件
const addEvent = (message, type = 'info') => {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  events.value.unshift({ time, message, type })
  if (events.value.length > 50) {
    events.value.pop()
  }
}

// 清空事件
const clearEvents = () => {
  events.value = []
}

// 加载实验数据
const loadExperimentData = async () => {
  if (!experimentUuid.value) return

  try {
    // 获取实验状态
    const statusRes = await getExperimentStatus(experimentUuid.value)
    if (statusRes.code === 200) {
      experimentStatus.value = statusRes.data.status
    }

    // 获取实验指标
    const metricsRes = await getExperimentMetrics(experimentUuid.value)
    if (metricsRes.code === 200) {
      const data = metricsRes.data
      // 更新基本指标
      metrics.currentEpisode = data.currentEpisode || 0
      metrics.totalEpisodes = data.totalEpisodes || 0
      // 更新统计数据
      if (data.statistics) {
        Object.assign(metrics, data.statistics)
      }
    }

    // 获取防御统计
    const defenseRes = await getDefenseStatistics()
    if (defenseRes.code === 200) {
      defenseStats.value = defenseRes.data
    }
  } catch (error) {
    console.error('加载实验数据失败:', error)
  }
}

// 暂停实验
const handlePause = async () => {
  try {
    const res = await pauseExperiment(experimentUuid.value)
    if (res.code === 200) {
      ElMessage.success('实验已暂停')
      addEvent('实验已暂停', 'warning')
      await loadExperimentData()
    }
  } catch (error) {
    ElMessage.error('暂停失败: ' + error.message)
  }
}

// 恢复实验
const handleResume = async () => {
  try {
    const res = await resumeExperiment(experimentUuid.value)
    if (res.code === 200) {
      ElMessage.success('实验已恢复')
      addEvent('实验已恢复', 'success')
      await loadExperimentData()
    }
  } catch (error) {
    ElMessage.error('恢复失败: ' + error.message)
  }
}

// 停止实验
const handleStop = async () => {
  try {
    await ElMessageBox.confirm('确定要停止实验吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    console.log('停止实验 - experimentUuid类型:', typeof experimentUuid.value)
    console.log('停止实验 - experimentUuid值:', experimentUuid.value)

    const res = await stopExperiment(experimentUuid.value)
    if (res.code === 200) {
      ElMessage.success('实验已停止')
      addEvent('实验已停止', 'danger')
      await loadExperimentData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('停止失败: ' + error.message)
    }
  }
}

// 重置实验
const handleReset = async () => {
  try {
    await ElMessageBox.confirm('确定要重置实验吗? 所有数据将被清空!', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await resetExperiment(experimentUuid.value)
    if (res.code === 200) {
      ElMessage.success('实验已重置')
      addEvent('实验已重置', 'info')
      events.value = []
      await loadExperimentData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重置失败: ' + error.message)
    }
  }
}

// 初始化 WebSocket 连接
const initWebSocket = () => {
  if (!experimentUuid.value) return

  const wsUrl = `ws://localhost:8080/ws/experiment`
  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    console.log('WebSocket 已连接')
    addEvent('实时连接已建立', 'success')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      // 只处理当前实验的消息
      if (data.experimentUuid !== experimentUuid.value) return

      switch (data.type) {
        case 'episode_completed':
          metrics.currentEpisode = data.currentEpisode
          metrics.totalEpisodes = data.totalEpisodes
          if (data.statistics) {
            Object.assign(metrics, data.statistics)
          }
          break

        case 'violation_detected':
          addEvent(`检测到违规: ${data.description}`, 'danger')
          metrics.violationCount++
          break

        case 'defense_action':
          addEvent(`防御动作: ${data.actionType} - ${data.reason}`, 'warning')
          break

        case 'experiment_completed':
          addEvent('实验已完成!', 'success')
          experimentStatus.value = 'COMPLETED'
          loadExperimentData()
          break

        case 'error':
          addEvent(`错误: ${data.error}`, 'danger')
          break
      }
    } catch (error) {
      console.error('处理 WebSocket 消息失败:', error)
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error)
    addEvent('实时连接错误', 'danger')
  }

  ws.onclose = () => {
    console.log('WebSocket 已断开')
    addEvent('实时连接已断开', 'warning')
  }
}

// 启动轮询(备用方案)
const startPolling = () => {
  pollingTimer = setInterval(() => {
    loadExperimentData()
  }, 2000) // 每2秒轮询一次
}

onMounted(async () => {
  if (experimentUuid.value) {
    addEvent('开始加载实验数据', 'info')
    await loadExperimentData()
    initWebSocket()
    startPolling()
  } else {
    ElMessage.warning('未指定实验UUID')
    addEvent('未指定实验UUID', 'warning')
  }
})

onUnmounted(() => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
  }
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.monitor-container {
  padding: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 10px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-right: 20px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 5px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
  color: #606266;
  font-size: 14px;
}

.control-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.events-container {
  max-height: 300px;
  overflow-y: auto;
}

.event-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.event-item:last-child {
  border-bottom: none;
}

.no-events {
  text-align: center;
  color: #909399;
  padding: 20px;
}

.defense-stats {
  padding: 10px 0;
}

.stat-row {
  display: flex;
  align-items: center;
  padding: 8px 0;
  font-size: 14px;
}

.stat-row .label {
  width: 60px;
  color: #606266;
}

.stat-row .value {
  margin-left: 10px;
  font-weight: bold;
  color: #303133;
}

.stat-row .value.danger {
  color: #f56c6c;
}

.stat-row .value.warning {
  color: #e6a23c;
}

.stat-row .value.success {
  color: #67c23a;
}

.stat-row .percent {
  margin-left: 5px;
  color: #909399;
  font-size: 12px;
}

.no-data {
  text-align: center;
  color: #909399;
  padding: 20px;
}
</style>
