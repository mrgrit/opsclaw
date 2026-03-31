import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import ChatBot from './ChatBot'

interface NavGroup {
  icon: string
  label: string
  children: { to: string; label: string; adminOnly?: boolean }[]
}

const navGroups: NavGroup[] = [
  {
    icon: 'ℹ️',
    label: '소개',
    children: [
      { to: '/about', label: '시스템 소개' },
      { to: '/manual', label: '매뉴얼' },
    ],
  },
  {
    icon: '📚',
    label: '학습',
    children: [
      { to: '/education', label: '교육과정' },
      { to: '/novel', label: '시나리오' },
      { to: '/ctf', label: 'CTF' },
    ],
  },
  {
    icon: '🏢',
    label: '커뮤니티',
    children: [
      { to: '/community', label: '게시판' },
      { to: '/members', label: '멤버' },
    ],
  },
  {
    icon: '💻',
    label: '도구',
    children: [
      { to: '/terminal', label: '터미널' },
      { to: '/admin-panel', label: '관리 콘솔', adminOnly: true },
    ],
  },
  {
    icon: '📄',
    label: '자료',
    children: [
      { to: '/papers', label: '연구자료', adminOnly: true },
    ],
  },
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
  const [roleLevel, setRoleLevel] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [pageContext, setPageContext] = useState('')
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({
    '\uD559\uC2B5': true,
    '\uCEE4\uBBA4\uB2C8\uD2F0': true,
    '\uB3C4\uAD6C': true,
    '\uC790\uB8CC': true,
  })

  const toggleGroup = (label: string) => {
    setOpenGroups(prev => ({ ...prev, [label]: !prev[label] }))
  }

  // 페이지 변경 시 컨텍스트 로드
  useEffect(() => {
    const path = location.pathname
    let apiUrl = ''

    // 교안 상세: /education/{course}/{week}
    const eduDetailMatch = path.match(/\/education\/([^/]+)\/([^/]+)/)
    if (eduDetailMatch) {
      apiUrl = `/portal/content/education/${eduDetailMatch[1]}/${eduDetailMatch[2]}`
    }
    // 교육과정 상세: /education/{course}
    else if (path.match(/\/education\/([^/]+)$/)) {
      const courseMatch = path.match(/\/education\/([^/]+)$/)!
      apiUrl = `/portal/content/education/${courseMatch[1]}`
    }
    // 교육과정 목록: /education
    else if (path === '/education') {
      apiUrl = `/portal/content/education`
    }
    // 시나리오 챕터: /novel/{volume}/{chapter}
    else if (path.match(/\/novel\/([^/]+)\/([^/]+)/)) {
      const novelMatch = path.match(/\/novel\/([^/]+)\/([^/]+)/)!
      apiUrl = `/portal/content/novel/${novelMatch[1]}/${novelMatch[2]}`
    }
    // 시나리오 볼륨 목록: /novel or /novel/{volume}
    else if (path.match(/\/novel(\/[^/]+)?$/)) {
      const volMatch = path.match(/\/novel(\/([^/]+))?$/)
      apiUrl = volMatch && volMatch[2]
        ? `/portal/content/novel/${volMatch[2]}`
        : `/portal/content/novel`
    }
    // 커뮤니티 게시판: /community
    else if (path.match(/\/community(\/[^/]+)?$/)) {
      const boardMatch = path.match(/\/community(\/([^/]+))?$/)
      apiUrl = boardMatch && boardMatch[2]
        ? `/portal/content/community/${boardMatch[2]}`
        : `/portal/content/community`
    }

    if (apiUrl) {
      fetch(apiUrl)
        .then(r => r.json())
        .then(d => setPageContext(d.content || d.summary || JSON.stringify(d)))
        .catch(() => setPageContext(''))
    } else {
      setPageContext('')
    }
  }, [location.pathname])

  useEffect(() => {
    const token = localStorage.getItem('portal_token')
    const username = localStorage.getItem('portal_username')
    if (token && username) {
      setUser(username)
      // Fetch role level for admin nav
      fetch('/portal/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : null)
        .then(data => { if (data?.role_level) setRoleLevel(data.role_level || '') })
        .catch(() => {})
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('portal_token')
    localStorage.removeItem('portal_username')
    setUser(null)
    setRoleLevel('')
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

        <nav style={{ display: 'flex', flexDirection: 'column', gap: 0, padding: '12px 0' }}>
          <NavLink
            to="/"
            end
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
            {'\u{1F3E0}'} 홈
          </NavLink>

          {navGroups.map(group => {
            const visibleChildren = group.children.filter(
              c => !c.adminOnly || roleLevel === 'admin'
            )
            if (visibleChildren.length === 0) return null
            const isOpen = openGroups[group.label] ?? false
            return (
              <div key={group.label}>
                <button
                  onClick={() => toggleGroup(group.label)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    width: '100%',
                    background: 'none',
                    border: 'none',
                    color: colors.textMuted,
                    padding: '10px 20px',
                    cursor: 'pointer',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    gap: 6,
                  }}
                >
                  <span>{group.icon}</span>
                  <span>{group.label}</span>
                  <span style={{ marginLeft: 'auto', fontSize: '0.65rem' }}>
                    {isOpen ? '\u25B2' : '\u25BC'}
                  </span>
                </button>
                {isOpen && visibleChildren.map(child => (
                  <NavLink
                    key={child.to}
                    to={child.to}
                    style={({ isActive }) => ({
                      padding: '8px 20px 8px 40px',
                      color: isActive ? colors.accent : colors.text,
                      background: isActive ? colors.accentBg : 'transparent',
                      textDecoration: 'none',
                      fontSize: '0.85rem',
                      borderLeft: isActive ? `3px solid ${colors.accent}` : '3px solid transparent',
                      display: 'block',
                      transition: 'background 0.15s',
                    })}
                  >
                    {child.label}
                  </NavLink>
                ))}
              </div>
            )
          })}

          {user && (
            <NavLink
              to="/profile"
              style={({ isActive }) => ({
                padding: '10px 20px',
                color: isActive ? colors.accent : colors.text,
                background: isActive ? colors.accentBg : 'transparent',
                textDecoration: 'none',
                fontSize: '0.9rem',
                borderLeft: isActive ? `3px solid ${colors.accent}` : '3px solid transparent',
                transition: 'background 0.15s',
                marginTop: 8,
              })}
            >
              내 프로필
            </NavLink>
          )}
        </nav>

        <div style={{ marginTop: 'auto', padding: '16px 20px', borderTop: `1px solid ${colors.border}` }}>
          <NavLink
            to="/admin"
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
