import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

export default function Blockchain() {
  const [blocks, setBlocks] = useState<any[]>([])
  const [verify, setVerify] = useState<any>(null)
  const [leaders, setLeaders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api('/blockchain/blocks').then(d => setBlocks(d.blocks || [])),
      api('/blockchain/verify').then(setVerify),
      api('/blockchain/leaderboard').then(d => setLeaders(d.leaderboard || [])),
    ])
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ color: '#8b949e', padding: 40 }}>Loading blockchain...</div>
  if (error) return <div style={{ color: '#f85149', padding: 40 }}>Error: {error}</div>

  return (
    <div>
      <h2 style={{ fontSize: 22, marginBottom: 24 }}>Unified Blockchain</h2>

      {/* Verification cards */}
      {verify?.verification && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
          {Object.entries(verify.verification).map(([iid, v]: [string, any]) => (
            <div key={iid} style={{
              background: v.valid ? '#0d1f0d' : '#1f0d0d', border: `1px solid ${v.valid ? '#238636' : '#da3633'}`,
              borderRadius: 8, padding: 16, flex: '1 1 200px',
            }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>{iid}</div>
              <div style={{ fontSize: 12, color: '#8b949e' }}>
                {v.blocks} blocks — {v.valid ? 'Valid' : `${v.tampered?.length || 0} tampered`}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Leaderboard */}
      {leaders.length > 0 && (
        <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 20, marginBottom: 24 }}>
          <h3 style={{ fontSize: 16, marginBottom: 12 }}>Unified Leaderboard</h3>
          {leaders.map((l, i) => (
            <div key={i} style={{ display: 'flex', gap: 12, padding: '8px 0', borderBottom: '1px solid #21262d', fontSize: 13 }}>
              <span style={{ width: 30, color: i < 3 ? '#ffd700' : '#8b949e', fontWeight: 700 }}>#{i + 1}</span>
              <span style={{ width: 120, color: '#a78bfa' }}>{l.instance_id}</span>
              <span style={{ flex: 1 }}><code>{l.agent_id}</code></span>
              <span style={{ color: '#3fb950' }}>{l.blocks} blocks</span>
              <span style={{ color: '#f0883e', fontWeight: 600, marginLeft: 8 }}>{l.total_reward?.toFixed(1)} pts</span>
            </div>
          ))}
        </div>
      )}

      {/* Blocks */}
      <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: 20 }}>
        <h3 style={{ fontSize: 16, marginBottom: 12 }}>Recent Blocks ({blocks.length})</h3>
        {blocks.length === 0 ? (
          <div style={{ color: '#8b949e', textAlign: 'center', padding: 20 }}>No blocks synced yet</div>
        ) : blocks.slice(0, 30).map((b, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, padding: '8px 0', borderBottom: '1px solid #21262d', fontSize: 12, alignItems: 'center' }}>
            <span style={{ background: '#21262d', borderRadius: 4, padding: '2px 8px', color: '#a78bfa', minWidth: 90, textAlign: 'center' }}>{b.instance_id}</span>
            <span style={{ color: '#8b949e', minWidth: 30 }}>#{b.block_index}</span>
            <code style={{ color: '#484f58' }}>{b.block_hash?.slice(0, 16)}...</code>
            <span style={{ flex: 1 }}><code style={{ fontSize: 11 }}>{b.agent_id}</code></span>
            <span style={{ color: '#f0883e' }}>{b.reward_amount} pts</span>
          </div>
        ))}
      </div>
    </div>
  )
}
