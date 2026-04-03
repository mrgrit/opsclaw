import React, { useEffect, useState } from 'react'
import { api } from '../api.ts'

const card = (label: string, value: string | number, color = '#a78bfa') => (
  <div style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: 8, padding: '20px 24px', flex: '1 1 180px' }}>
    <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 8 }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
  </div>
)

export default function Dashboard() {
  const [d, setD] = useState<any>(null)
  useEffect(() => { api('/admin/dashboard').then(setD).catch(console.error) }, [])
  if (!d) return <div style={{ color: '#8b949e' }}>Loading...</div>
  return (
    <div>
      <h2 style={{ fontSize: 22, marginBottom: 24 }}>Central Dashboard</h2>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {card('Instances', d.instances.total)}
        {card('OpsClaw', d.instances.by_type?.opsclaw || 0, '#58a6ff')}
        {card('Bastion', d.instances.by_type?.bastion || 0, '#3fb950')}
        {card('CCC', d.instances.by_type?.ccc || 0, '#f97316')}
        {card('Unified Blocks', d.blockchain.total_blocks, '#f0883e')}
        {card('CTF Challenges', d.ctf.challenges, '#bc8cff')}
      </div>
    </div>
  )
}
