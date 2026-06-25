<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="logo">
        <img src="/vite.svg" alt="logo" />
        <span>Claude-Codex</span>
      </div>
      <nav>
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <span class="icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <span class="version">v2.0.0</span>
      </div>
    </aside>
    <main class="content">
      <header class="topbar">
        <h1>{{ $route.name }}</h1>
        <div class="topbar-actions">
          <span class="status-dot" :class="{ online: isOnline }"></span>
          <span class="status-text">{{ isOnline ? 'Backend OK' : 'Offline' }}</span>
        </div>
      </header>
      <div class="page-body">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { healthCheck } from '@/api/client'

const isOnline = ref(false)

const navItems = [
  { path: '/', label: 'Dashboard', icon: '◫' },
  { path: '/pipeline', label: 'Pipeline', icon: '⛓' },
  { path: '/agents', label: 'Agents', icon: '◈' },
  { path: '/rag', label: 'Knowledge', icon: '◉' },
  { path: '/workflows', label: 'Workflows', icon: '⟳' },
  { path: '/tools', label: 'Tools', icon: '⚙' },
  { path: '/settings', label: 'Settings', icon: '⊙' },
]

onMounted(async () => {
  try {
    await healthCheck()
    isOnline.value = true
  } catch {
    isOnline.value = false
  }
})
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 220px;
  background: var(--bg-card);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  font-weight: 700;
  font-size: 16px;
}

.logo img { width: 28px; height: 28px; }

nav { flex: 1; padding: 12px 0; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  color: var(--text-muted);
  font-size: 14px;
  transition: all 0.2s;
  cursor: pointer;
  border-left: 3px solid transparent;
}

.nav-item:hover { background: var(--bg-hover); color: var(--text); }
.nav-item.active { color: var(--primary-light); border-left-color: var(--primary); background: var(--bg-hover); }

.icon { font-size: 16px; width: 20px; text-align: center; }

.sidebar-footer {
  padding: 12px 20px;
  border-top: 1px solid var(--border);
}

.version { font-size: 12px; color: var(--text-muted); }

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-card);
}

.topbar h1 { font-size: 20px; font-weight: 600; }

.topbar-actions { display: flex; align-items: center; gap: 8px; }

.status-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--danger);
}
.status-dot.online { background: var(--success); }

.status-text { font-size: 13px; color: var(--text-muted); }

.page-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
