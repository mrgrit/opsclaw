import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

export default function NMS() {
  const [nms, setNms] = useState<any>(null)
  const [metrics, setMetrics] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])

  useEffect(() => {
    api('/nms/status').then(setNms).catch(console.error)
    api('/sms/metrics').then(d => setMetrics(d.metrics)).catch(console.error)
    api('/sms/alerts').then(d => setAlerts(d.alerts)).catch(console.error)
  }, [])

  return (
    <div>
      <h2 style={{ fontSize: 22, marginBottom: 24 }}>NMS / SMS</h2>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div style={{ background: '#1f0d0d', border: '1px solid #da3633', borderRadius: 8, padding: 16, marginBottom: 24 }}>
          <h3 style={{ fontSize: 14, color: '#f85149', marginBottom: 8 }}>Alerts ({alerts.length})</h3>
          {alerts.map((a, i) => (
            <div key={i} style={{ fontSize: 13, padding: '4px 0' }}>
              <strong>{a.instance_id}</strong> — {a.type}: {a.status} (last: {a.last_heartbeat})
            </div>
          ))}
        </div>
      )}

      {/* Network Status */}
      <h3 style={{ fontSize: 16, marginBottom: 12 }}>Network Status</h3>
      {nms && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
          <div style={card}><div style={{ fontSize: 28, fontWeight: 700, color: '#a78bfa' }}>{nms.total}</div><div style={cl}>Total</div></div>
          <div style={card}><div style={{ fontSize: 28, fontWeight: 700, color: '#3fb950' }}>{nms.reachable}</div><div style={cl}>Reachable</div></div>
          <div style={card}><div style={{ fontSize: 28, fontWeight: 700, color: '#f85149' }}>{nms.total - nms.reachable}</div><div style={cl}>Down</div></div>
        </div>
      )}

      {nms?.instances && (
        <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 32 }}>
          <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
            {['Instance', 'Type', 'Reachable', 'Latency', 'Health'].map(h => (
              <th key={h} style={{ textAlign: 'left', padding: '10px 12px', fontSize: 12, color: '#8b949e' }}>{h}</th>
            ))}
          </tr></thead>
          <tbody>
            {nms.instances.map((inst: any) => (
              <tr key={inst.instance_id} style={{ borderBottom: '1px solid #21262d' }}>
                <td style={td}><strong>{inst.name}</strong><br /><code style={{ fontSize: 11, color: '#8b949e' }}>{inst.api_url}</code></td>
                <td style={td}>{inst.type}</td>
                <td style={td}><span style={{ color: inst.reachable ? '#3fb950' : '#f85149' }}>{inst.reachable ? 'Yes' : 'No'}</span></td>
                <td style={td}>{inst.latency_ms != null ? `${inst.latency_ms}ms` : '-'}</td>
                <td style={td}><code style={{ fontSize: 11 }}>{JSON.stringify(inst.health)?.slice(0, 40)}</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* System Metrics */}
      <h3 style={{ fontSize: 16, marginBottom: 12 }}>System Metrics</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
          {['Instance', 'Status', 'CPU', 'Memory', 'Disk', 'Agents', 'Uptime'].map(h => (
            <th key={h} style={{ textAlign: 'left', padding: '10px 12px', fontSize: 12, color: '#8b949e' }}>{h}</th>
          ))}
        </tr></thead>
        <tbody>
          {metrics.map(m => (
            <tr key={m.instance_id} style={{ borderBottom: '1px solid #21262d' }}>
              <td style={td}><strong>{m.name}</strong></td>
              <td style={td}><span style={{ color: m.status === 'healthy' ? '#3fb950' : '#d29922' }}>{m.status}</span></td>
              <td style={td}>{m.cpu != null ? `${m.cpu}%` : '-'}</td>
              <td style={td}>{m.mem != null ? `${m.mem}%` : '-'}</td>
              <td style={td}>{m.disk || '-'}</td>
              <td style={td}>{m.agents ?? '-'}</td>
              <td style={td}>{m.uptime ? `${Math.round(m.uptime / 3600)}h` : '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
const card: React.CSSProperties = { background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: '20px 24px', flex: 1, textAlign: 'center' }
const cl: React.CSSProperties = { fontSize: 12, color: '#8b949e', marginTop: 4 }
const td: React.CSSProperties = { padding: '10px 12px', fontSize: 13 }
