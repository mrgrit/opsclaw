import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Playbook, PlaybookStep } from '../api/types'
import ChatPanel from '../components/ChatPanel'

export default function Playbooks() {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([])
  const [selected, setSelected] = useState<Playbook | null>(null)
  const [steps, setSteps] = useState<PlaybookStep[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', version: '1.0.0', description: '' })
  const [runProjectId, setRunProjectId] = useState('')
  const [runResult, setRunResult] = useState('')
  const [stepForm, setStepForm] = useState({ order: 1, type: 'tool', ref: '', name: '', metadata: '{}' })
  const [showStepForm, setShowStepForm] = useState(false)

  async function loadPlaybooks() {
    const r = await api.get<{ playbooks: Playbook[] }>('/playbooks')
    setPlaybooks(r.playbooks ?? [])
  }

  useEffect(() => { loadPlaybooks() }, [])

  async function selectPlaybook(pb: Playbook) {
    setSelected(pb)
    const r = await api.get<{ steps: PlaybookStep[] }>(`/playbooks/${pb.id}/steps`)
    setSteps(r.steps ?? [])
  }

  async function createPlaybook() {
    await api.post('/playbooks', form)
    setShowForm(false)
    setForm({ name: '', version: '1.0.0', description: '' })
    loadPlaybooks()
  }

  async function addStep() {
    if (!selected) return
    try {
      let meta = {}
      try { meta = JSON.parse(stepForm.metadata) } catch { alert('metadata JSON 파싱 오류'); return }
      await api.post(`/playbooks/${selected.id}/steps`, [
        { order: stepForm.order, type: stepForm.type, ref: stepForm.ref, name: stepForm.name, metadata: meta },
      ])
      const r = await api.get<{ steps: PlaybookStep[] }>(`/playbooks/${selected.id}/steps`)
      setSteps(r.steps ?? [])
      setStepForm({ order: (r.steps?.length ?? 0) + 1, type: 'tool', ref: '', name: '', metadata: '{}' })
      setShowStepForm(false)
    } catch (e) { alert(String(e)) }
  }

  async function runPlaybook() {
    if (!selected || !runProjectId.trim()) return
    try {
      const r = await api.post<{ overall: string }>('/playbook/run', {
        playbook_id: selected.id,
        project_id: runProjectId.trim(),
        subagent_url: 'http://localhost:8002',
      })
      setRunResult(`실행 결과: ${r.overall}`)
    } catch (e) {
      setRunResult(String(e))
    }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: 24 }}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h1 style={{ margin: 0 }}>Playbooks</h1>
          <button onClick={() => setShowForm(!showForm)} style={btnStyle}>+ 신규</button>
        </div>

        {showForm && (
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginBottom: 16 }}>
            <input placeholder="이름" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} style={inputStyle} />
            <input placeholder="버전 (예: 1.0.0)" value={form.version} onChange={e => setForm({ ...form, version: e.target.value })} style={inputStyle} />
            <input placeholder="설명" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} style={inputStyle} />
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={createPlaybook} style={btnStyle}>생성</button>
              <button onClick={() => setShowForm(false)} style={{ ...btnStyle, background: '#6b7280' }}>취소</button>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {playbooks.map(pb => (
            <div key={pb.id} onClick={() => selectPlaybook(pb)} style={{
              background: selected?.id === pb.id ? '#eff6ff' : '#fff',
              border: `1px solid ${selected?.id === pb.id ? '#93c5fd' : '#e5e7eb'}`,
              borderRadius: 8, padding: '12px 16px', cursor: 'pointer',
            }}>
              <div style={{ fontWeight: 600 }}>{pb.name}</div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af' }}>v{pb.version} · {pb.description}</div>
            </div>
          ))}
          {playbooks.length === 0 && <p style={{ color: '#9ca3af' }}>Playbook 없음</p>}
        </div>
      </div>

      <div>
        {selected ? (
          <div>
            <h2 style={{ marginTop: 0 }}>{selected.name} <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>v{selected.version}</span></h2>
            {selected.description && <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>{selected.description}</p>}

            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>Steps ({steps.length})</h3>
                <button onClick={() => setShowStepForm(!showStepForm)} style={{ ...btnStyle, fontSize: '0.75rem', padding: '4px 10px' }}>+ Step 추가</button>
              </div>

              {showStepForm && (
                <div style={{ background: '#f9fafb', borderRadius: 8, padding: 12, marginBottom: 12 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '50px 80px 1fr 1fr', gap: 6, marginBottom: 6 }}>
                    <input placeholder="#" type="number" value={stepForm.order} onChange={e => setStepForm({ ...stepForm, order: +e.target.value })} style={inputStyle} />
                    <select value={stepForm.type} onChange={e => setStepForm({ ...stepForm, type: e.target.value })} style={inputStyle}>
                      <option value="tool">tool</option>
                      <option value="skill">skill</option>
                    </select>
                    <input placeholder="ref (예: run_command)" value={stepForm.ref} onChange={e => setStepForm({ ...stepForm, ref: e.target.value })} style={inputStyle} />
                    <input placeholder="이름" value={stepForm.name} onChange={e => setStepForm({ ...stepForm, name: e.target.value })} style={inputStyle} />
                  </div>
                  <textarea placeholder='metadata JSON (예: {"command":"hostname"})' value={stepForm.metadata}
                    onChange={e => setStepForm({ ...stepForm, metadata: e.target.value })}
                    style={{ ...inputStyle, fontFamily: 'monospace', fontSize: '0.75rem', height: 50 }} />
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={addStep} style={btnStyle}>추가</button>
                    <button onClick={() => setShowStepForm(false)} style={{ ...btnStyle, background: '#6b7280' }}>취소</button>
                  </div>
                </div>
              )}

              {steps.length === 0 ? <p style={{ color: '#9ca3af' }}>없음</p> : steps.map(s => (
                <div key={s.id} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', marginBottom: 8, padding: '8px 0', borderBottom: '1px solid #f3f4f6' }}>
                  <div style={{ fontWeight: 700, color: '#6b7280', minWidth: 24 }}>{s.step_order}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{s.step_type}: {(s as any).name || s.ref_id}</div>
                    {s.ref_id && <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>ref: {s.ref_id}</div>}
                    {s.params && <pre style={{ fontSize: '0.7rem', color: '#6b7280', margin: '4px 0 0', whiteSpace: 'pre-wrap' }}>{JSON.stringify(s.params, null, 2)}</pre>}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16 }}>
              <h3 style={{ margin: '0 0 12px', fontSize: '0.875rem', color: '#6b7280' }}>실행</h3>
              <input placeholder="Project ID" value={runProjectId} onChange={e => setRunProjectId(e.target.value)} style={inputStyle} />
              <button onClick={runPlaybook} style={btnStyle}>실행</button>
              {runResult && <p style={{ marginTop: 8, color: '#374151', fontSize: '0.875rem' }}>{runResult}</p>}
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#9ca3af' }}>
            Playbook을 선택하세요
          </div>
        )}
      </div>
      {selected && <ChatPanel contextType="playbook" contextId={selected.id} contextLabel={selected.name} />}
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
