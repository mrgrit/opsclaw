import { useState, useRef, useEffect } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const colors = {
  bg: '#0d1117',
  panel: '#161b22',
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  userBubble: '#1f3a5c',
  aiBubble: '#1c2d1c',
}

export default function ChatBot({ pageContext }: { pageContext: string }) {
  const [open, setOpen] = useState(false)
  const [selectionPopup, setSelectionPopup] = useState<{text: string, x: number, y: number} | null>(null)

  // 드래그 선택 → "AI튜터에게 질문하기" 팝업
  useEffect(() => {
    const handleMouseUp = (e: MouseEvent) => {
      // 팝업 버튼 클릭 시에는 무시
      if ((e.target as HTMLElement)?.closest('.ai-tutor-popup')) return
      setTimeout(() => {
        const sel = window.getSelection()
        const text = sel?.toString().trim()
        if (text && text.length > 3) {
          const range = sel!.getRangeAt(0)
          const rect = range.getBoundingClientRect()
          setSelectionPopup({ text, x: rect.left + rect.width / 2, y: rect.top + window.scrollY - 10 })
        } else {
          setSelectionPopup(null)
        }
      }, 10)
    }
    document.addEventListener('mouseup', handleMouseUp)
    return () => document.removeEventListener('mouseup', handleMouseUp)
  }, [])
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [model, setModel] = useState('gpt-oss:120b')
  const [models, setModels] = useState<{id:string, name:string}[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch('/portal/chat/models')
      .then(r => r.json())
      .then(d => setModels(d.models || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight)
  }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const userMsg: Message = { role: 'user', content: input.trim() }
    const newMsgs = [...messages, userMsg]
    setMessages(newMsgs)
    setInput('')
    setLoading(true)

    // 스트리밍 응답
    const assistantMsg: Message = { role: 'assistant', content: '' }
    setMessages([...newMsgs, assistantMsg])

    try {
      const res = await fetch('/portal/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          messages: newMsgs.map(m => ({ role: m.role, content: m.content })),
          context: pageContext,
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = { role: 'assistant', content: `오류: ${err.detail || res.status}` }
          return updated
        })
        return
      }

      const reader = res.body?.getReader()
      const decoder = new TextDecoder()
      let fullText = ''

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const chunk = decoder.decode(value, { stream: true })
          for (const line of chunk.split('\n')) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (data === '[DONE]') break
              try {
                const parsed = JSON.parse(data)
                if (parsed.content) {
                  fullText += parsed.content
                  setMessages(prev => {
                    const updated = [...prev]
                    updated[updated.length - 1] = { role: 'assistant', content: fullText }
                    return updated
                  })
                }
              } catch {}
            }
          }
        }
      }
    } catch (e) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { role: 'assistant', content: `연결 오류: ${e}` }
        return updated
      })
    } finally {
      setLoading(false)
    }
  }

  // 드래그 선택 → 채팅창에 복사 → 채팅 열기
  const handleSelectionToChat = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (selectionPopup) {
      const quoted = `"${selectionPopup.text}"\n\n이 부분에 대해 설명해주세요: `
      setInput(quoted)
      setOpen(true)
      // 약간의 딜레이 후 팝업 닫기
      setTimeout(() => setSelectionPopup(null), 100)
    }
  }

  // Floating button + 선택 팝업
  if (!open) {
    return (
      <>
        {selectionPopup && (
          <button
            className="ai-tutor-popup"
            onMouseDown={handleSelectionToChat}
            style={{
              position: 'absolute',
              left: selectionPopup.x - 70,
              top: selectionPopup.y - 36,
              background: colors.accent,
              color: '#fff',
              border: 'none',
              padding: '4px 10px',
              borderRadius: 6,
              fontSize: '0.75rem',
              cursor: 'pointer',
              zIndex: 1001,
              boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
              whiteSpace: 'nowrap',
            }}
          >
            🤖 AI튜터에게 질문하기
          </button>
        )}
        <button
          onClick={() => setOpen(true)}
          style={{
            position: 'fixed', bottom: 24, right: 24, width: 56, height: 56,
            borderRadius: '50%', background: colors.accent, border: 'none',
            color: '#fff', fontSize: '1.5rem', cursor: 'pointer',
            boxShadow: '0 4px 16px rgba(0,0,0,0.4)', zIndex: 1000,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
          title="AI 튜터"
        >
          💬
        </button>
      </>
    )
  }

  return (
    <div style={{
      position: 'fixed', bottom: 24, right: 24, width: 420, height: 560,
      background: colors.panel, border: `1px solid ${colors.border}`,
      borderRadius: 12, display: 'flex', flexDirection: 'column',
      boxShadow: '0 8px 32px rgba(0,0,0,0.5)', zIndex: 1000, overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 16px', borderBottom: `1px solid ${colors.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: colors.card,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.1rem' }}>🤖</span>
          <span style={{ fontWeight: 600, fontSize: '0.9rem', color: colors.text }}>AI 튜터</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <select
            value={model}
            onChange={e => setModel(e.target.value)}
            style={{
              background: colors.bg, color: colors.text, border: `1px solid ${colors.border}`,
              borderRadius: 4, padding: '4px 8px', fontSize: '0.75rem', cursor: 'pointer',
            }}
          >
            {models.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
          <button
            onClick={() => setOpen(false)}
            style={{
              background: 'none', border: 'none', color: colors.textMuted,
              cursor: 'pointer', fontSize: '1.2rem', padding: '0 4px',
            }}
          >✕</button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} style={{
        flex: 1, overflowY: 'auto', padding: 12, display: 'flex',
        flexDirection: 'column', gap: 10,
      }}>
        {messages.length === 0 && (
          <div style={{ color: colors.textMuted, fontSize: '0.85rem', textAlign: 'center', marginTop: 40 }}>
            현재 페이지 내용에 대해 질문하세요.<br/>
            AI가 교안/소설 내용을 참고하여 답변합니다.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '85%',
          }}>
            <div style={{
              background: m.role === 'user' ? colors.userBubble : colors.aiBubble,
              border: `1px solid ${colors.border}`,
              borderRadius: m.role === 'user' ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
              padding: '10px 14px',
              fontSize: '0.88rem',
              lineHeight: 1.6,
              color: colors.text,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}>
              {m.content}
            </div>
            <div style={{
              fontSize: '0.7rem', color: colors.textMuted, marginTop: 2,
              textAlign: m.role === 'user' ? 'right' : 'left',
            }}>
              {m.role === 'user' ? '나' : model}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ color: colors.textMuted, fontSize: '0.85rem', fontStyle: 'italic' }}>
            답변 생성 중...
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{
        padding: '10px 12px', borderTop: `1px solid ${colors.border}`,
        display: 'flex', gap: 8, background: colors.card,
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
          placeholder="질문을 입력하세요..."
          style={{
            flex: 1, background: colors.bg, border: `1px solid ${colors.border}`,
            borderRadius: 6, padding: '8px 12px', color: colors.text,
            fontSize: '0.88rem', outline: 'none',
          }}
          disabled={loading}
        />
        <button
          onClick={send}
          disabled={loading || !input.trim()}
          style={{
            background: colors.accent, color: '#fff', border: 'none',
            borderRadius: 6, padding: '8px 14px', cursor: loading ? 'wait' : 'pointer',
            fontSize: '0.88rem', fontWeight: 600, opacity: loading ? 0.6 : 1,
          }}
        >전송</button>
      </div>
    </div>
  )
}
