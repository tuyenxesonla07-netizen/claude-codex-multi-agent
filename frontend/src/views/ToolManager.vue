<template>
  <div class="tools-page">
    <h2>MCP Tools</h2>
    <div class="tool-list">
      <div v-for="tool in tools" :key="tool.name" class="tool-card">
        <div class="tool-header">
          <span class="tool-icon">⚙</span>
          <span class="tool-name">{{ tool.name }}</span>
          <button class="btn-sm" @click="handleCall(tool)">Call</button>
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
    </div>

    <div v-if="callResult" class="card slide-up">
      <h3>Result</h3>
      <CodeBlock :code="typeof callResult === 'string' ? callResult : JSON.stringify(callResult, null, 2)" language="json" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listMcpTools, callMcpTool } from '@/api/client'
import CodeBlock from '@/components/shared/CodeBlock.vue'

const tools = ref<any[]>([])
const callResult = ref<any>(null)

async function refresh() {
  try { const res = await listMcpTools(); tools.value = res.tools || [] } catch {}
}

async function handleCall(tool: any) {
  try {
    const args: Record<string, any> = {}
    if (tool.inputSchema?.properties) {
      for (const [key, prop] of Object.entries(tool.inputSchema.properties)) {
        if (prop.type === 'string') args[key] = ''
        else if (prop.type === 'integer') args[key] = 0
        else if (prop.type === 'number') args[key] = 0
        else if (prop.type === 'boolean') args[key] = false
        else args[key] = ''
      }
    }
    callResult.value = await callMcpTool(tool.name, args)
  } catch (e: any) { callResult.value = { error: e.message } }
}

onMounted(refresh)
</script>

<style scoped>
.tools-page {
  max-width: 680px;
  margin: 0 auto;
  padding: var(--space-6);
}
h2 { font-size: var(--font-size-lg); font-weight: 700; margin-bottom: var(--space-5); }

.tool-list { display: flex; flex-direction: column; gap: var(--space-3); margin-bottom: var(--space-5); }
.tool-card {
  padding: var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  transition: all var(--transition-fast);
}
.tool-card:hover { border-color: var(--accent); }

.tool-header { display: flex; align-items: center; gap: var(--space-3); margin-bottom: var(--space-2); }
.tool-icon { color: var(--accent); }
.tool-name { font-weight: 600; font-size: var(--font-size-sm); flex: 1; }

.tool-desc { font-size: var(--font-size-sm); color: var(--text-secondary); margin-bottom: var(--space-3); }

.tool-params { display: flex; flex-wrap: wrap; gap: var(--space-2); align-items: center; }
.params-title { font-size: var(--font-size-xs); color: var(--text-muted); }
.param-tag {
  display: inline-flex; gap: 4px;
  padding: 1px 8px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
}
.param-name { font-family: var(--font-mono); color: var(--text-primary); }
.param-type { color: var(--accent); }

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

.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  animation: slideUp 0.2s ease;
}
.card h3 { font-size: var(--font-size-base); font-weight: 600; margin-bottom: var(--space-3); }
@keyframes slideUp { from { transform: translateY(8px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
</style>
