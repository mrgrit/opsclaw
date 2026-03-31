const colors = {
  card: '#21262d',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  red: '#f85149',
}

export default function CTF() {
  // VS Code 포트포워딩: 같은 호스트에서 8080 포트로 접근
  // localhost -> localhost:8080, xxx.devtunnels.ms -> 같은 호스트의 8080 포워딩
  const hostname = window.location.hostname
  const protocol = window.location.protocol
  
  // VS Code devtunnels의 경우 포트가 URL에 포함됨
  // 일반 접근의 경우 :8080
  let ctfdUrl = `${protocol}//${hostname}:8080`
  
  // devtunnels.ms 같은 경우 포트 번호가 URL에 인코딩됨
  if (hostname.includes('devtunnels.ms') || hostname.includes('github.dev')) {
    // VS Code 포워딩: 8000 -> 다른포트, 8080 -> 다른포트
    // 현재 URL에서 8000 포트 부분을 8080으로 바꾸기
    const currentUrl = window.location.href
    ctfdUrl = currentUrl.replace(/\/app\/.*/, '').replace('8000', '8080')
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: 8 }}>CTF (Capture The Flag)</h1>
      <p style={{ color: colors.textMuted, fontSize: '0.95rem', lineHeight: 1.7, marginBottom: 24 }}>
        OpsClaw 보안 교육 CTF 플랫폼. 교안과 시나리오에서 배운 내용을 실전 문제로 풀어보세요.
      </p>

      <div style={{
        background: colors.card,
        border: `1px solid ${colors.border}`,
        borderRadius: 12,
        padding: 40,
        textAlign: 'center',
      }}>
        <div style={{ fontSize: '3rem', marginBottom: 16 }}>🏴</div>
        <h2 style={{ fontSize: '1.3rem', marginBottom: 12 }}>OpsClaw Security CTF</h2>
        <p style={{ color: colors.textMuted, marginBottom: 24, fontSize: '0.9rem' }}>
          CTFd 플랫폼에서 문제를 풀고 FLAG를 제출하세요.<br/>
          OpsClaw dispatch로 실제 서버를 조작하여 답을 찾을 수 있습니다.
        </p>
        
        <a
          href={ctfdUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-block',
            background: colors.red,
            color: '#fff',
            padding: '14px 40px',
            borderRadius: 8,
            textDecoration: 'none',
            fontSize: '1.1rem',
            fontWeight: 600,
          }}
        >
          CTFd 접속하기 →
        </a>

        <div style={{ marginTop: 16, color: colors.textMuted, fontSize: '0.8rem' }}>
          별도 탭에서 열립니다 · 회원가입 후 문제 풀이 가능
        </div>
      </div>

      <div style={{ marginTop: 24, padding: 20, background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 8 }}>
        <h3 style={{ fontSize: '1rem', marginBottom: 12 }}>💡 CTF 문제 풀이 방법</h3>
        <div style={{ color: colors.textMuted, fontSize: '0.88rem', lineHeight: 1.8 }}>
          1. CTFd에서 문제를 확인합니다<br/>
          2. 웹 터미널 또는 OpsClaw CLI로 서버에 접속합니다<br/>
          3. 문제에서 요구하는 작업을 수행합니다<br/>
          4. FLAG를 찾아 CTFd에 제출합니다<br/>
          5. OpsClaw evidence가 자동으로 기록됩니다
        </div>
      </div>
    </div>
  )
}
