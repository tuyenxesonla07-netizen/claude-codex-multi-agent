<template>
  <div class="dashboard">
    <!-- Centered Hero -->
    <div class="hero">
      <div class="hero-logo">✦</div>
      <h2>Claude-Codex Multi-Agent Pipeline</h2>
      <p>Schema-first multi-agent development pipeline — describe, compile, generate, review.</p>
      <div class="hero-actions">
        <button class="hero-btn primary" @click="$router.push('/pipeline')">▶ Run Pipeline</button>
        <button class="hero-btn" @click="$router.push('/rag')">📚 Knowledge Base</button>
      </div>
    </div>

    <!-- Quick Actions Grid -->
    <div class="grid">
      <div class="grid-card" @click="$router.push('/pipeline')">
        <span class="grid-icon">⛓</span>
        <h3>Pipeline</h3>
        <p>Compile schemas, generate code, review quality</p>
      </div>
      <div class="grid-card" @click="$router.push('/agents')">
        <span class="grid-icon">◈</span>
        <h3>Agents</h3>
        <p>{{ appStore.agents.length }} expert agents registered</p>
      </div>
      <div class="grid-card" @click="$router.push('/workflows')">
        <span class="grid-icon">⟳</span>
        <h3>Workflows</h3>
        <p>{{ appStore.workflows.length }} workflows configured</p>
      </div>
      <div class="grid-card" @click="$router.push('/tools')">
        <span class="grid-icon">⚙</span>
        <h3>Tools</h3>
        <p>MCP tools and built-in functions</p>
      </div>
    </div>

    <!-- Stats inline -->
    <div class="stats-row">
      <div class="stat-pill"><span class="stat-num">{{ appStore.modules.length }}</span> Modules</div>
      <div class="stat-pill"><span class="stat-num">{{ appStore.agents.length }}</span> Agents</div>
      <div class="stat-pill"><span class="stat-num">{{ appStore.ragStatsData.total_chunks || 0 }}</span> RAG Chunks</div>
      <div class="stat-pill"><span class="stat-num">{{ appStore.workflows.length }}</span> Workflows</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAppStore } from '@/stores'

const appStore = useAppStore()
onMounted(() => { appStore.fetchAll() })
</script>

<style scoped>
.dashboard {
  max-width: 680px;
  margin: 0 auto;
  padding: var(--space-10) var(--space-6);
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* ── Hero ── */
.hero {
  text-align: center;
  margin-bottom: var(--space-8);
}
.hero-logo {
  font-size: 42px;
  color: var(--accent);
  margin-bottom: var(--space-4);
  opacity: 0.9;
}
.hero h2 {
  font-size: var(--font-size-xl);
  font-weight: 700;
  margin-bottom: var(--space-2);
}
.hero p {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  margin-bottom: var(--space-5);
}
.hero-actions { display: flex; gap: var(--space-3); justify-content: center; }
.hero-btn {
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.hero-btn:hover { border-color: var(--accent); background: var(--accent-light); }
.hero-btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.hero-btn.primary:hover { background: var(--accent-hover); }

/* ── Grid ── */
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  width: 100%;
  margin-bottom: var(--space-8);
}
.grid-card {
  padding: var(--space-4) var(--space-5);
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.grid-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.grid-icon { font-size: 20px; display: block; margin-bottom: var(--space-2); }
.grid-card h3 { font-size: var(--font-size-base); font-weight: 600; margin-bottom: var(--space-1); }
.grid-card p { font-size: var(--font-size-sm); color: var(--text-muted); }

/* ── Stats ── */
.stats-row { display: flex; gap: var(--space-3); flex-wrap: wrap; justify-content: center; }
.stat-pill {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
.stat-num { color: var(--accent); font-weight: 700; }
</style>
