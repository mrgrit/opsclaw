import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { Project, Evidence } from '../api/types'
import StageBadge from '../components/StageBadge'

const STAGES = ['plan', 'execute', 'validate', 'close']

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selected, setSelected] = useState<Project | null>(null)
  const [evidence, setEvidence] = useState<Evidence[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', request_text: '', master_mode: 'external' })
  const wsRef = useRef<WebSocket | null>(null)

  async function loadProjects() {
    const r = await api.get<{ projects: Project[] }>('/projects').catch(() => ({ projects: [] as Project[] }))
    setProjects(r.projects ?? [])
  }

  useEffect(() => { loadProjects() }, [])

  async function selectProject(p: Project) {
    setSelected(p)
    const r = await api.get<{ evidence: Evidence[] }>(`/projects/${p.id}/evidence`)
    setEvidence(r.evidence ?? [])
    // WebSocket for real-time stage
    wsRef.current?.close()
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const wsBase = import.meta.env.DEV ? `${proto}://localhost:8000` : `${proto}://${location.host}`
    const ws = new WebSocket(`${wsBase}/ws/projects/${p.id}`)
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data)
        if (data.stage) {
          setSelected(prev => prev ? { ...prev, current_stage: data.stage } : prev)
        }
      } catch {}
    }
    wsRef.current = ws
  }

  async function transition(action: string) {
    if (!selected) return
    await api.post(`/projects/${selected.id}/${action}`)
    const updated = await api.get<{ project: Project }>(`/projects/${selected.id}`)
    setSelected(updated.project)
    loadProjects()
  }

  async function createProject() {
    await api.post('/projects', form)
    setShowForm(false)
    setForm({ name: '', request_text: '', master_mode: 'external' })
    loadProjects()
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: 24, height: '100%' }}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h1 style={{ margin: 0 }}>Projects</h1>
          <button onClick={() => setShowForm(!showForm)} style={btnStyle}>+ 신규</button>
        </div>

        {showForm && (
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginBottom: 16 }}>
            <input placeholder="이름" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
              style={inputStyle} />
            <textarea placeholder="작업 요청" value={form.request_text}
              onChange={e => setForm({ ...form, request_text: e.target.value })}
              style={{ ...inputStyle, height: 80, resize: 'vertical' }} />
            <select value={form.master_mode} onChange={e => setForm({ ...form, master_mode: e.target.value })}
              style={inputStyle}>
              <option value="external">external (AI 오케스트레이션)</option>
              <option value="native">native (자동)</option>
            </select>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button onClick={createProject} style={btnStyle}>생성</button>
              <button onClick={() => setShowForm(false)} style={{ ...btnStyle, background: '#6b7280' }}>취소</button>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {projects.map(p => (
            <div key={p.id} onClick={() => selectProject(p)} style={{
              background: selected?.id === p.id ? '#eff6ff' : '#fff',
              border: `1px solid ${selected?.id === p.id ? '#93c5fd' : '#e5e7eb'}`,
              borderRadius: 8,
              padding: '12px 16px',
              cursor: 'pointer',
            }}>
              <div style={{ fontWeight: 600 }}>{p.name}</div>
              <div style={{ marginTop: 4 }}>
                <StageBadge stage={p.current_stage} outcome={p.outcome} />
                <span style={{ marginLeft: 8, fontSize: '0.75rem', color: '#9ca3af' }}>
                  {new Date(p.created_at).toLocaleDateString('ko-KR')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        {selected ? (
          <div>
            <h2 style={{ marginTop: 0 }}>{selected.name}</h2>
            <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>{selected.request_text}</p>
            <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
              <StageBadge stage={selected.current_stage} outcome={selected.outcome} />
            </div>

            <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
              {STAGES.map(s => (
                <button key={s} onClick={() => transition(s)} style={{ ...btnStyle, background: '#4b5563', fontSize: '0.8rem' }}>
                  → {s}
                </button>
              ))}
            </div>

            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16 }}>
              <h3 style={{ margin: '0 0 12px', fontSize: '0.875rem', color: '#6b7280' }}>
                Evidence ({evidence.length})
              </h3>
              {evidence.length === 0 ? (
                <p style={{ color: '#9ca3af' }}>없음</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {evidence.map(ev => (
                    <div key={ev.id} style={{ borderLeft: `3px solid ${ev.exit_code === 0 ? '#10b981' : '#ef4444'}`, paddingLeft: 12 }}>
                      <div style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#374151' }}>{ev.command}</div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: 2 }}>
                        exit {ev.exit_code}
                      </div>
                      {ev.stdout && (
                        <pre style={{ margin: '4px 0 0', fontSize: '0.7rem', color: '#6b7280', whiteSpace: 'pre-wrap', maxHeight: 80, overflow: 'hidden' }}>
                          {ev.stdout.slice(0, 200)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#9ca3af' }}>
            프로젝트를 선택하세요
          </div>
        )}
      </div>
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  padding: '8px 14px', background: '#2563eb', color: '#fff',
  border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600, fontSize: '0.875rem',
}
const inputStyle: React.CSSProperties = {
  width: '100%', padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 6,
  fontSize: '0.875rem', marginBottom: 8, boxSizing: 'border-box',
}
