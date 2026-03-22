import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Project, LedgerEntry } from '../api/types'
import StageBadge from '../components/StageBadge'

interface Health { status: string }

export default function Dashboard() {
  const [health, setHealth] = useState<Health | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [leaderboard, setLeaderboard] = useState<LedgerEntry[]>([])

  useEffect(() => {
    api.get<Health>('/health').then(setHealth).catch(() => setHealth({ status: 'error' }))
    api.get<{ projects: Project[] }>('/projects?limit=5').then(r => setProjects(r.projects)).catch(() => {})
    api.get<{ leaderboard: LedgerEntry[] }>('/pow/leaderboard').then(r => setLeaderboard(r.leaderboard)).catch(() => {})
  }, [])

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Dashboard</h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16, marginBottom: 32 }}>
        <Card title="서비스 상태">
          <p style={{ color: health?.status === 'ok' ? '#10b981' : '#ef4444', fontWeight: 700 }}>
            {health ? health.status.toUpperCase() : 'loading...'}
          </p>
        </Card>
        <Card title="활성 프로젝트">
          <p style={{ fontSize: '2rem', fontWeight: 700 }}>
            {projects.filter(p => p.current_stage !== 'closed').length}
          </p>
        </Card>
        <Card title="에이전트 수">
          <p style={{ fontSize: '2rem', fontWeight: 700 }}>{leaderboard.length}</p>
        </Card>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <Card title="최근 프로젝트">
          {projects.length === 0 ? <p style={{ color: '#9ca3af' }}>없음</p> : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <th style={th}>이름</th>
                  <th style={th}>Stage</th>
                </tr>
              </thead>
              <tbody>
                {projects.map(p => (
                  <tr key={p.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={td}>{p.name}</td>
                    <td style={td}><StageBadge stage={p.current_stage} outcome={p.outcome} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card title="에이전트 보상 랭킹">
          {leaderboard.length === 0 ? <p style={{ color: '#9ca3af' }}>없음</p> : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <th style={th}>#</th>
                  <th style={th}>Agent</th>
                  <th style={th}>잔액</th>
                  <th style={th}>Tasks</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((e, i) => (
                  <tr key={e.agent_id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={td}>{i + 1}</td>
                    <td style={{ ...td, maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                      title={e.agent_id}>
                      {e.agent_id.replace(/^https?:\/\//, '')}
                    </td>
                    <td style={{ ...td, fontWeight: 600, color: e.balance >= 0 ? '#10b981' : '#ef4444' }}>
                      {e.balance.toFixed(2)}
                    </td>
                    <td style={td}>{e.total_tasks}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  )
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 20 }}>
      <h3 style={{ margin: '0 0 12px', fontSize: '0.9rem', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{title}</h3>
      {children}
    </div>
  )
}

const th: React.CSSProperties = { textAlign: 'left', padding: '4px 8px', color: '#6b7280', fontWeight: 600 }
const td: React.CSSProperties = { padding: '6px 8px' }
