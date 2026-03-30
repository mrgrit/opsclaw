import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  codeBg: '#161b22',
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/** Simple markdown to HTML converter */
function mdToHtml(md: string): string {
  let html = md
    // Code blocks (```...```)
    .replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang, code) =>
      `<pre style="background:#161b22;padding:16px;border-radius:6px;overflow-x:auto;border:1px solid #30363d"><code class="lang-${lang}">${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`
    )
    // Inline code
    .replace(/`([^`]+)`/g, '<code style="background:#161b22;padding:2px 6px;border-radius:3px;font-size:0.9em">$1</code>')
    // Headers
    .replace(/^### (.+)$/gm, '<h3 style="margin:20px 0 8px;font-size:1.1rem">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="margin:24px 0 10px;font-size:1.25rem">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="margin:28px 0 12px;font-size:1.5rem">$1</h1>')
    // Bold and italic
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Unordered lists
    .replace(/^- (.+)$/gm, '<li style="margin-left:20px;list-style:disc">$1</li>')
    // Blockquotes
    .replace(/^> (.+)$/gm, '<blockquote style="border-left:3px solid #30363d;padding-left:12px;color:#8b949e;margin:8px 0">$1</blockquote>')
    // Horizontal rules
    .replace(/^---$/gm, '<hr style="border:none;border-top:1px solid #30363d;margin:16px 0">')
    // Line breaks (double newline = paragraph)
    .replace(/\n\n/g, '<br/><br/>')

  return html
}

export default function Lecture() {
  const { course, week } = useParams<{ course: string; week: string }>()
  const navigate = useNavigate()
  const [content, setContent] = useState('')
  const [title, setTitle] = useState('')
  const [totalWeeks, setTotalWeeks] = useState(15)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const weekNum = parseInt(week || '1', 10)

  useEffect(() => {
    if (!course || !week) return
    setLoading(true)
    setError('')
    fetch(`/content/education/${course}/${week}`, { headers: authHeaders() })
      .then(r => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => {
        setContent(data.content || data.body || '')
        setTitle(data.title || `Week ${week}`)
        if (data.total_weeks) setTotalWeeks(data.total_weeks)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [course, week])

  const navButton = (label: string, targetWeek: number, disabled: boolean) => (
    <button
      onClick={() => navigate(`/education/${course}/${targetWeek}`)}
      disabled={disabled}
      style={{
        background: disabled ? colors.card : colors.accent,
        color: disabled ? colors.textMuted : '#fff',
        border: `1px solid ${disabled ? colors.border : colors.accent}`,
        padding: '8px 20px',
        borderRadius: 6,
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontSize: '0.9rem',
      }}
    >
      {label}
    </button>
  )

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <button
        onClick={() => navigate(`/education/${course}`)}
        style={{
          background: 'none', border: 'none', color: colors.accent,
          cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16, padding: 0,
        }}
      >
        ← 주차 목록으로
      </button>

      {loading ? (
        <div style={{ color: colors.textMuted }}>로딩 중...</div>
      ) : error ? (
        <div style={{ color: '#f85149' }}>오류: {error}</div>
      ) : (
        <>
          <h1 style={{ fontSize: '1.5rem', marginBottom: 8 }}>{title}</h1>
          <div style={{ color: colors.textMuted, fontSize: '0.85rem', marginBottom: 24 }}>
            {course} - Week {weekNum} / {totalWeeks}
          </div>

          <div
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              padding: 28,
              lineHeight: 1.7,
              fontSize: '0.95rem',
            }}
            dangerouslySetInnerHTML={{ __html: mdToHtml(content) }}
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 24 }}>
            {navButton('← 이전 주차', weekNum - 1, weekNum <= 1)}
            {navButton('다음 주차 →', weekNum + 1, weekNum >= totalWeeks)}
          </div>
        </>
      )}
    </div>
  )
}
