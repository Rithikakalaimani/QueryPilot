interface ResultTableProps {
  columns: string[]
  rows: unknown[][]
  rowCount: number
  error: string | null
}

export function ResultTable({ columns, rows, rowCount, error }: ResultTableProps) {
  return (
    <section
      style={{
        flex: 1,
        overflow: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <h2 style={{ margin: '0 0 12px 0', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>
        Results {rowCount >= 0 ? `(${rowCount} row${rowCount !== 1 ? 's' : ''})` : ''}
      </h2>
      {error && (
        <p style={{ color: 'var(--error)', fontSize: '0.9rem' }}>{error}</p>
      )}
      {!error && columns.length > 0 && (
        <div style={{ overflow: 'auto', flex: 1, border: '1px solid var(--border)', borderRadius: '8px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-input)' }}>
                {columns.map((col) => (
                  <th
                    key={col}
                    style={{
                      padding: '10px 12px',
                      textAlign: 'left',
                      borderBottom: '1px solid var(--border)',
                      fontWeight: 600,
                    }}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                  {row.map((cell, j) => (
                    <td
                      key={j}
                      style={{
                        padding: '8px 12px',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.8rem',
                      }}
                    >
                      {cell != null ? String(cell) : '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {!error && columns.length === 0 && rowCount === 0 && (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No results yet. Ask a question to see generated SQL and results.</p>
      )}
    </section>
  )
}
