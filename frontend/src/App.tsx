import { useState, useCallback, useEffect } from 'react'
import { ChatPanel } from './components/ChatPanel'
import { SQLPreview } from './components/SQLPreview'
import { ResultTable } from './components/ResultTable'
import { Header } from './components/Header'
import { MetricsDashboard } from './components/MetricsDashboard'
import { ConnectionForm, loadConnection, saveConnection } from './components/ConnectionForm'
import type { MetricsData } from './components/MetricsDashboard'
import type { ConnectionConfig } from './components/ConnectionForm'
import { api } from './api'
import type { ChatResponse, SyncSchemaResponse } from './api'

function connectionToBody(c: ConnectionConfig | null): { host: string; port: number; user: string; password: string; database: string; database_type: string } | null {
  if (!c || !c.database) return null
  return {
    host: c.host,
    port: c.port,
    user: c.user,
    password: c.password,
    database: c.database,
    database_type: c.database_type,
  }
}

export default function App() {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string; sql?: string; response?: ChatResponse }>>([])
  const [currentSql, setCurrentSql] = useState<string | null>(null)
  const [currentResult, setCurrentResult] = useState<ChatResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [schemaSyncing, setSchemaSyncing] = useState(false)
  const [evaluating, setEvaluating] = useState(false)
  const [metricsData, setMetricsData] = useState<MetricsData | null>(null)
  const [metricsError, setMetricsError] = useState<string | null>(null)
  const [connection, setConnection] = useState<ConnectionConfig>(() => loadConnection())
  const [connectionCollapsed, setConnectionCollapsed] = useState(true)

  useEffect(() => {
    saveConnection(connection)
  }, [connection])

  const handleSyncSchema = useCallback(async (useAsync = false) => {
    setSchemaSyncing(true)
    try {
      const body = { connection: connectionToBody(connection), async_mode: useAsync }
      const res = await api.syncSchema(body)
      if ('job_id' in res) {
        const jobId = res.job_id
        const poll = async (): Promise<SyncSchemaResponse> => {
          const status = await api.syncStatus(jobId)
          if (status.status === 'done' && status.result) return status.result
          if (status.status === 'failed') throw new Error(status.error || 'Sync failed')
          await new Promise((r) => setTimeout(r, 1500))
          return poll()
        }
        const result = await poll()
        alert(`Schema synced: ${result.tables} tables, ${result.chunks} chunks, ${result.vectors_upserted} vectors.`)
      } else {
        alert(`Schema synced: ${res.tables} tables, ${res.chunks} chunks, ${res.vectors_upserted} vectors.`)
      }
    } catch (e) {
      alert('Sync failed: ' + (e instanceof Error ? e.message : String(e)))
    } finally {
      setSchemaSyncing(false)
    }
  }, [connection])

  const handleEvaluate = useCallback(async () => {
    setEvaluating(true)
    setMetricsError(null)
    try {
      const res = await api.evaluate()
      setMetricsData({
        n: res.n,
        faithfulness_avg: res.faithfulness_avg,
        answer_relevancy_avg: res.answer_relevancy_avg,
        context_precision_avg: res.context_precision_avg,
        context_recall_avg: res.context_recall_avg,
        execution_accuracy_avg: res.execution_accuracy_avg,
        results: (res.results as MetricsData['results']) ?? [],
      })
    } catch (e) {
      setMetricsError(e instanceof Error ? e.message : String(e))
      setMetricsData(null)
    } finally {
      setEvaluating(false)
    }
  }, [])

  const handleSend = useCallback(async (text: string) => {
    if (!text.trim() || loading) return
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setLoading(true)
    setCurrentSql(null)
    setCurrentResult(null)
    try {
      const res = await api.chat({
        message: text,
        include_summary: true,
        connection: connectionToBody(connection),
      })
      setCurrentSql(res.sql)
      setCurrentResult(res)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.summary ?? (res.error ?? (res.valid ? `Returned ${res.row_count} row(s).` : 'Invalid SQL.')),
          sql: res.sql,
          response: res,
        },
      ])
    } catch (e) {
      const err = e instanceof Error ? e.message : String(e)
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error: ' + err }])
    } finally {
      setLoading(false)
    }
  }, [loading, connection])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <Header
        onSyncSchema={() => handleSyncSchema(false)}
        schemaSyncing={schemaSyncing}
        onEvaluate={handleEvaluate}
        evaluating={evaluating}
      />
      <ConnectionForm
        connection={connection}
        onChange={setConnection}
        onSave={() => saveConnection(connection)}
        collapsed={connectionCollapsed}
        onToggleCollapsed={() => setConnectionCollapsed((c) => !c)}
      />
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>
        <div style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden' }}>
          <ChatPanel messages={messages} onSend={handleSend} loading={loading} />
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, minHeight: 0, borderLeft: '1px solid var(--border)', overflow: 'auto' }}>
            {currentResult?.multi_results && currentResult.multi_results.length > 0 ? (
              currentResult.multi_results.map((r, i) => (
                <div key={i} style={{ borderBottom: '1px solid var(--border)', padding: '12px 16px' }}>
                  <SQLPreview sql={r.sql} error={null} valid={true} />
                  <ResultTable
                    columns={r.columns}
                    rows={r.rows}
                    rowCount={r.row_count}
                    error={null}
                  />
                </div>
              ))
            ) : (
              <>
                <SQLPreview sql={currentSql} error={currentResult?.error ?? null} valid={currentResult?.valid ?? false} />
                <ResultTable
                  columns={currentResult?.columns ?? []}
                  rows={currentResult?.rows ?? []}
                  rowCount={currentResult?.row_count ?? 0}
                  error={currentResult?.error ?? null}
                />
              </>
            )}
          </div>
        </div>
        <div style={{ flexShrink: 0, maxHeight: '280px', overflow: 'auto', borderTop: '1px solid var(--border)' }}>
          <MetricsDashboard data={metricsData} loading={evaluating} error={metricsError} />
        </div>
      </main>
    </div>
  )
}
