import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { PoWBlock, LedgerEntry } from '../api/types'

interface VerifyResult { valid: boolean; blocks: number; tampered: { id: string; reason: string }[] }

export default function PoW() {
  const [leaderboard, setLeaderboard] = useState<LedgerEntry[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [blocks, setBlocks] = useState<PoWBlock[]>([])
  const [verify, setVerify] = useState<VerifyResult | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.get<{ leaderboard: LedgerEntry[] }>('/pow/leaderboard?limit=20')
      .then(r => setLeaderboard(r.leaderboard))
      .catch(() => {})
  }, [])

  async function selectAgent(agentId: string) {
    setSelectedAgent(agentId)
    setLoading(true)
    try {
      const [br, vr] = await Promise.all([
        api.get<{ blocks: PoWBlock[] }>(`/pow/blocks?agent_id=${encodeURIComponent(agentId)}&limit=50`),
        api.get<{ result: VerifyResult }>(`/pow/verify?agent_id=${encodeURIComponent(agentId)}`),
      ])
      setBlocks(br.blocks)
      setVerify(vr.result)
    } catch {
      setBlocks([])
      setVerify(null)
    } finally {
      setLoading(false)
    }
  }

  const selected = leaderboard.find(e => e.agent_id === selectedAgent)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 24, height: '100%' }}>
      {/* 에이전트 목록 */}
      <div>
        <h1 style={{ margin: '0 0 16px', fontSize: '1.25rem' }}>PoW 에이전트</h1>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {leaderboard.map((e, i) => (
            <div
              key={e.agent_id}
              onClick={() => selectAgent(e.agent_id)}
              style={{
                background: selectedAgent === e.agent_id ? '#eff6ff' : '#fff',
                border: `1px solid ${selectedAgent === e.agent_id ? '#93c5fd' : '#e5e7eb'}`,
                borderRadius: 8,
                padding: '10px 14px',
                cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: '#9ca3af', fontWeight: 700 }}>#{i + 1}</span>
                <span style={{
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  color: e.balance >= 0 ? '#10b981' : '#ef4444',
                }}>
                  {e.balance >= 0 ? '+' : ''}{e.balance.toFixed(2)}
                </span>
              </div>
              <div style={{
                fontSize: '0.8rem',
                fontWeight: 600,
                color: '#374151',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                marginTop: 4,
              }} title={e.agent_id}>
                {e.agent_id.replace(/^https?:\/\//, '')}
              </div>
              <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginTop: 2 }}>
                tasks {e.total_tasks} · ✓{e.success_count} ✗{e.fail_count}
              </div>
            </div>
          ))}
          {leaderboard.length === 0 && <p style={{ color: '#9ca3af' }}>에이전트 없음</p>}
        </div>
      </div>

      {/* 블록 상세 */}
      <div>
        {selectedAgent ? (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '1rem', wordBreak: 'break-all' }}>{selectedAgent}</h2>
                {selected && (
                  <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
                    <Stat label="잔액" value={`${selected.balance >= 0 ? '+' : ''}${selected.balance.toFixed(4)}`}
                      color={selected.balance >= 0 ? '#10b981' : '#ef4444'} />
                    <Stat label="총 작업" value={String(selected.total_tasks)} />
                    <Stat label="성공" value={String(selected.success_count)} color="#10b981" />
                    <Stat label="실패" value={String(selected.fail_count)} color={selected.fail_count > 0 ? '#ef4444' : undefined} />
                    {verify && (
                      <Stat
                        label="체인 무결성"
                        value={verify.valid ? '✓ 정상' : `✗ 변조 ${verify.tampered.length}건`}
                        color={verify.valid ? '#10b981' : '#ef4444'}
                      />
                    )}
                  </div>
                )}
              </div>
            </div>

            {loading ? (
              <p style={{ color: '#9ca3af' }}>로딩 중...</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '32px 1fr 80px 70px 70px 50px 90px 100px',
                  gap: 8,
                  padding: '4px 12px',
                  fontSize: '0.7rem',
                  color: '#9ca3af',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                }}>
                  <div>#</div><div>작업</div><div>보상</div><div>Exit</div><div>Nonce</div><div>Diff</div><div>블록 해시</div><div>시간</div>
                </div>
                {blocks.map((b, i) => (
                  <div key={b.id} style={{
                    background: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: 8,
                    padding: '10px 12px',
                    display: 'grid',
                    gridTemplateColumns: '32px 1fr 80px 70px 70px 50px 90px 100px',
                    gap: 8,
                    alignItems: 'center',
                  }}>
                    <div style={{ fontSize: '0.75rem', color: '#9ca3af', fontWeight: 700 }}>{blocks.length - i}</div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{b.task_title}</div>
                      <div style={{ fontSize: '0.7rem', color: '#9ca3af', fontFamily: 'monospace' }}>
                        prev: {b.prev_hash.slice(0, 8)}...
                      </div>
                    </div>
                    <div style={{
                      fontSize: '0.875rem',
                      fontWeight: 700,
                      color: (b.total_reward ?? 0) >= 0 ? '#10b981' : '#ef4444',
                    }}>
                      {(b.total_reward ?? 0) >= 0 ? '+' : ''}{(b.total_reward ?? 0).toFixed(2)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                      task #{b.task_order}
                    </div>
                    <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#6b7280' }}>
                      {(b.nonce ?? 0).toLocaleString()}
                    </div>
                    <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#6b7280' }}>
                      {b.difficulty ?? 0}
                    </div>
                    <div style={{ fontSize: '0.7rem', fontFamily: 'monospace', color: '#6b7280' }}>
                      {b.block_hash.slice(0, 10)}...
                    </div>
                    <div style={{ fontSize: '0.7rem', color: '#9ca3af' }}>
                      {new Date(b.ts).toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                ))}
                {blocks.length === 0 && <p style={{ color: '#9ca3af' }}>PoW 블록 없음</p>}
              </div>
            )}
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#9ca3af' }}>
            에이전트를 선택하세요
          </div>
        )}
      </div>
    </div>
  )
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '8px 14px' }}>
      <div style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase', fontWeight: 700 }}>{label}</div>
      <div style={{ fontWeight: 700, fontSize: '1rem', color: color ?? '#111827', marginTop: 2 }}>{value}</div>
    </div>
  )
}
