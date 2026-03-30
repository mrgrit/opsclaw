import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import MarkdownRenderer from '../../components/portal/MarkdownRenderer'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function Lecture() {
  const { course, week } = useParams<{ course: string; week: string }>()
  const navigate = useNavigate()
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const weekNum = parseInt((week || 'week01').replace('week', ''), 10)

  useEffect(() => {
    if (!course || !week) return
    setLoading(true)
    setError('')
    fetch(`/portal/content/education/${course}/${week}`, { headers: authHeaders() })
      .then(r => { if (!r.ok) throw new Error(`Error ${r.status}`); return r.json() })
      .then(data => setContent(data.content || ''))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [course, week])

  const goWeek = (n: number) => {
    const w = `week${String(n).padStart(2, '0')}`
    navigate(`/education/${course}/${w}`)
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <button
        onClick={() => navigate(`/education/${course}`)}
        style={{ background: 'none', border: 'none', color: colors.accent, cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16, padding: 0 }}
      >
        ← 주차 목록으로
      </button>

      {loading ? (
        <div style={{ color: colors.textMuted }}>로딩 중...</div>
      ) : error ? (
        <div style={{ color: '#f85149' }}>오류: {error}</div>
      ) : (
        <>
          <div style={{ color: colors.textMuted, fontSize: '0.85rem', marginBottom: 16 }}>
            {course} — {week}
          </div>

          <div style={{
            background: colors.card,
            border: `1px solid ${colors.border}`,
            borderRadius: 8,
            padding: '24px 32px',
          }}>
            <MarkdownRenderer content={content} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 24 }}>
            <button
              onClick={() => goWeek(weekNum - 1)}
              disabled={weekNum <= 1}
              style={{
                background: weekNum <= 1 ? colors.card : colors.accent,
                color: weekNum <= 1 ? colors.textMuted : '#fff',
                border: `1px solid ${weekNum <= 1 ? colors.border : colors.accent}`,
                padding: '8px 20px', borderRadius: 6, cursor: weekNum <= 1 ? 'not-allowed' : 'pointer', fontSize: '0.9rem',
              }}
            >← 이전 주차</button>
            <button
              onClick={() => goWeek(weekNum + 1)}
              disabled={weekNum >= 15}
              style={{
                background: weekNum >= 15 ? colors.card : colors.accent,
                color: weekNum >= 15 ? colors.textMuted : '#fff',
                border: `1px solid ${weekNum >= 15 ? colors.border : colors.accent}`,
                padding: '8px 20px', borderRadius: 6, cursor: weekNum >= 15 ? 'not-allowed' : 'pointer', fontSize: '0.9rem',
              }}
            >다음 주차 →</button>
          </div>
        </>
      )}
    </div>
  )
}
