import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/views/MainLayout.vue'),
    redirect: '/monitor',
    children: [
      {
        path: 'monitor',
        name: 'ExperimentMonitor',
        component: () => import('@/views/ExperimentMonitor.vue'),
        meta: { title: '实验监控' }
      },
      {
        path: 'evolution',
        name: 'EvolutionAnalysis',
        component: () => import('@/views/EvolutionAnalysis.vue'),
        meta: { title: '进化分析' }
      },
      {
        path: 'conversation',
        name: 'ConversationViewer',
        component: () => import('@/views/ConversationViewer.vue'),
        meta: { title: '对话查看' }
      },
      {
        path: 'control',
        name: 'ExperimentControl',
        component: () => import('@/views/ExperimentControl.vue'),
        meta: { title: '实验控制' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
