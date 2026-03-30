import { useState, useEffect } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import MarkdownRenderer from '../../components/portal/MarkdownRenderer'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  inputBg: '#161b22',
  error: '#f85149',
}

const authHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : ({} as Record<string, string>)
}

export default function PostWrite() {
  const { slug } = useParams<{ slug: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const editId = searchParams.get('edit')

  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [preview, setPreview] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [boardAllowFiles, setBoardAllowFiles] = useState(true)

  // Load existing post for edit
  useEffect(() => {
    if (editId) {
      fetch(`/portal/posts/${editId}`, { headers: authHeaders() })
        .then(r => r.json())
        .then(data => {
          const p = data.post || data
          setTitle(p.title || '')
          setContent(p.content || '')
        })
        .catch(() => {})
    }
    // Check board settings
    if (slug) {
      fetch(`/portal/boards/${slug}`, { headers: authHeaders() })
        .then(r => r.json())
        .then(data => {
          if (data.allow_files === false) setBoardAllowFiles(false)
        })
        .catch(() => {})
    }
  }, [editId, slug])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !content.trim()) {
      setError('Title and content are required')
      return
    }
    setLoading(true)
    setError('')

    try {
      let url: string
      let method: string

      if (editId) {
        url = `/portal/posts/${editId}`
        method = 'PUT'
      } else {
        url = `/portal/boards/${slug}/posts`
        method = 'POST'
      }

      // If files, use FormData; otherwise JSON
      if (files.length > 0 && !editId) {
        const fd = new FormData()
        fd.append('title', title)
        fd.append('content', content)
        files.forEach(f => fd.append('files', f))
        const res = await fetch(url, {
          method,
          headers: authHeaders(),
          body: fd,
        })
        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          throw new Error(data.detail || `Error ${res.status}`)
        }
        const data = await res.json()
        navigate(`/community/${slug}/${data.id || data.post?.id || ''}`)
      } else {
        const res = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json', ...authHeaders() },
          body: JSON.stringify({ title, content }),
        })
        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          throw new Error(data.detail || `Error ${res.status}`)
        }
        const data = await res.json()
        navigate(`/community/${slug}/${data.id || data.post?.id || ''}`)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 12px',
    background: colors.inputBg,
    border: `1px solid ${colors.border}`,
    borderRadius: 6,
    color: colors.text,
    fontSize: '0.9rem',
    outline: 'none',
    boxSizing: 'border-box',
  }

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <button
        onClick={() => navigate(`/community/${slug}`)}
        style={{
          background: 'none', border: 'none', color: colors.accent,
          cursor: 'pointer', fontSize: '0.85rem', marginBottom: 16, padding: 0,
        }}
      >
        &larr; Back to board
      </button>

      <h1 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: 20 }}>
        {editId ? 'Edit Post' : 'New Post'}
      </h1>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', fontSize: '0.85rem', color: colors.textMuted, marginBottom: 6 }}>
            Title
          </label>
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            required
            style={inputStyle}
            placeholder="Post title"
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <label style={{ fontSize: '0.85rem', color: colors.textMuted }}>
              Content (Markdown)
            </label>
            <button
              type="button"
              onClick={() => setPreview(!preview)}
              style={{
                background: colors.card,
                border: `1px solid ${colors.border}`,
                color: preview ? colors.accent : colors.textMuted,
                padding: '4px 12px',
                borderRadius: 4,
                cursor: 'pointer',
                fontSize: '0.8rem',
              }}
            >
              {preview ? 'Edit' : 'Preview'}
            </button>
          </div>

          {preview ? (
            <div style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: 6,
              padding: 20,
              minHeight: 300,
            }}>
              <MarkdownRenderer content={content || '*Nothing to preview*'} />
            </div>
          ) : (
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              required
              style={{
                ...inputStyle,
                minHeight: 300,
                resize: 'vertical',
                fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                lineHeight: 1.6,
              }}
              placeholder="Write your post in Markdown..."
            />
          )}
        </div>

        {/* File upload */}
        {boardAllowFiles && !editId && (
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: colors.textMuted, marginBottom: 6 }}>
              Attachments
            </label>
            <input
              type="file"
              multiple
              onChange={e => setFiles(Array.from(e.target.files || []))}
              style={{
                background: colors.inputBg,
                border: `1px solid ${colors.border}`,
                borderRadius: 6,
                padding: 8,
                color: colors.text,
                fontSize: '0.85rem',
                width: '100%',
              }}
            />
            {files.length > 0 && (
              <div style={{ marginTop: 8, fontSize: '0.8rem', color: colors.textMuted }}>
                {files.length} file(s) selected
              </div>
            )}
          </div>
        )}

        {error && (
          <div style={{
            color: colors.error, fontSize: '0.85rem', padding: '8px 12px',
            background: '#2d1418', borderRadius: 6, marginBottom: 16,
          }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            type="submit"
            disabled={loading}
            style={{
              background: colors.accent,
              color: '#fff',
              border: 'none',
              padding: '10px 28px',
              borderRadius: 6,
              fontSize: '0.95rem',
              fontWeight: 600,
              cursor: loading ? 'wait' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? '...' : editId ? 'Update' : 'Publish'}
          </button>
          <button
            type="button"
            onClick={() => navigate(`/community/${slug}`)}
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              color: colors.textMuted,
              padding: '10px 20px',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: '0.95rem',
            }}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
