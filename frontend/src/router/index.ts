import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Chat', component: () => import('@/views/ChatView.vue') },
  { path: '/pipeline', name: 'Pipeline', component: () => import('@/views/PipelineView.vue') },
  { path: '/agents', name: 'Agents', component: () => import('@/views/AgentDetail.vue') },
  { path: '/rag', name: 'Knowledge', component: () => import('@/views/RAGManager.vue') },
  { path: '/workflows', name: 'Workflows', component: () => import('@/views/WorkflowDesigner.vue') },
  { path: '/tools', name: 'Tools', component: () => import('@/views/ToolManager.vue') },
  { path: '/settings', name: 'Settings', component: () => import('@/views/Settings.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
