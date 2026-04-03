# Week 06: 실시간 방어 — 라이브 IPS, 자동 차단, fail2ban

## 학습 목표
- 실시간 침입 방지 시스템(IPS)의 동작 원리와 배치 아키텍처를 이해한다
- Suricata IPS 모드에서 라이브 트래픽 차단 규칙을 작성하고 적용할 수 있다
- fail2ban을 활용한 자동 IP 차단 시스템을 구성할 수 있다
- nftables 기반 동적 방화벽 규칙을 OpsClaw로 자동화할 수 있다
- 실시간 방어 체계의 오탐(False Positive) 관리 전략을 수립할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- Week 01-05 공격 기법 전반 이해
- 네트워크 방화벽, IDS/IPS 기본 개념

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 시뮬레이션 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | IPS + nftables 방화벽 | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹 서버 (보호 대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 모니터링 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | IPS 아키텍처 이론 | 강의 |
| 0:30-1:10 | Suricata IPS 규칙 작성 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | fail2ban 구성 실습 | 실습 |
| 2:00-2:40 | OpsClaw 자동 차단 파이프라인 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | 오탐 관리 토론 + 퀴즈 | 토론 |

---

# Part 1: IPS 아키텍처 이론 (30분)

## 1.1 IDS vs IPS

| 특성 | IDS (탐지) | IPS (방지) |
|------|-----------|-----------|
| 동작 | 패시브 미러링 | 인라인 차단 |
| 배치 | SPAN/TAP | 브릿지/인라인 |
| 응답 | 알림 생성 | 패킷 드롭 |
| 지연 | 없음 | 미세 지연 |
| 위험 | 공격 통과 | 오탐 시 정상 트래픽 차단 |

## 1.2 Suricata IPS 배치 아키텍처

```
[인터넷] → [secu:nftables] → [Suricata IPS] → [내부 네트워크]
                  ↓                  ↓
             패킷 필터링        시그니처 매칭
                                    ↓
                             DROP / PASS / ALERT
```

## 1.3 방어 계층 구조

```
Layer 1: nftables     — IP/포트 기반 정적 필터링
Layer 2: Suricata IPS — 시그니처 + 프로토콜 분석
Layer 3: fail2ban     — 로그 기반 동적 차단
Layer 4: WAF          — HTTP 계층 보호 (BunkerWeb)
Layer 5: SIEM         — 상관 분석 및 알림
```

---

# Part 2: Suricata IPS 규칙 실습 (40분)

## 실습 2.1: Suricata IPS 모드 활성화 및 규칙 작성

> **목적**: Suricata를 IPS 모드로 운영하고 공격 트래픽을 차단한다
> **배우는 것**: Suricata 규칙 문법, DROP 액션

```bash
# Suricata IPS 상태 확인 (secu)
systemctl status suricata
suricata --build-info | grep NFQ

# 커스텀 규칙 작성
cat > /tmp/custom_ips.rules << 'EOF'
# SQL Injection 차단
drop http any any -> $HOME_NET any (msg:"SQL Injection Attempt"; flow:to_server; http.uri; pcre:"/(\%27)|(\')|(\-\-)|(%23)|(#)/i"; sid:3000001; rev:1;)

# 포트 스캔 차단 (5초 내 20개 이상 SYN)
drop tcp any any -> $HOME_NET any (msg:"Port Scan Detected"; flags:S; threshold:type both, track by_src, count 20, seconds 5; sid:3000002; rev:1;)

# DNS Tunneling 차단
drop dns any any -> any any (msg:"DNS Tunnel Blocked"; dns.query; pcre:"/^[a-zA-Z0-9+\/=]{50,}\./"; sid:3000003; rev:1;)

# Reverse Shell 차단
drop tcp $HOME_NET any -> $EXTERNAL_NET 4444 (msg:"Reverse Shell to port 4444"; flow:to_server,established; sid:3000004; rev:1;)
EOF

# 규칙 적용 (secu)
cp /tmp/custom_ips.rules /etc/suricata/rules/custom.rules
suricata -T -c /etc/suricata/suricata.yaml  # 문법 검증
systemctl reload suricata
```

## 실습 2.2: IPS 규칙 테스트

> **목적**: 작성한 규칙이 실제 공격을 차단하는지 검증한다
> **배우는 것**: 규칙 효과 검증, 로그 분석

```bash
# 공격 시뮬레이션 (opsclaw → web)
# SQL Injection 시도
curl "http://10.20.30.80:3000/rest/products/search?q=test'%20OR%201=1--"

# 포트 스캔 시도
nmap -sS -T4 10.20.30.80

# 탐지/차단 로그 확인 (secu)
tail -f /var/log/suricata/fast.log
cat /var/log/suricata/eve.json | jq 'select(.alert)' | tail -5
```

---

# Part 3: fail2ban 구성 (40분)

## 실습 3.1: fail2ban SSH 보호

> **목적**: SSH 브루트포스 공격을 자동으로 차단한다
> **배우는 것**: fail2ban 필터/액션 구성

```bash
# fail2ban 설치 및 SSH jail 설정 (web)
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 600
findtime = 300
action = nftables-allports[name=sshd]
EOF

# 서비스 시작
systemctl restart fail2ban

# 브루트포스 시뮬레이션 (opsclaw)
for i in $(seq 1 5); do
  sshpass -p "wrong" ssh -o StrictHostKeyChecking=no test@10.20.30.80 2>/dev/null
done

# 차단 상태 확인 (web)
fail2ban-client status sshd
nft list ruleset | grep -A2 "fail2ban"
```

## 실습 3.2: 커스텀 fail2ban 필터 (웹 공격)

> **목적**: 웹 공격 패턴을 감지하여 자동 차단한다
> **배우는 것**: 정규식 기반 로그 매칭

```bash
# 커스텀 필터: SQL Injection 시도 탐지
cat > /etc/fail2ban/filter.d/web-sqli.conf << 'EOF'
[Definition]
failregex = ^<HOST> .* "(GET|POST) .*(union|select|insert|update|delete|drop).*HTTP
ignoreregex =
EOF

cat > /etc/fail2ban/jail.d/web-sqli.conf << 'EOF'
[web-sqli]
enabled = true
filter = web-sqli
logpath = /var/log/nginx/access.log
maxretry = 5
bantime = 3600
EOF
```

---

# Part 4: OpsClaw 자동 차단 파이프라인 (40분)

## 실습 4.1: OpsClaw를 통한 자동 방어

> **목적**: 공격 탐지부터 차단까지 자동화 파이프라인을 구성한다
> **배우는 것**: OpsClaw execute-plan 활용, 다중 서버 조율

```bash
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"suricata-update && systemctl reload suricata","risk_level":"medium","subagent_url":"http://10.20.30.1:8002"},
      {"order":2,"instruction_prompt":"fail2ban-client status","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":3,"instruction_prompt":"nft list ruleset | grep drop | wc -l","risk_level":"low","subagent_url":"http://10.20.30.1:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'
```

---

## 검증 체크리스트
- [ ] Suricata IPS 규칙(drop 액션)을 작성하고 적용할 수 있다
- [ ] fail2ban jail을 설정하여 SSH/웹 공격을 자동 차단할 수 있다
- [ ] nftables 동적 규칙을 확인하고 관리할 수 있다
- [ ] OpsClaw로 다중 서버 방어 태스크를 자동화할 수 있다
- [ ] 오탐(False Positive) 발생 시 대응 절차를 설명할 수 있다

## 자가 점검 퀴즈
1. IDS와 IPS의 배치 위치가 다른 이유를 네트워크 아키텍처 관점에서 설명하시오.
2. Suricata에서 `drop`과 `reject` 액션의 차이점은?
3. fail2ban의 `findtime`, `maxretry`, `bantime` 파라미터 간의 관계를 설명하시오.
4. IPS 오탐으로 정상 서비스가 차단되었을 때의 긴급 대응 절차를 서술하시오.
5. 실시간 방어 체계에서 계층적 방어(Defense in Depth)가 중요한 이유를 설명하시오.
