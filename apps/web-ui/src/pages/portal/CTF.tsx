const colors = {
  bg: '#0d1117',
  card: '#21262d',
  cardHover: '#292e36',
  border: '#30363d',
  accent: '#58a6ff',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  red: '#f85149',
  green: '#3fb950',
  purple: '#bc8cff',
  orange: '#d29922',
  gradStart: '#1a1b2e',
  gradEnd: '#0d1117',
}

const categories = [
  { icon: '⚔️', name: '공격 기술', desc: 'SQLi, XSS, 권한상승, 네트워크 공격', color: colors.red, count: 'C1·C3' },
  { icon: '🛡️', name: '방어 운영', desc: 'nftables, Suricata, Wazuh 룰 작성', color: colors.green, count: 'C2·C5' },
  { icon: '☁️', name: '인프라 보안', desc: 'Docker, 클라우드 설정, 컴플라이언스', color: colors.accent, count: 'C4·C6' },
  { icon: '🤖', name: 'AI 보안', desc: 'LLM 탈옥, 프롬프트 인젝션, 에이전트', color: colors.purple, count: 'C7~C10' },
]

const features = [
  { icon: '🖥️', title: '실제 서버에서 실습', desc: 'v-secu / v-web / v-siem 가상 서버에 직접 접속하여 문제를 풀어요' },
  { icon: '📝', title: 'Evidence 자동 기록', desc: 'OpsClaw가 모든 작업을 PoW 체인에 기록 — 실습 증적이 자동으로 남아요' },
  { icon: '🤖', title: 'AI 튜터 지원', desc: '막히면 AI 튜터(💬)에게 힌트를 물어보세요 — 교안 내용을 참고해서 답해줘요' },
  { icon: '🏆', title: '리더보드 경쟁', desc: '누가 가장 빨리, 가장 많이 풀었는지 실시간 순위를 확인하세요' },
]

export default function CTF() {
  const hostname = window.location.hostname
  const protocol = window.location.protocol
  let ctfdUrl = `${protocol}//${hostname}:8080`
  if (hostname.includes('devtunnels.ms') || hostname.includes('github.dev')) {
    ctfdUrl = window.location.href.replace(/\/app\/.*/, '').replace('8000', '8080')
  }

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>

      {/* Hero */}
      <div style={{
        background: `linear-gradient(135deg, ${colors.gradStart}, ${colors.gradEnd})`,
        border: `1px solid ${colors.border}`,
        borderRadius: 16,
        padding: '48px 40px',
        textAlign: 'center',
        marginBottom: 32,
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* 배경 패턴 */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, opacity: 0.03,
          backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 35px, #58a6ff 35px, #58a6ff 36px)',
        }} />

        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ fontSize: '3.5rem', marginBottom: 12 }}>🏴‍☠️</div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: 8, letterSpacing: '-0.02em' }}>
            <span style={{ color: colors.red }}>OpsClaw</span> Security CTF
          </h1>
          <p style={{ color: colors.textMuted, fontSize: '1rem', lineHeight: 1.7, maxWidth: 520, margin: '0 auto 28px' }}>
            교안에서 배운 이론, 시나리오에서 읽은 기술을<br/>
            <strong style={{ color: colors.text }}>실제 서버</strong>에서 직접 해킹하고 방어하세요.
          </p>

          <a
            href={ctfdUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: `linear-gradient(135deg, ${colors.red}, #d63030)`,
              color: '#fff', padding: '14px 36px', borderRadius: 10,
              textDecoration: 'none', fontSize: '1.05rem', fontWeight: 700,
              boxShadow: '0 4px 16px rgba(248,81,73,0.3)',
              transition: 'transform 0.15s, box-shadow 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 24px rgba(248,81,73,0.4)' }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 4px 16px rgba(248,81,73,0.3)' }}
          >
            CTF 시작하기 →
          </a>

          <div style={{ marginTop: 14, color: colors.textMuted, fontSize: '0.78rem' }}>
            별도 탭에서 열립니다 · 회원가입 후 문제 풀이 가능
          </div>
        </div>
      </div>

      {/* 문제 카테고리 */}
      <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: colors.textMuted, marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        문제 카테고리
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: 12, marginBottom: 32 }}>
        {categories.map(c => (
          <div key={c.name} style={{
            background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 10,
            padding: '18px 16px', borderLeft: `3px solid ${c.color}`,
            transition: 'border-color 0.15s',
          }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = c.color)}
            onMouseLeave={e => (e.currentTarget.style.borderColor = colors.border)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span style={{ fontSize: '1.4rem' }}>{c.icon}</span>
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{c.name}</span>
            </div>
            <div style={{ color: colors.textMuted, fontSize: '0.8rem', lineHeight: 1.5, marginBottom: 6 }}>{c.desc}</div>
            <div style={{ color: c.color, fontSize: '0.72rem', fontWeight: 600 }}>{c.count}</div>
          </div>
        ))}
      </div>

      {/* OpsClaw 특징 */}
      <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: colors.textMuted, marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        OpsClaw CTF가 다른 점
      </h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: 12, marginBottom: 32 }}>
        {features.map(f => (
          <div key={f.title} style={{
            background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 10,
            padding: '18px 16px',
          }}>
            <div style={{ fontSize: '1.6rem', marginBottom: 10 }}>{f.icon}</div>
            <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 6 }}>{f.title}</div>
            <div style={{ color: colors.textMuted, fontSize: '0.8rem', lineHeight: 1.5 }}>{f.desc}</div>
          </div>
        ))}
      </div>

      {/* 풀이 가이드 */}
      <div style={{
        background: colors.card, border: `1px solid ${colors.border}`, borderRadius: 12,
        padding: '24px 28px',
      }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1.2rem' }}>💡</span> 문제 풀이 워크플로
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {[
            { step: '1', text: 'CTFd에서 문제를 확인', detail: '카테고리별 문제를 선택하고 요구사항을 파악합니다', color: colors.accent },
            { step: '2', text: '웹 터미널 또는 OpsClaw CLI로 접속', detail: 'opsclaw dispatch "명령어" -t v-secu 또는 포탈의 터미널 사용', color: colors.green },
            { step: '3', text: '실제 서버에서 작업 수행', detail: '교안에서 배운 기술을 적용하여 취약점을 찾거나 방어를 구축합니다', color: colors.orange },
            { step: '4', text: 'FLAG를 찾아 CTFd에 제출', detail: 'FLAG{answer} 형태의 정답을 CTFd에 입력하면 점수 획득', color: colors.red },
            { step: '5', text: 'OpsClaw Evidence에 자동 기록', detail: '모든 작업이 PoW 체인에 기록되어 실습 증적이 자동으로 남습니다', color: colors.purple },
          ].map((s, i) => (
            <div key={s.step} style={{ display: 'flex', gap: 16, alignItems: 'flex-start', padding: '10px 0' }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                background: `${s.color}22`, color: s.color, display: 'flex',
                alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', fontWeight: 700,
              }}>{s.step}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 2 }}>{s.text}</div>
                <div style={{ color: colors.textMuted, fontSize: '0.8rem' }}>{s.detail}</div>
              </div>
              {i < 4 && <div style={{ position: 'absolute', left: 33, marginTop: 28, width: 1, height: 20, background: colors.border }} />}
            </div>
          ))}
        </div>
      </div>

      {/* OpsClaw 명령어 예시 */}
      <div style={{
        marginTop: 16, background: '#0d1117', border: `1px solid ${colors.border}`, borderRadius: 10,
        padding: '16px 20px', fontFamily: "'Fira Code', monospace", fontSize: '0.82rem',
        color: colors.green, lineHeight: 1.8,
      }}>
        <div style={{ color: colors.textMuted, marginBottom: 8, fontFamily: 'system-ui', fontSize: '0.78rem' }}>
          OpsClaw로 CTF 문제 풀기 — 예시
        </div>
        <div><span style={{color:colors.textMuted}}># 포트 스캔으로 열린 서비스 찾기</span></div>
        <div>$ opsclaw dispatch <span style={{color:colors.accent}}>"nmap -sV 192.168.0.110"</span> -t v-secu</div>
        <div style={{marginTop:4}}><span style={{color:colors.textMuted}}># nftables로 공격 IP 차단</span></div>
        <div>$ opsclaw dispatch <span style={{color:colors.accent}}>"sudo nft add rule inet filter input ip saddr 203.0.113.50 drop"</span> -t v-secu</div>
        <div style={{marginTop:4}}><span style={{color:colors.textMuted}}># Wazuh 경보에서 브루트포스 룰 확인</span></div>
        <div>$ opsclaw dispatch <span style={{color:colors.accent}}>"sudo grep 5712 /var/ossec/ruleset/rules/0095-sshd_rules.xml"</span> -t v-siem</div>
      </div>
    </div>
  )
}
