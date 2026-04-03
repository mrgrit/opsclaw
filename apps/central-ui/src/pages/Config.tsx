import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const prefixes = ['all', 'infra', 'service', 'subagent', 'llm', 'db', 'auth', 'ssh'] as const

export default function Config() {
  const [configs, setConfigs] = useState<Record<string, any>>({})
  const [filter, setFilter] = useState('all')
  const [editing, setEditing] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [editDesc, setEditDesc] = useState('')

  const load = () => {
    const prefix = filter === 'all' ? '' : `?prefix=${filter}`
    api(`/config${prefix}`).then(d => setConfigs(d.config)).catch(console.error)
  }
  useEffect(load, [filter])

  const save = async (key: string) => {
    let val: any = editValue
    try { val = JSON.parse(editValue) } catch {}
    await api(`/config/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value: val, description: editDesc || undefined }),
    })
    setEditing(null)
    load()
  }

  return (
    <div>
      <h2 style={{ fontSize: 22, marginBottom: 24 }}>Configuration</h2>

      <div style={{ display: 'flex', gap: 6, marginBottom: 20 }}>
        {prefixes.map(p => (
          <button key={p} onClick={() => setFilter(p)} style={{
            padding: '6px 14px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
            background: filter === p ? '#a78bfa' : '#21262d', color: '#e6edf3',
            border: filter === p ? 'none' : '1px solid #30363d',
          }}>{p}</button>
        ))}
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead><tr style={{ borderBottom: '1px solid #30363d' }}>
          {['Key', 'Value', 'Description', ''].map(h => (
            <th key={h} style={{ textAlign: 'left', padding: '10px 12px', fontSize: 12, color: '#8b949e' }}>{h}</th>
          ))}
        </tr></thead>
        <tbody>
          {Object.entries(configs).sort().map(([key, cfg]) => (
            <tr key={key} style={{ borderBottom: '1px solid #21262d' }}>
              <td style={td}><code style={{ fontSize: 12, color: '#a78bfa' }}>{key}</code></td>
              <td style={td}>
                {editing === key ? (
                  <input value={editValue} onChange={e => setEditValue(e.target.value)} style={input} autoFocus />
                ) : (
                  <code style={{ fontSize: 12 }}>{JSON.stringify(cfg.value)}</code>
                )}
              </td>
              <td style={td}>
                {editing === key ? (
                  <input value={editDesc} onChange={e => setEditDesc(e.target.value)} style={input} placeholder="설명" />
                ) : (
                  <span style={{ fontSize: 11, color: '#8b949e' }}>{cfg.description}</span>
                )}
              </td>
              <td style={{ ...td, width: 80 }}>
                {editing === key ? (
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button onClick={() => save(key)} style={{ ...btn, background: '#238636' }}>Save</button>
                    <button onClick={() => setEditing(null)} style={btn}>X</button>
                  </div>
                ) : (
                  <button onClick={() => { setEditing(key); setEditValue(JSON.stringify(cfg.value)); setEditDesc(cfg.description || '') }} style={btn}>Edit</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const td: React.CSSProperties = { padding: '8px 12px', fontSize: 13 }
const btn: React.CSSProperties = { background: '#21262d', color: '#e6edf3', border: '1px solid #30363d', borderRadius: 4, padding: '4px 10px', cursor: 'pointer', fontSize: 11 }
const input: React.CSSProperties = { background: '#0d1117', color: '#e6edf3', border: '1px solid #30363d', borderRadius: 4, padding: '4px 8px', fontSize: 12, width: '100%' }
