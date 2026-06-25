<template>
  <div class="agents-view">
    <div class="card">
      <h2>Agent Registry ({{ agents.length }})</h2>
      <div class="agent-grid">
        <div v-for="agent in agents" :key="agent.agent_id" class="agent-card">
          <div class="agent-card-header">
            <span class="agent-role" :class="agent.role">{{ agent.role }}</span>
            <span class="agent-id">{{ agent.agent_id }}</span>
          </div>
          <div class="agent-module">Module: {{ agent.module }}</div>
          <div class="agent-caps">
            <span v-for="cap in agent.capabilities" :key="cap" class="cap-tag">{{ cap }}</span>
          </div>
          <div v-if="agent.dependencies?.length" class="agent-deps">
            Dependencies: {{ agent.dependencies.join(', ') }}
          </div>
          <div class="agent-actions">
            <button @click="handleCall(agent)" class="btn small primary">Call Direct</button>
          </div>
        </div>
      </div>
      <div v-if="!agents.length" class="empty">No agents loaded</div>
    </div>

    <!-- Call Result -->
    <div v-if="callResult" class="card">
      <h2>Call Result</h2>
      <pre class="result-box">{{ typeof callResult === 'string' ? callResult : JSON.stringify(callResult, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listAgents, callAgent } from '@/api/client'

const agents = ref<any[]>([])
const callResult = ref<any>(null)

async function refresh() {
  try {
    const res = await listAgents()
    agents.value = res.agents || []
  } catch { /* ignore */ }
}

async function handleCall(agent: any) {
  try {
    callResult.value = await callAgent(agent.module, {
      requirement: 'Hello, introduce yourself as a ' + agent.role,
      constraints: [],
    })
  } catch (e: any) {
    callResult.value = { error: e.message }
  }
}

onMounted(refresh)
</script>

<style scoped>
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 24px;
}
.card h2 { font-size: 16px; margin-bottom: 16px; }

.agent-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }

.agent-card {
  padding: 16px;
  background: var(--bg);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.agent-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }

.agent-role {
  font-size: 10px; font-weight: 600; padding: 2px 8px;
  border-radius: 4px; text-transform: uppercase;
}
.agent-role.expert { background: #1e3a5f; color: #60a5fa; }
.agent-role.supervisor { background: #3b1f5e; color: #c084fc; }
.agent-role.integrator { background: #1a3a2a; color: #4ade80; }
.agent-role.plugin { background: #3a2a1a; color: #fbbf24; }

.agent-id { font-weight: 600; font-size: 14px; }
.agent-module { font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }

.agent-caps { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.cap-tag {
  font-size: 11px; padding: 2px 6px;
  background: var(--bg-hover); border-radius: 3px;
  color: var(--text-muted);
}

.agent-deps { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
.agent-actions { margin-top: 8px; }

.btn {
  padding: 6px 14px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-hover);
  color: var(--text);
  cursor: pointer;
  font-size: 13px;
}
.btn.primary { background: var(--primary); }
.btn.small { padding: 4px 10px; font-size: 12px; }

.result-box {
  padding: 16px;
  background: var(--bg);
  border-radius: 6px;
  font-size: 13px;
  overflow-x: auto;
  white-space: pre-wrap;
  font-family: 'JetBrains Mono', monospace;
}

.empty { color: var(--text-muted); text-align: center; padding: 40px; }
</style>
