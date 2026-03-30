import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  green: '#3fb950',
  purple: '#bc8cff',
  orange: '#d29922',
}

interface Board {
  id: number
  name: string
  slug: string
  description: string
  type: 'board' | 'blog'
  post_count: number
  icon?: string
  theme_color?: string
  featured_image?: string
}

const authHeaders = () => {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : ({} as Record<string, string>)
}

export default function Community() {
  const navigate = useNavigate()
  const [boards, setBoards] = useState<Board[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/portal/boards', { headers: authHeaders() })
      .then(r => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => setBoards(Array.isArray(data) ? data : data.boards || []))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const boardType = boards.filter(b => b.type === 'board')
  const blogType = boards.filter(b => b.type === 'blog')

  if (loading) return <div style={{ color: colors.textMuted, textAlign: 'center', padding: 40 }}>Loading...</div>
  if (error) return <div style={{ color: '#f85149', textAlign: 'center', padding: 40 }}>{error}</div>

  const renderBoardCard = (b: Board) => (
    <div
      key={b.slug}
      onClick={() => navigate(`/community/${b.slug}`)}
      style={{
        background: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        padding: 20,
        cursor: 'pointer',
        transition: 'border-color 0.15s',
      }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = b.theme_color || colors.accent)}
      onMouseLeave={e => (e.currentTarget.style.borderColor = colors.border)}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <span style={{ fontSize: '1.4rem' }}>{b.icon || (b.type === 'blog' ? '\u270D' : '\uD83D\uDCCB')}</span>
        <span style={{ fontSize: '1.1rem', fontWeight: 600, color: b.theme_color || colors.accent }}>{b.name}</span>
      </div>
      <div style={{ color: colors.textMuted, fontSize: '0.85rem', lineHeight: 1.5, marginBottom: 12 }}>
        {b.description || 'No description'}
      </div>
      <div style={{ color: colors.textMuted, fontSize: '0.8rem' }}>
        {b.post_count ?? 0} posts
      </div>
    </div>
  )

  const renderBlogCard = (b: Board) => (
    <div
      key={b.slug}
      onClick={() => navigate(`/community/${b.slug}`)}
      style={{
        background: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        cursor: 'pointer',
        transition: 'border-color 0.15s',
        overflow: 'hidden',
      }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = b.theme_color || colors.purple)}
      onMouseLeave={e => (e.currentTarget.style.borderColor = colors.border)}
    >
      <div style={{
        height: 120,
        background: b.featured_image ? `url(${b.featured_image}) center/cover` : `linear-gradient(135deg, ${colors.card}, #1c2333)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}>
        {!b.featured_image && <span style={{ fontSize: '2.5rem' }}>{b.icon || '\u270D'}</span>}
      </div>
      <div style={{ padding: 16 }}>
        <div style={{ fontSize: '1.1rem', fontWeight: 600, color: b.theme_color || colors.purple, marginBottom: 8 }}>
          {b.name}
        </div>
        <div style={{ color: colors.textMuted, fontSize: '0.85rem', lineHeight: 1.5, marginBottom: 10 }}>
          {b.description || 'No description'}
        </div>
        <div style={{ color: colors.textMuted, fontSize: '0.8rem' }}>
          {b.post_count ?? 0} posts
        </div>
      </div>
    </div>
  )

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: 8 }}>Community</h1>
      <p style={{ color: colors.textMuted, marginBottom: 32 }}>Boards and blogs</p>

      {boardType.length > 0 && (
        <>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: colors.accent, marginBottom: 16 }}>Boards</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16, marginBottom: 32 }}>
            {boardType.map(renderBoardCard)}
          </div>
        </>
      )}

      {blogType.length > 0 && (
        <>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: colors.purple, marginBottom: 16 }}>Blogs</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16, marginBottom: 32 }}>
            {blogType.map(renderBlogCard)}
          </div>
        </>
      )}

      {boards.length === 0 && (
        <div style={{ color: colors.textMuted, textAlign: 'center', padding: 60 }}>
          No boards available yet.
        </div>
      )}
    </div>
  )
}
