import { useState, useEffect } from 'react'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  inputBg: '#161b22',
  error: '#f85149',
  green: '#3fb950',
}

const authHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('portal_token')
  return token ? { Authorization: `Bearer ${token}` } : ({} as Record<string, string>)
}

type Tab = 'users' | 'groups' | 'boards'

interface User {
  id: number
  username: string
  email: string
  role_level: number
  groups: string[]
  created_at: string
}

interface Group {
  id: number
  name: string
  permissions: Record<string, boolean>
  member_count: number
}

interface Board {
  id: number
  name: string
  slug: string
  type: 'board' | 'blog'
  description: string
  permissions: Record<string, unknown>
}

const inputStyle: React.CSSProperties = {
  padding: '8px 12px',
  background: '#161b22',
  border: '1px solid #30363d',
  borderRadius: 6,
  color: '#c9d1d9',
  fontSize: '0.85rem',
  outline: 'none',
}

export default function AdminPanel() {
  const [tab, setTab] = useState<Tab>('users')
  const [users, setUsers] = useState<User[]>([])
  const [groups, setGroups] = useState<Group[]>([])
  const [boards, setBoards] = useState<Board[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // New group form
  const [newGroupName, setNewGroupName] = useState('')
  // New board form
  const [newBoard, setNewBoard] = useState({ name: '', slug: '', type: 'board' as 'board' | 'blog', description: '' })
  // Feedback
  const [message, setMessage] = useState('')

  const fetchTab = (t: Tab) => {
    setLoading(true)
    setError('')
    const url = t === 'users' ? '/portal/admin/users'
      : t === 'groups' ? '/portal/admin/groups'
        : '/portal/admin/boards'
    fetch(url, { headers: authHeaders() })
      .then(r => {
        if (!r.ok) throw new Error(r.status === 403 ? 'Admin access required' : `Error ${r.status}`)
        return r.json()
      })
      .then(data => {
        if (t === 'users') setUsers(Array.isArray(data) ? data : data.users || [])
        else if (t === 'groups') setGroups(Array.isArray(data) ? data : data.groups || [])
        else setBoards(Array.isArray(data) ? data : data.boards || [])
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchTab(tab) }, [tab])

  const showMsg = (m: string) => { setMessage(m); setTimeout(() => setMessage(''), 3000) }

  // User management
  const handleRoleChange = async (userId: number, newRole: number) => {
    const res = await fetch(`/portal/admin/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ role_level: newRole }),
    })
    if (res.ok) { showMsg('Role updated'); fetchTab('users') }
    else alert('Failed to update role')
  }

  const handleAssignGroup = async (userId: number, groupName: string) => {
    if (!groupName) return
    const res = await fetch(`/portal/admin/users/${userId}/groups`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ group: groupName }),
    })
    if (res.ok) { showMsg('Group assigned'); fetchTab('users') }
    else alert('Failed to assign group')
  }

  // Group management
  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newGroupName.trim()) return
    const res = await fetch('/portal/admin/groups', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ name: newGroupName, permissions: {} }),
    })
    if (res.ok) { showMsg('Group created'); setNewGroupName(''); fetchTab('groups') }
    else alert('Failed to create group')
  }

  const handleUpdatePermissions = async (groupId: number, permissions: Record<string, boolean>) => {
    const res = await fetch(`/portal/admin/groups/${groupId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ permissions }),
    })
    if (res.ok) { showMsg('Permissions updated'); fetchTab('groups') }
    else alert('Failed to update permissions')
  }

  // Board management
  const handleCreateBoard = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newBoard.name.trim() || !newBoard.slug.trim()) return
    const res = await fetch('/portal/admin/boards', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(newBoard),
    })
    if (res.ok) { showMsg('Board created'); setNewBoard({ name: '', slug: '', type: 'board', description: '' }); fetchTab('boards') }
    else alert('Failed to create board')
  }

  const tabStyle = (t: Tab): React.CSSProperties => ({
    padding: '10px 20px',
    background: tab === t ? colors.accent : 'transparent',
    color: tab === t ? '#fff' : colors.textMuted,
    border: `1px solid ${tab === t ? colors.accent : colors.border}`,
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: tab === t ? 600 : 400,
  })

  const permissionKeys = ['read', 'write', 'delete', 'manage_users', 'manage_boards']

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 20 }}>Admin Panel</h1>

      {/* Feedback */}
      {message && (
        <div style={{
          background: '#0d2818', border: `1px solid ${colors.green}`,
          color: colors.green, padding: '8px 14px', borderRadius: 6,
          marginBottom: 16, fontSize: '0.85rem',
        }}>
          {message}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <button style={tabStyle('users')} onClick={() => setTab('users')}>User Management</button>
        <button style={tabStyle('groups')} onClick={() => setTab('groups')}>Group Management</button>
        <button style={tabStyle('boards')} onClick={() => setTab('boards')}>Board Management</button>
      </div>

      {error && (
        <div style={{ color: colors.error, padding: '12px 16px', background: '#2d1418', borderRadius: 6, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {loading && <div style={{ color: colors.textMuted, padding: 20 }}>Loading...</div>}

      {/* Users tab */}
      {!loading && tab === 'users' && (
        <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 8, overflow: 'hidden' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 150px 80px 160px 100px',
            padding: '10px 16px',
            background: colors.inputBg,
            borderBottom: `1px solid ${colors.border}`,
            fontSize: '0.8rem', color: colors.textMuted, fontWeight: 600,
          }}>
            <span>Username</span>
            <span>Email</span>
            <span>Role</span>
            <span>Groups</span>
            <span>Actions</span>
          </div>
          {users.map(u => (
            <div key={u.id} style={{
              display: 'grid',
              gridTemplateColumns: '1fr 150px 80px 160px 100px',
              padding: '10px 16px',
              borderBottom: `1px solid ${colors.border}`,
              alignItems: 'center',
              fontSize: '0.85rem',
            }}>
              <span style={{ color: colors.text }}>{u.username}</span>
              <span style={{ color: colors.textMuted, overflow: 'hidden', textOverflow: 'ellipsis' }}>{u.email}</span>
              <select
                value={u.role_level}
                onChange={e => handleRoleChange(u.id, Number(e.target.value))}
                style={{ ...inputStyle, padding: '4px 6px', width: 60 }}
              >
                <option value={0}>0</option>
                <option value={1}>1</option>
                <option value={5}>5</option>
                <option value={9}>9</option>
                <option value={10}>10</option>
              </select>
              <span style={{ color: colors.textMuted, fontSize: '0.8rem' }}>
                {u.groups?.join(', ') || '-'}
              </span>
              <select
                defaultValue=""
                onChange={e => { handleAssignGroup(u.id, e.target.value); e.target.value = '' }}
                style={{ ...inputStyle, padding: '4px 6px', fontSize: '0.8rem' }}
              >
                <option value="">+ Group</option>
                {groups.map(g => (
                  <option key={g.id} value={g.name}>{g.name}</option>
                ))}
              </select>
            </div>
          ))}
          {users.length === 0 && (
            <div style={{ padding: 30, textAlign: 'center', color: colors.textMuted }}>No users found</div>
          )}
        </div>
      )}

      {/* Groups tab */}
      {!loading && tab === 'groups' && (
        <div>
          {/* Create group form */}
          <form onSubmit={handleCreateGroup} style={{
            display: 'flex', gap: 10, marginBottom: 20,
            background: colors.card, border: `1px solid ${colors.border}`,
            borderRadius: 8, padding: 16,
          }}>
            <input
              value={newGroupName}
              onChange={e => setNewGroupName(e.target.value)}
              placeholder="New group name"
              style={{ ...inputStyle, flex: 1 }}
            />
            <button type="submit" style={{
              background: colors.accent, color: '#fff', border: 'none',
              padding: '8px 16px', borderRadius: 6, cursor: 'pointer', fontSize: '0.85rem',
            }}>
              Create Group
            </button>
          </form>

          {/* Groups list */}
          {groups.map(g => (
            <div key={g.id} style={{
              background: colors.card, border: `1px solid ${colors.border}`,
              borderRadius: 8, padding: 16, marginBottom: 12,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <span style={{ fontWeight: 600, fontSize: '1rem' }}>{g.name}</span>
                <span style={{ color: colors.textMuted, fontSize: '0.8rem' }}>{g.member_count} members</span>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                {permissionKeys.map(key => (
                  <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', color: colors.textMuted, cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={!!g.permissions[key]}
                      onChange={e => handleUpdatePermissions(g.id, { ...g.permissions, [key]: e.target.checked })}
                    />
                    {key}
                  </label>
                ))}
              </div>
            </div>
          ))}
          {groups.length === 0 && (
            <div style={{ color: colors.textMuted, textAlign: 'center', padding: 30 }}>No groups yet</div>
          )}
        </div>
      )}

      {/* Boards tab */}
      {!loading && tab === 'boards' && (
        <div>
          {/* Create board form */}
          <form onSubmit={handleCreateBoard} style={{
            background: colors.card, border: `1px solid ${colors.border}`,
            borderRadius: 8, padding: 16, marginBottom: 20,
            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12,
          }}>
            <input
              value={newBoard.name}
              onChange={e => setNewBoard(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Board name"
              style={inputStyle}
              required
            />
            <input
              value={newBoard.slug}
              onChange={e => setNewBoard(prev => ({ ...prev, slug: e.target.value }))}
              placeholder="slug (URL-safe)"
              style={inputStyle}
              required
            />
            <select
              value={newBoard.type}
              onChange={e => setNewBoard(prev => ({ ...prev, type: e.target.value as 'board' | 'blog' }))}
              style={inputStyle}
            >
              <option value="board">Board</option>
              <option value="blog">Blog</option>
            </select>
            <input
              value={newBoard.description}
              onChange={e => setNewBoard(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Description"
              style={inputStyle}
            />
            <div style={{ gridColumn: '1 / -1' }}>
              <button type="submit" style={{
                background: colors.accent, color: '#fff', border: 'none',
                padding: '8px 20px', borderRadius: 6, cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600,
              }}>
                Create Board
              </button>
            </div>
          </form>

          {/* Boards list */}
          <div style={{ background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 8, overflow: 'hidden' }}>
            {boards.map(b => (
              <div key={b.id} style={{
                padding: '12px 16px',
                borderBottom: `1px solid ${colors.border}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  <span style={{ fontWeight: 600, color: colors.text, marginRight: 10 }}>{b.name}</span>
                  <span style={{ color: colors.textMuted, fontSize: '0.8rem' }}>/{b.slug}</span>
                  <span style={{
                    marginLeft: 10,
                    fontSize: '0.7rem',
                    padding: '2px 8px',
                    borderRadius: 4,
                    background: b.type === 'blog' ? '#2d1f4e' : colors.inputBg,
                    color: b.type === 'blog' ? '#bc8cff' : colors.textMuted,
                  }}>
                    {b.type}
                  </span>
                </div>
                <span style={{ color: colors.textMuted, fontSize: '0.8rem' }}>
                  {b.description}
                </span>
              </div>
            ))}
            {boards.length === 0 && (
              <div style={{ padding: 30, textAlign: 'center', color: colors.textMuted }}>No boards yet</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
