<template>
  <div class="rag-view">
    <!-- Upload Section -->
    <div class="card">
      <h2>Upload Document</h2>
      <div class="upload-zone" @drop.prevent="onDrop" @dragover.prevent @click="fileInput?.click()">
        <p v-if="!uploading">Drop files here or click to upload (PDF, DOCX, TXT, MD)</p>
        <p v-else>Uploading...</p>
        <input ref="fileInput" type="file" hidden accept=".pdf,.docx,.txt,.md" @change="onFileSelect" />
      </div>

      <div class="form-row" style="margin-top:16px">
        <input v-model="crawlUrl" placeholder="https://example.com" class="input" />
        <button @click="handleCrawl" :disabled="crawling" class="btn primary">
          {{ crawling ? 'Crawling...' : 'Crawl URL' }}
        </button>
      </div>
    </div>

    <!-- Query Section -->
    <div class="card">
      <h2>Knowledge Base Query</h2>
      <div class="form-row">
        <input v-model="query" placeholder="Ask a question..." class="input" @keyup.enter="handleQuery" />
        <button @click="handleQuery" :disabled="querying" class="btn primary">
          {{ querying ? 'Querying...' : 'Search' }}
        </button>
      </div>

      <div v-if="queryResult" class="query-result">
        <div class="answer">
          <h3>Answer</h3>
          <p>{{ queryResult.answer }}</p>
        </div>
        <div v-if="queryResult.sources?.length" class="sources">
          <h3>Sources ({{ queryResult.sources.length }})</h3>
          <div v-for="(src, i) in queryResult.sources" :key="i" class="source-item">
            <span class="src-num">[{{ i + 1 }}]</span>
            <span class="src-source">{{ src.source }}</span>
            <p>{{ src.content }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Documents -->
    <div class="card">
      <h2>Documents ({{ documents.length }})</h2>
      <div class="doc-list">
        <div v-for="doc in documents" :key="doc.document_id" class="doc-item">
          <div class="doc-info">
            <span class="doc-id">{{ doc.document_id.slice(0, 8) }}</span>
            <span class="doc-chunks">{{ doc.chunk_count }} chunks</span>
          </div>
          <button @click="handleDelete(doc.document_id)" class="btn danger small">Delete</button>
        </div>
        <div v-if="!documents.length" class="empty">No documents yet</div>
      </div>
    </div>
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
  try {
    const res = await listDocuments()
    documents.value = res.documents || []
  } catch { /* ignore */ }
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
  try {
    await uploadDocument(file)
    await refreshDocs()
  } catch (e: any) {
    alert('Upload failed: ' + e.message)
  } finally {
    uploading.value = false
  }
}

async function handleCrawl() {
  if (!crawlUrl.value) return
  crawling.value = true
  try {
    await crawlDocument(crawlUrl.value)
    await refreshDocs()
    crawlUrl.value = ''
  } catch (e: any) {
    alert('Crawl failed: ' + e.message)
  } finally {
    crawling.value = false
  }
}

async function handleQuery() {
  if (!query.value) return
  querying.value = true
  try {
    queryResult.value = await ragQuery(query.value)
  } catch (e: any) {
    alert('Query failed: ' + e.message)
  } finally {
    querying.value = false
  }
}

async function handleDelete(docId: string) {
  try {
    await deleteDocument(docId)
    await refreshDocs()
  } catch (e: any) {
    alert('Delete failed: ' + e.message)
  }
}

refreshDocs()
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
.card h3 { font-size: 14px; margin: 12px 0 8px; color: var(--text-muted); }

.upload-zone {
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 40px;
  text-align: center;
  cursor: pointer;
  color: var(--text-muted);
  transition: border-color 0.2s;
}
.upload-zone:hover { border-color: var(--primary); }

.form-row { display: flex; gap: 12px; align-items: center; }

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
.btn.danger { background: transparent; color: var(--danger); border-color: var(--danger); }
.btn.small { padding: 4px 10px; font-size: 12px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.query-result { margin-top: 16px; }
.answer p { padding: 12px; background: var(--bg); border-radius: 6px; white-space: pre-wrap; }

.sources { margin-top: 12px; }
.source-item {
  padding: 10px 12px;
  background: var(--bg);
  border-radius: 6px;
  margin-bottom: 8px;
}
.src-num { color: var(--primary-light); font-weight: 600; margin-right: 8px; }
.src-source { font-size: 12px; color: var(--text-muted); }
.source-item p { margin-top: 4px; font-size: 13px; color: var(--text-muted); }

.doc-list { display: flex; flex-direction: column; gap: 8px; }
.doc-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: var(--bg); border-radius: 6px;
}
.doc-id { font-family: monospace; font-size: 13px; }
.doc-chunks { color: var(--text-muted); font-size: 13px; margin-left: 12px; }

.empty { color: var(--text-muted); text-align: center; padding: 20px; }
</style>
