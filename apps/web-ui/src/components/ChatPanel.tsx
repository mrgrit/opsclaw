import { useState, useRef, useEffect } from 'react'
import { api } from '../api/client'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  contextType: 'project' | 'agent' | 'playbook'
  contextId: string
  contextLabel?: string
}

export default function ChatPanel({ contextType, contextId, contextLabel }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // contextId 변경 시 대화 초기화
  useEffect(() => {
    setMessages([])
  }, [contextId])

  async function send() {
    const msg = input.trim()
    if (!msg || loading) return
    setInput('')
    const userMsg: Message = { role: 'user', content: msg }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    try {
      const r = await api.post<{ reply: string; rag_sources: number }>('/chat', {
        message: msg,
        context_type: contextType,
        context_id: contextId,
        history: [...messages, userMsg].slice(-6),
      })
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: r.reply + (r.rag_sources > 0 ? `\n\n_(RAG ${r.rag_sources}건 참조)_` : ''),
      }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `오류: ${e}` }])
    } finally {
      setLoading(false)
    }
  }

  if (!contextId) return null

  return (
    <>
      {/* 플로팅 토글 버튼 */}
      <button
        onClick={() => setOpen(!open)}
        style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 1100,
          width: 48, height: 48, borderRadius: '50%',
          background: '#2563eb', color: '#fff', border: 'none',
          fontSize: '1.3rem', cursor: 'pointer', boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
        title="AI 채팅"
      >
        {open ? 'X' : '\u{1F4AC}'}
      </button>

      {/* 채팅 패널 */}
      {open && (
        <div style={{
          position: 'fixed', bottom: 80, right: 24, zIndex: 1100,
          width: 400, height: 500, background: '#fff',
          borderRadius: 12, boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
          border: '1px solid #e5e7eb',
        }}>
          {/* 헤더 */}
          <div style={{
            padding: '12px 16px', background: '#2563eb', color: '#fff',
            fontSize: '0.85rem', fontWeight: 700,
          }}>
            AI Chat — {contextType}: {contextLabel || contextId.slice(0, 20)}
          </div>

          {/* 메시지 영역 */}
          <div style={{ flex: 1, overflow: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
            {messages.length === 0 && (
              <div style={{ color: '#9ca3af', fontSize: '0.8rem', textAlign: 'center', marginTop: 40 }}>
                이 {contextType === 'project' ? '프로젝트' : contextType === 'agent' ? '에이전트' : 'Playbook'}에 대해 질문하세요.
                <br />RAG 기반으로 관련 evidence, 보고서, 경험을 참조합니다.
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} style={{
                alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '85%',
                background: m.role === 'user' ? '#2563eb' : '#f3f4f6',
                color: m.role === 'user' ? '#fff' : '#374151',
                borderRadius: 12,
                padding: '8px 12px',
                fontSize: '0.85rem',
                lineHeight: 1.5,
                whiteSpace: 'pre-wrap',
              }}>
                {m.content}
              </div>
            ))}
            {loading && (
              <div style={{ alignSelf: 'flex-start', color: '#9ca3af', fontSize: '0.8rem', padding: '4px 12px' }}>
                응답 생성 중...
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* 입력 영역 */}
          <div style={{ padding: '8px 12px', borderTop: '1px solid #e5e7eb', display: 'flex', gap: 8 }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
              placeholder="질문을 입력하세요..."
              disabled={loading}
              style={{
                flex: 1, padding: '8px 10px', border: '1px solid #d1d5db', borderRadius: 8,
                fontSize: '0.85rem', outline: 'none',
              }}
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              style={{
                padding: '8px 14px', background: loading ? '#9ca3af' : '#2563eb', color: '#fff',
                border: 'none', borderRadius: 8, cursor: loading ? 'default' : 'pointer',
                fontWeight: 600, fontSize: '0.85rem',
              }}
            >
              전송
            </button>
          </div>
        </div>
      )}
    </>
  )
}
