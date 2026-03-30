import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  green: '#3fb950',
  inputBg: '#161b22',
}

interface Post {
  id: number
  title: string
  author: string
  created_at: string
  view_count: number
  pinned: boolean
  comment_count?: number
}

interface BoardInfo {
  id: number
  name: string
  slug: string
  description: string
  type: string
  can_write?: boolean
}

const authHeaders = () => {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : ({} as Record<string, string>)
}

export default function Board() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const [board, setBoard] = useState<BoardInfo | null>(null)
  const [posts, setPosts] = useState<Post[]>([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!slug) return
    setLoading(true)

    Promise.all([
      fetch(`/portal/boards/${slug}`, { headers: authHeaders() }).then(r => r.ok ? r.json() : null),
      fetch(`/portal/boards/${slug}/posts?page=${page}`, { headers: authHeaders() }).then(r => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      }),
    ])
      .then(([boardData, postsData]) => {
        if (boardData) setBoard(boardData)
        const list = Array.isArray(postsData) ? postsData : postsData.posts || []
        setPosts(list)
        if (postsData.total_pages) setTotalPages(postsData.total_pages)
        if (postsData.board) setBoard(postsData.board)
        if (boardData?.can_write !== undefined && board) {
          setBoard(prev => prev ? { ...prev, can_write: boardData.can_write } : prev)
        }
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [slug, page])

  const formatDate = (d: string) => {
    try { return new Date(d).toLocaleDateString('ko-KR') } catch { return d }
  }

  if (loading) return <div style={{ color: colors.textMuted, textAlign: 'center', padding: 40 }}>Loading...</div>
  if (error) return <div style={{ color: '#f85149', textAlign: 'center', padding: 40 }}>{error}</div>

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>
            {board?.name || slug}
          </h1>
          {board?.description && (
            <p style={{ color: colors.textMuted, fontSize: '0.9rem', margin: 0 }}>{board.description}</p>
          )}
        </div>
        {(board?.can_write !== false && localStorage.getItem('portal_token')) && (
          <button
            onClick={() => navigate(`/community/${slug}/write`)}
            style={{
              background: colors.accent,
              color: '#fff',
              border: 'none',
              padding: '8px 20px',
              borderRadius: 6,
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.9rem',
            }}
          >
            New Post
          </button>
        )}
      </div>

      {/* Post list */}
      <div style={{
        background: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        overflow: 'hidden',
      }}>
        {/* Header row */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 120px 100px 70px',
          padding: '10px 16px',
          background: colors.inputBg,
          borderBottom: `1px solid ${colors.border}`,
          fontSize: '0.8rem',
          color: colors.textMuted,
          fontWeight: 600,
        }}>
          <span>Title</span>
          <span>Author</span>
          <span>Date</span>
          <span style={{ textAlign: 'right' }}>Views</span>
        </div>

        {posts.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: colors.textMuted }}>
            No posts yet.
          </div>
        ) : (
          posts.map(p => (
            <div
              key={p.id}
              onClick={() => navigate(`/community/${slug}/${p.id}`)}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 120px 100px 70px',
                padding: '12px 16px',
                borderBottom: `1px solid ${colors.border}`,
                cursor: 'pointer',
                transition: 'background 0.1s',
                alignItems: 'center',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = colors.inputBg)}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
                {p.pinned && (
                  <span style={{
                    background: colors.green,
                    color: '#fff',
                    fontSize: '0.7rem',
                    padding: '1px 6px',
                    borderRadius: 4,
                    fontWeight: 600,
                    flexShrink: 0,
                  }}>
                    PIN
                  </span>
                )}
                <span style={{
                  fontSize: '0.9rem',
                  color: colors.text,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {p.title}
                </span>
                {(p.comment_count ?? 0) > 0 && (
                  <span style={{ color: colors.accent, fontSize: '0.8rem', flexShrink: 0 }}>
                    [{p.comment_count}]
                  </span>
                )}
              </span>
              <span style={{ fontSize: '0.85rem', color: colors.textMuted }}>{p.author}</span>
              <span style={{ fontSize: '0.8rem', color: colors.textMuted }}>{formatDate(p.created_at)}</span>
              <span style={{ fontSize: '0.8rem', color: colors.textMuted, textAlign: 'right' }}>{p.view_count}</span>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 20 }}>
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => p - 1)}
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              color: page <= 1 ? colors.textMuted : colors.text,
              padding: '6px 14px',
              borderRadius: 6,
              cursor: page <= 1 ? 'default' : 'pointer',
              fontSize: '0.85rem',
            }}
          >
            Prev
          </button>
          <span style={{ color: colors.textMuted, padding: '6px 10px', fontSize: '0.85rem' }}>
            {page} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(p => p + 1)}
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              color: page >= totalPages ? colors.textMuted : colors.text,
              padding: '6px 14px',
              borderRadius: 6,
              cursor: page >= totalPages ? 'default' : 'pointer',
              fontSize: '0.85rem',
            }}
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
