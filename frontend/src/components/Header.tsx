interface HeaderProps {
  onSyncSchema: () => void
  schemaSyncing: boolean
  onEvaluate?: () => void
  evaluating?: boolean
}

export function Header({ onSyncSchema, schemaSyncing, onEvaluate, evaluating }: HeaderProps) {
  return (
    <header
      style={{
        padding: '12px 20px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--bg-panel)',
      }}
    >
      <h1 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600 }}>
        QueryPilot
      </h1>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {onEvaluate && (
          <button
            onClick={onEvaluate}
            disabled={evaluating}
            style={{
              padding: '8px 16px',
              background: 'var(--bg-input)',
              color: 'var(--text)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              fontWeight: 500,
            }}
          >
            {evaluating ? 'Running…' : 'Run RAGAS eval'}
          </button>
        )}
        <button
          onClick={onSyncSchema}
          disabled={schemaSyncing}
          style={{
            padding: '8px 16px',
            background: 'var(--accent-dim)',
            color: 'var(--accent)',
            border: '1px solid var(--accent)',
            borderRadius: '8px',
            fontWeight: 500,
          }}
        >
          {schemaSyncing ? 'Syncing…' : 'Sync schema'}
        </button>
      </div>
    </header>
  )
}
