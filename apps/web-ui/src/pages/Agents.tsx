import { useEffect, useState } from 'react'
import { api } from '../api/client'

interface LedgerEntry {
  agent_id: string
  balance: number
  total_tasks: number
  success_count: number
  fail_count: number
  updated_at: string
}

export default function Agents() {
  const [entries, setEntries] = useState<LedgerEntry[]>([])
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const r = await api.get<{ leaderboard: LedgerEntry[] }>('/pow/leaderboard?limit=50')
      setEntries(r.leaderboard ?? [])
    } catch {
      setEntries([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0 }}>Agents</h1>
        <button onClick={load} disabled={loading} style={btnStyle}>
          {loading ? '로딩 중...' : '새로고침'}
        </button>
      </div>

      {entries.length === 0 ? (
        <p style={{ color: '#9ca3af' }}>등록된 에이전트 없음 (execute-plan 실행 후 자동 등록)</p>
      ) : (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
                <th style={thStyle}>Agent ID</th>
                <th style={thStyle}>잔액</th>
                <th style={thStyle}>전체</th>
                <th style={thStyle}>성공</th>
                <th style={thStyle}>실패</th>
                <th style={thStyle}>마지막 업데이트</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e, i) => (
                <tr key={e.agent_id} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                  <td style={tdStyle}>
                    <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#374151' }}>
                      {e.agent_id}
                    </span>
                  </td>
                  <td style={{ ...tdStyle, fontWeight: 700, color: e.balance >= 0 ? '#059669' : '#dc2626' }}>
                    {e.balance.toFixed(4)}
                  </td>
                  <td style={tdStyle}>{e.total_tasks}</td>
                  <td style={{ ...tdStyle, color: '#059669' }}>{e.success_count}</td>
                  <td style={{ ...tdStyle, color: e.fail_count > 0 ? '#dc2626' : '#6b7280' }}>{e.fail_count}</td>
                  <td style={{ ...tdStyle, color: '#9ca3af', fontSize: '0.75rem' }}>
                    {e.updated_at ? new Date(e.updated_at).toLocaleString('ko-KR') : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  padding: '8px 14px', background: '#2563eb', color: '#fff',
  border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem',
}
const thStyle: React.CSSProperties = {
  padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#374151', fontSize: '0.8rem',
}
const tdStyle: React.CSSProperties = {
  padding: '10px 16px', color: '#374151',
}
