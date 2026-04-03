import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

export default function NMS() {
  const [nms, setNms] = useState<any>(null)
  const [metrics, setMetrics] = useState<any[]>([])
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api('/nms/status').then(setNms),
      api('/sms/metrics').then(d => setMetrics(d.metrics || [])),
      api('/sms/alerts').then(d => setAlerts(d.alerts || [])),
    ])
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: '#8b949e', padding: 40 }}>Loading NMS/SMS...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40 }}>Error: {error}</div>

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

      {/* Network summary */}
      {nms && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
          <div style={cardStyle}><div style={{ fontSize: 28, fontWeight: 700, color: '#a78bfa' }}>{nms.total}</div><div style={labelStyle}>Total</div></div>
          <div style={cardStyle}><div style={{ fontSize: 28, fontWeight: 700, color: '#3fb950' }}>{nms.reachable}</div><div style={labelStyle}>Reachable</div></div>
          <div style={cardStyle}><div style={{ fontSize: 28, fontWeight: 700, color: '#f85149' }}>{nms.total - nms.reachable}</div><div style={labelStyle}>Down</div></div>
        </div>
      )}

      {/* Network detail */}
      <h3 style={{ fontSize: 16, marginBottom: 12 }}>Network Status</h3>
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden', marginBottom: 32 }}>
        {nms?.instances?.length ? (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
              {['Instance', 'Type', 'Reachable', 'Latency', 'Health'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '12px 16px', fontSize: 12, color: '#8b949e', fontWeight: 600 }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {nms.instances.map((inst: any, i: number) => (
                <tr key={inst.instance_id} style={{ borderBottom: i < nms.instances.length - 1 ? '1px solid #21262d' : 'none' }}>
                  <td style={td}><strong>{inst.name}</strong><br /><code style={{ fontSize: 11, color: '#8b949e' }}>{inst.api_url}</code></td>
                  <td style={td}>{inst.type}</td>
                  <td style={td}><span style={{ color: inst.reachable ? '#3fb950' : '#f85149', fontWeight: 600 }}>{inst.reachable ? 'Yes' : 'No'}</span></td>
                  <td style={td}>{inst.latency_ms != null ? `${inst.latency_ms}ms` : '-'}</td>
                  <td style={td}><code style={{ fontSize: 11 }}>{inst.health ? JSON.stringify(inst.health).slice(0, 50) : '-'}</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ padding: 40, textAlign: 'center', color: '#8b949e' }}>No instances found</div>
        )}
      </div>

      {/* System Metrics */}
      <h3 style={{ fontSize: 16, marginBottom: 12 }}>System Metrics</h3>
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, overflow: 'hidden' }}>
        {metrics.length ? (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
              {['Instance', 'Status', 'CPU', 'Memory', 'Agents', 'Uptime'].map(h => (
                <th key={h} style={{ textAlign: 'left', padding: '12px 16px', fontSize: 12, color: '#8b949e', fontWeight: 600 }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {metrics.map((m, i) => (
                <tr key={m.instance_id} style={{ borderBottom: i < metrics.length - 1 ? '1px solid #21262d' : 'none' }}>
                  <td style={td}><strong>{m.name}</strong></td>
                  <td style={td}><span style={{ color: m.status === 'healthy' ? '#3fb950' : '#d29922' }}>{m.status}</span></td>
                  <td style={td}>{m.cpu != null ? `${m.cpu}%` : '-'}</td>
                  <td style={td}>{m.mem != null ? `${m.mem}%` : '-'}</td>
                  <td style={td}>{m.agents ?? '-'}</td>
                  <td style={td}>{m.uptime ? `${Math.round(m.uptime / 3600)}h` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ padding: 40, textAlign: 'center', color: '#8b949e' }}>No metrics available. Send heartbeats with metrics.</div>
        )}
      </div>
    </div>
  )
}

const cardStyle: React.CSSProperties = { background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: '20px 24px', flex: 1, textAlign: 'center' }
const labelStyle: React.CSSProperties = { fontSize: 12, color: '#8b949e', marginTop: 4 }
const td: React.CSSProperties = { padding: '12px 16px', fontSize: 13 }
