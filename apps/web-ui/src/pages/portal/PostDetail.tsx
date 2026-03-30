import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import MarkdownRenderer from '../../components/portal/MarkdownRenderer'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  inputBg: '#161b22',
  error: '#f85149',
  green: '#3fb950',
}

interface PostData {
  id: number
  title: string
  content: string
  author: string
  created_at: string
  updated_at?: string
  view_count: number
  board_slug: string
  files?: { id: number; name: string; url: string; size?: number }[]
}

interface Comment {
  id: number
  content: string
  author: string
  created_at: string
  parent_id?: number | null
  replies?: Comment[]
}

const authHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : ({} as Record<string, string>)
}

const currentUser = () => localStorage.getItem('portal_username')

export default function PostDetail() {
  const { slug, postId } = useParams<{ slug: string; postId: string }>()
  const navigate = useNavigate()
  const [post, setPost] = useState<PostData | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [newComment, setNewComment] = useState('')
  const [replyTo, setReplyTo] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const fetchPost = () => {
    fetch(`/portal/posts/${postId}`, { headers: authHeaders() })
      .then(r => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => {
        setPost(data.post || data)
        setComments(data.comments || [])
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchPost() }, [postId])

  const handleDelete = async () => {
    if (!confirm('Delete this post?')) return
    const res = await fetch(`/portal/posts/${postId}`, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    if (res.ok) navigate(`/community/${slug}`)
    else alert('Failed to delete')
  }

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newComment.trim()) return
    setSubmitting(true)
    try {
      const body: Record<string, unknown> = { content: newComment }
      if (replyTo) body.parent_id = replyTo
      const res = await fetch(`/portal/posts/${postId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      setNewComment('')
      setReplyTo(null)
      fetchPost()
    } catch {
      alert('Failed to post comment')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteComment = async (commentId: number) => {
    if (!confirm('Delete this comment?')) return
    const res = await fetch(`/portal/comments/${commentId}`, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    if (res.ok) fetchPost()
  }

  const formatDate = (d: string) => {
    try { return new Date(d).toLocaleString('ko-KR') } catch { return d }
  }

  const formatSize = (bytes?: number) => {
    if (!bytes) return ''
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1048576).toFixed(1)} MB`
  }

  const renderComment = (c: Comment, depth = 0) => (
    <div key={c.id} style={{ marginLeft: depth * 24, marginBottom: 12 }}>
      <div style={{
        background: depth > 0 ? colors.inputBg : colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        padding: '12px 16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: colors.accent + '33',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '0.75rem', color: colors.accent, fontWeight: 600,
            }}>
              {c.author?.[0]?.toUpperCase() || '?'}
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: colors.text }}>{c.author}</span>
            <span style={{ fontSize: '0.75rem', color: colors.textMuted }}>{formatDate(c.created_at)}</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {currentUser() && (
              <button
                onClick={() => setReplyTo(replyTo === c.id ? null : c.id)}
                style={{
                  background: 'none', border: 'none', color: colors.accent,
                  cursor: 'pointer', fontSize: '0.8rem',
                }}
              >
                {replyTo === c.id ? 'Cancel' : 'Reply'}
              </button>
            )}
            {currentUser() === c.author && (
              <button
                onClick={() => handleDeleteComment(c.id)}
                style={{
                  background: 'none', border: 'none', color: colors.error,
                  cursor: 'pointer', fontSize: '0.8rem',
                }}
              >
                Delete
              </button>
            )}
          </div>
        </div>
        <div style={{ fontSize: '0.9rem', color: colors.text, lineHeight: 1.6 }}>{c.content}</div>
      </div>
      {replyTo === c.id && (
        <form onSubmit={handleCommentSubmit} style={{ marginTop: 8, marginLeft: 24, display: 'flex', gap: 8 }}>
          <input
            value={newComment}
            onChange={e => setNewComment(e.target.value)}
            placeholder="Reply..."
            style={{
              flex: 1, padding: '8px 12px', background: colors.inputBg,
              border: `1px solid ${colors.border}`, borderRadius: 6,
              color: colors.text, fontSize: '0.85rem', outline: 'none',
            }}
          />
          <button type="submit" disabled={submitting} style={{
            background: colors.accent, color: '#fff', border: 'none',
            padding: '8px 14px', borderRadius: 6, cursor: 'pointer', fontSize: '0.85rem',
          }}>
            Send
          </button>
        </form>
      )}
      {c.replies?.map(r => renderComment(r, depth + 1))}
    </div>
  )

  if (loading) return <div style={{ color: colors.textMuted, textAlign: 'center', padding: 40 }}>Loading...</div>
  if (error) return <div style={{ color: colors.error, textAlign: 'center', padding: 40 }}>{error}</div>
  if (!post) return <div style={{ color: colors.textMuted, textAlign: 'center', padding: 40 }}>Post not found</div>

  const isAuthor = currentUser() === post.author

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      {/* Back link */}
      <button
        onClick={() => navigate(`/community/${slug}`)}
        style={{
          background: 'none', border: 'none', color: colors.accent,
          cursor: 'pointer', fontSize: '0.85rem', marginBottom: 16, padding: 0,
        }}
      >
        &larr; Back to board
      </button>

      {/* Post */}
      <div style={{
        background: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        padding: 28,
        marginBottom: 24,
      }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 12 }}>{post.title}</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20, fontSize: '0.85rem', color: colors.textMuted }}>
          <span>{post.author}</span>
          <span>{formatDate(post.created_at)}</span>
          <span>Views: {post.view_count}</span>
          {post.updated_at && <span>(edited {formatDate(post.updated_at)})</span>}
        </div>

        {isAuthor && (
          <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
            <button
              onClick={() => navigate(`/community/${slug}/write?edit=${post.id}`)}
              style={{
                background: colors.card, border: `1px solid ${colors.border}`,
                color: colors.accent, padding: '6px 14px', borderRadius: 6,
                cursor: 'pointer', fontSize: '0.8rem',
              }}
            >
              Edit
            </button>
            <button
              onClick={handleDelete}
              style={{
                background: colors.card, border: `1px solid ${colors.border}`,
                color: colors.error, padding: '6px 14px', borderRadius: 6,
                cursor: 'pointer', fontSize: '0.8rem',
              }}
            >
              Delete
            </button>
          </div>
        )}

        <div style={{ borderTop: `1px solid ${colors.border}`, paddingTop: 20 }}>
          <MarkdownRenderer content={post.content} />
        </div>

        {/* Attached files */}
        {post.files && post.files.length > 0 && (
          <div style={{ borderTop: `1px solid ${colors.border}`, paddingTop: 16, marginTop: 20 }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 8, color: colors.textMuted }}>
              Attachments
            </div>
            {post.files.map(f => (
              <a
                key={f.id}
                href={f.url}
                download
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 10px',
                  background: colors.inputBg,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 6,
                  marginBottom: 6,
                  color: colors.accent,
                  textDecoration: 'none',
                  fontSize: '0.85rem',
                }}
              >
                <span>{f.name}</span>
                {f.size && <span style={{ color: colors.textMuted, fontSize: '0.75rem' }}>({formatSize(f.size)})</span>}
              </a>
            ))}
          </div>
        )}
      </div>

      {/* Comments */}
      <div style={{ marginBottom: 24 }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 16 }}>
          Comments ({comments.length})
        </h3>
        {comments.map(c => renderComment(c))}
        {comments.length === 0 && (
          <div style={{ color: colors.textMuted, fontSize: '0.85rem', padding: 20, textAlign: 'center' }}>
            No comments yet.
          </div>
        )}
      </div>

      {/* New comment form */}
      {currentUser() && replyTo === null && (
        <form onSubmit={handleCommentSubmit} style={{
          background: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
          padding: 16,
          display: 'flex',
          gap: 10,
        }}>
          <input
            value={newComment}
            onChange={e => setNewComment(e.target.value)}
            placeholder="Write a comment..."
            style={{
              flex: 1, padding: '10px 12px', background: colors.inputBg,
              border: `1px solid ${colors.border}`, borderRadius: 6,
              color: colors.text, fontSize: '0.9rem', outline: 'none',
            }}
          />
          <button type="submit" disabled={submitting} style={{
            background: colors.accent, color: '#fff', border: 'none',
            padding: '10px 20px', borderRadius: 6, cursor: 'pointer',
            fontWeight: 600, fontSize: '0.9rem',
          }}>
            {submitting ? '...' : 'Comment'}
          </button>
        </form>
      )}
    </div>
  )
}
