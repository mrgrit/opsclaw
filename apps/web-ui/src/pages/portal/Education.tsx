import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  green: '#3fb950',
}

interface Course {
  id: string
  name: string
  weeks: number
  description?: string
}

interface WeekItem {
  week: number
  title: string
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export default function Education() {
  const navigate = useNavigate()
  const { course } = useParams<{ course: string }>()
  const [courses, setCourses] = useState<Course[]>([])
  const [weeks, setWeeks] = useState<WeekItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    fetch('/portal/content/education', { headers: authHeaders() })
      .then(r => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => setCourses(Array.isArray(data) ? data : data.courses || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!course) { setWeeks([]); return }
    fetch(`/portal/content/education/${course}`, { headers: authHeaders() })
      .then(r => {
        if (!r.ok) throw new Error(`Error ${r.status}`)
        return r.json()
      })
      .then(data => setWeeks(Array.isArray(data) ? data : data.weeks || []))
      .catch(e => setError(e.message))
  }, [course])

  if (loading) return <div style={{ color: colors.textMuted }}>로딩 중...</div>
  if (error) return <div style={{ color: '#f85149' }}>오류: {error}</div>

  // If a course is selected, show its weeks
  if (course) {
    const courseInfo = courses.find(c => c.id === course)
    return (
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        <button
          onClick={() => navigate('/portal/education')}
          style={{
            background: 'none', border: 'none', color: colors.accent,
            cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16, padding: 0,
          }}
        >
          ← 과목 목록으로
        </button>
        <h2 style={{ fontSize: '1.4rem', marginBottom: 24 }}>
          {courseInfo?.name || course}
        </h2>

        {weeks.length === 0 ? (
          <div style={{ color: colors.textMuted }}>주차 정보가 없습니다.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {weeks.map(w => (
              <div
                key={w.week}
                onClick={() => navigate(`/portal/education/${course}/${w.week}`)}
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
                onMouseEnter={e => (e.currentTarget.style.borderColor = colors.accent)}
                onMouseLeave={e => (e.currentTarget.style.borderColor = colors.border)}
              >
                <span style={{
                  background: colors.accent,
                  color: '#fff',
                  width: 32, height: 32,
                  borderRadius: '50%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.85rem', fontWeight: 600, flexShrink: 0,
                }}>
                  {w.week}
                </span>
                <span>{w.title}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Course list
  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <h2 style={{ fontSize: '1.4rem', marginBottom: 24 }}>교육과정</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {courses.map(c => (
          <div
            key={c.id}
            onClick={() => navigate(`/portal/education/${c.id}`)}
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              padding: 20,
              cursor: 'pointer',
              transition: 'border-color 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = colors.accent)}
            onMouseLeave={e => (e.currentTarget.style.borderColor = colors.border)}
          >
            <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 8 }}>{c.name}</div>
            {c.description && (
              <div style={{ color: colors.textMuted, fontSize: '0.85rem', marginBottom: 8 }}>{c.description}</div>
            )}
            <div style={{ color: colors.green, fontSize: '0.8rem' }}>{c.weeks}주 과정</div>
          </div>
        ))}
      </div>
    </div>
  )
}
