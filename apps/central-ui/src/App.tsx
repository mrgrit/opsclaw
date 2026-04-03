import React from 'react'
import { Routes, Route, NavLink, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard.tsx'
import Instances from './pages/Instances.tsx'
import Blockchain from './pages/Blockchain.tsx'
import CTF from './pages/CTF.tsx'
import NMS from './pages/NMS.tsx'
import Config from './pages/Config.tsx'

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/instances', label: 'Instances', icon: '🖥️' },
  { to: '/blockchain', label: 'Blockchain', icon: '⛓️' },
  { to: '/ctf', label: 'CTF', icon: '🏁' },
  { to: '/nms', label: 'NMS/SMS', icon: '📡' },
  { to: '/config', label: 'Config', icon: '⚙️' },
]

export default function App() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <nav style={{ width: 220, background: '#161b22', borderRight: '1px solid #30363d', padding: '20px 0', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '0 20px 24px', borderBottom: '1px solid #30363d' }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: '#a78bfa' }}>Central</h1>
          <div style={{ fontSize: 11, color: '#8b949e', marginTop: 4 }}>OpsClaw 통합 관리</div>
        </div>
        <div style={{ marginTop: 16, flex: 1 }}>
          {nav.map(n => (
            <NavLink key={n.to} to={n.to} style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10, padding: '10px 20px',
              color: isActive ? '#a78bfa' : '#8b949e', background: isActive ? '#1f2937' : 'transparent',
              textDecoration: 'none', fontSize: 14, borderLeft: isActive ? '3px solid #a78bfa' : '3px solid transparent',
            })}><span>{n.icon}</span><span>{n.label}</span></NavLink>
          ))}
        </div>
        <div style={{ padding: '12px 20px', fontSize: 11, color: '#484f58', borderTop: '1px solid #30363d' }}>v0.1.0 — :7000</div>
      </nav>
      <main style={{ flex: 1, padding: 32, overflow: 'auto' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/instances" element={<Instances />} />
          <Route path="/blockchain" element={<Blockchain />} />
          <Route path="/ctf" element={<CTF />} />
          <Route path="/nms" element={<NMS />} />
          <Route path="/config" element={<Config />} />
        </Routes>
      </main>
    </div>
  )
}
