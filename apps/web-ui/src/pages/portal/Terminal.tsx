import { useState, useRef, useEffect, useCallback } from 'react'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  green: '#3fb950',
  red: '#f85149',
  termBg: '#0d1117',
}

const servers = [
  { id: 'v-secu', label: 'v-secu (방화벽/IPS)', host: 'v-secu' },
  { id: 'v-web', label: 'v-web (WAF/웹서버)', host: 'v-web' },
  { id: 'v-siem', label: 'v-siem (SIEM)', host: 'v-siem' },
]

export default function Terminal() {
  const [server, setServer] = useState(servers[0].host)
  const [connected, setConnected] = useState(false)
  const [output, setOutput] = useState<string[]>([])
  const [input, setInput] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const outputRef = useRef<HTMLPreElement>(null)

  const addOutput = useCallback((line: string) => {
    setOutput(prev => [...prev, line])
  }, [])

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [output])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const connect = () => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    const token = localStorage.getItem('portal_token') || ''
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // 서버별 SSH 사용자 매핑
    const sshUsers: Record<string, string> = { 'v-secu': 'secu', 'v-web': 'web', 'v-siem': 'siem' }
    const sshUser = sshUsers[server] || 'root'
    const wsUrl = `${protocol}//${window.location.host}/portal/ws/terminal?host=${server}&user=${sshUser}&password=1&token=${token}`

    addOutput(`[*] ${server}에 연결 중...`)

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      addOutput(`[+] ${server} 연결 완료`)
    }

    ws.onmessage = (event) => {
      addOutput(event.data)
    }

    ws.onerror = () => {
      addOutput(`[!] 연결 오류 발생`)
    }

    ws.onclose = () => {
      setConnected(false)
      addOutput(`[-] 연결 종료`)
    }
  }

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
  }

  const sendCommand = (e: React.FormEvent) => {
    e.preventDefault()
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    if (!input.trim()) return

    addOutput(`$ ${input}`)
    wsRef.current.send(input)
    setInput('')
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <h2 style={{ fontSize: '1.4rem', marginBottom: 16 }}>웹 터미널</h2>

      {/* Controls */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        marginBottom: 12,
        padding: '12px 16px',
        background: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
      }}>
        <select
          value={server}
          onChange={e => setServer(e.target.value)}
          disabled={connected}
          style={{
            background: colors.termBg,
            color: colors.text,
            border: `1px solid ${colors.border}`,
            borderRadius: 6,
            padding: '8px 12px',
            fontSize: '0.9rem',
          }}
        >
          {servers.map(s => (
            <option key={s.id} value={s.host}>{s.label}</option>
          ))}
        </select>

        {!connected ? (
          <button
            onClick={connect}
            style={{
              background: colors.green,
              color: '#fff',
              border: 'none',
              padding: '8px 20px',
              borderRadius: 6,
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.9rem',
            }}
          >
            연결
          </button>
        ) : (
          <button
            onClick={disconnect}
            style={{
              background: colors.red,
              color: '#fff',
              border: 'none',
              padding: '8px 20px',
              borderRadius: 6,
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.9rem',
            }}
          >
            연결 해제
          </button>
        )}

        <span style={{
          marginLeft: 'auto',
          fontSize: '0.8rem',
          color: connected ? colors.green : colors.textMuted,
        }}>
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Terminal output */}
      <pre
        ref={outputRef}
        style={{
          flex: 1,
          background: colors.termBg,
          border: `1px solid ${colors.border}`,
          borderRadius: '8px 8px 0 0',
          padding: 16,
          margin: 0,
          overflowY: 'auto',
          fontFamily: "'Cascadia Code', 'Fira Code', 'Consolas', monospace",
          fontSize: '0.85rem',
          lineHeight: 1.6,
          color: colors.green,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-all',
        }}
      >
        {output.length === 0 ? (
          <span style={{ color: colors.textMuted }}>서버를 선택하고 연결 버튼을 누르세요.</span>
        ) : (
          output.map((line, i) => (
            <div key={i}>{line}</div>
          ))
        )}
      </pre>

      {/* Input */}
      <form onSubmit={sendCommand} style={{ display: 'flex' }}>
        <span style={{
          background: colors.card,
          color: colors.green,
          padding: '10px 12px',
          borderLeft: `1px solid ${colors.border}`,
          borderBottom: `1px solid ${colors.border}`,
          borderBottomLeftRadius: 8,
          fontFamily: 'monospace',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
        }}>
          $
        </span>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={!connected}
          placeholder={connected ? '명령어를 입력하세요...' : '연결되지 않음'}
          style={{
            flex: 1,
            background: colors.card,
            color: colors.text,
            border: `1px solid ${colors.border}`,
            borderLeft: 'none',
            borderBottomRightRadius: 8,
            padding: '10px 12px',
            fontFamily: "'Cascadia Code', 'Fira Code', 'Consolas', monospace",
            fontSize: '0.85rem',
            outline: 'none',
          }}
        />
      </form>
    </div>
  )
}
