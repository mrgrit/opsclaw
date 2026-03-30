import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import ChatBot from './ChatBot'

const navItems = [
  { to: '/', label: '홈', end: true },
  { to: '/education', label: '교육과정' },
  { to: '/novel', label: '소설' },
  { to: '/ctf', label: 'CTF' },
  { to: '/terminal', label: '터미널' },
  { to: '/papers', label: '논문' },
]

const colors = {
  bg: '#0d1117',
  sidebar: '#161b22',
  topbar: '#161b22',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  accent: '#58a6ff',
  accentBg: '#1f3a5c',
  border: '#30363d',
  card: '#21262d',
}

export default function PortalLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState<string | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const [pageContext, setPageContext] = useState('')

  // 페이지 변경 시 컨텍스트 로드
  useEffect(() => {
    const path = location.pathname
    let apiUrl = ''
    // 교안 상세
    const eduMatch = path.match(/\/education\/([^/]+)\/([^/]+)/)
    if (eduMatch) apiUrl = `/portal/content/education/${eduMatch[1]}/${eduMatch[2]}`
    // 소설 챕터
    const novelMatch = path.match(/\/novel\/([^/]+)\/([^/]+)/)
    if (novelMatch) apiUrl = `/portal/content/novel/${novelMatch[1]}/${novelMatch[2]}`

    if (apiUrl) {
      fetch(apiUrl).then(r => r.json()).then(d => setPageContext(d.content || '')).catch(() => setPageContext(''))
    } else {
      setPageContext('')
    }
  }, [location.pathname])

  useEffect(() => {
    const token = localStorage.getItem('portal_token')
    const username = localStorage.getItem('portal_username')
    if (token && username) {
      setUser(username)
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('portal_token')
    localStorage.removeItem('portal_username')
    setUser(null)
    setMenuOpen(false)
    navigate('/')
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: "'Segoe UI', system-ui, sans-serif", background: colors.bg, color: colors.text }}>
      {/* Sidebar */}
      <aside style={{
        width: 220,
        background: colors.sidebar,
        borderRight: `1px solid ${colors.border}`,
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
      }}>
        <div style={{
          padding: '20px',
          borderBottom: `1px solid ${colors.border}`,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}>
          <span style={{ fontSize: '1.3rem', fontWeight: 700, color: colors.accent }}>OpsClaw</span>
          <span style={{ fontSize: '0.75rem', color: colors.textMuted, background: colors.card, padding: '2px 8px', borderRadius: 4 }}>Portal</span>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: 2, padding: '12px 0' }}>
          {navItems.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              style={({ isActive }) => ({
                padding: '10px 20px',
                color: isActive ? colors.accent : colors.text,
                background: isActive ? colors.accentBg : 'transparent',
                textDecoration: 'none',
                fontSize: '0.9rem',
                borderLeft: isActive ? `3px solid ${colors.accent}` : '3px solid transparent',
                transition: 'background 0.15s',
              })}
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div style={{ marginTop: 'auto', padding: '16px 20px', borderTop: `1px solid ${colors.border}` }}>
          <NavLink
            to="/"
            style={{ color: colors.textMuted, textDecoration: 'none', fontSize: '0.8rem' }}
          >
            OpsClaw 관리 콘솔로 이동
          </NavLink>
        </div>
      </aside>

      {/* Main area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Top bar */}
        <header style={{
          height: 52,
          background: colors.topbar,
          borderBottom: `1px solid ${colors.border}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-end',
          padding: '0 24px',
          flexShrink: 0,
        }}>
          {user ? (
            <div style={{ position: 'relative' }}>
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                style={{
                  background: colors.card,
                  border: `1px solid ${colors.border}`,
                  color: colors.text,
                  padding: '6px 14px',
                  borderRadius: 6,
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                }}
              >
                {user}
              </button>
              {menuOpen && (
                <div style={{
                  position: 'absolute',
                  right: 0,
                  top: 40,
                  background: colors.card,
                  border: `1px solid ${colors.border}`,
                  borderRadius: 6,
                  padding: 4,
                  zIndex: 100,
                  minWidth: 120,
                }}>
                  <button
                    onClick={handleLogout}
                    style={{
                      display: 'block',
                      width: '100%',
                      background: 'none',
                      border: 'none',
                      color: '#f85149',
                      padding: '8px 12px',
                      cursor: 'pointer',
                      textAlign: 'left',
                      fontSize: '0.85rem',
                      borderRadius: 4,
                    }}
                  >
                    로그아웃
                  </button>
                </div>
              )}
            </div>
          ) : (
            <NavLink
              to="/login"
              style={{
                background: colors.accent,
                color: '#fff',
                padding: '6px 16px',
                borderRadius: 6,
                textDecoration: 'none',
                fontSize: '0.85rem',
                fontWeight: 600,
              }}
            >
              로그인
            </NavLink>
          )}
        </header>

        {/* Content */}
        <main style={{ flex: 1, padding: 32, overflowY: 'auto' }}>
          <Outlet />
        </main>
      </div>

      {/* AI 튜터 챗봇 */}
      <ChatBot pageContext={pageContext} />
    </div>
  )
}
