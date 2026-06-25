import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  listModules,
  listAgents,
  ragStats,
  listWorkflows,
  type CompileRequest,
} from '@/api/client'

// ─── App State ────────────────────────────────────────────────
export const useAppStore = defineStore('app', () => {
  const modules = ref<string[]>([])
  const agents = ref<any[]>([])
  const workflows = ref<any[]>([])
  const ragStatsData = ref({ total_chunks: 0, total_documents: 0 })
  const loading = ref(false)
  const error = ref('')

  async function fetchModules() {
    try {
      const res = await listModules()
      modules.value = res.modules || []
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function fetchAgents() {
    try {
      const res = await listAgents()
      agents.value = res.agents || []
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function fetchWorkflows() {
    try {
      const res = await listWorkflows()
      workflows.value = res.workflows || []
    } catch (e: any) {
      error.value = e.message
    }
  }

  async function fetchRagStats() {
    try {
      ragStatsData.value = await ragStats()
    } catch (e: any) {
      // RAG may not be available
    }
  }

  async function fetchAll() {
    loading.value = true
    try {
      await Promise.all([fetchModules(), fetchAgents(), fetchWorkflows(), fetchRagStats()])
    } finally {
      loading.value = false
    }
  }

  return {
    modules,
    agents,
    workflows,
    ragStatsData,
    loading,
    error,
    fetchModules,
    fetchAgents,
    fetchWorkflows,
    fetchRagStats,
    fetchAll,
  }
})

// ─── Pipeline State ───────────────────────────────────────────
export const usePipelineStore = defineStore('pipeline', () => {
  const compiled = ref<any>(null)
  const codeArtifact = ref<Record<string, string>>({})
  const status = ref<any>(null)
  const running = ref(false)

  async function compile(req: CompileRequest) {
    running.value = true
    try {
      const { compilePipeline } = await import('@/api/client')
      compiled.value = await compilePipeline(req)
      return compiled.value
    } finally {
      running.value = false
    }
  }

  async function run(requirement: string, modules?: string[]) {
    running.value = true
    try {
      const { runPipeline } = await import('@/api/client')
      const result = await runPipeline(requirement, modules)
      if (result.code_artifact) {
        codeArtifact.value = result.code_artifact
      }
      return result
    } finally {
      running.value = false
    }
  }

  return { compiled, codeArtifact, status, running, compile, run }
})

// ─── RAG State ────────────────────────────────────────────────
export const useRagStore = defineStore('rag', () => {
  const documents = ref<any[]>([])
  const queryResult = ref<any>(null)
  const loading = ref(false)

  async function fetchDocuments() {
    loading.value = true
    try {
      const { listDocuments } = await import('@/api/client')
      const res = await listDocuments()
      documents.value = res.documents || []
    } finally {
      loading.value = false
    }
  }

  async function upload(file: File) {
    const { uploadDocument } = await import('@/api/client')
    const res = await uploadDocument(file)
    await fetchDocuments()
    return res
  }

  async function crawl(url: string) {
    const { crawlDocument } = await import('@/api/client')
    const res = await crawlDocument(url)
    await fetchDocuments()
    return res
  }

  async function query(question: string, topK = 5) {
    loading.value = true
    try {
      const { ragQuery } = await import('@/api/client')
      queryResult.value = await ragQuery(question, topK)
      return queryResult.value
    } finally {
      loading.value = false
    }
  }

  async function remove(docId: string) {
    const { deleteDocument } = await import('@/api/client')
    await deleteDocument(docId)
    await fetchDocuments()
  }

  return { documents, queryResult, loading, fetchDocuments, upload, crawl, query, remove }
})

// ─── Workflow State ───────────────────────────────────────────
export const useWorkflowStore = defineStore('workflow', () => {
  const workflows = ref<any[]>([])
  const current = ref<any>(null)
  const runResult = ref<any>(null)
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      const { listWorkflows } = await import('@/api/client')
      const res = await listWorkflows()
      workflows.value = res.workflows || []
    } finally {
      loading.value = false
    }
  }

  async function create(definition: Record<string, any>) {
    const { createWorkflow } = await import('@/api/client')
    const res = await createWorkflow(definition)
    await fetchAll()
    return res
  }

  async function get(id: string) {
    const { getWorkflow } = await import('@/api/client')
    current.value = await getWorkflow(id)
    return current.value
  }

  async function run(id: string, inputData: Record<string, any> = {}) {
    const { runWorkflow } = await import('@/api/client')
    return await runWorkflow(id, inputData)
  }

  async function getRun(runId: string) {
    const { getWorkflowRun } = await import('@/api/client')
    runResult.value = await getWorkflowRun(runId)
    return runResult.value
  }

  return { workflows, current, runResult, loading, fetchAll, create, get, run, getRun }
})
