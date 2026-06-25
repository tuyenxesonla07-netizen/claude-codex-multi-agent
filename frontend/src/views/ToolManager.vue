<template>
  <div class="tool-view">
    <div class="card">
      <h2>Available MCP Tools</h2>
      <div class="tool-list">
        <div v-for="tool in tools" :key="tool.name" class="tool-item">
          <div class="tool-header">
            <span class="tool-name">{{ tool.name }}</span>
            <button @click="handleCall(tool)" class="btn small primary">Call</button>
          </div>
          <p class="tool-desc">{{ tool.description }}</p>
          <div v-if="tool.inputSchema?.properties" class="tool-params">
            <span class="params-title">Parameters:</span>
            <span v-for="(prop, key) in tool.inputSchema.properties" :key="key" class="param-tag">
              <span class="param-name">{{ key }}</span>
              <span class="param-type">{{ prop.type || 'any' }}</span>
            </span>
          </div>
        </div>
        <div v-if="!tools.length" class="empty">No tools available</div>
      </div>
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
import { listMcpTools, callMcpTool } from '@/api/client'

const tools = ref<any[]>([])
const callResult = ref<any>(null)

async function refresh() {
  try {
    const res = await listMcpTools()
    tools.value = res.tools || []
  } catch (e: any) {
    console.error('Failed to load tools:', e)
  }
}

async function handleCall(tool: any) {
  try {
    // Build sample arguments from schema
    const args: Record<string, any> = {}
    if (tool.inputSchema?.properties) {
      for (const [key, prop] of Object.entries(tool.inputSchema.properties)) {
        if (prop.type === 'string') args[key] = ''
        else if (prop.type === 'integer') args[key] = 0
        else if (prop.type === 'number') args[key] = 0
        else if (prop.type === 'boolean') args[key] = false
        else if (prop.type === 'object') args[key] = {}
        else args[key] = ''
      }
    }
    callResult.value = await callMcpTool(tool.name, args)
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

.tool-list { display: flex; flex-direction: column; gap: 12px; }

.tool-item {
  padding: 14px 16px;
  background: var(--bg);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.tool-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.tool-name { font-weight: 600; font-size: 15px; }

.tool-desc { color: var(--text-muted); font-size: 13px; margin-bottom: 8px; }

.tool-params { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.params-title { font-size: 12px; color: var(--text-muted); margin-right: 4px; }

.param-tag {
  display: inline-flex; gap: 4px;
  padding: 2px 8px; border-radius: 4px;
  background: var(--bg-hover); font-size: 12px;
}
.param-name { font-family: monospace; }
.param-type { color: var(--primary-light); }

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

.empty { color: var(--text-muted); text-align: center; padding: 20px; }
</style>
