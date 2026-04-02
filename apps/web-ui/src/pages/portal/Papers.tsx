import { useState, useEffect } from 'react'
import MarkdownRenderer from '../../components/portal/MarkdownRenderer'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  orange: '#d29922',
  purple: '#bc8cff',
}

interface PaperGroup {
  name: string
  title: string
  icon: string
  files: string[]
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : ({} as Record<string, string>)
}

export default function Papers() {
  const [groups, setGroups] = useState<PaperGroup[]>([])
  const [content, setContent] = useState('')
  const [viewing, setViewing] = useState<{group: string, file: string, title: string} | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [forbidden, setForbidden] = useState(false)

  useEffect(() => {
    fetch('/portal/content/papers', { headers: authHeaders() })
      .then(r => {
        if (r.status === 401 || r.status === 403) { setForbidden(true); throw new Error('forbidden') }
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => setGroups(data.papers || []))
      .catch(e => { if (!forbidden) setError(e.message) })
      .finally(() => setLoading(false))
  }, [])

  const openFile = (groupName: string, filename: string) => {
    setContent('')
    setViewing({ group: groupName, file: filename, title: filename.replace('.md', '') })
    fetch(`/portal/content/papers/${groupName}/${filename}`, { headers: authHeaders() })
      .then(r => { if (!r.ok) throw new Error(`Error ${r.status}`); return r.json() })
      .then(data => setContent(data.content || ''))
      .catch(e => setContent(`오류: ${e.message}`))
  }

  if (loading) return <div style={{ color: colors.textMuted, textAlign: 'center', padding: 40 }}>로딩 중...</div>

  if (forbidden) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '50vh' }}>
        <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 12, padding: 48, textAlign: 'center' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 16 }}>🔒</div>
          <h2 style={{ fontSize: '1.3rem', marginBottom: 8 }}>관리자 전용</h2>
          <p style={{ color: colors.textMuted, fontSize: '0.9rem' }}>연구자료는 관리자 계정으로 로그인해야 열람할 수 있습니다.</p>
        </div>
      </div>
    )
  }

  if (error) return <div style={{ color: '#f85149', textAlign: 'center', padding: 40 }}>오류: {error}</div>

  // 파일 내용 보기
  if (viewing) {
    return (
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <button
          onClick={() => setViewing(null)}
          style={{ background: 'none', border: 'none', color: colors.orange, cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16, padding: 0 }}
        >← 연구자료 목록</button>

        <div style={{ color: colors.textMuted, fontSize: '0.85rem', marginBottom: 16 }}>
          {viewing.group} / {viewing.file}
        </div>

        <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 8, padding: '24px 32px' }}>
          {content ? <MarkdownRenderer content={content} /> : <div style={{ color: colors.textMuted }}>로딩 중...</div>}
        </div>
      </div>
    )
  }

  // 목록
  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: 8 }}>연구자료</h1>
      <p style={{ color: colors.textMuted, fontSize: '0.9rem', marginBottom: 28 }}>
        OpsClaw 관련 연구 논문과 아이디어. 관리자만 열람 가능합니다.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {groups.map(g => (
          <div key={g.name} style={{
            background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 10,
            padding: 20,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
              <span style={{ fontSize: '1.4rem' }}>{g.icon}</span>
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{g.title}</span>
              <span style={{ marginLeft: 'auto', fontSize: '0.72rem', color: colors.textMuted, background: '#161b22', padding: '2px 8px', borderRadius: 10 }}>
                {g.files.length}
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {g.files.map(f => (
                <div
                  key={f}
                  onClick={() => openFile(g.name, f)}
                  style={{
                    padding: '6px 10px', fontSize: '0.83rem', color: colors.accent,
                    cursor: 'pointer', borderRadius: 4, transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#1f3a5c')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  {f.replace('.md', '')}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
