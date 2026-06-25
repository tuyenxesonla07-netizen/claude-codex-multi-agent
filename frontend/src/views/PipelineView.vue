<template>
  <div class="pipeline-page">
    <div class="pipeline-header">
      <h2>Pipeline Compiler</h2>
      <p>Compile module schemas and generate production-ready code.</p>
    </div>

    <!-- Compile Form -->
    <section class="card">
      <h3>Compile</h3>
      <div class="form-row">
        <input v-model="projectName" placeholder="Project name..." class="input" />
      </div>
      <div class="form-row">
        <textarea v-model="requirement" placeholder="Describe your project requirement..." class="input" rows="3"></textarea>
      </div>
      <div class="form-row">
        <label class="label">Modules (optional)</label>
        <select v-model="selectedModules" multiple class="input" size="4">
          <option v-for="m in appStore.modules" :key="m" :value="m">{{ m }}</option>
        </select>
      </div>
      <button class="btn primary" @click="handleCompile" :disabled="compiling">
        {{ compiling ? 'Compiling...' : 'Compile Pipeline' }}
      </button>
    </section>

    <!-- Result -->
    <section v-if="compiled" class="card slide-up">
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
          <Badge :variant="gate.blocking ? 'warning' : 'default'">{{ gate.blocking ? 'BLOCKING' : 'advisory' }}</Badge>
          <span class="gate-name">{{ gate.name }}</span>
          <span class="gate-expr">{{ gate.metric }} {{ gate.operator }} {{ gate.threshold }}</span>
        </div>
      </div>

      <h3>Prompt Template</h3>
      <CodeBlock :code="compiled.prompt_template" language="markdown" />
    </section>

    <!-- Run -->
    <section class="card">
      <h3>Run Pipeline</h3>
      <div class="form-row">
        <textarea v-model="runRequirement" placeholder="Describe what to build..." class="input" rows="3"></textarea>
      </div>
      <button class="btn primary" @click="handleRun" :disabled="running">
        {{ running ? 'Running...' : 'Run Pipeline' }}
      </button>
    </section>

    <!-- Code Results -->
    <section v-if="Object.keys(codeArtifact).length" class="card slide-up">
      <h3>Generated Code</h3>
      <div v-for="(code, mod) in codeArtifact" :key="mod" class="code-section">
        <h4>{{ mod }} <span class="code-lines">{{ code.split('\n').length }} lines</span></h4>
        <CodeBlock :code="code" language="python" />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '@/stores'
import CodeBlock from '@/components/shared/CodeBlock.vue'
import Badge from '@/components/shared/Badge.vue'
import { compilePipeline, runPipeline } from '@/api/client'

const appStore = useAppStore()
const projectName = ref('Untitled')
const requirement = ref('')
const runRequirement = ref('')
const selectedModules = ref<string[]>([])
const compiled = ref<any>(null)
const codeArtifact = ref<Record<string, string>>({})
const compiling = ref(false)
const running = ref(false)

async function handleCompile() {
  compiling.value = true
  codeArtifact.value = {}
  try {
    const req: any = { project_name: projectName.value }
    if (requirement.value) req.requirement = requirement.value
    if (selectedModules.value.length) req.modules = selectedModules.value
    compiled.value = await compilePipeline(req)
  } catch (e: any) {
    console.error('Compile failed:', e)
  } finally {
    compiling.value = false
  }
}

async function handleRun() {
  if (!runRequirement.value.trim()) return
  running.value = true
  try {
    const result = await runPipeline(runRequirement.value, selectedModules.value.length ? selectedModules.value : undefined)
    if (result.code_artifact) codeArtifact.value = result.code_artifact
    if (result.compiled) compiled.value = result.compiled
  } catch (e: any) {
    console.error('Run failed:', e)
  } finally {
    running.value = false
  }
}
</script>

<style scoped>
.pipeline-page {
  max-width: 680px;
  margin: 0 auto;
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.pipeline-header { text-align: center; margin-bottom: var(--space-4); }
.pipeline-header h2 { font-size: var(--font-size-lg); font-weight: 700; margin-bottom: var(--space-1); }
.pipeline-header p { color: var(--text-secondary); font-size: var(--font-size-sm); }

.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
}
.card h3 { font-size: var(--font-size-base); font-weight: 600; margin-bottom: var(--space-4); }
.card h4 {
  font-size: var(--font-size-sm);
  font-weight: 600;
  margin-bottom: var(--space-2);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.form-row { margin-bottom: var(--space-3); }
.label {
  display: block;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-1);
}
.input {
  width: 100%;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: var(--font-size-base);
  outline: none;
  transition: border-color var(--transition-fast);
}
.input:focus { border-color: var(--accent); }
textarea.input { resize: vertical; min-height: 60px; }
select.input { height: auto; }

.btn {
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn:hover { background: var(--bg-hover); }
.btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.btn.primary:hover { background: var(--accent-hover); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.order-list { display: flex; flex-wrap: wrap; gap: var(--space-2); margin-bottom: var(--space-5); }
.order-item {
  display: flex; align-items: center; gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
}
.order-num { color: var(--accent); font-weight: 700; }

.gates-list { display: flex; flex-direction: column; gap: var(--space-2); margin-bottom: var(--space-5); }
.gate-item {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
}
.gate-name { flex: 1; }
.gate-expr { font-family: var(--font-mono); color: var(--text-muted); font-size: var(--font-size-xs); }

.code-section { margin-bottom: var(--space-4); }
.code-lines { color: var(--text-muted); font-weight: 400; font-size: var(--font-size-xs); }

.slide-up { animation: slideUp 0.3s ease; }
@keyframes slideUp {
  from { transform: translateY(12px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>
