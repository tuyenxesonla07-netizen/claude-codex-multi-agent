import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
  { path: '/pipeline', name: 'Pipeline', component: () => import('@/views/PipelineView.vue') },
  { path: '/agents', name: 'Agents', component: () => import('@/views/AgentDetail.vue') },
  { path: '/rag', name: 'RAG', component: () => import('@/views/RAGManager.vue') },
  { path: '/workflows', name: 'Workflows', component: () => import('@/views/WorkflowDesigner.vue') },
  { path: '/tools', name: 'Tools', component: () => import('@/views/ToolManager.vue') },
  { path: '/settings', name: 'Settings', component: () => import('@/views/Settings.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
