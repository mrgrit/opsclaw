import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  green: '#3fb950',
}

interface Member {
  id: number
  username: string
  role_level: string
  photo_url: string | null
  bio_short: string
  created_at: string
}

const roleColors: Record<string, string> = {
  admin: '#f85149',
  ycdc: '#3fb950',
  demo: '#d29922',
  general: '#8b949e',
}

const roleLabels: Record<string, string> = {
  admin: '관리자',
  ycdc: 'YCDC',
  demo: '데모',
  general: '일반',
}

export default function Members() {
  const navigate = useNavigate()
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/portal/members')
      .then(r => r.json())
      .then(d => setMembers(d.members || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: colors.textMuted, textAlign: 'center', padding: 40 }}>Loading...</div>

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 8 }}>멤버</h1>
      <p style={{ color: colors.textMuted, marginBottom: 24, fontSize: '0.9rem' }}>
        {members.length}명의 멤버
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16 }}>
        {members.map(m => (
          <div
            key={m.id}
            onClick={() => navigate(`/profile/${m.username}`)}
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: 12,
              padding: 20,
              cursor: 'pointer',
              textAlign: 'center',
              transition: 'border-color 0.15s, transform 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = colors.accent; e.currentTarget.style.transform = 'translateY(-2px)' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = colors.border; e.currentTarget.style.transform = 'none' }}
          >
            {/* 프로필 사진 */}
            {m.photo_url ? (
              <img
                src={m.photo_url}
                alt={m.username}
                style={{
                  width: 72, height: 72, borderRadius: '50%',
                  objectFit: 'cover', margin: '0 auto 12px',
                  display: 'block', border: `2px solid ${roleColors[m.role_level] || colors.border}`,
                }}
              />
            ) : (
              <div style={{
                width: 72, height: 72, borderRadius: '50%',
                background: `${colors.accent}22`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 12px', fontSize: '1.8rem', fontWeight: 700,
                color: colors.accent, border: `2px solid ${roleColors[m.role_level] || colors.border}`,
              }}>
                {m.username[0]?.toUpperCase()}
              </div>
            )}

            {/* 이름 */}
            <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 4 }}>{m.username}</div>

            {/* 등급 뱃지 */}
            <span style={{
              display: 'inline-block',
              fontSize: '0.7rem',
              padding: '2px 8px',
              borderRadius: 10,
              background: `${roleColors[m.role_level] || colors.textMuted}22`,
              color: roleColors[m.role_level] || colors.textMuted,
              marginBottom: 8,
            }}>
              {roleLabels[m.role_level] || m.role_level}
            </span>

            {/* 한줄 소개 */}
            {m.bio_short && (
              <div style={{
                color: colors.textMuted, fontSize: '0.8rem',
                overflow: 'hidden', textOverflow: 'ellipsis',
                whiteSpace: 'nowrap', marginTop: 4,
              }}>
                {m.bio_short}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
