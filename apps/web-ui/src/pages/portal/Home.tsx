import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  green: '#3fb950',
  purple: '#bc8cff',
  orange: '#d29922',
  red: '#f85149',
}

const stats = [
  { label: '교육과정', value: '10', unit: '과목', color: colors.accent },
  { label: '강의자료', value: '150', unit: '개', color: colors.green },
  { label: '시나리오', value: '10', unit: '부작', color: colors.purple },
  { label: 'CTF', value: 'Live', unit: '', color: colors.red },
]

const sections = [
  { to: '/education', title: '교육과정', desc: '사이버보안 10개 과목, 15주 분량의 체계적 교육과정', color: colors.accent },
  { to: '/novel', title: '시나리오', desc: '보안 시나리오 10부작 — 읽으면서 배우는 사이버보안', color: colors.purple },
  { to: '/ctf', title: 'CTF', desc: 'Capture The Flag 실습 환경 (CTFd)', color: colors.red },
  { to: '/terminal', title: '웹 터미널', desc: '실습 서버에 직접 접속하여 명령 실행', color: colors.green },
  { to: '/papers', title: '논문', desc: 'OpsClaw 연구 논문 (관리자 전용)', color: colors.orange },
]

export default function Home() {
  const navigate = useNavigate()
  const [loggedIn, setLoggedIn] = useState(false)

  useEffect(() => {
    setLoggedIn(!!localStorage.getItem('portal_token'))
  }, [])

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: 8 }}>
        OpsClaw Education Portal
      </h1>
      <p style={{ color: colors.textMuted, marginBottom: 32, fontSize: '1rem' }}>
        사이버보안 교육, 시나리오, CTF 실습을 한곳에서
      </p>

      {!loggedIn && (
        <div style={{
          background: '#1c2333',
          border: `1px solid ${colors.accent}`,
          borderRadius: 8,
          padding: '16px 20px',
          marginBottom: 28,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <span>로그인하면 모든 콘텐츠에 접근할 수 있습니다.</span>
          <button
            onClick={() => navigate('/login')}
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
            로그인
          </button>
        </div>
      )}

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
        {stats.map(s => (
          <div key={s.label} style={{
            background: colors.card,
            border: `1px solid ${colors.border}`,
            borderRadius: 8,
            padding: '20px 16px',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '2rem', fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ color: colors.textMuted, fontSize: '0.85rem', marginTop: 4 }}>
              {s.label} {s.unit}
            </div>
          </div>
        ))}
      </div>

      {/* Section cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {sections.map(s => (
          <div
            key={s.to}
            onClick={() => navigate(s.to)}
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              borderRadius: 8,
              padding: 20,
              cursor: 'pointer',
              transition: 'border-color 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = s.color)}
            onMouseLeave={e => (e.currentTarget.style.borderColor = colors.border)}
          >
            <div style={{ fontSize: '1.1rem', fontWeight: 600, color: s.color, marginBottom: 8 }}>
              {s.title}
            </div>
            <div style={{ color: colors.textMuted, fontSize: '0.85rem', lineHeight: 1.5 }}>
              {s.desc}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
