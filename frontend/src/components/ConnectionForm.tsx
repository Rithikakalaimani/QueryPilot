import { useState, useEffect } from 'react'

export interface ConnectionConfig {
  host: string
  port: number
  user: string
  password: string
  database: string
  database_type: 'mysql' | 'postgres'
}

const STORAGE_KEY = 'querypilot_connection'

const defaultConnection: ConnectionConfig = {
  host: 'localhost',
  port: 3306,
  user: 'root',
  password: '',
  database: '',
  database_type: 'mysql',
}

export function loadConnection(): ConnectionConfig {
  try {
    const s = localStorage.getItem(STORAGE_KEY)
    if (s) {
      const parsed = JSON.parse(s) as Partial<ConnectionConfig>
      return {
        ...defaultConnection,
        host: parsed.host ?? defaultConnection.host,
        port: parsed.port ?? defaultConnection.port,
        user: parsed.user ?? defaultConnection.user,
        database_type: parsed.database_type ?? defaultConnection.database_type,
        password: '',
        database: '',
      }
    }
  } catch (_) {}
  return { ...defaultConnection }
}

export function saveConnection(conn: ConnectionConfig) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      host: conn.host,
      port: conn.port,
      user: conn.user,
      database_type: conn.database_type,
    }))
  } catch (_) {}
}

interface ConnectionFormProps {
  connection: ConnectionConfig
  onChange: (c: ConnectionConfig) => void
  onSave: () => void
  collapsed: boolean
  onToggleCollapsed: () => void
}

export function ConnectionForm({
  connection,
  onChange,
  onSave,
  collapsed,
  onToggleCollapsed,
}: ConnectionFormProps) {
  const [saveFeedback, setSaveFeedback] = useState<string | null>(null)

  useEffect(() => {
    if (!saveFeedback) return
    const t = setTimeout(() => setSaveFeedback(null), 3000)
    return () => clearTimeout(t)
  }, [saveFeedback])

  const handleSave = () => {
    try {
      onSave()
      setSaveFeedback('Connection saved')
    } catch {
      setSaveFeedback('Failed to save')
    }
  }

  return (
    <section
      style={{
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-panel)',
      }}
    >
      <button
        type="button"
        onClick={onToggleCollapsed}
        style={{
          width: '100%',
          padding: '10px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'none',
          border: 'none',
          color: 'var(--text)',
          fontSize: '0.9rem',
          cursor: 'pointer',
        }}
      >
        <span style={{ fontWeight: 500 }}>Database connection</span>
        <span style={{ color: 'var(--text-muted)' }}>{collapsed ? '▼' : '▲'}</span>
      </button>
      {!collapsed && (
        <div style={{ padding: '0 16px 16px 16px', display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'flex-end' }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Host
            <input
              type="text"
              value={connection.host}
              onChange={(e) => onChange({ ...connection, host: e.target.value })}
              placeholder="localhost"
              style={{
                padding: '6px 10px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                color: 'var(--text)',
                width: '120px',
              }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Port
            <input
              type="number"
              value={connection.port}
              onChange={(e) => onChange({ ...connection, port: parseInt(e.target.value, 10) || 3306 })}
              style={{
                padding: '6px 10px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                color: 'var(--text)',
                width: '70px',
              }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            User
            <input
              type="text"
              value={connection.user}
              onChange={(e) => onChange({ ...connection, user: e.target.value })}
              placeholder="root"
              style={{
                padding: '6px 10px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                color: 'var(--text)',
                width: '100px',
              }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Password
            <input
              type="password"
              value={connection.password}
              onChange={(e) => onChange({ ...connection, password: e.target.value })}
              placeholder=""
              style={{
                padding: '6px 10px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                color: 'var(--text)',
                width: '100px',
              }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Database
            <input
              type="text"
              value={connection.database}
              onChange={(e) => onChange({ ...connection, database: e.target.value })}
              placeholder="text_to_sql_demo"
              style={{
                padding: '6px 10px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                color: 'var(--text)',
                width: '140px',
              }}
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Type
            <select
              value={connection.database_type}
              onChange={(e) => onChange({ ...connection, database_type: e.target.value as 'mysql' | 'postgres' })}
              style={{
                padding: '6px 10px',
                background: 'var(--bg-input)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                color: 'var(--text)',
                width: '100px',
              }}
            >
              <option value="mysql">MySQL</option>
              <option value="postgres">Postgres</option>
            </select>
          </label>
          <button
            type="button"
            onClick={handleSave}
            style={{
              padding: '8px 14px',
              background: 'var(--accent)',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            Save connection
          </button>
          {saveFeedback && (
            <span
              style={{
                fontSize: saveFeedback.startsWith('Failed') ? '0.85rem' : '1.25rem',
                color: saveFeedback.startsWith('Failed') ? 'var(--error)' : 'var(--success)',
                alignSelf: 'center',
                lineHeight: 1,
              }}
              title={saveFeedback}
            >
              {saveFeedback.startsWith('Failed') ? saveFeedback : '✓'}
            </span>
          )}
        </div>
      )}
    </section>
  )
}
