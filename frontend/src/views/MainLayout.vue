<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <h2>智能体进化分析</h2>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/monitor">
          <el-icon><Monitor /></el-icon>
          <span>实验监控</span>
        </el-menu-item>
        <el-menu-item index="/evolution">
          <el-icon><TrendCharts /></el-icon>
          <span>进化分析</span>
        </el-menu-item>
        <el-menu-item index="/conversation">
          <el-icon><ChatDotRound /></el-icon>
          <span>对话查看</span>
        </el-menu-item>
        <el-menu-item index="/control">
          <el-icon><Setting /></el-icon>
          <span>实验控制</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-title">
          <h3>{{ currentPageTitle }}</h3>
        </div>
        <div class="header-actions">
          <el-button type="primary" size="small">导出数据</el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
const currentPageTitle = computed(() => route.meta.title || '客服智能体系统')
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2b3a4a;
  border-bottom: 1px solid #1f2d3d;
}

.logo h2 {
  font-size: 18px;
  color: #fff;
  margin: 0;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-title h3 {
  margin: 0;
  color: #333;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
