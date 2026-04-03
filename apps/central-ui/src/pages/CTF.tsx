import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

export default function CTF() {
  const [challenges, setChallenges] = useState<any[]>([])
  const [scoreboard, setScoreboard] = useState<any[]>([])

  useEffect(() => {
    api('/ctf/challenges').then(d => setChallenges(d.challenges)).catch(console.error)
    api('/ctf/scoreboard').then(d => setScoreboard(d.scoreboard)).catch(console.error)
  }, [])

  const diffColor: Record<string, string> = { easy: '#3fb950', medium: '#d29922', hard: '#f85149' }

  return (
    <div>
      <h2 style={{ fontSize: 22, marginBottom: 24 }}>CTF Server</h2>
      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
        <div style={{ flex: 2, minWidth: 400 }}>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>Challenges ({challenges.length})</h3>
          {challenges.map(c => (
            <div key={c.id} style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16, marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <strong>{c.title}</strong>
                <span style={{ color: '#a78bfa', fontWeight: 600 }}>{c.points} pts</span>
              </div>
              <div style={{ display: 'flex', gap: 8, fontSize: 12 }}>
                <span style={{ padding: '2px 8px', borderRadius: 4, background: '#21262d', color: '#8b949e' }}>{c.category}</span>
                <span style={{ padding: '2px 8px', borderRadius: 4, color: diffColor[c.difficulty] || '#8b949e' }}>{c.difficulty}</span>
              </div>
              {c.description && <div style={{ fontSize: 12, color: '#8b949e', marginTop: 8 }}>{c.description}</div>}
            </div>
          ))}
        </div>
        <div style={{ flex: 1, minWidth: 300 }}>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>Scoreboard</h3>
          <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 16 }}>
            {scoreboard.map((s, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, padding: '8px 0', borderBottom: '1px solid #21262d', fontSize: 13 }}>
                <span style={{ width: 24, color: i < 3 ? '#ffd700' : '#8b949e', fontWeight: 700 }}>#{i + 1}</span>
                <span style={{ flex: 1 }}>{s.student_id}</span>
                <span style={{ color: '#8b949e' }}>{s.instance_id}</span>
                <span style={{ color: '#a78bfa', fontWeight: 600 }}>{s.total_points} pts</span>
              </div>
            ))}
            {scoreboard.length === 0 && <div style={{ color: '#8b949e' }}>No submissions yet</div>}
          </div>
        </div>
      </div>
    </div>
  )
}
