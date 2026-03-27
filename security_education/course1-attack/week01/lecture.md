# Week 01: 보안 개론 + 실습 환경 구축

## 학습 목표
- 사이버보안의 기본 개념과 용어를 이해한다
- 실습 인프라에 접속하고 각 서버의 역할을 파악한다
- 기본 리눅스 명령어와 네트워크 도구를 사용할 수 있다
- OpsClaw 플랫폼의 기본 사용법을 익힌다

## 전제 조건
- 리눅스 터미널 기본 사용 경험 (ls, cd, cat 수준)
- SSH 클라이언트 설치 (Windows: PuTTY 또는 WSL, Mac/Linux: 내장 ssh)

---

## 1. 사이버보안 개론 (30분)

### 1.1 사이버보안이란?

사이버보안(Cybersecurity)은 컴퓨터 시스템, 네트워크, 데이터를 무단 접근, 손상, 도난으로부터 보호하는 활동이다.

### 1.2 핵심 용어

| 용어 | 설명 | 예시 |
|------|------|------|
| **취약점 (Vulnerability)** | 시스템의 약점 | SQL Injection이 가능한 로그인 폼 |
| **위협 (Threat)** | 취약점을 악용할 수 있는 잠재적 위험 | 해커가 SQLi로 DB를 탈취 |
| **공격 (Attack)** | 위협이 실제로 실행된 것 | `' OR 1=1--` 페이로드 전송 |
| **자산 (Asset)** | 보호해야 할 대상 | 사용자 DB, 웹 서버, 네트워크 |
| **리스크 (Risk)** | 위협 × 취약점 × 영향도 | SQLi로 10만 건 개인정보 유출 |
| **CVE** | Common Vulnerabilities and Exposures | CVE-2021-44228 (Log4Shell) |
| **MITRE ATT&CK** | 공격 전술·기법의 체계적 분류 | T1190 (Exploit Public-Facing App) |
| **OWASP Top 10** | 가장 흔한 웹 취약점 10가지 | Injection, XSS, SSRF 등 |

### 1.3 보안의 3요소 (CIA Triad)

```
        기밀성 (Confidentiality)
           /\
          /  \
         /    \
        /______\
무결성              가용성
(Integrity)    (Availability)
```

- **기밀성**: 인가된 사용자만 정보에 접근 (예: 암호화, 접근제어)
- **무결성**: 정보가 무단으로 변경되지 않음 (예: 해시 검증, 디지털 서명)
- **가용성**: 필요할 때 정보에 접근 가능 (예: 이중화, DDoS 방어)

### 1.4 공격자의 유형

| 유형 | 동기 | 기술 수준 |
|------|------|---------|
| 스크립트 키디 | 호기심, 과시 | 낮음 (도구 사용) |
| 핵티비스트 | 정치/사회적 목적 | 중간 |
| 사이버 범죄자 | 금전적 이익 | 높음 |
| 국가 지원 해커 (APT) | 첩보, 파괴 | 매우 높음 |
| 내부자 위협 | 불만, 금전 | 시스템 지식 보유 |

---

## 2. 실습 인프라 소개 (30분)

### 2.1 인프라 구성도

```
┌─────────────────────────────────────────────────────┐
│  학생 PC → SSH → opsclaw (10.20.30.201)             │
│                    ↕ OpsClaw Manager API             │
├─────────────────────────────────────────────────────┤
│  secu (10.20.30.1)                                   │
│  → 역할: 네트워크 방화벽 + IPS (침입방지시스템)       │
│  → SW: nftables, Suricata                            │
│                                                      │
│  web (10.20.30.80)                                   │
│  → 역할: 웹 서버 (공격 대상)                          │
│  → SW: Apache, JuiceShop, BunkerWeb WAF              │
│                                                      │
│  siem (10.20.30.100)                                 │
│  → 역할: 보안 모니터링                                │
│  → SW: Wazuh SIEM, OpenCTI                           │
│                                                      │
│  dgx-spark (192.168.0.105)                           │
│  → 역할: AI/GPU 서버                                  │
│  → SW: Ollama LLM, NVIDIA GPU                        │
└─────────────────────────────────────────────────────┘
```

### 2.2 각 서버의 보안 역할

| 서버 | 비유 | 실제 역할 |
|------|------|---------|
| secu | 건물 입구 경비원 | 네트워크 트래픽을 검사하고 차단 |
| web | 은행 창구 | 고객(사용자)이 접근하는 서비스, 공격 대상 |
| siem | CCTV 관제실 | 모든 로그를 수집·분석하여 이상 탐지 |
| opsclaw | 보안 관리 본부 | 전체 보안 작업을 지시·기록·관리 |

---

## 3. 실습: 환경 접속 및 기본 명령어 (60분)

### 실습 3.1: SSH 접속

opsclaw 서버에 SSH로 접속한다.

```bash
# 학생 PC에서 실행
ssh student@10.20.30.201
# 비밀번호: 1
```

접속 확인:
```bash
hostname
# 예상 출력: opsclaw

whoami
# 예상 출력: student (또는 opsclaw)
```

### 실습 3.2: 다른 서버에 SSH 접속

opsclaw에서 다른 서버로 접속한다.

```bash
# web 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 'hostname'
# 예상 출력: web

# secu 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 'hostname'
# 예상 출력: secu

# siem 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 'hostname'
# 예상 출력: siem
```

> **용어 설명**
> - `sshpass -p1`: 비밀번호를 자동 입력 (-p 뒤가 비밀번호)
> - `-o StrictHostKeyChecking=no`: 처음 접속하는 서버의 키를 자동 수락
> - `web@10.20.30.80`: 사용자명@IP주소

### 실습 3.3: 시스템 정보 수집

각 서버의 기본 정보를 확인한다.

```bash
# 현재 서버 (opsclaw)
echo "=== 운영체제 ===" && cat /etc/os-release | head -3
# 예상 출력: Ubuntu 22.04

echo "=== 커널 ===" && uname -r
# 예상 출력: 6.8.0-106-generic (유사)

echo "=== CPU ===" && nproc
# 예상 출력: 숫자 (코어 수)

echo "=== 메모리 ===" && free -h | head -2
# 예상 출력: total/used/free/available 형태

echo "=== 디스크 ===" && df -h / | tail -1
# 예상 출력: 디바이스명 크기 사용 가용 사용% 마운트

echo "=== 네트워크 ===" && ip addr show | grep "inet " | grep -v 127.0.0.1
# 예상 출력: IP 주소 목록
```

### 실습 3.4: 네트워크 기본 도구

```bash
# ping: 서버가 살아있는지 확인
ping -c 3 10.20.30.80
# 예상 출력: 3 packets transmitted, 3 received, 0% packet loss

# 웹 서버 응답 확인
curl -s -I http://10.20.30.80:3000 | head -5
# 예상 출력: HTTP/1.1 200 OK ...

# 열린 포트 확인 (간단한 방법)
for port in 22 80 443 3000 8002; do
    timeout 1 bash -c "echo >/dev/tcp/10.20.30.80/$port" 2>/dev/null && echo "$port: open" || echo "$port: closed"
done
# 예상 출력:
# 22: open
# 80: open
# 443: closed
# 3000: open
# 8002: open
```

### 실습 3.5: nmap으로 포트 스캔

nmap은 네트워크 스캐닝 도구이다. **허가된 환경에서만 사용해야 한다.**

```bash
# 기본 포트 스캔 (상위 1000개 포트)
nmap 10.20.30.80
# 예상 출력:
# PORT     STATE SERVICE
# 22/tcp   open  ssh
# 80/tcp   open  http
# 3000/tcp open  ppp
# 8002/tcp open  teradataordbms
# 8081/tcp open  blackice-icecap
# 8082/tcp open  blackice-alerts

# 서비스 버전 탐지 (주요 포트만)
nmap -sV -p 22,80,3000 10.20.30.80
# 예상 출력: SSH 버전, Apache 버전, Node.js 등 표시
```

> **주의**: nmap은 강력한 도구이다. 허가 없는 대상에 사용하면 **불법**이다.
> 본 실습에서는 교육용으로 구성된 내부 서버에서만 사용한다.

---

## 4. OpsClaw 소개 실습 (30분)

OpsClaw는 보안 작업을 자동화하고 기록하는 플랫폼이다. 모든 작업이 자동으로 증적(evidence)에 기록된다.

### 실습 4.1: OpsClaw로 명령 실행

```bash
# 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week01-lab","request_text":"Week 01 실습","master_mode":"external"}'
# 응답에서 project.id 값을 확인 (예: prj_xxxxxxxx)

# Stage 전환 (plan → execute)
curl -s -X POST http://localhost:8000/projects/{project_id}/plan \
  -H "X-API-Key: opsclaw-api-key-2026"

curl -s -X POST http://localhost:8000/projects/{project_id}/execute \
  -H "X-API-Key: opsclaw-api-key-2026"

# web 서버에 명령 실행 (OpsClaw 경유)
curl -s -X POST http://localhost:8000/projects/{project_id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"command":"hostname && uptime","subagent_url":"http://10.20.30.80:8002"}'
# 예상 출력: web 서버의 hostname과 uptime
```

### 실습 4.2: 병렬 실행 (여러 서버 동시 점검)

```bash
curl -s -X POST http://localhost:8000/projects/{project_id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"opsclaw 점검","instruction_prompt":"hostname && uptime","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"web 점검","instruction_prompt":"hostname && uptime","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":3,"title":"siem 점검","instruction_prompt":"hostname && uptime","risk_level":"low","subagent_url":"http://10.20.30.100:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }'
# 예상 출력: overall=success, tasks_ok=3
```

> **핵심 개념**: OpsClaw를 통해 실행하면 모든 명령과 결과가 **자동으로 기록**된다.
> 직접 SSH로 실행하면 아무것도 남지 않는다. 보안 작업에서 증적(evidence)은 필수이다.

---

## 5. 과제

### 과제 1: 인프라 파악 보고서
각 서버(opsclaw, secu, web, siem)에 접속하여 다음 정보를 수집하고 보고서를 작성하라:
- 운영체제 및 버전
- CPU/메모리/디스크 사양
- 열린 포트 목록 (nmap 또는 ss -tlnp)
- 실행 중인 주요 서비스 (systemctl list-units --type=service --state=running)

### 과제 2: OpsClaw 프로젝트 생성
OpsClaw를 사용하여 과제 1의 정보 수집을 자동화하라. execute-plan으로 4개 서버를 병렬 점검하고, evidence를 확인하라.

---

## 검증 체크리스트

- [ ] 4개 서버에 SSH 접속 성공
- [ ] 각 서버의 hostname 확인
- [ ] nmap으로 web 서버 포트 스캔 성공
- [ ] curl로 JuiceShop (포트 3000) 접근 확인
- [ ] OpsClaw dispatch 명령 실행 성공
- [ ] OpsClaw execute-plan 병렬 실행 성공

---

## 다음 주 예고
**Week 02: 정보수집과 정찰 (Reconnaissance)**
- nmap 고급 스캔 기법
- DNS 정보 수집 (dig, whois)
- 웹 서버 핑거프린팅
- robots.txt, 디렉토리 열거
