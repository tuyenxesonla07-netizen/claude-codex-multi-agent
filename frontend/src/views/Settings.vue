<template>
  <div class="settings-page">
    <h2>Settings</h2>

    <!-- LLM Provider -->
    <section class="card">
      <h3>LLM Provider</h3>
      <div class="form-row">
        <label class="label">Backend</label>
        <select v-model="llmBackend" class="input">
          <option value="mock">Mock (Test)</option>
          <option value="anthropic">Anthropic Claude</option>
          <option value="deepseek">DeepSeek</option>
          <option value="qwen">Qwen</option>
          <option value="gemini">Google Gemini</option>
          <option value="minimax">MiniMax</option>
          <option value="glm">GLM (智谱)</option>
          <option value="openai-compatible">OpenAI-compatible</option>
        </select>
      </div>
      <div class="form-row">
        <label class="label">API Key</label>
        <input v-model="llmApiKey" type="password" placeholder="sk-..." class="input" />
      </div>
      <div class="form-row">
        <label class="label">Base URL</label>
        <input v-model="llmBaseUrl" placeholder="https://api.openai.com/v1" class="input" />
      </div>
      <div class="form-row">
        <label class="label">Model</label>
        <input v-model="llmModel" placeholder="claude-opus-4-7" class="input" />
      </div>
      <div class="form-row">
        <label class="label">Temperature</label>
        <div class="slider-row">
          <input type="range" v-model.number="llmTemperature" min="0" max="1" step="0.1" class="slider" />
          <span class="slider-val">{{ llmTemperature }}</span>
        </div>
      </div>
      <button class="btn primary" @click="saveLlmConfig">Save</button>
    </section>

    <!-- Database -->
    <section class="card">
      <h3>Database</h3>
      <div class="form-row">
        <label class="label">PostgreSQL</label>
        <input v-model="databaseUrl" placeholder="postgresql://user:pass@localhost:5432/db" class="input" />
      </div>
      <p class="hint">Leave empty to use SQLite fallback. Requires: pip install asyncpg</p>
      <button class="btn primary" @click="saveDbConfig">Save</button>
    </section>

    <!-- System Info -->
    <section class="card">
      <h3>System Info</h3>
      <div class="info-grid">
        <div class="info-item"><span class="info-label">Version</span><span class="info-val">v3.0.0</span></div>
        <div class="info-item"><span class="info-label">LLM Backend</span><span class="info-val">{{ llmBackend }}</span></div>
        <div class="info-item"><span class="info-label">Modules</span><span class="info-val">{{ appStore.modules.length }}</span></div>
        <div class="info-item"><span class="info-label">Agents</span><span class="info-val">{{ appStore.agents.length }}</span></div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAppStore } from '@/stores'

const appStore = useAppStore()

const llmBackend = ref('mock')
const llmApiKey = ref('')
const llmBaseUrl = ref('')
const llmModel = ref('')
const llmTemperature = ref(0.7)
const databaseUrl = ref('')

onMounted(() => {
  const saved = localStorage.getItem('llm_config')
  if (saved) {
    try {
      const cfg = JSON.parse(saved)
      llmBackend.value = cfg.backend || 'mock'
      llmApiKey.value = cfg.api_key || ''
      llmBaseUrl.value = cfg.base_url || ''
      llmModel.value = cfg.model || ''
      llmTemperature.value = cfg.temperature ?? 0.7
    } catch {}
  }
  const dbSaved = localStorage.getItem('db_config')
  if (dbSaved) {
    try { databaseUrl.value = JSON.parse(dbSaved).database_url || '' } catch {}
  }
})

function saveLlmConfig() {
  localStorage.setItem('llm_config', JSON.stringify({
    backend: llmBackend.value, api_key: llmApiKey.value,
    base_url: llmBaseUrl.value, model: llmModel.value, temperature: llmTemperature.value,
  }))
  alert('LLM config saved (requires backend restart)')
}

function saveDbConfig() {
  localStorage.setItem('db_config', JSON.stringify({ database_url: databaseUrl.value }))
  alert('Database config saved (requires backend restart)')
}
</script>

<style scoped>
.settings-page {
  max-width: 560px;
  margin: 0 auto;
  padding: var(--space-6);
}
h2 { font-size: var(--font-size-lg); font-weight: 700; margin-bottom: var(--space-5); }

.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  margin-bottom: var(--space-4);
}
.card h3 { font-size: var(--font-size-base); font-weight: 600; margin-bottom: var(--space-4); }

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
  padding: var(--space-2) var(--space-3);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  outline: none;
  transition: border-color var(--transition-fast);
}
.input:focus { border-color: var(--accent); }
select.input { height: 36px; }

.slider-row { display: flex; align-items: center; gap: var(--space-3); }
.slider { flex: 1; accent-color: var(--accent); }
.slider-val { font-family: var(--font-mono); font-size: var(--font-size-sm); color: var(--accent); min-width: 30px; }

.hint { font-size: var(--font-size-xs); color: var(--text-muted); margin-bottom: var(--space-3); }

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

.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); }
.info-item {
  padding: var(--space-3);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
}
.info-label { display: block; font-size: var(--font-size-xs); color: var(--text-muted); margin-bottom: var(--space-1); }
.info-val { font-weight: 600; font-size: var(--font-size-sm); }
</style>
