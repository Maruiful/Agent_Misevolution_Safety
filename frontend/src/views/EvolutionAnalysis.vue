<template>
  <div class="evolution-container">
    <el-card>
      <template #header>
        <span>策略进化趋势</span>
      </template>
      <div ref="chartRef" style="width: 100%; height: 400px"></div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)

onMounted(() => {
  if (chartRef.value) {
    const chart = echarts.init(chartRef.value)
    const option = {
      title: {
        text: '策略分布变化'
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['礼貌回复', '高效处理', '违规操作']
      },
      xAxis: {
        type: 'category',
        data: ['0-100', '100-200', '200-300', '300-400', '400-500', '500-600', '600-700', '700-800', '800-900', '900-1000']
      },
      yAxis: {
        type: 'value',
        name: '使用次数'
      },
      series: [
        {
          name: '礼貌回复',
          type: 'line',
          data: [30, 35, 40, 38, 35, 30, 25, 20, 18, 15]
        },
        {
          name: '高效处理',
          type: 'line',
          data: [20, 25, 30, 40, 45, 50, 52, 55, 58, 60]
        },
        {
          name: '违规操作',
          type: 'line',
          data: [0, 1, 2, 5, 10, 15, 25, 35, 45, 55]
        }
      ]
    }
    chart.setOption(option)
  }
})
</script>

<style scoped>
.evolution-container {
  padding: 20px;
}
</style>
