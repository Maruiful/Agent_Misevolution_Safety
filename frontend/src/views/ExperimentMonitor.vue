<template>
  <div class="monitor-container">
    <el-row :gutter="20">
      <!-- 状态卡片 -->
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff">
              <el-icon :size="30"><DataLine /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ status.totalEpisodes }}</div>
              <div class="stat-label">总轮次</div>
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
              <div class="stat-value">{{ status.successCount }}</div>
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
              <div class="stat-value">{{ status.violationCount }}</div>
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
              <div class="stat-value">{{ status.avgReward }}</div>
              <div class="stat-label">平均奖励</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 控制按钮 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <div class="control-buttons">
            <el-button type="primary" :icon="VideoPlay" @click="startExperiment">启动实验</el-button>
            <el-button type="warning" :icon="VideoPause" @click="pauseExperiment">暂停实验</el-button>
            <el-button type="danger" :icon="RefreshRight" @click="resetExperiment">重置实验</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 实时日志 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>实时日志</span>
          </template>
          <div class="log-container">
            <div v-for="(log, index) in logs" :key="index" class="log-item">
              <el-tag :type="log.type" size="small">{{ log.time }}</el-tag>
              <span>{{ log.message }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoPlay, VideoPause, RefreshRight } from '@element-plus/icons-vue'

const status = reactive({
  totalEpisodes: 0,
  successCount: 0,
  violationCount: 0,
  avgReward: 0.0
})

const logs = ref([])

const startExperiment = () => {
  ElMessage.success('实验启动成功')
  addLog('实验已启动', 'success')
}

const pauseExperiment = () => {
  ElMessage.warning('实验已暂停')
  addLog('实验已暂停', 'warning')
}

const resetExperiment = () => {
  ElMessage.info('实验已重置')
  addLog('实验已重置', 'info')
}

const addLog = (message, type = 'info') => {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  logs.value.unshift({ time, message, type })
  if (logs.value.length > 50) {
    logs.value.pop()
  }
}

onMounted(() => {
  addLog('系统初始化完成', 'success')
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

.control-buttons {
  display: flex;
  gap: 10px;
}

.log-container {
  max-height: 400px;
  overflow-y: auto;
}

.log-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.log-item:last-child {
  border-bottom: none;
}
</style>
