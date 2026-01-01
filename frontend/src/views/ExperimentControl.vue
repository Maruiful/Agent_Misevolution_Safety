<template>
  <div class="control-container">
    <el-card>
      <template #header>
        <span>实验配置</span>
      </template>
      <el-form :model="config" label-width="150px">
        <el-form-item label="实验轮次">
          <el-input-number v-model="config.episodes" :min="100" :max="10000" :step="100" />
        </el-form-item>
        <el-form-item label="启用记忆">
          <el-switch v-model="config.enableMemory" />
        </el-form-item>
        <el-form-item label="启用进化">
          <el-switch v-model="config.enableEvolution" />
        </el-form-item>
        <el-form-item label="启用防御">
          <el-switch v-model="config.enableDefense" />
        </el-form-item>
        <el-form-item label="短期奖励权重">
          <el-slider v-model="config.shortTermWeight" :min="0" :max="1" :step="0.1" show-input />
        </el-form-item>
        <el-form-item label="长期奖励权重">
          <el-slider v-model="config.longTermWeight" :min="0" :max="1" :step="0.1" show-input />
        </el-form-item>
        <el-form-item>
          <el-button type="primary">保存配置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const config = reactive({
  episodes: 1000,
  enableMemory: true,
  enableEvolution: true,
  enableDefense: false,
  shortTermWeight: 0.5,
  longTermWeight: 0.5
})
</script>

<style scoped>
.control-container {
  padding: 20px;
}
</style>
