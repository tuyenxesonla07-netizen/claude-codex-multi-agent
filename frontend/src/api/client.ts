import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('[API Error]', err.response?.status, err.message)
    return Promise.reject(err)
  },
)

export default client

// ─── Pipeline API ──────────────────────────────────────────────
export interface CompileRequest {
  project_name?: string
  project_description?: string
  modules?: string[]
  global_constraints?: Record<string, string>
}

export async function compilePipeline(req: CompileRequest) {
  const { data } = await client.post('/pipeline/compile', req)
  return data
}

export async function runPipeline(requirement: string, modules?: string[], stream = false) {
  const { data } = await client.post('/pipeline/run', { requirement, modules, stream })
  return data
}

export async function getPipelineStatus(taskId: string) {
  const { data } = await client.get(`/pipeline/status/${taskId}`)
  return data
}

// ─── Agent API ─────────────────────────────────────────────────
export async function listAgents() {
  const { data } = await client.get('/agents')
  return data
}

export async function callAgent(moduleName: string, body: Record<string, any>) {
  const { data } = await client.post(`/agent/${moduleName}/direct`, body)
  return data
}

// ─── RAG API ──────────────────────────────────────────────────
export async function uploadDocument(file: File) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post('/rag/documents/upload', form)
  return data
}

export async function crawlDocument(url: string) {
  const { data } = await client.post('/rag/documents/crawl', { url })
  return data
}

export async function listDocuments(limit = 100, offset = 0) {
  const { data } = await client.get('/rag/documents', { params: { limit, offset } })
  return data
}

export async function deleteDocument(docId: string) {
  const { data } = await client.delete(`/rag/documents/${docId}`)
  return data
}

export async function ragQuery(question: string, topK = 5) {
  const { data } = await client.post('/rag/query', { question, top_k: topK })
  return data
}

export async function ragStats() {
  const { data } = await client.get('/rag/stats')
  return data
}

// ─── Workflow API ─────────────────────────────────────────────
export async function listWorkflows() {
  const { data } = await client.get('/workflows')
  return data
}

export async function createWorkflow(definition: Record<string, any>) {
  const { data } = await client.post('/workflows', definition)
  return data
}

export async function getWorkflow(id: string) {
  const { data } = await client.get(`/workflows/${id}`)
  return data
}

export async function deleteWorkflow(id: string) {
  const { data } = await client.delete(`/workflows/${id}`)
  return data
}

export async function runWorkflow(id: string, inputData: Record<string, any> = {}) {
  const { data } = await client.post(`/workflows/${id}/run`, inputData)
  return data
}

export async function getWorkflowRun(runId: string) {
  const { data } = await client.get(`/workflows/runs/${runId}`)
  return data
}

export async function listWorkflowRuns(workflowId: string) {
  const { data } = await client.get(`/workflows/${workflowId}/runs`)
  return data
}

// ─── MCP Tool API ─────────────────────────────────────────────
export async function listMcpTools() {
  const { data } = await client.get('/mcp/tools')
  return data
}

export async function callMcpTool(name: string, args: Record<string, any> = {}) {
  const { data } = await client.post(`/mcp/tools/${name}/call`, { name, arguments: args })
  return data
}

// ─── System ───────────────────────────────────────────────────
export async function healthCheck() {
  const { data } = await client.get('/health')
  return data
}

export async function listModules() {
  const { data } = await client.get('/modules')
  return data
}
