<template>
  <div class="rag-page">
    <div class="page-header">
      <h2>Knowledge Base</h2>
    </div>

    <!-- Upload + Crawl -->
    <section class="card">
      <div class="upload-zone" @drop.prevent="onDrop" @dragover.prevent @click="fileInput?.click()">
        <span class="upload-icon">📄</span>
        <p v-if="!uploading">Drop files here or click to upload (PDF, DOCX, TXT, MD)</p>
        <p v-else>Uploading...</p>
        <input ref="fileInput" type="file" hidden accept=".pdf,.docx,.txt,.md" @change="onFileSelect" />
      </div>
      <div class="crawl-row">
        <input v-model="crawlUrl" placeholder="https://example.com" class="input" />
        <button class="btn" @click="handleCrawl" :disabled="crawling">
          {{ crawling ? 'Crawling...' : 'Crawl URL' }}
        </button>
      </div>
    </section>

    <!-- Query -->
    <section class="card">
      <h3>Ask a Question</h3>
      <div class="query-row">
        <input v-model="query" placeholder="Ask about your documents..." class="input" @keyup.enter="handleQuery" />
        <button class="btn primary" @click="handleQuery" :disabled="querying">
          {{ querying ? 'Searching...' : 'Search' }}
        </button>
      </div>

      <div v-if="queryResult" class="query-result">
        <div class="answer">{{ queryResult.answer }}</div>
        <div v-if="queryResult.sources?.length" class="sources">
          <h4>Sources ({{ queryResult.sources.length }})</h4>
          <div v-for="(src, i) in queryResult.sources" :key="i" class="source-item">
            <span class="src-num">[{{ i + 1 }}]</span>
            <span class="src-source">{{ src.source }}</span>
            <p>{{ src.content }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Documents -->
    <section class="card">
      <h3>Documents ({{ documents.length }})</h3>
      <div class="doc-list">
        <div v-for="doc in documents" :key="doc.document_id" class="doc-item">
          <div class="doc-info">
            <span class="doc-id">{{ doc.document_id.slice(0, 8) }}</span>
            <span class="doc-chunks">{{ doc.chunk_count }} chunks</span>
          </div>
          <button class="btn-sm danger" @click="handleDelete(doc.document_id)">Delete</button>
        </div>
        <div v-if="!documents.length" class="empty">No documents yet</div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { uploadDocument, crawlDocument, ragQuery, listDocuments, deleteDocument } from '@/api/client'

const fileInput = ref<HTMLInputElement>()
const uploading = ref(false)
const crawling = ref(false)
const querying = ref(false)
const crawlUrl = ref('')
const query = ref('')
const queryResult = ref<any>(null)
const documents = ref<any[]>([])

async function refreshDocs() {
  try { const res = await listDocuments(); documents.value = res.documents || [] } catch {}
}

async function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.length) await uploadFile(target.files[0])
}

async function onDrop(e: DragEvent) {
  const file = e.dataTransfer?.files[0]
  if (file) await uploadFile(file)
}

async function uploadFile(file: File) {
  uploading.value = true
  try { await uploadDocument(file); await refreshDocs() } catch {}
  finally { uploading.value = false }
}

async function handleCrawl() {
  if (!crawlUrl.value) return
  crawling.value = true
  try { await crawlDocument(crawlUrl.value); await refreshDocs(); crawlUrl.value = '' } catch {}
  finally { crawling.value = false }
}

async function handleQuery() {
  if (!query.value.trim()) return
  querying.value = true
  try { queryResult.value = await ragQuery(query.value) } catch {}
  finally { querying.value = false }
}

async function handleDelete(docId: string) {
  try { await deleteDocument(docId); await refreshDocs() } catch {}
}

refreshDocs()
</script>

<style scoped>
.rag-page {
  max-width: 680px;
  margin: 0 auto;
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.page-header h2 { font-size: var(--font-size-lg); font-weight: 700; }

.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
}
.card h3 { font-size: var(--font-size-base); font-weight: 600; margin-bottom: var(--space-3); }

.upload-zone {
  border: 2px dashed var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  text-align: center;
  cursor: pointer;
  color: var(--text-muted);
  transition: border-color var(--transition-fast);
}
.upload-zone:hover { border-color: var(--accent); color: var(--text-secondary); }
.upload-icon { font-size: 28px; display: block; margin-bottom: var(--space-2); }

.crawl-row { display: flex; gap: var(--space-3); margin-top: var(--space-3); }
.input {
  flex: 1;
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

.btn {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}
.btn:hover { background: var(--bg-hover); }
.btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.btn.primary:hover { background: var(--accent-hover); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.query-row { display: flex; gap: var(--space-3); }
.query-result { margin-top: var(--space-4); }
.answer {
  padding: var(--space-3) var(--space-4);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-3);
  line-height: var(--line-height);
}
.sources h4 { font-size: var(--font-size-sm); color: var(--text-muted); margin-bottom: var(--space-2); }
.source-item {
  padding: var(--space-2) var(--space-3);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-2);
  border-left: 3px solid var(--accent);
}
.src-num { color: var(--accent); font-weight: 600; margin-right: var(--space-2); }
.src-source { font-size: var(--font-size-xs); color: var(--text-muted); }
.source-item p { font-size: var(--font-size-sm); color: var(--text-secondary); margin-top: var(--space-1); }

.doc-list { display: flex; flex-direction: column; gap: var(--space-2); }
.doc-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: var(--space-2) var(--space-3);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
}
.doc-id { font-family: var(--font-mono); font-size: var(--font-size-sm); }
.doc-chunks { color: var(--text-muted); font-size: var(--font-size-xs); margin-left: var(--space-3); }

.btn-sm {
  padding: var(--space-1) var(--space-3);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text-muted);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.btn-sm:hover { border-color: var(--accent); color: var(--accent); }
.btn-sm.danger:hover { border-color: var(--error); color: var(--error); }

.empty { text-align: center; color: var(--text-muted); padding: var(--space-6); }
</style>
