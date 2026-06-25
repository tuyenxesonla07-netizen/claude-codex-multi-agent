<template>
  <span class="badge" :class="`badge-${variant}`">
    <span v-if="dot" class="badge-dot"></span>
    <slot />
  </span>
</template>

<script setup lang="ts">
defineProps<{
  variant?: 'expert' | 'supervisor' | 'integrator' | 'plugin' | 'success' | 'error' | 'warning' | 'info' | 'default' | 'llm' | 'rag' | 'tool' | 'code' | 'branch'
  dot?: boolean
}>()
</script>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.badge-dot {
  width: 5px; height: 5px;
  border-radius: var(--radius-full);
  background: currentColor;
}

/* Role colors */
.badge-expert { background: #1e3a5f; color: #60a5fa; }
.badge-supervisor { background: #3b1f5e; color: #c084fc; }
.badge-integrator { background: #1a3a2a; color: #4ade80; }
.badge-plugin { background: #3a2a1a; color: #fbbf24; }

/* Status colors */
.badge-success { background: #1a3a2a; color: #4ade80; }
.badge-error { background: #3a1a1a; color: #f87171; }
.badge-warning { background: #3a2a1a; color: #fbbf24; }
.badge-info { background: #1e3a5f; color: #60a5fa; }
.badge-default { background: var(--bg-tertiary); color: var(--text-muted); }

/* Node type colors */
.badge-llm { background: #1e3a5f; color: #60a5fa; }
.badge-rag { background: #1a3a2a; color: #4ade80; }
.badge-tool { background: #3a2a1a; color: #fbbf24; }
.badge-code { background: #3b1f5e; color: #c084fc; }
.badge-branch { background: #3a1a1a; color: #f87171; }
</style>
