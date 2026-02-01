import { useState, useRef, useEffect } from 'react'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  sql?: string
}

interface ChatPanelProps {
  messages: Message[]
  onSend: (text: string) => void
  loading: boolean
}

export function ChatPanel({ messages, onSend, loading }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    listRef.current?.scrollTo(0, listRef.current.scrollHeight)
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const t = input.trim()
    if (t) {
      onSend(t)
      setInput('')
    }
  }

  return (
    <div
      style={{
        width: '380px',
        minWidth: '380px',
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
        borderRight: '1px solid var(--border)',
        background: 'var(--bg-panel)',
      }}
    >
      <div
        ref={listRef}
        style={{
          flex: 1,
          minHeight: 0,
          overflow: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
        }}
      >
        {messages.length === 0 && (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Ask a question in natural language. Example: &quot;How many users are there?&quot; or &quot;List the first 10 orders.&quot;
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '90%',
              padding: '10px 14px',
              borderRadius: '12px',
              background: m.role === 'user' ? 'var(--accent-dim)' : 'var(--bg-input)',
              border: '1px solid var(--border)',
            }}
          >
            <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{m.content}</div>
          </div>
        ))}
        {loading && (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Generating SQL…</div>
        )}
      </div>
      <form
        onSubmit={handleSubmit}
        style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--border)',
        }}
      >
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            disabled={loading}
            style={{
              flex: 1,
              padding: '10px 14px',
              background: 'var(--bg-input)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              color: 'var(--text)',
              fontSize: '0.95rem',
            }}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            style={{
              padding: '10px 18px',
              background: 'var(--accent)',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              fontWeight: 500,
            }}
          >
            Send
          </button>
        </div>
      </form>
    </div>
  )
}
