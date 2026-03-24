import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import type { Project, Evidence, TaskItem, ExecutePlanResult, DispatchResult } from '../api/types'
import StageBadge from '../components/StageBadge'
import ChatPanel from '../components/ChatPanel'

const STAGES = ['plan', 'execute', 'validate', 'close']
const RISK_LEVELS = ['low', 'medium', 'high', 'critical']
const DEFAULT_AGENT = 'http://localhost:8002'

export default function Projects() {
  const [projects, setProjects] = useState<Project[]>([])
  const [selected, setSelected] = useState<Project | null>(null)
  const [evidence, setEvidence] = useState<Evidence[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', request_text: '', master_mode: 'external' })
  const wsRef = useRef<WebSocket | null>(null)

  // Dispatch state
  const [dispCmd, setDispCmd] = useState('')
  const [dispMode, setDispMode] = useState('shell')
  const [dispAgent, setDispAgent] = useState(DEFAULT_AGENT)
  const [dispResult, setDispResult] = useState<DispatchResult['result'] | null>(null)
  const [dispLoading, setDispLoading] = useState(false)

  // Execute-plan state
  const [tab, setTab] = useState<'evidence' | 'dispatch' | 'execute'>('evidence')
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [taskForm, setTaskForm] = useState<TaskItem>({ order: 1, title: '', instruction_prompt: '', risk_level: 'medium' })
  const [epAgent, setEpAgent] = useState(DEFAULT_AGENT)
  const [epParallel, setEpParallel] = useState(false)
  const [epConfirmed, setEpConfirmed] = useState(false)
  const [epResult, setEpResult] = useState<ExecutePlanResult | null>(null)
  const [epLoading, setEpLoading] = useState(false)
  const [expandedTask, setExpandedTask] = useState<number | null>(null)

  async function loadProjects() {
    const r = await api.get<{ projects: Project[] }>('/projects').catch(() => ({ projects: [] as Project[] }))
    setProjects(r.projects ?? [])
  }
  useEffect(() => { loadProjects() }, [])

  async function selectProject(p: Project) {
    setSelected(p)
    setEpResult(null); setDispResult(null); setTasks([])
    const r = await api.get<{ evidence: Evidence[] }>(`/projects/${p.id}/evidence`).catch(() => ({ evidence: [] as Evidence[] }))
    setEvidence(r.evidence ?? [])
    wsRef.current?.close()
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const wsBase = import.meta.env.DEV ? `${proto}://localhost:8000` : `${proto}://${location.host}`
    const ws = new WebSocket(`${wsBase}/ws/projects/${p.id}`)
    ws.onmessage = (ev) => { try { const d = JSON.parse(ev.data); if (d.stage) setSelected(prev => prev ? { ...prev, current_stage: d.stage } : prev) } catch {} }
    wsRef.current = ws
  }

  async function transition(action: string) {
    if (!selected) return
    await api.post(`/projects/${selected.id}/${action}`)
    const u = await api.get<{ project: Project }>(`/projects/${selected.id}`)
    setSelected(u.project); loadProjects()
  }

  async function createProject() {
    await api.post('/projects', form)
    setShowForm(false); setForm({ name: '', request_text: '', master_mode: 'external' }); loadProjects()
  }

  // ── Dispatch ──
  async function runDispatch() {
    if (!selected || !dispCmd.trim()) return
    setDispLoading(true); setDispResult(null)
    try {
      const r = await api.post<DispatchResult>(`/projects/${selected.id}/dispatch`, {
        command: dispCmd, mode: dispMode, subagent_url: dispAgent,
      })
      setDispResult(r.result)
      // evidence 새로고침
      const ev = await api.get<{ evidence: Evidence[] }>(`/projects/${selected.id}/evidence`).catch(() => ({ evidence: [] as Evidence[] }))
      setEvidence(ev.evidence ?? [])
    } catch (e) { setDispResult({ exit_code: -1, stdout: '', stderr: String(e), command: dispCmd }) }
    finally { setDispLoading(false) }
  }

  // ── Execute Plan ──
  function addTask() {
    setTasks([...tasks, { ...taskForm, order: tasks.length + 1 }])
    setTaskForm({ order: tasks.length + 2, title: '', instruction_prompt: '', risk_level: 'medium' })
  }
  function removeTask(idx: number) {
    setTasks(tasks.filter((_, i) => i !== idx).map((t, i) => ({ ...t, order: i + 1 })))
  }
  async function runExecutePlan() {
    if (!selected || tasks.length === 0) return
    setEpLoading(true); setEpResult(null)
    try {
      const r = await api.post<ExecutePlanResult>(`/projects/${selected.id}/execute-plan`, {
        tasks, subagent_url: epAgent, parallel: epParallel, confirmed: epConfirmed,
      })
      setEpResult(r)
      const ev = await api.get<{ evidence: Evidence[] }>(`/projects/${selected.id}/evidence`).catch(() => ({ evidence: [] as Evidence[] }))
      setEvidence(ev.evidence ?? [])
    } catch (e) { alert(String(e)) }
    finally { setEpLoading(false) }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 24, height: '100%' }}>
      {/* 프로젝트 목록 */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h1 style={{ margin: 0, fontSize: '1.2rem' }}>Projects</h1>
          <button onClick={() => setShowForm(!showForm)} style={btnStyle}>+ 신규</button>
        </div>
        {showForm && (
          <div style={cardStyle}>
            <input placeholder="이름" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} style={inputStyle} />
            <textarea placeholder="작업 요청" value={form.request_text} onChange={e => setForm({ ...form, request_text: e.target.value })}
              style={{ ...inputStyle, height: 60, resize: 'vertical' }} />
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={createProject} style={btnStyle}>생성</button>
              <button onClick={() => setShowForm(false)} style={{ ...btnStyle, background: '#6b7280' }}>취소</button>
            </div>
          </div>
        )}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {projects.map(p => (
            <div key={p.id} onClick={() => selectProject(p)} style={{
              background: selected?.id === p.id ? '#eff6ff' : '#fff',
              border: `1px solid ${selected?.id === p.id ? '#93c5fd' : '#e5e7eb'}`,
              borderRadius: 8, padding: '10px 14px', cursor: 'pointer',
            }}>
              <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{p.name}</div>
              <div style={{ marginTop: 4, display: 'flex', gap: 8, alignItems: 'center' }}>
                <StageBadge stage={p.current_stage} outcome={p.outcome} />
                <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>{new Date(p.created_at).toLocaleDateString('ko-KR')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 상세 패널 */}
      <div style={{ overflow: 'auto' }}>
        {selected ? (
          <div>
            <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>{selected.name}</h2>
            <p style={{ color: '#6b7280', fontSize: '0.8rem', margin: '4px 0 12px' }}>{selected.request_text}</p>
            <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
              <StageBadge stage={selected.current_stage} outcome={selected.outcome} />
              {STAGES.map(s => (
                <button key={s} onClick={() => transition(s)} style={{ ...btnSmall, background: '#4b5563' }}>→ {s}</button>
              ))}
            </div>

            {/* 탭 */}
            <div style={{ display: 'flex', gap: 0, marginBottom: 16, borderBottom: '2px solid #e5e7eb' }}>
              {(['evidence', 'dispatch', 'execute'] as const).map(t => (
                <button key={t} onClick={() => setTab(t)} style={{
                  padding: '8px 16px', background: 'none', border: 'none', cursor: 'pointer',
                  fontWeight: 600, fontSize: '0.85rem',
                  color: tab === t ? '#2563eb' : '#6b7280',
                  borderBottom: tab === t ? '2px solid #2563eb' : '2px solid transparent',
                  marginBottom: -2,
                }}>{t === 'evidence' ? `Evidence (${evidence.length})` : t === 'dispatch' ? '명령 실행' : '태스크 실행'}</button>
              ))}
            </div>

            {/* Evidence 탭 */}
            {tab === 'evidence' && (
              <div style={cardStyle}>
                {evidence.length === 0 ? <p style={{ color: '#9ca3af' }}>없음</p> : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {evidence.map(ev => (
                      <div key={ev.id} style={{ borderLeft: `3px solid ${ev.exit_code === 0 ? '#10b981' : '#ef4444'}`, paddingLeft: 12 }}>
                        <div style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#374151' }}>{ev.command}</div>
                        <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: 2 }}>exit {ev.exit_code}</div>
                        {ev.stdout && <pre style={{ margin: '4px 0 0', fontSize: '0.7rem', color: '#6b7280', whiteSpace: 'pre-wrap', maxHeight: 80, overflow: 'auto' }}>{ev.stdout.slice(0, 500)}</pre>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Dispatch 탭 */}
            {tab === 'dispatch' && (
              <div style={cardStyle}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px 1fr', gap: 8, marginBottom: 8 }}>
                  <input placeholder="SubAgent URL" value={dispAgent} onChange={e => setDispAgent(e.target.value)} style={inputStyle} />
                  <select value={dispMode} onChange={e => setDispMode(e.target.value)} style={inputStyle}>
                    <option value="shell">shell</option>
                    <option value="auto">auto</option>
                    <option value="adhoc">adhoc</option>
                  </select>
                  <div />
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input placeholder="명령어 (예: hostname, df -h, sudo systemctl status nginx)"
                    value={dispCmd} onChange={e => setDispCmd(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && runDispatch()}
                    style={{ ...inputStyle, flex: 1, marginBottom: 0 }} />
                  <button onClick={runDispatch} disabled={dispLoading} style={btnStyle}>
                    {dispLoading ? '실행 중...' : '실행'}
                  </button>
                </div>
                {dispResult && (
                  <div style={{ marginTop: 12, background: '#f9fafb', borderRadius: 8, padding: 12 }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: dispResult.exit_code === 0 ? '#059669' : '#dc2626' }}>
                      exit {dispResult.exit_code} {dispResult.llm_converted ? '(LLM 변환)' : ''}
                    </div>
                    {dispResult.stdout && <pre style={preStyle}>{dispResult.stdout}</pre>}
                    {dispResult.stderr && <pre style={{ ...preStyle, color: '#dc2626' }}>{dispResult.stderr}</pre>}
                  </div>
                )}
              </div>
            )}

            {/* Execute-Plan 탭 */}
            {tab === 'execute' && (
              <div style={cardStyle}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto auto auto', gap: 8, marginBottom: 12, alignItems: 'center' }}>
                  <input placeholder="SubAgent URL" value={epAgent} onChange={e => setEpAgent(e.target.value)} style={{ ...inputStyle, marginBottom: 0 }} />
                  <label style={checkLabel}><input type="checkbox" checked={epParallel} onChange={e => setEpParallel(e.target.checked)} /> 병렬</label>
                  <label style={checkLabel}><input type="checkbox" checked={epConfirmed} onChange={e => setEpConfirmed(e.target.checked)} /> critical 허용</label>
                  <button onClick={runExecutePlan} disabled={epLoading || tasks.length === 0} style={btnStyle}>
                    {epLoading ? '실행 중...' : `실행 (${tasks.length})`}
                  </button>
                </div>

                {/* 태스크 추가 폼 */}
                <div style={{ display: 'grid', gridTemplateColumns: '50px 150px 1fr 100px 40px', gap: 6, marginBottom: 8, alignItems: 'end' }}>
                  <input placeholder="#" type="number" value={taskForm.order} onChange={e => setTaskForm({ ...taskForm, order: +e.target.value })}
                    style={{ ...inputStyle, marginBottom: 0, textAlign: 'center' }} />
                  <input placeholder="제목" value={taskForm.title} onChange={e => setTaskForm({ ...taskForm, title: e.target.value })}
                    style={{ ...inputStyle, marginBottom: 0 }} />
                  <input placeholder="실행 명령 (instruction_prompt)" value={taskForm.instruction_prompt}
                    onChange={e => setTaskForm({ ...taskForm, instruction_prompt: e.target.value })}
                    onKeyDown={e => e.key === 'Enter' && taskForm.title && taskForm.instruction_prompt && addTask()}
                    style={{ ...inputStyle, marginBottom: 0, fontFamily: 'monospace', fontSize: '0.8rem' }} />
                  <select value={taskForm.risk_level} onChange={e => setTaskForm({ ...taskForm, risk_level: e.target.value })}
                    style={{ ...inputStyle, marginBottom: 0 }}>
                    {RISK_LEVELS.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                  <button onClick={addTask} disabled={!taskForm.title || !taskForm.instruction_prompt}
                    style={{ ...btnSmall, background: '#059669' }}>+</button>
                </div>

                {/* 태스크 목록 */}
                {tasks.length > 0 && (
                  <div style={{ marginBottom: 12 }}>
                    {tasks.map((t, i) => (
                      <div key={i} style={{
                        display: 'grid', gridTemplateColumns: '30px 1fr 80px 30px', gap: 8,
                        padding: '6px 8px', borderBottom: '1px solid #f3f4f6', alignItems: 'center', fontSize: '0.8rem',
                      }}>
                        <span style={{ color: '#9ca3af', fontWeight: 700 }}>#{t.order}</span>
                        <div>
                          <span style={{ fontWeight: 600 }}>{t.title}</span>
                          <div style={{ fontFamily: 'monospace', fontSize: '0.7rem', color: '#6b7280' }}>{t.instruction_prompt.slice(0, 80)}</div>
                        </div>
                        <span style={{ fontSize: '0.7rem', color: t.risk_level === 'critical' ? '#dc2626' : '#6b7280' }}>{t.risk_level}</span>
                        <button onClick={() => removeTask(i)} style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontWeight: 700 }}>X</button>
                      </div>
                    ))}
                  </div>
                )}

                {/* 실행 결과 */}
                {epResult && (
                  <div style={{ background: '#f9fafb', borderRadius: 8, padding: 12 }}>
                    <div style={{ display: 'flex', gap: 16, marginBottom: 8, fontSize: '0.85rem' }}>
                      <span style={{ fontWeight: 700, color: epResult.overall === 'success' ? '#059669' : epResult.overall === 'failed' ? '#dc2626' : '#d97706' }}>
                        {epResult.overall.toUpperCase()}
                      </span>
                      <span>Total: {epResult.tasks_total}</span>
                      <span style={{ color: '#059669' }}>OK: {epResult.tasks_ok}</span>
                      <span style={{ color: '#dc2626' }}>Fail: {epResult.tasks_failed}</span>
                    </div>
                    {epResult.task_results.map((tr, i) => (
                      <div key={i} style={{
                        borderLeft: `3px solid ${tr.status === 'ok' ? '#10b981' : tr.status === 'dry_run' ? '#f59e0b' : '#ef4444'}`,
                        paddingLeft: 10, marginBottom: 6, cursor: 'pointer',
                      }} onClick={() => setExpandedTask(expandedTask === i ? null : i)}>
                        <div style={{ display: 'flex', gap: 12, fontSize: '0.8rem', alignItems: 'center' }}>
                          <span style={{ fontWeight: 700, color: '#374151' }}>#{tr.order}</span>
                          <span style={{ fontWeight: 600 }}>{tr.title}</span>
                          <span style={{ color: tr.status === 'ok' ? '#059669' : '#dc2626', fontSize: '0.75rem' }}>{tr.status}</span>
                          <span style={{ color: '#9ca3af', fontSize: '0.7rem' }}>{tr.duration_s}s</span>
                          {tr.sudo_elevated && <span style={{ color: '#d97706', fontSize: '0.7rem' }}>sudo</span>}
                        </div>
                        {expandedTask === i && tr.detail && (
                          <div style={{ marginTop: 4 }}>
                            {tr.detail.exit_code !== undefined && <div style={{ fontSize: '0.7rem', color: '#6b7280' }}>exit {tr.detail.exit_code}</div>}
                            {tr.detail.stdout && <pre style={preStyle}>{tr.detail.stdout}</pre>}
                            {tr.detail.stderr && <pre style={{ ...preStyle, color: '#dc2626' }}>{tr.detail.stderr}</pre>}
                            {tr.detail.error && <pre style={{ ...preStyle, color: '#dc2626' }}>{tr.detail.error}</pre>}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#9ca3af' }}>
            프로젝트를 선택하세요
          </div>
        )}
      </div>
      {selected && <ChatPanel contextType="project" contextId={selected.id} contextLabel={selected.name} />}
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  padding: '8px 14px', background: '#2563eb', color: '#fff',
  border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
}
const btnSmall: React.CSSProperties = {
  padding: '4px 10px', background: '#2563eb', color: '#fff',
  border: 'none', borderRadius: 4, cursor: 'pointer', fontWeight: 600, fontSize: '0.8rem',
}
const inputStyle: React.CSSProperties = {
  width: '100%', padding: '7px 10px', border: '1px solid #d1d5db', borderRadius: 6,
  fontSize: '0.85rem', marginBottom: 8, boxSizing: 'border-box',
}
const cardStyle: React.CSSProperties = {
  background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16,
}
const preStyle: React.CSSProperties = {
  margin: '4px 0', fontSize: '0.7rem', color: '#374151', whiteSpace: 'pre-wrap',
  maxHeight: 150, overflow: 'auto', background: '#f9fafb', padding: 8, borderRadius: 4,
}
const checkLabel: React.CSSProperties = {
  fontSize: '0.8rem', color: '#374151', display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap',
}
