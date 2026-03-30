import { useState, useEffect } from 'react'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  orange: '#d29922',
}

interface Paper {
  id: string
  title: string
  abstract?: string
  content?: string
  date?: string
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function mdToHtml(md: string): string {
  return md
    .replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang, code) =>
      `<pre style="background:#161b22;padding:16px;border-radius:6px;overflow-x:auto;border:1px solid #30363d"><code class="lang-${lang}">${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`
    )
    .replace(/`([^`]+)`/g, '<code style="background:#161b22;padding:2px 6px;border-radius:3px;font-size:0.9em">$1</code>')
    .replace(/^### (.+)$/gm, '<h3 style="margin:20px 0 8px;font-size:1.1rem">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="margin:24px 0 10px;font-size:1.25rem">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="margin:28px 0 12px;font-size:1.5rem">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li style="margin-left:20px;list-style:disc">$1</li>')
    .replace(/^> (.+)$/gm, '<blockquote style="border-left:3px solid #30363d;padding-left:12px;color:#8b949e;margin:8px 0">$1</blockquote>')
    .replace(/^---$/gm, '<hr style="border:none;border-top:1px solid #30363d;margin:16px 0">')
    .replace(/\n\n/g, '<br/><br/>')
}

export default function Papers() {
  const [papers, setPapers] = useState<Paper[]>([])
  const [selected, setSelected] = useState<Paper | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [forbidden, setForbidden] = useState(false)

  useEffect(() => {
    fetch('/content/papers', { headers: authHeaders() })
      .then(r => {
        if (r.status === 403) {
          setForbidden(true)
          throw new Error('forbidden')
        }
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => setPapers(Array.isArray(data) ? data : data.papers || []))
      .catch(e => {
        if (!forbidden) setError(e.message)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: colors.textMuted }}>로딩 중...</div>

  if (forbidden) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '50vh',
      }}>
        <div style={{
          background: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          padding: 40,
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '2rem', marginBottom: 16, color: colors.orange }}>Access Denied</div>
          <p style={{ color: colors.textMuted }}>관리자만 접근 가능합니다.</p>
        </div>
      </div>
    )
  }

  if (error) return <div style={{ color: '#f85149' }}>오류: {error}</div>

  if (selected) {
    return (
      <div style={{ maxWidth: 860, margin: '0 auto' }}>
        <button
          onClick={() => setSelected(null)}
          style={{
            background: 'none', border: 'none', color: colors.orange,
            cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16, padding: 0,
          }}
        >
          ← 논문 목록으로
        </button>

        <h1 style={{ fontSize: '1.5rem', marginBottom: 8 }}>{selected.title}</h1>
        {selected.date && (
          <div style={{ color: colors.textMuted, fontSize: '0.85rem', marginBottom: 24 }}>{selected.date}</div>
        )}

        <div
          style={{
            background: colors.card,
            border: `1px solid ${colors.border}`,
            borderRadius: 8,
            padding: 28,
            lineHeight: 1.7,
            fontSize: '0.95rem',
          }}
          dangerouslySetInnerHTML={{ __html: mdToHtml(selected.content || selected.abstract || '') }}
        />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <h2 style={{ fontSize: '1.4rem', marginBottom: 24 }}>논문</h2>

      {papers.length === 0 ? (
        <div style={{ color: colors.textMuted }}>등록된 논문이 없습니다.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {papers.map(p => (
            <div
              key={p.id}
              onClick={() => setSelected(p)}
              style={{
                background: colors.card,
                border: `1px solid ${colors.border}`,
                borderRadius: 8,
                padding: 20,
                cursor: 'pointer',
                transition: 'border-color 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = colors.orange)}
              onMouseLeave={e => (e.currentTarget.style.borderColor = colors.border)}
            >
              <div style={{ fontSize: '1rem', fontWeight: 600, color: colors.orange, marginBottom: 6 }}>
                {p.title}
              </div>
              {p.abstract && (
                <div style={{ color: colors.textMuted, fontSize: '0.85rem', lineHeight: 1.5 }}>
                  {p.abstract.slice(0, 200)}{p.abstract.length > 200 ? '...' : ''}
                </div>
              )}
              {p.date && (
                <div style={{ color: colors.textMuted, fontSize: '0.75rem', marginTop: 8 }}>{p.date}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
