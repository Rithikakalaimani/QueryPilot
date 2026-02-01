interface SQLPreviewProps {
  sql: string | null
  error: string | null
  valid: boolean
}

export function SQLPreview({ sql, error, valid }: SQLPreviewProps) {
  return (
    <section
      style={{
        padding: '12px 16px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-panel)',
      }}
    >
      <h2 style={{ margin: '0 0 8px 0', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>
        Generated SQL
      </h2>
      <pre
        style={{
          margin: 0,
          padding: '12px',
          background: 'var(--bg-input)',
          border: `1px solid ${valid ? 'var(--border)' : 'var(--error)'}`,
          borderRadius: '8px',
          fontSize: '0.8rem',
          overflow: 'auto',
          maxHeight: '180px',
          color: valid ? 'var(--text)' : 'var(--error)',
        }}
      >
        {sql || '—'}
      </pre>
      {error && (
        <p style={{ margin: '8px 0 0 0', fontSize: '0.85rem', color: 'var(--error)' }}>{error}</p>
      )}
    </section>
  )
}
