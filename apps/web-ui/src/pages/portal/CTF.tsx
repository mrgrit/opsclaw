import { useState } from 'react'

const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  red: '#f85149',
}

export default function CTF() {
  const [mode, setMode] = useState<'iframe' | 'link'>('iframe')
  const ctfdUrl = `${window.location.protocol}//${window.location.host}/ctfd`

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ fontSize: '1.4rem', margin: 0 }}>CTF (Capture The Flag)</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setMode(mode === 'iframe' ? 'link' : 'iframe')}
            style={{
              background: colors.card,
              border: `1px solid ${colors.border}`,
              color: colors.text,
              padding: '6px 14px',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: '0.85rem',
            }}
          >
            {mode === 'iframe' ? '링크 모드' : '임베드 모드'}
          </button>
          <a
            href={ctfdUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              background: colors.red,
              color: '#fff',
              padding: '6px 14px',
              borderRadius: 6,
              textDecoration: 'none',
              fontSize: '0.85rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            새 탭에서 열기
          </a>
        </div>
      </div>

      {mode === 'iframe' ? (
        <div style={{
          flex: 1,
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
          overflow: 'hidden',
          background: '#000',
        }}>
          <iframe
            src={ctfdUrl}
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
            }}
            title="CTFd"
          />
        </div>
      ) : (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: colors.card,
          border: `1px solid ${colors.border}`,
          borderRadius: 8,
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '3rem', marginBottom: 16, color: colors.red }}>CTFd</div>
            <p style={{ color: colors.textMuted, marginBottom: 24 }}>
              CTF 플랫폼은 별도 서비스로 운영됩니다.
            </p>
            <a
              href={ctfdUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                background: colors.red,
                color: '#fff',
                padding: '12px 32px',
                borderRadius: 8,
                textDecoration: 'none',
                fontSize: '1rem',
                fontWeight: 600,
              }}
            >
              CTFd 접속하기
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
