import { NavLink, Outlet } from 'react-router-dom'

const nav = [
  { to: '/', label: 'Dashboard' },
  { to: '/projects', label: 'Projects' },
  { to: '/playbooks', label: 'Playbooks' },
  { to: '/replay', label: 'PoW Replay' },
  { to: '/settings', label: 'Settings' },
]

export default function Layout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      <aside style={{
        width: 200,
        background: '#111827',
        color: '#f9fafb',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 0',
        flexShrink: 0,
      }}>
        <div style={{ padding: '0 20px 24px', fontWeight: 700, fontSize: '1.1rem', letterSpacing: '-0.02em' }}>
          OpsClaw
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {nav.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              style={({ isActive }) => ({
                padding: '8px 20px',
                color: isActive ? '#60a5fa' : '#d1d5db',
                background: isActive ? '#1e3a5f' : 'transparent',
                textDecoration: 'none',
                fontSize: '0.9rem',
                borderLeft: isActive ? '3px solid #60a5fa' : '3px solid transparent',
              })}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main style={{ flex: 1, padding: 32, background: '#f9fafb', overflowY: 'auto' }}>
        <Outlet />
      </main>
    </div>
  )
}
