import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { NotificationChannel, NotificationRule } from '../api/types'

const EVENT_TYPES = ['task_completed', 'task_failed', 'stage_changed', 'approval_required', 'project_closed']

export default function Settings() {
  const [channels, setChannels] = useState<NotificationChannel[]>([])
  const [rules, setRules] = useState<NotificationRule[]>([])
  const [tab, setTab] = useState<'channels' | 'rules'>('channels')
  const [channelForm, setChannelForm] = useState({ channel_type: 'slack', name: '', config: '{}' })
  const [ruleForm, setRuleForm] = useState({ event_type: 'task_failed', channel_id: '' })

  async function load() {
    const [c, r] = await Promise.all([
      api.get<{ channels: NotificationChannel[] }>('/notifications/channels').catch(() => ({ channels: [] })),
      api.get<{ rules: NotificationRule[] }>('/notifications/rules').catch(() => ({ rules: [] })),
    ])
    setChannels(c.channels ?? [])
    setRules(r.rules ?? [])
  }

  useEffect(() => { load() }, [])

  async function addChannel() {
    let config: Record<string, unknown>
    try { config = JSON.parse(channelForm.config) } catch { alert('config JSON 파싱 오류'); return }
    await api.post('/notifications/channels', { ...channelForm, config })
    load()
  }

  async function addRule() {
    if (!ruleForm.channel_id) { alert('채널 선택 필요'); return }
    await api.post('/notifications/rules', ruleForm)
    load()
  }

  return (
    <div>
      <h1 style={{ marginTop: 0 }}>Settings</h1>
      <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: '2px solid #e5e7eb' }}>
        {(['channels', 'rules'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '8px 20px', background: 'none', border: 'none', cursor: 'pointer',
            fontWeight: 600, fontSize: '0.9rem',
            color: tab === t ? '#2563eb' : '#6b7280',
            borderBottom: tab === t ? '2px solid #2563eb' : '2px solid transparent',
            marginBottom: -2,
          }}>{t === 'channels' ? '알림 채널' : '알림 규칙'}</button>
        ))}
      </div>

      {tab === 'channels' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16 }}>
            <h3 style={{ margin: '0 0 12px' }}>채널 추가</h3>
            <select value={channelForm.channel_type}
              onChange={e => setChannelForm({ ...channelForm, channel_type: e.target.value })}
              style={inputStyle}>
              <option value="slack">Slack</option>
              <option value="email">Email</option>
              <option value="webhook">Webhook</option>
            </select>
            <input placeholder="채널명" value={channelForm.name}
              onChange={e => setChannelForm({ ...channelForm, name: e.target.value })} style={inputStyle} />
            <textarea placeholder='config JSON (예: {"url":"https://..."})'
              value={channelForm.config}
              onChange={e => setChannelForm({ ...channelForm, config: e.target.value })}
              style={{ ...inputStyle, height: 80, resize: 'vertical', fontFamily: 'monospace' }} />
            <button onClick={addChannel} style={btnStyle}>추가</button>
          </div>
          <div>
            <h3 style={{ margin: '0 0 12px' }}>등록된 채널 ({channels.length})</h3>
            {channels.map(c => (
              <div key={c.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '10px 14px', marginBottom: 8 }}>
                <div style={{ fontWeight: 600 }}>{c.name}</div>
                <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{c.channel_type} · {c.id.slice(0, 8)}</div>
              </div>
            ))}
            {channels.length === 0 && <p style={{ color: '#9ca3af' }}>없음</p>}
          </div>
        </div>
      )}

      {tab === 'rules' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16 }}>
            <h3 style={{ margin: '0 0 12px' }}>규칙 추가</h3>
            <select value={ruleForm.event_type}
              onChange={e => setRuleForm({ ...ruleForm, event_type: e.target.value })}
              style={inputStyle}>
              {EVENT_TYPES.map(e => <option key={e} value={e}>{e}</option>)}
            </select>
            <select value={ruleForm.channel_id}
              onChange={e => setRuleForm({ ...ruleForm, channel_id: e.target.value })}
              style={inputStyle}>
              <option value="">채널 선택...</option>
              {channels.map(c => <option key={c.id} value={c.id}>{c.name} ({c.channel_type})</option>)}
            </select>
            <button onClick={addRule} style={btnStyle}>추가</button>
          </div>
          <div>
            <h3 style={{ margin: '0 0 12px' }}>등록된 규칙 ({rules.length})</h3>
            {rules.map(r => {
              const ch = channels.find(c => c.id === r.channel_id)
              return (
                <div key={r.id} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '10px 14px', marginBottom: 8 }}>
                  <div style={{ fontWeight: 600 }}>{r.event_type}</div>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>→ {ch?.name ?? r.channel_id}</div>
                </div>
              )
            })}
            {rules.length === 0 && <p style={{ color: '#9ca3af' }}>없음</p>}
          </div>
        </div>
      )}
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
