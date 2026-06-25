<template>
  <div class="wf-page">
    <div class="page-header">
      <h2>Workflows</h2>
      <button class="btn primary" @click="showCreate = !showCreate">
        {{ showCreate ? 'Cancel' : '+ New' }}
      </button>
    </div>

    <!-- Create Form -->
    <div v-if="showCreate" class="card slide-up">
      <div class="form-row">
        <input v-model="newName" placeholder="Workflow name..." class="input" />
      </div>
      <div class="form-row">
        <textarea v-model="newDef" placeholder='{"nodes":[...],"edges":[...]}' class="input" rows="3"></textarea>
      </div>
      <button class="btn primary" @click="handleCreate">Create</button>
    </div>

    <!-- Workflow List -->
    <div v-for="wf in workflows" :key="wf.id" class="card wf-card">
      <div class="wf-header">
        <div>
          <h3>{{ wf.name }}</h3>
          <span class="wf-meta">{{ wf.node_count }} nodes</span>
        </div>
        <div class="wf-actions">
          <button class="btn-sm" @click="handleRun(wf.id)" :disabled="running">▶ Run</button>
          <button class="btn-sm danger" @click="handleDelete(wf.id)">Delete</button>
        </div>
      </div>

      <!-- Node visualization -->
      <div class="node-graph">
        <div v-for="node in (wf.nodes || [])" :key="node.id" class="graph-node" :class="node.type">
          <span class="node-badge">{{ node.type }}</span>
          <span class="node-name">{{ node.name || node.id }}</span>
        </div>
      </div>
    </div>

    <div v-if="!workflows.length" class="empty">No workflows yet. Create one to get started.</div>

    <!-- Run Result -->
    <div v-if="runResult" class="card slide-up">
      <h3>Run Result</h3>
      <Badge :variant="runResult.status === 'success' ? 'success' : 'error'">{{ runResult.status }}</Badge>
      <div class="run-outputs">
        <div v-for="(output, key) in runResult.outputs || {}" :key="key" class="output-item">
          <span class="output-key">{{ key }}</span>
          <CodeBlock v-if="typeof output === 'string' && output.length > 200" :code="output" language="python" />
          <pre v-else class="output-short">{{ typeof output === 'string' ? output : JSON.stringify(output, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listWorkflows, createWorkflow, deleteWorkflow, runWorkflow, getWorkflowRun } from '@/api/client'
import CodeBlock from '@/components/shared/CodeBlock.vue'
import Badge from '@/components/shared/Badge.vue'

const workflows = ref<any[]>([])
const runResult = ref<any>(null)
const showCreate = ref(false)
const newName = ref('')
const newDef = ref('{\n  "nodes": [\n    {"id": "n1", "type": "llm", "name": "Step 1", "config": {"prompt": "Hello"}}\n  ],\n  "edges": []\n}')
const running = ref(false)

async function refresh() {
  try { const res = await listWorkflows(); workflows.value = res.workflows || [] } catch {}
}

async function handleCreate() {
  try {
    const def = JSON.parse(newDef.value)
    def.name = newName.value || 'Untitled'
    await createWorkflow(def)
    showCreate.value = false
    newName.value = ''
    await refresh()
  } catch (e: any) { alert('Invalid JSON: ' + e.message) }
}

async function handleRun(id: string) {
  running.value = true
  try {
    const res = await runWorkflow(id, {})
    if (res.run_id) {
      setTimeout(async () => {
        try { runResult.value = await getWorkflowRun(res.run_id) } catch {}
        running.value = false
      }, 2000)
    }
  } catch { running.value = false }
}

async function handleDelete(id: string) {
  try { await deleteWorkflow(id); await refresh() } catch {}
}

onMounted(refresh)
</script>

<style scoped>
.wf-page {
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

.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  margin-bottom: var(--space-4);
}
.card h3 { font-size: var(--font-size-base); font-weight: 600; }

.form-row { margin-bottom: var(--space-3); }
.input {
  width: 100%;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  outline: none;
}
.input:focus { border-color: var(--accent); }

.btn {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn:hover { background: var(--bg-hover); }
.btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.btn.primary:hover { background: var(--accent-hover); }

.btn-sm {
  padding: var(--space-1) var(--space-3);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn-sm:hover { border-color: var(--accent); color: var(--accent); }
.btn-sm.danger:hover { border-color: var(--error); color: var(--error); }

.wf-card { padding: var(--space-4); }
.wf-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--space-3); }
.wf-meta { font-size: var(--font-size-xs); color: var(--text-muted); }
.wf-actions { display: flex; gap: var(--space-2); }

.node-graph { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.graph-node {
  padding: var(--space-2) var(--space-3);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 100px;
}
.node-badge {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  padding: 1px 4px;
  border-radius: var(--radius-sm);
  display: inline-block;
}
.graph-node.llm .node-badge { background: #1e3a5f; color: #60a5fa; }
.graph-node.rag .node-badge { background: #1a3a2a; color: #4ade80; }
.graph-node.tool .node-badge { background: #3a2a1a; color: #fbbf24; }
.graph-node.code .node-badge { background: #3b1f5e; color: #c084fc; }
.graph-node.branch .node-badge { background: #3a1a1a; color: #f87171; }
.node-name { font-size: var(--font-size-xs); color: var(--text-secondary); }

.run-outputs { margin-top: var(--space-3); }
.output-item { margin-bottom: var(--space-2); }
.output-key { font-weight: 600; font-size: var(--font-size-sm); display: block; margin-bottom: var(--space-1); }
.output-short {
  font-family: var(--font-mono);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  background: var(--bg-primary);
  padding: var(--space-2);
  border-radius: var(--radius-sm);
  white-space: pre-wrap;
  max-height: 120px;
  overflow: auto;
}

.empty { text-align: center; color: var(--text-muted); padding: var(--space-8); }
.slide-up { animation: slideUp 0.2s ease; }
@keyframes slideUp { from { transform: translateY(8px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
</style>
