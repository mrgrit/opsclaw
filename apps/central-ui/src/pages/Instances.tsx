import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const sc: Record<string, string> = { healthy: '#3fb950', registered: '#d29922', degraded: '#f85149', offline: '#484f58' }

export default function Instances() {
  const [rows, setRows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/instances')
      .then(d => setRows(d.instances || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: '#8b949e', padding: 40 }}>Loading instances...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40 }}>Error: {error}</div>

  return (
    <div>
      <h2 style={{ fontSize: 22, marginBottom: 24 }}>Instances ({rows.length})</h2>
      {rows.length === 0 ? (
        <div style={{ color: '#8b949e', background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 40, textAlign: 'center' }}>
          No instances registered. Use the API to register instances.
        </div>
      ) : (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
              {['ID', 'Name', 'Type', 'Status', 'API URL', 'Last Heartbeat'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '12px 16px', fontSize: 12, color: '#8b949e', fontWeight: 600, textTransform: 'uppercase' as const }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.instance_id} style={{ borderBottom: i < rows.length - 1 ? '1px solid #21262d' : 'none' }}>
                  <td style={td}><code style={{ fontSize: 12 }}>{r.instance_id}</code></td>
                  <td style={td}><strong>{r.name}</strong></td>
                  <td style={td}>
                    <span style={{ padding: '2px 10px', borderRadius: 10, fontSize: 11, fontWeight: 600, background: r.instance_type === 'bastion' ? '#0d2818' : r.instance_type === 'ccc' ? '#2d1b00' : '#1a1b3a', color: r.instance_type === 'bastion' ? '#3fb950' : r.instance_type === 'ccc' ? '#f97316' : '#58a6ff' }}>{r.instance_type}</span>
                  </td>
                  <td style={td}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: sc[r.status] || '#8b949e' }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'currentColor' }} />{r.status}
                    </span>
                  </td>
                  <td style={td}><code style={{ fontSize: 11, color: '#8b949e' }}>{r.api_url}</code></td>
                  <td style={td}><span style={{ fontSize: 11, color: '#8b949e' }}>{r.last_heartbeat ? new Date(r.last_heartbeat).toLocaleString('ko') : '-'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
const td: React.CSSProperties = { padding: '12px 16px', fontSize: 13 }
