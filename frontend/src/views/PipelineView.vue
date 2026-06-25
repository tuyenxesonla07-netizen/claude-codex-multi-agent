<template>
  <div class="pipeline-view">
    <!-- Compile Section -->
    <div class="card">
      <h2>Compile Pipeline</h2>
      <div class="form-row">
        <input v-model="projectName" placeholder="Project name..." class="input" />
        <input v-model="requirement" placeholder="Requirement text..." class="input wide" />
        <button @click="handleCompile" :disabled="compiling" class="btn primary">
          {{ compiling ? 'Compiling...' : 'Compile' }}
        </button>
      </div>

      <!-- Compiled Result -->
      <div v-if="compiled" class="result-section">
        <h3>Implementation Order</h3>
        <div class="order-list">
          <div v-for="(mod, idx) in compiled.implementation_order" :key="mod" class="order-item">
            <span class="order-num">{{ idx + 1 }}</span>
            <span class="order-name">{{ mod }}</span>
          </div>
        </div>

        <h3>Quality Gates ({{ compiled.quality_gates?.length || 0 }})</h3>
        <div class="gates-list">
          <div v-for="gate in compiled.quality_gates" :key="gate.name" class="gate-item">
            <span class="gate-name">{{ gate.name }}</span>
            <span class="gate-expr">{{ gate.metric }} {{ gate.operator }} {{ gate.threshold }}</span>
            <span v-if="gate.blocking" class="gate-blocking">BLOCKING</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Run Section -->
    <div class="card">
      <h2>Run Pipeline</h2>
      <div class="form-row">
        <textarea v-model="runRequirement" placeholder="Describe what to build..." class="input wide" rows="3"></textarea>
      </div>
      <div class="form-row">
        <button @click="handleRun" :disabled="running" class="btn primary">
          {{ running ? 'Running...' : 'Run Pipeline' }}
        </button>
      </div>

      <!-- Code Results -->
      <div v-if="Object.keys(codeArtifact).length" class="code-results">
        <h3>Generated Code</h3>
        <div v-for="(code, mod) in codeArtifact" :key="mod" class="code-block">
          <div class="code-header">
            <span class="code-mod">{{ mod }}</span>
            <span class="code-lines">{{ code.split('\n').length }} lines</span>
          </div>
          <pre><code>{{ code }}</code></pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { compilePipeline, runPipeline } from '@/api/client'

const projectName = ref('Untitled')
const requirement = ref('')
const runRequirement = ref('')
const compiled = ref<any>(null)
const codeArtifact = ref<Record<string, string>>({})
const compiling = ref(false)
const running = ref(false)

async function handleCompile() {
  compiling.value = true
  try {
    compiled.value = await compilePipeline({
      project_name: projectName.value,
      requirement: requirement.value || undefined,
    })
  } catch (e: any) {
    alert('Compile failed: ' + e.message)
  } finally {
    compiling.value = false
  }
}

async function handleRun() {
  running.value = true
  try {
    const result = await runPipeline(runRequirement.value)
    if (result.code_artifact) {
      codeArtifact.value = result.code_artifact
    }
  } catch (e: any) {
    alert('Run failed: ' + e.message)
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.form-row { display: flex; gap: 12px; margin-bottom: 16px; align-items: flex-start; }

.input {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 14px;
  color: var(--text);
  font-size: 14px;
  outline: none;
  flex: 1;
}
.input:focus { border-color: var(--primary); }
.input.wide { flex: 2; }

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-hover);
  color: var(--text);
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}
.btn.primary { background: var(--primary); border-color: var(--primary); }
.btn.primary:hover { background: var(--primary-dark); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 24px;
}
.card h2 { font-size: 16px; margin-bottom: 16px; }
.card h3 { font-size: 14px; margin: 16px 0 8px; color: var(--text-muted); }

.order-list { display: flex; flex-wrap: wrap; gap: 8px; }
.order-item {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 12px; background: var(--bg); border-radius: 6px;
}
.order-num { color: var(--primary-light); font-weight: 700; }

.gates-list { display: flex; flex-direction: column; gap: 4px; }
.gate-item { display: flex; gap: 12px; padding: 6px 12px; background: var(--bg); border-radius: 4px; font-size: 13px; }
.gate-name { flex: 1; }
.gate-expr { color: var(--text-muted); font-family: monospace; }
.gate-blocking { font-size: 10px; color: var(--danger); font-weight: 600; }

.code-results { margin-top: 16px; }
.code-block { margin-bottom: 16px; border-radius: 6px; overflow: hidden; border: 1px solid var(--border); }
.code-header {
  display: flex; justify-content: space-between;
  padding: 8px 16px; background: var(--bg-hover);
  font-size: 13px;
}
.code-mod { font-weight: 600; }
.code-lines { color: var(--text-muted); }
pre { padding: 16px; overflow-x: auto; font-size: 13px; line-height: 1.5; margin: 0; }
code { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
</style>
