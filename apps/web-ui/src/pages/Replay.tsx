import { useState } from 'react'
import { api } from '../api/client'
import type { Replay as ReplayType } from '../api/types'

interface VerifyResult { valid: boolean; blocks: number; tampered: { id: string; reason: string }[] }

export default function Replay() {
  const [projectId, setProjectId] = useState('')
  const [replay, setReplay] = useState<ReplayType | null>(null)
  const [verify, setVerify] = useState<VerifyResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    if (!projectId.trim()) return
    setLoading(true)
    setError('')
    try {
      const [r, v] = await Promise.all([
        api.get<ReplayType>(`/projects/${projectId.trim()}/replay`),
        api.get<{ result: VerifyResult }>(`/pow/verify?agent_id=http://localhost:8002`),
      ])
      setReplay(r)
      setVerify(v.result)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>PoW Replay 뷰어</h1>
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <input
          value={projectId}
          onChange={e => setProjectId(e.target.value)}
          placeholder="Project ID"
          style={{ flex: 1, padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.9rem' }}
          onKeyDown={e => e.key === 'Enter' && load()}
        />
        <button onClick={load} disabled={loading} style={btnStyle}>
          {loading ? '로딩...' : '조회'}
        </button>
      </div>

      {error && <p style={{ color: '#ef4444' }}>{error}</p>}

      {replay && (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            <Stat label="총 Steps" value={replay.steps_total} />
            <Stat label="성공" value={replay.steps_success} />
            <Stat label="총 보상" value={replay.total_reward.toFixed(4)} />
            {verify && (
              <Stat
                label="체인 무결성"
                value={verify.valid ? '✓ 정상' : `✗ 변조 ${verify.tampered.length}건`}
                color={verify.valid ? '#10b981' : '#ef4444'}
              />
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {replay.timeline.map(step => (
              <div key={step.task_order} style={{
                background: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: 8,
                padding: '12px 16px',
                display: 'grid',
                gridTemplateColumns: '40px 1fr auto auto auto auto',
                gap: 12,
                alignItems: 'center',
              }}>
                <div style={{ fontWeight: 700, color: '#6b7280', fontSize: '0.8rem' }}>#{step.task_order}</div>
                <div style={{ fontWeight: 600 }}>{step.task_title}</div>
                <div>
                  <span style={{
                    padding: '2px 8px',
                    borderRadius: 4,
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    background: step.exit_code === 0 ? '#d1fae5' : '#fee2e2',
                    color: step.exit_code === 0 ? '#065f46' : '#991b1b',
                  }}>
                    exit {step.exit_code}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>{step.duration_s.toFixed(1)}s</div>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  color: step.total_reward >= 0 ? '#10b981' : '#ef4444',
                }}>
                  {step.total_reward >= 0 ? '+' : ''}{step.total_reward.toFixed(2)}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#9ca3af', fontFamily: 'monospace' }}>
                  {step.block_hash.slice(0, 8)}...
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function Stat({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '12px 16px', minWidth: 100 }}>
      <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: 4 }}>{label}</div>
      <div style={{ fontWeight: 700, fontSize: '1.1rem', color: color ?? '#111827' }}>{value}</div>
    </div>
  )
}

const btnStyle: React.CSSProperties = {
  padding: '8px 16px',
  background: '#2563eb',
  color: '#fff',
  border: 'none',
  borderRadius: 6,
  cursor: 'pointer',
  fontWeight: 600,
}
