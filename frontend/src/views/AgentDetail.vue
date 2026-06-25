<template>
  <div class="agents-page">
    <div class="page-header">
      <h2>Agent Registry</h2>
      <div class="search-bar">
        <input v-model="search" placeholder="Filter agents..." class="input" />
      </div>
    </div>

    <div class="agent-grid">
      <div v-for="agent in filteredAgents" :key="agent.agent_id" class="agent-card">
        <div class="card-header">
          <Badge :variant="agent.role">{{ agent.role }}</Badge>
          <span class="agent-id">{{ agent.agent_id }}</span>
        </div>
        <div class="card-module">{{ agent.module }}</div>
        <div class="card-caps">
          <span v-for="cap in agent.capabilities?.slice(0, 4)" :key="cap" class="cap-tag">{{ cap }}</span>
          <span v-if="(agent.capabilities?.length || 0) > 4" class="cap-more">
            +{{ agent.capabilities.length - 4 }}
          </span>
        </div>
        <div v-if="agent.dependencies?.length" class="card-deps">
          deps: {{ agent.dependencies.join(', ') }}
        </div>
        <button class="btn-sm" @click="handleCall(agent)">Call Direct</button>
      </div>
    </div>

    <div v-if="!filteredAgents.length" class="empty">No agents found</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores'
import Badge from '@/components/shared/Badge.vue'
import { callAgent } from '@/api/client'

const appStore = useAppStore()
const search = ref('')

const filteredAgents = computed(() => {
  if (!search.value) return appStore.agents
  const q = search.value.toLowerCase()
  return appStore.agents.filter(a =>
    a.agent_id.toLowerCase().includes(q) ||
    a.module?.toLowerCase().includes(q) ||
    a.role?.toLowerCase().includes(q)
  )
})

async function handleCall(agent: any) {
  try {
    await callAgent(agent.module, { requirement: 'Hello from agent direct call', constraints: [] })
  } catch (e) { console.error('Call failed:', e) }
}

onMounted(() => { if (!appStore.agents.length) appStore.fetchAgents() })
</script>

<style scoped>
.agents-page {
  max-width: 680px;
  margin: 0 auto;
  padding: var(--space-6);
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-5);
}
.page-header h2 { font-size: var(--font-size-lg); font-weight: 700; }
.search-bar { width: 220px; }
.input {
  width: 100%;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  outline: none;
  transition: border-color var(--transition-fast);
}
.input:focus { border-color: var(--accent); }

.agent-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}
.agent-card {
  padding: var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  transition: all var(--transition-fast);
}
.agent-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}

.card-header { display: flex; align-items: center; gap: var(--space-2); margin-bottom: var(--space-2); }
.agent-id { font-weight: 600; font-size: var(--font-size-sm); }
.card-module { font-size: var(--font-size-sm); color: var(--text-muted); margin-bottom: var(--space-2); }

.card-caps { display: flex; flex-wrap: wrap; gap: var(--space-1); margin-bottom: var(--space-2); }
.cap-tag {
  font-size: var(--font-size-xs);
  padding: 1px 6px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
}
.cap-more { font-size: var(--font-size-xs); color: var(--text-muted); }

.card-deps {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-bottom: var(--space-3);
}

.btn-sm {
  padding: var(--space-1) var(--space-3);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--accent);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn-sm:hover { border-color: var(--accent); background: var(--accent-light); }

.empty { text-align: center; color: var(--text-muted); padding: var(--space-8); }
</style>
