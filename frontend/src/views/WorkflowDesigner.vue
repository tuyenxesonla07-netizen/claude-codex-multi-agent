<template>
  <div class="workflow-view">
    <!-- Workflow List -->
    <div class="card">
      <div class="card-header">
        <h2>Workflows</h2>
        <button @click="showCreate = !showCreate" class="btn primary small">+ New</button>
      </div>

      <!-- Create Form -->
      <div v-if="showCreate" class="create-form">
        <input v-model="newName" placeholder="Workflow name..." class="input" />
        <textarea v-model="newDef" placeholder='{"nodes":[...],"edges":[...]}' class="input" rows="4"></textarea>
        <button @click="handleCreate" class="btn primary small">Create</button>
      </div>

      <div class="wf-list">
        <div v-for="wf in workflows" :key="wf.id" class="wf-item" @click="selectWorkflow(wf)">
          <span class="wf-name">{{ wf.name }}</span>
          <span class="wf-nodes">{{ wf.node_count }} nodes</span>
        </div>
        <div v-if="!workflows.length" class="empty">No workflows yet</div>
      </div>
    </div>

    <!-- Workflow Detail -->
    <div v-if="currentWorkflow" class="card">
      <div class="card-header">
        <h2>{{ currentWorkflow.name }}</h2>
        <div>
          <button @click="handleRun" :disabled="running" class="btn primary small">
            {{ running ? 'Running...' : 'Run' }}
          </button>
          <button @click="handleDelete" class="btn danger small" style="margin-left:8px">Delete</button>
        </div>
      </div>

      <!-- Node Visualization -->
      <div class="node-graph">
        <div v-for="node in currentWorkflow.nodes" :key="node.id" class="graph-node" :class="node.type">
          <span class="node-type-badge">{{ node.type }}</span>
          <span class="node-name">{{ node.name || node.id }}</span>
          <span v-if="node.inputs?.length" class="node-inputs">← {{ node.inputs.join(', ') }}</span>
        </div>
      </div>

      <!-- Edges -->
      <div v-if="currentWorkflow.edges?.length" class="edges">
        <h3>Edges</h3>
        <div v-for="edge in currentWorkflow.edges" :key="edge.from + edge.to" class="edge-item">
          {{ edge.from }} → {{ edge.to }}
        </div>
      </div>
    </div>

    <!-- Run Result -->
    <div v-if="runResult" class="card">
      <h2>Run Result</h2>
      <div class="run-status" :class="runResult.status">{{ runResult.status }}</div>
      <div class="run-outputs">
        <div v-for="(output, key) in runResult.outputs" :key="key" class="output-item">
          <span class="output-key">{{ key }}</span>
          <pre>{{ typeof output === 'string' ? output : JSON.stringify(output, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listWorkflows, createWorkflow, getWorkflow, deleteWorkflow, runWorkflow, getWorkflowRun } from '@/api/client'

const workflows = ref<any[]>([])
const currentWorkflow = ref<any>(null)
const runResult = ref<any>(null)
const showCreate = ref(false)
const newName = ref('')
const newDef = ref('{\n  "nodes": [\n    {"id": "n1", "type": "llm", "name": "Step 1", "config": {"prompt": "Hello"}}\n  ],\n  "edges": []\n}')
const running = ref(false)

async function refresh() {
  try {
    const res = await listWorkflows()
    workflows.value = res.workflows || []
  } catch { /* ignore */ }
}

async function handleCreate() {
  try {
    const def = JSON.parse(newDef.value)
    def.name = newName.value || 'Untitled'
    await createWorkflow(def)
    showCreate.value = false
    newName.value = ''
    await refresh()
  } catch (e: any) {
    alert('Create failed: ' + e.message)
  }
}

async function selectWorkflow(wf: any) {
  try {
    currentWorkflow.value = await getWorkflow(wf.id)
    runResult.value = null
  } catch { /* ignore */ }
}

async function handleRun() {
  if (!currentWorkflow.value) return
  running.value = true
  try {
    const res = await runWorkflow(currentWorkflow.value.id, {})
    if (res.run_id) {
      // Poll for result
      setTimeout(async () => {
        try {
          runResult.value = await getWorkflowRun(res.run_id)
        } catch { /* ignore */ }
        running.value = false
      }, 2000)
    }
  } catch (e: any) {
    alert('Run failed: ' + e.message)
    running.value = false
  }
}

async function handleDelete() {
  if (!currentWorkflow.value) return
  try {
    await deleteWorkflow(currentWorkflow.value.id)
    currentWorkflow.value = null
    await refresh()
  } catch { /* ignore */ }
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
.card h2 { font-size: 16px; }
.card h3 { font-size: 14px; margin: 12px 0 8px; color: var(--text-muted); }

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }

.input {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 14px;
  color: var(--text);
  font-size: 14px;
  outline: none;
  width: 100%;
  margin-bottom: 8px;
  display: block;
}
.input:focus { border-color: var(--primary); }

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-hover);
  color: var(--text);
  cursor: pointer;
  font-size: 14px;
}
.btn.primary { background: var(--primary); }
.btn.danger { background: transparent; color: var(--danger); border-color: var(--danger); }
.btn.small { padding: 6px 12px; font-size: 12px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.create-form { margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }

.wf-list { display: flex; flex-direction: column; gap: 8px; }
.wf-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; background: var(--bg); border-radius: 6px;
  cursor: pointer;
}
.wf-item:hover { background: var(--bg-hover); }
.wf-name { font-weight: 500; }
.wf-nodes { color: var(--text-muted); font-size: 13px; }

.node-graph { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
.graph-node {
  padding: 12px 16px;
  background: var(--bg);
  border-radius: 8px;
  border: 1px solid var(--border);
  display: flex; flex-direction: column; gap: 4px;
  min-width: 150px;
}
.node-type-badge {
  font-size: 10px; font-weight: 600; padding: 2px 6px;
  border-radius: 3px; text-transform: uppercase;
  display: inline-block;
}
.graph-node.llm .node-type-badge { background: #1e3a5f; color: #60a5fa; }
.graph-node.rag .node-type-badge { background: #1a3a2a; color: #4ade80; }
.graph-node.tool .node-type-badge { background: #3a2a1a; color: #fbbf24; }
.graph-node.code .node-type-badge { background: #3b1f5e; color: #c084fc; }
.graph-node.branch .node-type-badge { background: #3a1a1a; color: #f87171; }

.node-name { font-weight: 500; font-size: 14px; }
.node-inputs { font-size: 12px; color: var(--text-muted); }

.edges { margin-top: 12px; }
.edge-item { padding: 4px 0; font-family: monospace; font-size: 13px; color: var(--text-muted); }

.run-status { font-weight: 600; margin-bottom: 12px; }
.run-status.success { color: var(--success); }
.run-status.failed { color: var(--danger); }
.run-status.running { color: var(--warning); }

.output-item { margin-bottom: 8px; }
.output-key { font-weight: 600; font-size: 13px; }
.output-item pre {
  padding: 8px 12px; background: var(--bg); border-radius: 4px;
  font-size: 12px; overflow-x: auto; margin-top: 4px;
}

.empty { color: var(--text-muted); text-align: center; padding: 20px; }
</style>
