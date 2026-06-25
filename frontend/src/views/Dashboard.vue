<template>
  <div class="dashboard">
    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">◈</div>
        <div class="stat-info">
          <span class="stat-value">{{ appStore.agents.length }}</span>
          <span class="stat-label">Agents</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⛓</div>
        <div class="stat-info">
          <span class="stat-value">{{ appStore.modules.length }}</span>
          <span class="stat-label">Modules</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">◉</div>
        <div class="stat-info">
          <span class="stat-value">{{ appStore.ragStatsData.total_chunks || 0 }}</span>
          <span class="stat-label">RAG Chunks</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⟳</div>
        <div class="stat-info">
          <span class="stat-value">{{ appStore.workflows.length }}</span>
          <span class="stat-label">Workflows</span>
        </div>
      </div>
    </div>

    <!-- Agents Overview -->
    <div class="card">
      <h2>Agent Overview</h2>
      <div class="agent-list">
        <div v-for="agent in appStore.agents" :key="agent.agent_id" class="agent-item">
          <span class="agent-role" :class="agent.role">{{ agent.role }}</span>
          <span class="agent-name">{{ agent.agent_id }}</span>
          <span class="agent-module">{{ agent.module }}</span>
          <span class="agent-caps">{{ agent.capabilities?.length || 0 }} caps</span>
        </div>
        <div v-if="!appStore.agents.length" class="empty">No agents loaded</div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="card">
      <h2>Quick Actions</h2>
      <div class="actions">
        <router-link to="/pipeline" class="action-btn primary">Run Pipeline</router-link>
        <router-link to="/rag" class="action-btn">Upload Document</router-link>
        <router-link to="/workflows" class="action-btn">Create Workflow</router-link>
        <router-link to="/tools" class="action-btn">Browse Tools</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppStore } from '@/stores'

const appStore = useAppStore()

onMounted(() => {
  appStore.fetchAll()
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon { font-size: 28px; opacity: 0.8; }

.stat-info { display: flex; flex-direction: column; }
.stat-value { font-size: 24px; font-weight: 700; }
.stat-label { font-size: 13px; color: var(--text-muted); }

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 24px;
}

.card h2 { font-size: 16px; margin-bottom: 16px; }

.agent-list { display: flex; flex-direction: column; gap: 8px; }

.agent-item {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  background: var(--bg);
}

.agent-role {
  font-size: 11px; font-weight: 600; padding: 2px 8px;
  border-radius: 4px; text-transform: uppercase;
}
.agent-role.expert { background: #1e3a5f; color: #60a5fa; }
.agent-role.supervisor { background: #3b1f5e; color: #c084fc; }
.agent-role.integrator { background: #1a3a2a; color: #4ade80; }
.agent-role.plugin { background: #3a2a1a; color: #fbbf24; }

.agent-name { font-weight: 500; flex: 1; }
.agent-module { color: var(--text-muted); font-size: 13px; }
.agent-caps { font-size: 12px; color: var(--text-muted); }

.empty { color: var(--text-muted); text-align: center; padding: 20px; }

.actions { display: flex; gap: 12px; flex-wrap: wrap; }

.action-btn {
  padding: 10px 20px;
  border-radius: 6px;
  border: 1px solid var(--border);
  color: var(--text);
  font-size: 14px;
  transition: all 0.2s;
}
.action-btn:hover { background: var(--bg-hover); text-decoration: none; }
.action-btn.primary { background: var(--primary); border-color: var(--primary); }
.action-btn.primary:hover { background: var(--primary-dark); }
</style>
