// In production (Vercel/Netlify), set VITE_API_URL to your backend origin (e.g. https://your-backend.railway.app)
const BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL.replace(/\/$/, '')}/api` : '/api'

export interface ConnectionBody {
  host?: string
  port?: number
  user?: string
  password?: string
  database?: string
  database_type?: string
}

export interface ChatRequest {
  message: string
  include_summary?: boolean
  connection?: ConnectionBody | null
}

export interface SingleResult {
  sql: string
  columns: string[]
  rows: unknown[][]
  row_count: number
}

export interface ChatResponse {
  sql: string
  valid: boolean
  error: string | null
  columns: string[]
  rows: unknown[][]
  row_count: number
  summary: string | null
  intent?: { intent: string; entities: string[]; summary: string }
  multi_results?: SingleResult[]  // when user asks for "tables separately"
}

export interface SyncSchemaResponse {
  tables: number
  chunks: number
  vectors_upserted: number
}

export interface SyncSchemaAsyncResponse {
  job_id: string
  status: string
  message?: string
}

export interface SyncStatusResponse {
  job_id: string
  status: 'running' | 'done' | 'failed'
  result?: SyncSchemaResponse
  error?: string
}

export const api = {
  async chat(body: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },
  async syncSchema(body: { connection?: ConnectionBody | null; async_mode?: boolean } = {}): Promise<SyncSchemaResponse | SyncSchemaAsyncResponse> {
    const res = await fetch(`${BASE}/sync-schema`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },
  async syncStatus(jobId: string): Promise<SyncStatusResponse> {
    const res = await fetch(`${BASE}/sync-status?job_id=${encodeURIComponent(jobId)}`)
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },
  async evaluate(): Promise<{
    n: number
    faithfulness_avg: number
    answer_relevancy_avg: number
    context_precision_avg: number
    context_recall_avg: number
    execution_accuracy_avg: number
    results: unknown[]
  }> {
    const res = await fetch(`${BASE}/evaluate`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    return res.json()
  },
}
