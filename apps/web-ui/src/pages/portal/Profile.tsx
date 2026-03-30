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
}

interface UserProfile {
  username: string
  email?: string
  bio?: string
  photo_url?: string
  role_level?: number
  created_at?: string
  recent_posts?: { id: number; title: string; board_slug: string; created_at: string }[]
}

const authHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : ({} as Record<string, string>)
}

export default function Profile() {
  const { username: paramUser } = useParams<{ username: string }>()
  const navigate = useNavigate()
  const currentUser = localStorage.getItem('portal_username')
  const targetUser = paramUser || currentUser

  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [bio, setBio] = useState('')
  const [photoFile, setPhotoFile] = useState<File | null>(null)
  const [saving, setSaving] = useState(false)

  const isOwn = !paramUser || paramUser === currentUser

  useEffect(() => {
    if (!targetUser) {
      navigate('/login')
      return
    }
    setLoading(true)
    fetch(`/portal/profile/${targetUser}`, { headers: authHeaders() })
      .then(r => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => {
        setProfile(data)
        setBio(data.bio || '')
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [targetUser])

  const handleSaveBio = async () => {
    setSaving(true)
    try {
      const res = await fetch(`/portal/profile/${targetUser}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ bio }),
      })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const data = await res.json()
      setProfile(prev => prev ? { ...prev, bio: data.bio || bio } : prev)
      setEditing(false)
    } catch {
      alert('Failed to save bio')
    } finally {
      setSaving(false)
    }
  }

  const handlePhotoUpload = async () => {
    if (!photoFile) return
    setSaving(true)
    try {
      const fd = new FormData()
      fd.append('photo', photoFile)
      const res = await fetch(`/portal/profile/${targetUser}/photo`, {
        method: 'POST',
        headers: authHeaders(),
        body: fd,
      })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const data = await res.json()
      setProfile(prev => prev ? { ...prev, photo_url: data.photo_url } : prev)
      setPhotoFile(null)
    } catch {
      alert('Failed to upload photo')
    } finally {
      setSaving(false)
    }
  }

  const formatDate = (d: string) => {
    try { return new Date(d).toLocaleDateString('ko-KR') } catch { return d }
  }

  if (loading) return <div style={{ color: colors.textMuted, textAlign: 'center', padding: 40 }}>Loading...</div>
  if (error) return <div style={{ color: colors.error, textAlign: 'center', padding: 40 }}>{error}</div>
  if (!profile) return <div style={{ color: colors.textMuted, textAlign: 'center', padding: 40 }}>User not found</div>

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      {/* Profile header */}
      <div style={{
        background: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        padding: 28,
        marginBottom: 24,
        display: 'flex',
        gap: 24,
        alignItems: 'flex-start',
      }}>
        {/* Avatar */}
        <div style={{ flexShrink: 0 }}>
          {profile.photo_url ? (
            <img
              src={profile.photo_url}
              alt={profile.username}
              style={{ width: 80, height: 80, borderRadius: '50%', objectFit: 'cover' }}
            />
          ) : (
            <div style={{
              width: 80, height: 80, borderRadius: '50%',
              background: colors.accent + '33',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '2rem', color: colors.accent, fontWeight: 700,
            }}>
              {profile.username[0]?.toUpperCase()}
            </div>
          )}
          {isOwn && (
            <div style={{ marginTop: 8 }}>
              <input
                type="file"
                accept="image/*"
                onChange={e => setPhotoFile(e.target.files?.[0] || null)}
                style={{ display: 'none' }}
                id="photo-upload"
              />
              <label
                htmlFor="photo-upload"
                style={{
                  display: 'block',
                  textAlign: 'center',
                  color: colors.accent,
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                }}
              >
                Change photo
              </label>
              {photoFile && (
                <button
                  onClick={handlePhotoUpload}
                  disabled={saving}
                  style={{
                    display: 'block', margin: '4px auto 0', background: colors.accent,
                    color: '#fff', border: 'none', padding: '4px 10px', borderRadius: 4,
                    cursor: 'pointer', fontSize: '0.75rem',
                  }}
                >
                  Upload
                </button>
              )}
            </div>
          )}
        </div>

        {/* Info */}
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: 4 }}>{profile.username}</h1>
          {profile.email && (
            <div style={{ color: colors.textMuted, fontSize: '0.85rem', marginBottom: 4 }}>{profile.email}</div>
          )}
          {profile.created_at && (
            <div style={{ color: colors.textMuted, fontSize: '0.8rem', marginBottom: 12 }}>
              Joined {formatDate(profile.created_at)}
            </div>
          )}

          {/* Bio */}
          {editing ? (
            <div>
              <textarea
                value={bio}
                onChange={e => setBio(e.target.value)}
                style={{
                  width: '100%', minHeight: 100, padding: '10px 12px',
                  background: colors.inputBg, border: `1px solid ${colors.border}`,
                  borderRadius: 6, color: colors.text, fontSize: '0.9rem',
                  outline: 'none', resize: 'vertical', boxSizing: 'border-box',
                  fontFamily: "'JetBrains Mono', monospace",
                }}
                placeholder="Write something about yourself (Markdown)..."
              />
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <button
                  onClick={handleSaveBio}
                  disabled={saving}
                  style={{
                    background: colors.accent, color: '#fff', border: 'none',
                    padding: '6px 16px', borderRadius: 6, cursor: 'pointer', fontSize: '0.85rem',
                  }}
                >
                  {saving ? '...' : 'Save'}
                </button>
                <button
                  onClick={() => { setEditing(false); setBio(profile.bio || '') }}
                  style={{
                    background: colors.card, border: `1px solid ${colors.border}`,
                    color: colors.textMuted, padding: '6px 16px', borderRadius: 6,
                    cursor: 'pointer', fontSize: '0.85rem',
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div>
              {profile.bio ? (
                <MarkdownRenderer content={profile.bio} />
              ) : (
                <div style={{ color: colors.textMuted, fontSize: '0.85rem', fontStyle: 'italic' }}>
                  No bio yet.
                </div>
              )}
              {isOwn && (
                <button
                  onClick={() => setEditing(true)}
                  style={{
                    background: 'none', border: 'none', color: colors.accent,
                    cursor: 'pointer', fontSize: '0.8rem', marginTop: 8, padding: 0,
                  }}
                >
                  Edit bio
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Recent posts */}
      <h2 style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: 12 }}>Recent Posts</h2>
      <div style={{
        background: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
        overflow: 'hidden',
      }}>
        {(!profile.recent_posts || profile.recent_posts.length === 0) ? (
          <div style={{ padding: 30, textAlign: 'center', color: colors.textMuted, fontSize: '0.85rem' }}>
            No posts yet.
          </div>
        ) : (
          profile.recent_posts.map(p => (
            <div
              key={p.id}
              onClick={() => navigate(`/community/${p.board_slug}/${p.id}`)}
              style={{
                padding: '12px 16px',
                borderBottom: `1px solid ${colors.border}`,
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                transition: 'background 0.1s',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = colors.inputBg)}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <span style={{ fontSize: '0.9rem', color: colors.text }}>{p.title}</span>
              <span style={{ fontSize: '0.8rem', color: colors.textMuted }}>{formatDate(p.created_at)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
