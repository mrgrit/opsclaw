import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  green: '#3fb950',
  bg: '#0d1117',
}

interface Course {
  name: string
  title: string
  group: string
  icon: string
  color: string
  description: string
  weeks: string[]
  week_count: number
}

interface CourseGroup {
  name: string
  courses: Course[]
}

interface WeekItem {
  week: string
  title: string
  id: string
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : ({} as Record<string, string>)
}

export default function Education() {
  const navigate = useNavigate()
  const { course } = useParams<{ course: string }>()
  const [groups, setGroups] = useState<CourseGroup[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [weeks, setWeeks] = useState<WeekItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    fetch('/portal/content/education', { headers: authHeaders() })
      .then(r => { if (!r.ok) throw new Error(`Error ${r.status}`); return r.json() })
      .then(data => {
        setCourses(data.courses || [])
        setGroups(data.groups || [])
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!course) { setWeeks([]); return }
    fetch(`/portal/content/education/${course}`, { headers: authHeaders() })
      .then(r => { if (!r.ok) throw new Error(`Error ${r.status}`); return r.json() })
      .then(data => setWeeks(data.weeks || []))
      .catch(e => setError(e.message))
  }, [course])

  if (loading) return <div style={{ color: colors.textMuted, textAlign: 'center', padding: 40 }}>로딩 중...</div>
  if (error) return <div style={{ color: '#f85149', textAlign: 'center', padding: 40 }}>오류: {error}</div>

  // 주차 목록 뷰 (코스 선택 후)
  if (course) {
    const courseInfo = courses.find(c => c.name === course)
    return (
      <div style={{ maxWidth: 860, margin: '0 auto' }}>
        <button
          onClick={() => navigate('/education')}
          style={{ background: 'none', border: 'none', color: colors.accent, cursor: 'pointer', fontSize: '0.9rem', marginBottom: 16, padding: 0 }}
        >← 교육과정 목록</button>

        {courseInfo && (
          <div style={{
            background: colors.card, border: `1px solid ${colors.border}`,
            borderRadius: 8, padding: 20, marginBottom: 24,
            borderLeft: `4px solid ${courseInfo.color}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <span style={{ fontSize: '1.5rem' }}>{courseInfo.icon}</span>
              <h2 style={{ fontSize: '1.3rem', margin: 0 }}>{courseInfo.title}</h2>
            </div>
            <div style={{ color: colors.textMuted, fontSize: '0.9rem', lineHeight: 1.6 }}>
              {courseInfo.description}
            </div>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {weeks.map(w => (
            <div
              key={w.id}
              onClick={() => navigate(`/education/${course}/${w.id}`)}
              style={{
                background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 8,
                padding: '12px 20px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 14,
                transition: 'border-color 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = courseInfo?.color || colors.accent)}
              onMouseLeave={e => (e.currentTarget.style.borderColor = colors.border)}
            >
              <span style={{
                background: courseInfo?.color || colors.accent, color: '#fff',
                width: 32, height: 32, borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.8rem', fontWeight: 600, flexShrink: 0,
              }}>{w.week}</span>
              <span style={{ fontSize: '0.9rem' }}>{w.title}</span>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // 교육과정 목록 — 그룹별 카드
  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: 8 }}>교육과정</h1>
      <p style={{ color: colors.textMuted, fontSize: '0.95rem', lineHeight: 1.7, marginBottom: 32 }}>
        10개 과목 / 150강 / 총 450시간의 보안 교육 커리큘럼.<br/>
        실습 인프라(secu/web/siem)와 OpsClaw를 활용한 <strong>실습 중심</strong> 교육입니다.
      </p>

      {groups.map(g => (
        <div key={g.name} style={{ marginBottom: 32 }}>
          <h2 style={{
            fontSize: '1rem', fontWeight: 600, color: colors.textMuted,
            textTransform: 'uppercase', letterSpacing: '0.5px',
            marginBottom: 14, paddingBottom: 8,
            borderBottom: `1px solid ${colors.border}`,
          }}>
            {g.name} ({g.courses.length}과목)
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
            {g.courses.map(c => (
              <div
                key={c.name}
                onClick={() => navigate(`/education/${c.name}`)}
                style={{
                  background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 8,
                  padding: 18, cursor: 'pointer', transition: 'border-color 0.15s, transform 0.15s',
                  borderLeft: `3px solid ${c.color}`,
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = c.color; e.currentTarget.style.transform = 'translateY(-2px)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = colors.border; e.currentTarget.style.transform = 'none' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span style={{ fontSize: '1.3rem' }}>{c.icon}</span>
                  <span style={{ fontSize: '0.95rem', fontWeight: 600 }}>{c.title}</span>
                </div>
                <div style={{
                  color: colors.textMuted, fontSize: '0.82rem', lineHeight: 1.5,
                  marginBottom: 10,
                  display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as const,
                  overflow: 'hidden',
                }}>
                  {c.description}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: c.color, fontSize: '0.78rem', fontWeight: 600 }}>
                    {c.week_count}주 과정
                  </span>
                  <span style={{ color: colors.textMuted, fontSize: '0.75rem' }}>
                    {c.week_count * 3}시간
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
