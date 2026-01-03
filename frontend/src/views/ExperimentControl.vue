<template>
  <div class="control-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>实验配置</span>
          <div class="preset-buttons">
            <el-button size="small" @click="loadPreset('baseline')">基线实验</el-button>
            <el-button size="small" @click="loadPreset('induced')">诱导实验</el-button>
            <el-button size="small" @click="loadPreset('defense')">防御实验</el-button>
          </div>
        </div>
      </template>

      <el-form :model="config" label-width="150px">
        <el-form-item label="实验名称">
          <el-input v-model="config.name" placeholder="请输入实验名称" />
        </el-form-item>

        <el-divider content-position="left">基本配置</el-divider>

        <el-form-item label="实验轮次">
          <el-input-number
            v-model="config.episodes"
            :min="10"
            :max="10000"
            :step="10"
            :precision="0"
          />
          <span class="unit-text">轮</span>
          <span class="help-text">建议测试时使用 50-100 轮</span>
        </el-form-item>

        <el-form-item label="场景类型">
          <el-select v-model="config.scenario" placeholder="请选择场景">
            <el-option label="客服智能体" value="customer_service" />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">功能开关</el-divider>

        <el-form-item label="启用记忆">
          <el-switch v-model="config.enableMemory" />
          <span class="switch-label">存储和检索历史经验</span>
        </el-form-item>

        <el-form-item label="启用进化">
          <el-switch v-model="config.enableEvolution" />
          <span class="switch-label">根据经验优化策略</span>
        </el-form-item>

        <el-form-item label="启用防御">
          <el-switch v-model="config.enableDefense" />
          <span class="switch-label">安全哨兵拦截违规行为</span>
        </el-form-item>

        <el-divider content-position="left">奖励权重配置</el-divider>

        <el-form-item label="短期奖励权重">
          <el-slider
            v-model="config.rewardWeights.shortTerm"
            :min="0"
            :max="1"
            :step="0.1"
            show-input
            :show-input-controls="false"
          />
          <span class="help-text">快速响应、关闭工单等立即反馈</span>
        </el-form-item>

        <el-form-item label="长期奖励权重">
          <el-slider
            v-model="config.rewardWeights.longTerm"
            :min="0"
            :max="1"
            :step="0.1"
            show-input
            :show-input-controls="false"
          />
          <span class="help-text">客户满意度、合规性等延迟反馈</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleStart">
            启动实验
          </el-button>
          <el-button @click="resetConfig">重置配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { startExperiment } from '@/api/experiment'

const router = useRouter()
const loading = ref(false)

const config = reactive({
  name: '',
  scenario: 'customer_service',
  episodes: 1000,
  enableMemory: true,
  enableEvolution: true,
  enableDefense: false,
  rewardWeights: {
    shortTerm: 0.5,
    longTerm: 0.5
  }
})

// 预设配置
const presets = {
  baseline: {
    name: '基线实验',
    episodes: 1000,
    enableMemory: false,
    enableEvolution: false,
    enableDefense: false,
    rewardWeights: { shortTerm: 0.5, longTerm: 0.5 }
  },
  induced: {
    name: '诱导实验',
    episodes: 1000,
    enableMemory: true,
    enableEvolution: true,
    enableDefense: false,
    rewardWeights: { shortTerm: 0.8, longTerm: 0.2 }
  },
  defense: {
    name: '防御实验',
    episodes: 1000,
    enableMemory: true,
    enableEvolution: true,
    enableDefense: true,
    rewardWeights: { shortTerm: 0.8, longTerm: 0.2 }
  }
}

// 加载预设配置
const loadPreset = (type) => {
  const preset = presets[type]
  Object.assign(config, preset)
  ElMessage.success(`已加载${preset.name}配置`)
}

// 重置配置
const resetConfig = () => {
  config.name = ''
  config.scenario = 'customer_service'
  config.episodes = 1000
  config.enableMemory = true
  config.enableEvolution = true
  config.enableDefense = false
  config.rewardWeights = { shortTerm: 0.5, longTerm: 0.5 }
  ElMessage.info('配置已重置')
}

// 启动实验
const handleStart = async () => {
  // 验证配置
  if (!config.name) {
    ElMessage.warning('请输入实验名称')
    return
  }

  if (config.episodes < 10) {
    ElMessage.warning('实验轮次不能少于 10')
    return
  }

  // 验证奖励权重
  const totalWeight = config.rewardWeights.shortTerm + config.rewardWeights.longTerm
  if (Math.abs(totalWeight - 1.0) > 0.01) {
    ElMessage.warning('短期和长期奖励权重之和必须等于 1.0')
    return
  }

  loading.value = true

  try {
    // 构建请求数据，按照后端期望的格式
    const requestData = {
      name: config.name,
      config: {
        scenario: config.scenario,
        episodes: config.episodes,
        enableMemory: config.enableMemory,
        enableEvolution: config.enableEvolution,
        enableDefense: config.enableDefense,
        rewardWeights: {
          shortTermWeight: config.rewardWeights.shortTerm,
          longTermWeight: config.rewardWeights.longTerm,
          violationWeight: 1.0
        },
        epsilon: 0.1
      }
    }

    const res = await startExperiment(requestData)

    if (res.code === 200) {
      ElMessage.success('实验启动成功')
      // 跳转到监控页面
      router.push({
        path: '/monitor',
        query: { experimentUuid: res.data.experimentUuid }
      })
    } else {
      ElMessage.error(res.message || '启动实验失败')
    }
  } catch (error) {
    console.error('启动实验失败:', error)
    ElMessage.error('启动实验失败: ' + (error.message || '网络错误'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.control-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.config-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preset-buttons {
  display: flex;
  gap: 10px;
}

.unit-text {
  margin-left: 10px;
  color: #909399;
  font-size: 14px;
}

.switch-label {
  margin-left: 10px;
  color: #606266;
  font-size: 14px;
}

.help-text {
  display: block;
  margin-top: 5px;
  color: #909399;
  font-size: 12px;
}

:deep(.el-divider__text) {
  font-weight: bold;
  color: #409eff;
}
</style>
