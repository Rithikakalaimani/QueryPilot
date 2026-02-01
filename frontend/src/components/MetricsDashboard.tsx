interface EvalResult {
  question: string
  generated_sql: string
  execution_success: boolean
  faithfulness?: number
  answer_relevancy?: number
  context_precision?: number
  context_recall?: number
  execution_accuracy?: number
  error?: string | null
}

export interface MetricsData {
  n: number
  faithfulness_avg: number
  answer_relevancy_avg: number
  context_precision_avg: number
  context_recall_avg: number
  execution_accuracy_avg: number
  results: EvalResult[]
}

interface MetricsDashboardProps {
  data: MetricsData | null
  loading: boolean
  error: string | null
}

function MetricCard({ label, value, pct }: { label: string; value: number; pct: number }) {
  return (
    <div
      style={{
        background: 'var(--bg-input)',
        border: '1px solid var(--border)',
        borderRadius: '10px',
        padding: '14px 16px',
        minWidth: '120px',
      }}
    >
      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>{label}</div>
      <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{pct.toFixed(1)}%</div>
    </div>
  )
}

export function MetricsDashboard({ data, loading, error }: MetricsDashboardProps) {
  if (loading) {
    return (
      <section
        style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-panel)',
        }}
      >
        <h2 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>
          RAGAS Metrics
        </h2>
        <p style={{ margin: 0, color: 'var(--text-muted)' }}>Running evaluation…</p>
      </section>
    )
  }

  if (error) {
    return (
      <section
        style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-panel)',
        }}
      >
        <h2 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>
          RAGAS Metrics
        </h2>
        <p style={{ margin: 0, color: 'var(--error)' }}>{error}</p>
      </section>
    )
  }

  if (!data) {
    return (
      <section
        style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-panel)',
        }}
      >
        <h2 style={{ margin: '0 0 12px 0', fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>
          RAGAS Metrics
        </h2>
        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Click &quot;Run RAGAS eval&quot; to see metrics.
        </p>
      </section>
    )
  }

  const { n, faithfulness_avg, answer_relevancy_avg, context_precision_avg, context_recall_avg, execution_accuracy_avg, results } = data

  return (
    <section
      style={{
        padding: '16px 20px',
        borderTop: '1px solid var(--border)',
        background: 'var(--bg-panel)',
        overflow: 'auto',
      }}
    >
      <h2 style={{ margin: '0 0 16px 0', fontSize: '0.95rem', fontWeight: 600 }}>
        RAGAS Metrics Dashboard
      </h2>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
          gap: '12px',
          marginBottom: '20px',
        }}
      >
        <MetricCard label="Faithfulness" value={faithfulness_avg} pct={faithfulness_avg * 100} />
        <MetricCard label="Answer Relevancy" value={answer_relevancy_avg} pct={answer_relevancy_avg * 100} />
        <MetricCard label="Context Precision" value={context_precision_avg} pct={context_precision_avg * 100} />
        <MetricCard label="Context Recall" value={context_recall_avg} pct={context_recall_avg * 100} />
        <MetricCard label="Execution Accuracy" value={execution_accuracy_avg} pct={execution_accuracy_avg * 100} />
      </div>
      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
        Benchmark: {n} question{n !== 1 ? 's' : ''}
      </div>
      {results.length > 0 && (
        <details style={{ marginTop: '8px' }}>
          <summary style={{ cursor: 'pointer', fontSize: '0.85rem', color: 'var(--accent)' }}>
            View per-question results ({results.length})
          </summary>
          <div
            style={{
              marginTop: '12px',
              overflow: 'auto',
              maxHeight: '280px',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              fontSize: '0.8rem',
            }}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--bg-input)' }}>
                  <th style={{ padding: '8px 10px', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>Question</th>
                  <th style={{ padding: '8px 10px', textAlign: 'left', borderBottom: '1px solid var(--border)' }}>SQL</th>
                  <th style={{ padding: '8px 10px', textAlign: 'center', borderBottom: '1px solid var(--border)' }}>Exec</th>
                  <th style={{ padding: '8px 10px', textAlign: 'center', borderBottom: '1px solid var(--border)' }}>Faith</th>
                  <th style={{ padding: '8px 10px', textAlign: 'center', borderBottom: '1px solid var(--border)' }}>Relev</th>
                  <th style={{ padding: '8px 10px', textAlign: 'center', borderBottom: '1px solid var(--border)' }}>Prec</th>
                  <th style={{ padding: '8px 10px', textAlign: 'center', borderBottom: '1px solid var(--border)' }}>Recall</th>
                  <th style={{ padding: '8px 10px', textAlign: 'center', borderBottom: '1px solid var(--border)' }}>Acc</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '8px 10px', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.question}>
                      {r.question}
                    </td>
                    <td style={{ padding: '8px 10px', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontFamily: 'var(--font-mono)' }} title={r.generated_sql}>
                      {r.generated_sql}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                      {r.execution_success ? '✓' : '✗'}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                      {r.faithfulness != null ? `${(r.faithfulness * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                      {r.answer_relevancy != null ? `${(r.answer_relevancy * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                      {r.context_precision != null ? `${(r.context_precision * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                      {r.context_recall != null ? `${(r.context_recall * 100).toFixed(0)}%` : '—'}
                    </td>
                    <td style={{ padding: '8px 10px', textAlign: 'center' }}>
                      {r.execution_accuracy != null ? `${(r.execution_accuracy * 100).toFixed(0)}%` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </section>
  )
}
