<template>
  <div class="app-shell">
    <!-- ── Sidebar: Conversation List ── -->
    <aside class="sidebar">
      <div class="sidebar-top">
        <button class="new-chat-btn" @click="newConversation">
          <span>+</span> New Chat
        </button>
        <div class="search-box">
          <span class="search-icon">⌕</span>
          <input v-model="searchQuery" placeholder="Search..." class="search-input" />
        </div>
      </div>

      <div class="conv-list">
        <div v-for="group in groupedConversations" :key="group.label" class="conv-group">
          <div class="conv-group-label">{{ group.label }}</div>
          <div
            v-for="conv in group.items"
            :key="conv.id"
            class="conv-item"
            :class="{ active: conv.id === currentConvId }"
            @click="selectConversation(conv.id)"
          >
            <span class="conv-icon">💬</span>
            <span class="conv-title">{{ conv.title }}</span>
          </div>
        </div>
        <div v-if="!conversations.length" class="conv-empty">No conversations yet</div>
      </div>

      <div class="sidebar-bottom">
        <button class="sidebar-btn" @click="$router.push('/settings')">⚙ Settings</button>
        <div class="user-avatar">{{ userInitial }}</div>
      </div>
    </aside>

    <!-- ── Main: Chat Area ── -->
    <main class="chat-main">
      <header class="chat-topbar">
        <h2>{{ currentTitle }}</h2>
        <div class="topbar-right">
          <span class="status-dot" :class="{ online: isOnline }"></span>
          <span class="status-label">{{ isOnline ? 'Connected' : 'Offline' }}</span>
        </div>
      </header>

      <div class="chat-body" ref="chatBodyRef">
        <!-- Messages -->
        <div v-for="msg in messages" :key="msg.id" class="msg-row" :class="`msg-${msg.role}`">
          <div class="msg-avatar">
            {{ msg.role === 'user' ? userInitial : '✦' }}
          </div>
          <div class="msg-content">
            <!-- Text -->
            <div v-if="msg.text" class="msg-text">{{ msg.text }}</div>
            <!-- Tool use -->
            <div v-if="msg.toolUse" class="tool-block">
              <div class="tool-header">
                <span class="tool-cog">⚙</span>
                <span class="tool-name">{{ msg.toolUse.name }}</span>
                <span class="tool-status" :class="msg.toolStatus">{{ msg.toolStatus }}</span>
              </div>
              <div v-if="msg.toolUse.args" class="tool-args">
                <CodeBlock :code="msg.toolUse.args" language="json" />
              </div>
            </div>
            <!-- Tool result -->
            <div v-if="msg.toolResult" class="tool-result">
              <div class="tool-result-header">
                <span>{{ msg.toolResult.ok ? '✓' : '✗' }}</span>
                <span>{{ msg.toolResult.ok ? 'Completed' : 'Failed' }}</span>
              </div>
            </div>
            <!-- Thinking -->
            <div v-if="msg.thinking" class="thinking-block" :class="{ expanded: msg.thinkingExpanded }">
              <div class="thinking-header" @click="msg.thinkingExpanded = !msg.thinkingExpanded">
                <span class="thinking-dot pulse">●</span>
                <span>Thinking...</span>
                <span class="thinking-toggle">{{ msg.thinkingExpanded ? '▾' : '▸' }}</span>
              </div>
              <div v-if="msg.thinkingExpanded" class="thinking-body">{{ msg.thinking }}</div>
            </div>
            <!-- Code -->
            <div v-if="msg.code" class="msg-code">
              <CodeBlock :code="msg.code" :language="msg.codeLang || 'python'" />
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="!messages.length" class="chat-empty">
          <div class="empty-logo">✦</div>
          <h3>Claude-Codex Multi-Agent</h3>
          <p>Describe what you want to build and I'll generate it with expert agents.</p>
          <div class="empty-actions">
            <button class="empty-btn" @click="quickSend('Build authentication module')">🔐 Auth Module</button>
            <button class="empty-btn" @click="quickSend('Create REST API for products')">📦 REST API</button>
            <button class="empty-btn" @click="quickSend('Design order system with state machine')">🔄 State Machine</button>
            <button class="empty-btn" @click="$router.push('/rag')">📚 Knowledge Base</button>
          </div>
        </div>
      </div>

      <!-- Input -->
      <div class="chat-inputbar">
        <!-- Attachment chips -->
        <div v-if="attachments.length" class="attachment-chips">
          <div v-for="(att, i) in attachments" :key="i" class="att-chip">
            <span class="att-icon">{{ att.icon }}</span>
            <span class="att-name">{{ att.name }}</span>
            <span class="att-remove" @click="removeAttachment(i)">×</span>
          </div>
        </div>
        <!-- Toolbar + Input -->
        <div class="input-wrapper">
          <!-- Attachment toolbar -->
          <div class="input-toolbar">
            <button class="tool-btn" @click="triggerUpload('files')" title="Add files or photos">
              <span class="tool-icon">📎</span><span class="tool-label">Files</span>
            </button>
            <button class="tool-btn" @click="triggerUpload('folder')" title="Add folder">
              <span class="tool-icon">📁</span><span class="tool-label">Folder</span>
            </button>
            <button class="tool-btn" @click="openConnectors" title="Add connectors">
              <span class="tool-icon">🔌</span><span class="tool-label">Connectors</span>
            </button>
            <button class="tool-btn" @click="openPlugins" title="Add plugins">
              <span class="tool-icon">🧩</span><span class="tool-label">Plugins</span>
            </button>
          </div>
          <textarea
            v-model="inputText"
            ref="inputRef"
            placeholder="Describe what to build... (Ctrl+Enter to send)"
            class="chat-input"
            rows="1"
            @input="autoResize"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.ctrl.enter.prevent="sendMessage"
            @paste="onPaste"
          />
          <button
            v-if="isStreaming"
            class="btn-stop"
            @click="stopGeneration"
            title="Stop (Esc)"
          >■</button>
          <button
            v-else
            class="btn-send"
            @click="sendMessage"
            :disabled="!inputText.trim() && !attachments.length"
            title="Send (Ctrl+Enter)"
          >➤</button>
        </div>
        <!-- Hidden file inputs -->
        <input ref="fileInput" type="file" multiple hidden @change="onFilePicked" />
        <input ref="folderInput" type="file" webkitdirectory hidden @change="onFolderPicked" />
      </div>

      <!-- Connector Picker -->
      <Teleport to="body">
        <div v-if="showConnectors" class="overlay" @click.self="showConnectors = false">
          <div class="picker-panel">
            <div class="picker-header"><h3>Connectors</h3><button class="picker-close" @click="showConnectors = false">×</button></div>
            <div class="picker-desc">Connect external data sources or services.</p></div>
            <div class="picker-grid">
              <div v-for="conn in connectors" :key="conn.id" class="picker-card" @click="addConnector(conn)">
                <span class="card-icon">{{ conn.icon }}</span>
                <span class="card-name">{{ conn.name }}</span>
                <span class="card-desc">{{ conn.desc }}</span>
              </div>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Plugin Picker -->
      <Teleport to="body">
        <div v-if="showPlugins" class="overlay" @click.self="showPlugins = false">
          <div class="picker-panel">
            <div class="picker-header"><h3>Plugins</h3><button class="picker-close" @click="showPlugins = false">×</button></div>
            <div class="picker-desc">Extend pipeline capabilities with plugins.</p></div>
            <div class="picker-grid">
              <div v-for="plugin in plugins" :key="plugin.id" class="picker-card" @click="addPlugin(plugin)">
                <span class="card-icon">{{ plugin.icon }}</span>
                <span class="card-name">{{ plugin.name }}</span>
                <span class="card-desc">{{ plugin.desc }}</span>
              </div>
            </div>
          </div>
        </div>
      </Teleport>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CodeBlock from '@/components/shared/CodeBlock.vue'
import { healthCheck } from '@/api/client'

const router = useRouter()

// ── Attachments ──
interface Attachment { type: string; name: string; icon: string; size?: string }

const attachments = ref<Attachment[]>([])
const fileInput = ref<HTMLInputElement>()
const folderInput = ref<HTMLInputElement>()
const showConnectors = ref(false)
const showPlugins = ref(false)

const connectors = [
  { id: 'db', name: 'Database', icon: '🗄', desc: 'PostgreSQL / MySQL / SQLite' },
  { id: 'api', name: 'REST API', icon: '🌐', desc: 'External API endpoint' },
  { id: 'git', name: 'Git Repo', icon: '🔀', desc: 'Clone & index a repository' },
  { id: 's3', name: 'S3 Bucket', icon: '☁', desc: 'AWS S3 / compatible storage' },
]

const plugins = [
  { id: 'review', name: 'Code Review', icon: '🔍', desc: 'Automated quality review agent' },
  { id: 'test', name: 'Test Gen', icon: '🧪', desc: 'Auto-generate test suites' },
  { id: 'deploy', name: 'Deploy', icon: '🚀', desc: 'CI/CD pipeline integration' },
  { id: 'docs', name: 'Doc Gen', icon: '📝', desc: 'Auto-generate documentation' },
]

function triggerUpload(type: 'files' | 'folder') {
  if (type === 'files') fileInput.value?.click()
  else folderInput.value?.click()
}

function onFilePicked(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files) return
  for (const f of Array.from(files)) {
    const isImage = f.type.startsWith('image/')
    attachments.value.push({
      type: 'file',
      name: f.name,
      icon: isImage ? '🖼' : '📄',
      size: f.size < 1024 ? f.size + 'B' : f.size < 1048576 ? (f.size / 1024).toFixed(0) + 'KB' : (f.size / 1048576).toFixed(1) + 'MB',
    })
  }
  e.target && ((e.target as HTMLInputElement).value = '')
}

function onFolderPicked(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (!files || !files.length) return
  const folderName = files[0].webkitRelativePath.split('/')[0]
  attachments.value.push({ type: 'folder', name: folderName, icon: '📁', size: files.length + ' files' })
  e.target && ((e.target as HTMLInputElement).value = '')
}

function onPaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  for (const item of Array.from(items)) {
    if (item.type.startsWith('image/')) {
      attachments.value.push({ type: 'image', name: 'Pasted image', icon: '🖼' })
    }
  }
}

function removeAttachment(i: number) {
  attachments.value.splice(i, 1)
}

function addConnector(conn: typeof connectors[0]) {
  attachments.value.push({ type: 'connector', name: conn.name, icon: conn.icon })
  showConnectors.value = false
}

function addPlugin(plugin: typeof plugins[0]) {
  attachments.value.push({ type: 'plugin', name: plugin.name, icon: plugin.icon })
  showPlugins.value = false
}
const isOnline = ref(false)
const searchQuery = ref('')
const inputText = ref('')
const inputRef = ref<HTMLTextAreaElement>()
const chatBodyRef = ref<HTMLElement>()
const isStreaming = ref(false)
const currentConvId = ref('default')
const userInitial = ref('U')

interface Conversation { id: string; title: string; timestamp: string }
interface ChatMsg {
  id: string; role: 'user' | 'assistant'; text?: string;
  toolUse?: { name: string; args: string }; toolStatus?: string;
  toolResult?: { ok: boolean };
  thinking?: string; thinkingExpanded?: boolean;
  code?: string; codeLang?: string;
}

const conversations = ref<Conversation[]>([
  { id: 'default', title: 'New Chat', timestamp: new Date().toISOString() },
])
const messages = ref<ChatMsg[]>([])

// ── Computed ──
const currentTitle = computed(() => {
  const conv = conversations.value.find(c => c.id === currentConvId.value)
  return conv?.title || 'New Chat'
})

const groupedConversations = computed(() => {
  const filtered = conversations.value.filter(c =>
    !searchQuery.value || c.title.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
  return [
    { label: 'Today', items: filtered },
  ]
})

// ── Methods ──
function newConversation() {
  const id = 'conv_' + Date.now()
  conversations.value.unshift({ id, title: 'New Chat', timestamp: new Date().toISOString() })
  currentConvId.value = id
  messages.value = []
}

function selectConversation(id: string) {
  currentConvId.value = id
  messages.value = []  // In real app, load from store
}

function quickSend(text: string) {
  inputText.value = text
  sendMessage()
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text && !attachments.value.length) return

  const userText = attachments.value.length
    ? `${text}\n\n[Attachments: ${attachments.value.map(a => a.name).join(', ')}]`
    : text

  messages.value.push({ id: 'm_' + Date.now(), role: 'user', text: userText })
  inputText.value = ''
  attachments.value = []
  autoResize()
  scrollToBottom()

  isStreaming.value = true
  await simulateResponse(text)
  isStreaming.value = false
}

async function simulateResponse(input: string) {
  const msgId = 'm_' + Date.now()
  const assistantMsg: ChatMsg = { id: msgId, role: 'assistant', text: '' }
  messages.value.push(assistantMsg)
  const idx = messages.value.length - 1

  // Thinking
  assistantMsg.thinking = 'Analyzing requirement, selecting agents, preparing compilation...'
  await delay(600)
  assistantMsg.thinkingExpanded = false

  // Tool use
  assistantMsg.toolUse = { name: 'compile_pipeline', args: JSON.stringify({ input }, null, 2) }
  assistantMsg.toolStatus = 'running'
  await delay(800)
  assistantMsg.toolStatus = 'done'

  // Tool result
  assistantMsg.toolResult = { ok: true }
  await delay(300)

  // Code
  assistantMsg.code = `# Generated for: ${input}\nclass AuthService:\n    """Authentication service with JWT."""\n    def login(self, email: str, password: str) -> dict:\n        ...\n`
  assistantMsg.codeLang = 'python'

  // Text
  assistantMsg.text = `I've analyzed your requirement and generated the module. The compilation pipeline produced the following results:\n\n- **5 components** generated\n- **3 interfaces** defined\n- **Quality gates**: all passed`

  messages.value[idx] = { ...assistantMsg }
  scrollToBottom()
}

function stopGeneration() {
  isStreaming.value = false
}

function autoResize() {
  const el = inputRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatBodyRef.value) {
      chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
    }
  })
}

function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

onMounted(async () => {
  try { await healthCheck(); isOnline.value = true } catch {}
  inputText.value = ''
})
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-primary);
}

/* ── Sidebar ── */
.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.sidebar-top {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.new-chat-btn {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  transition: background var(--transition-fast);
}
.new-chat-btn:hover { background: var(--accent-hover); }

.search-box {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}
.search-icon { color: var(--text-muted); font-size: 14px; }
.search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  outline: none;
}
.search-input::placeholder { color: var(--text-muted); }

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-3);
}
.conv-group { margin-bottom: var(--space-4); }
.conv-group-label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: var(--space-2) var(--space-3);
}
.conv-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}
.conv-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.conv-item.active {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-left: 3px solid var(--accent);
}
.conv-icon { font-size: 13px; }
.conv-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-empty {
  text-align: center;
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  padding: var(--space-6);
}

.sidebar-bottom {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.sidebar-btn {
  flex: 1;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.sidebar-btn:hover { border-color: var(--accent); color: var(--accent); }
.user-avatar {
  width: 32px; height: 32px;
  border-radius: var(--radius-full);
  background: var(--accent-light);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  font-weight: 600;
}

/* ── Chat Main ── */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}
.chat-topbar {
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.chat-topbar h2 {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-primary);
}
.topbar-right { display: flex; align-items: center; gap: var(--space-2); }
.status-dot {
  width: 7px; height: 7px;
  border-radius: var(--radius-full);
  background: var(--error);
}
.status-dot.online { background: var(--success); }
.status-label { font-size: var(--font-size-xs); color: var(--text-muted); }

/* ── Messages ── */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.msg-row {
  display: flex;
  gap: var(--space-3);
  max-width: var(--chat-max-width);
  animation: slideUp 0.2s ease;
}
@keyframes slideUp {
  from { transform: translateY(8px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.msg-user { flex-direction: row-reverse; margin-left: auto; }
.msg-avatar {
  width: 28px; height: 28px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
  background: var(--bg-secondary);
  color: var(--text-secondary);
}
.msg-user .msg-avatar { background: var(--accent); color: #fff; }
.msg-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.msg-text {
  font-size: var(--font-size-base);
  line-height: var(--line-height);
  color: var(--text-primary);
  white-space: pre-wrap;
}

/* ── Tool Block ── */
.tool-block {
  background: var(--bg-tool);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.tool-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-secondary);
  font-size: var(--font-size-xs);
  font-family: var(--font-mono);
}
.tool-cog { color: var(--accent); }
.tool-name { color: var(--text-primary); font-weight: 500; }
.tool-status { margin-left: auto; color: var(--text-muted); }
.tool-status.running { color: var(--accent); }
.tool-status.done { color: var(--success); }
.tool-args { padding: var(--space-2); }

.tool-result {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  border-left: 3px solid var(--success);
}
.tool-result-header { display: flex; align-items: center; gap: var(--space-2); }

/* ── Thinking Block ── */
.thinking-block {
  background: var(--bg-secondary);
  border-left: 3px solid var(--accent);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  overflow: hidden;
}
.thinking-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  cursor: pointer;
  user-select: none;
}
.thinking-dot { color: var(--accent); font-size: 10px; }
.thinking-toggle { margin-left: auto; }
.thinking-body {
  padding: 0 var(--space-3) var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  font-style: italic;
}

.msg-code {
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border);
}

/* ── Empty State ── */
.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--space-10);
}
.empty-logo {
  font-size: 48px;
  color: var(--accent);
  margin-bottom: var(--space-4);
  opacity: 0.8;
}
.chat-empty h3 {
  font-size: var(--font-size-xl);
  font-weight: 700;
  margin-bottom: var(--space-2);
}
.chat-empty p {
  color: var(--text-secondary);
  font-size: var(--font-size-base);
  margin-bottom: var(--space-6);
  max-width: 400px;
}
.empty-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  max-width: 480px;
}
.empty-btn {
  padding: var(--space-3) var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
}
.empty-btn:hover {
  border-color: var(--accent);
  background: var(--accent-light);
  transform: translateY(-1px);
}

/* ── Attachment Chips ── */
.attachment-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4) 0;
}
.att-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 3px 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}
.att-chip:hover { border-color: var(--accent); }
.att-icon { font-size: 12px; }
.att-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.att-remove {
  font-size: 14px;
  color: var(--text-muted);
  cursor: pointer;
  margin-left: 2px;
  line-height: 1;
}
.att-remove:hover { color: var(--error); }

/* ── Input Bar ── */
.chat-inputbar {
  padding: var(--space-3) var(--space-6);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}
.input-wrapper {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  transition: border-color var(--transition-fast);
}
.input-wrapper:focus-within {
  border-color: var(--accent);
}

/* ── Toolbar ── */
.input-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: var(--space-2) var(--space-3) 0;
}
.tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.tool-btn:hover {
  background: var(--bg-secondary);
  border-color: var(--border);
  color: var(--text-primary);
}
.tool-btn:active {
  background: var(--bg-tertiary);
}
.tool-icon { font-size: 13px; }
.tool-label { font-weight: 500; }

.chat-input {
  width: 100%;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: var(--font-size-base);
  line-height: 1.5;
  resize: none;
  outline: none;
  max-height: 160px;
  padding: var(--space-2) var(--space-4);
}
.chat-input::placeholder { color: var(--text-muted); }

.btn-send, .btn-stop {
  width: 32px; height: 32px;
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  transition: all var(--transition-fast);
  align-self: flex-end;
  margin-bottom: var(--space-1);
}
.btn-send { background: var(--accent); color: #fff; }
.btn-send:hover { background: var(--accent-hover); }
.btn-send:disabled { background: var(--bg-tertiary); color: var(--text-muted); cursor: not-allowed; }
.btn-stop { background: var(--bg-tertiary); color: var(--error); }
.btn-stop:hover { background: var(--error); color: #fff; }

/* ── Picker Overlay ── */
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.15s ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.picker-panel {
  width: 420px;
  max-height: 520px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  animation: slideUp 0.2s ease;
}
@keyframes slideUp { from { transform: translateY(12px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-5) var(--space-2);
}
.picker-header h3 { font-size: var(--font-size-base); font-weight: 600; }
.picker-close {
  width: 28px; height: 28px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}
.picker-close:hover { border-color: var(--accent); color: var(--accent); }

.picker-desc {
  padding: 0 var(--space-5) var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.picker-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
  padding: 0 var(--space-5) var(--space-5);
  overflow-y: auto;
}
.picker-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.picker-card:hover {
  border-color: var(--accent);
  background: var(--accent-light);
  transform: translateY(-1px);
}
.card-icon { font-size: 20px; }
.card-name { font-size: var(--font-size-sm); font-weight: 600; }
.card-desc { font-size: var(--font-size-xs); color: var(--text-muted); line-height: 1.4; }
</style>
