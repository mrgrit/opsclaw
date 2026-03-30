import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import MarkdownRenderer from '../../components/portal/MarkdownRenderer'

const colors = {
  card: '#21262d',
  border: '#30363d',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  purple: '#bc8cff',
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function Chapter() {
  const { vol, chapter } = useParams<{ vol: string; chapter: string }>()
  const navigate = useNavigate()
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const chapterNum = parseInt((chapter || 'ch01').replace('ch', ''), 10)

  useEffect(() => {
    if (!vol || !chapter) return
    setLoading(true)
    setError('')
    fetch(`/portal/content/novel/${vol}/${chapter}`, { headers: authHeaders() })
      .then(r => { if (!r.ok) throw new Error(`Error ${r.status}`); return r.json() })
      .then(data => setContent(data.content || ''))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [vol, chapter])

  const goCh = (n: number) => {
    const ch = `ch${String(n).padStart(2, '0')}`
    navigate(`/novel/${vol}/${ch}`)
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <button
        onClick={() => navigate(`/novel/${vol}`)}
        style={{ background: 'none', border: 'none', color: colors.purple, cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16, padding: 0 }}
      >
        ← 챕터 목록으로
      </button>

      {loading ? (
        <div style={{ color: colors.textMuted }}>로딩 중...</div>
      ) : error ? (
        <div style={{ color: '#f85149' }}>오류: {error}</div>
      ) : (
        <>
          <div style={{ color: colors.textMuted, fontSize: '0.85rem', marginBottom: 16 }}>
            {vol} — {chapter}
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
              onClick={() => goCh(chapterNum - 1)}
              disabled={chapterNum <= 1}
              style={{
                background: chapterNum <= 1 ? colors.card : colors.purple,
                color: chapterNum <= 1 ? colors.textMuted : '#fff',
                border: `1px solid ${chapterNum <= 1 ? colors.border : colors.purple}`,
                padding: '8px 20px', borderRadius: 6, cursor: chapterNum <= 1 ? 'not-allowed' : 'pointer', fontSize: '0.9rem',
              }}
            >← 이전 챕터</button>
            <button
              onClick={() => goCh(chapterNum + 1)}
              disabled={chapterNum >= 12}
              style={{
                background: chapterNum >= 12 ? colors.card : colors.purple,
                color: chapterNum >= 12 ? colors.textMuted : '#fff',
                border: `1px solid ${chapterNum >= 12 ? colors.border : colors.purple}`,
                padding: '8px 20px', borderRadius: 6, cursor: chapterNum >= 12 ? 'not-allowed' : 'pointer', fontSize: '0.9rem',
              }}
            >다음 챕터 →</button>
          </div>
        </>
      )}
    </div>
  )
}
