import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import MarkdownRenderer from '../../components/portal/MarkdownRenderer'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
}

interface ManualFile {
  id: string
  title: string
  filename: string
}

interface ManualSection {
  slug: string
  title: string
  icon: string
  description: string
  files: ManualFile[]
  file_count: number
}

export default function Manual() {
  const navigate = useNavigate()
  const { section, file } = useParams<{ section: string; file: string }>()
  const [sections, setSections] = useState<ManualSection[]>([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // 섹션 목록 로드
  useEffect(() => {
    fetch('/portal/content/manual')
      .then(r => { if (!r.ok) throw new Error(`Error ${r.status}`); return r.json() })
      .then(data => setSections(data.sections || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  // 페이지 내용 로드
  useEffect(() => {
    if (!section || !file) { setContent(''); return }
    setLoading(true)
    fetch(`/portal/content/manual/${section}/${file}`)
      .then(r => { if (!r.ok) throw new Error(`Error ${r.status}`); return r.json() })
      .then(data => setContent(data.content || ''))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [section, file])

  if (error) return <div style={{ color: '#f85149', textAlign: 'center', padding: 40 }}>오류: {error}</div>

  // 매뉴얼 페이지 내용 보기
  if (section && file) {
    const sec = sections.find(s => s.slug === section)
    return (
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <button
          onClick={() => navigate('/manual')}
          style={{ background: 'none', border: 'none', color: colors.accent, cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16, padding: 0 }}
        >← 매뉴얼 목록</button>

        {sec && (
          <div style={{ color: colors.textMuted, fontSize: '0.85rem', marginBottom: 16 }}>
            {sec.icon} {sec.title} / {file}
          </div>
        )}

        <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 8, padding: '24px 32px' }}>
          {loading ? (
            <div style={{ color: colors.textMuted }}>로딩 중...</div>
          ) : (
            <MarkdownRenderer content={content} />
          )}
        </div>
      </div>
    )
  }

  // 섹션 목록
  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: 8 }}>매뉴얼</h1>
      <p style={{ color: colors.textMuted, fontSize: '0.95rem', lineHeight: 1.7, marginBottom: 32 }}>
        OpsClaw 사용 가이드 — 설치부터 실전 운영까지.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {sections.map(s => (
          <div
            key={s.slug}
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              padding: 20,
              transition: 'border-color 0.15s',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <span style={{ fontSize: '1.4rem' }}>{s.icon}</span>
              <span style={{ fontSize: '1rem', fontWeight: 600 }}>{s.title}</span>
              <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: colors.textMuted, background: '#161b22', padding: '2px 8px', borderRadius: 10 }}>
                {s.file_count}
              </span>
            </div>
            <div style={{ color: colors.textMuted, fontSize: '0.85rem', marginBottom: 12 }}>{s.description}</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {s.files.map(f => (
                <div
                  key={f.id}
                  onClick={() => navigate(`/manual/${s.slug}/${f.id}`)}
                  style={{
                    padding: '6px 10px',
                    fontSize: '0.85rem',
                    color: colors.accent,
                    cursor: 'pointer',
                    borderRadius: 4,
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#1f3a5c')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  {f.title}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
