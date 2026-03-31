import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  purple: '#bc8cff',
}

interface Volume {
  name: string
  chapters: string[]
  chapter_count: number
}

interface ChapterItem {
  id: string
  title: string
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function Novel() {
  const navigate = useNavigate()
  const { vol } = useParams<{ vol: string }>()
  const [volumes, setVolumes] = useState<Volume[]>([])
  const [chapters, setChapters] = useState<ChapterItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    fetch('/portal/content/novel', { headers: authHeaders() })
      .then(r => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => setVolumes(Array.isArray(data) ? data : data.volumes || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!vol) { setChapters([]); return }
    fetch(`/portal/content/novel/${vol}`, { headers: authHeaders() })
      .then(r => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => setChapters(Array.isArray(data) ? data : data.chapters || []))
      .catch(e => setError(e.message))
  }, [vol])

  if (loading) return <div style={{ color: colors.textMuted }}>로딩 중...</div>
  if (error) return <div style={{ color: '#f85149' }}>오류: {error}</div>

  if (vol) {
    const volInfo = volumes.find(v => v.name === vol)
    return (
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        <button
          onClick={() => navigate('/novel')}
          style={{
            background: 'none', border: 'none', color: colors.purple,
            cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16, padding: 0,
          }}
        >
          ← 시나리오 목록으로
        </button>
        <h2 style={{ fontSize: '1.4rem', marginBottom: 24 }}>
          {volInfo?.name || `Volume ${vol}`}
        </h2>

        {chapters.length === 0 ? (
          <div style={{ color: colors.textMuted }}>챕터 정보가 없습니다.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {chapters.map(ch => (
              <div
                key={ch.id}
                onClick={() => navigate(`/novel/${vol}/${ch.id}`)}
                style={{
                  background: colors.card,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 8,
                  padding: '14px 20px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 16,
                  transition: 'border-color 0.15s',
                }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = colors.purple)}
                onMouseLeave={e => (e.currentTarget.style.borderColor = colors.border)}
              >
                <span style={{
                  background: colors.purple,
                  color: '#fff',
                  width: 32, height: 32,
                  borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.85rem', fontWeight: 600, flexShrink: 0,
                }}>
                  {ch.id}
                </span>
                <span>{ch.title}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <h1 style={{ fontSize: "1.6rem", fontWeight: 700, marginBottom: 8 }}>보안 시나리오: OpsClaw</h1>
      <p style={{ color: colors.textMuted, fontSize: '0.95rem', lineHeight: 1.7, marginBottom: 24 }}>
        넥서스AI SOC팀의 보안 사건을 다룬 10부작 사이버보안 시나리오.<br/>
        120개 교육 주제가 스토리에 자연스럽게 녹아들어, 읽기만 해도 보안의 핵심을 배울 수 있습니다.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
        {volumes.map(v => (
          <div
            key={v.name}
            onClick={() => navigate(`/novel/${v.name}`)}
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              padding: 20,
              cursor: 'pointer',
              transition: 'border-color 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = colors.purple)}
            onMouseLeave={e => (e.currentTarget.style.borderColor = colors.border)}
          >
            <div style={{ fontSize: '1rem', fontWeight: 600, color: colors.purple, marginBottom: 8 }}>
              {v.name}
            </div>
            <div style={{ color: colors.textMuted, fontSize: '0.8rem' }}>{v.chapter_count}개 챕터</div>
          </div>
        ))}
      </div>
    </div>
  )
}
