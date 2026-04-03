import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const sc: Record<string, string> = { healthy: '#3fb950', registered: '#d29922', degraded: '#f85149', offline: '#484f58' }

export default function Instances() {
  const [rows, setRows] = useState<any[]>([])
  useEffect(() => { api('/instances').then(d => setRows(d.instances)).catch(console.error) }, [])

  return (
    <div>
      <h2 style={{ fontSize: 22, marginBottom: 24 }}>Instances</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
          {['ID', 'Name', 'Type', 'Status', 'API URL', 'Last Heartbeat'].map(h => (
            <th key={h} style={{ textAlign: 'left', padding: '10px 12px', fontSize: 12, color: '#8b949e' }}>{h}</th>
          ))}
        </tr></thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.instance_id} style={{ borderBottom: '1px solid #21262d' }}>
              <td style={td}><code>{r.instance_id}</code></td>
              <td style={td}><strong>{r.name}</strong></td>
              <td style={td}>
                <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 11, background: r.instance_type === 'bastion' ? '#0d2818' : r.instance_type === 'ccc' ? '#2d1b00' : '#1a1b3a', color: r.instance_type === 'bastion' ? '#3fb950' : r.instance_type === 'ccc' ? '#f97316' : '#58a6ff' }}>{r.instance_type}</span>
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
  )
}
const td: React.CSSProperties = { padding: '10px 12px', fontSize: 13 }
