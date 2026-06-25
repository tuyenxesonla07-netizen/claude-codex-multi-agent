<template>
  <div class="settings-view">
    <!-- LLM Provider Config -->
    <div class="card">
      <h2>LLM Provider</h2>
      <div class="form-row">
        <label>Backend</label>
        <select v-model="llmBackend" class="input">
          <option value="mock">Mock (Test)</option>
          <option value="anthropic">Anthropic Claude</option>
          <option value="deepseek">DeepSeek</option>
          <option value="qwen">Qwen (通义千问)</option>
          <option value="gemini">Google Gemini</option>
          <option value="minimax">MiniMax</option>
          <option value="glm">GLM (智谱)</option>
          <option value="openai-compatible">OpenAI-compatible</option>
        </select>
      </div>
      <div class="form-row">
        <label>API Key</label>
        <input v-model="llmApiKey" type="password" placeholder="sk-..." class="input" />
      </div>
      <div class="form-row">
        <label>Base URL</label>
        <input v-model="llmBaseUrl" placeholder="https://api.openai.com/v1" class="input" />
      </div>
      <div class="form-row">
        <label>Model</label>
        <input v-model="llmModel" placeholder="claude-opus-4-7" class="input" />
      </div>
      <button @click="saveLlmConfig" class="btn primary">Save</button>
    </div>

    <!-- Database Config -->
    <div class="card">
      <h2>Database</h2>
      <div class="form-row">
        <label>PostgreSQL</label>
        <input v-model="databaseUrl" placeholder="postgresql://user:pass@localhost:5432/db" class="input" />
      </div>
      <p class="hint">Leave empty to use SQLite fallback. Requires: pip install asyncpg</p>
      <button @click="saveDbConfig" class="btn primary">Save</button>
    </div>

    <!-- System Info -->
    <div class="card">
      <h2>System Info</h2>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Version</span>
          <span class="info-value">2.0.0</span>
        </div>
        <div class="info-item">
          <span class="info-label">LLM Providers</span>
          <span class="info-value">{{ providerCount }} available</span>
        </div>
        <div class="info-item">
          <span class="info-label">Backend</span>
          <span class="info-value">{{ llmBackend }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { healthCheck } from '@/api/client'

const llmBackend = ref('mock')
const llmApiKey = ref('')
const llmBaseUrl = ref('')
const llmModel = ref('')
const databaseUrl = ref('')
const providerCount = ref(0)

onMounted(async () => {
  try {
    await healthCheck()
  } catch { /* ignore */ }
})

function saveLlmConfig() {
  localStorage.setItem('llm_config', JSON.stringify({
    backend: llmBackend.value,
    api_key: llmApiKey.value,
    base_url: llmBaseUrl.value,
    model: llmModel.value,
  }))
  alert('LLM config saved (requires backend restart)')
}

function saveDbConfig() {
  localStorage.setItem('db_config', JSON.stringify({
    database_url: databaseUrl.value,
  }))
  alert('Database config saved (requires backend restart)')
}
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

.form-row { display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }
.form-row label { width: 120px; font-size: 14px; color: var(--text-muted); flex-shrink: 0; }

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

.hint { font-size: 12px; color: var(--text-muted); margin-bottom: 12px; }

.info-grid { display: flex; flex-direction: column; gap: 8px; }
.info-item {
  display: flex; justify-content: space-between;
  padding: 8px 12px; background: var(--bg); border-radius: 6px;
}
.info-label { color: var(--text-muted); }
.info-value { font-weight: 500; }
</style>
