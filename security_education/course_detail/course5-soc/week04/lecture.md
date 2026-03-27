# Week 04: Wazuh 관제 환경 (상세 버전)

## 학습 목표
- Wazuh SIEM의 아키텍처를 이해한다
- Wazuh Dashboard에 접속하여 알림을 확인할 수 있다
- 에이전트 관리 방법을 익힌다
- 주요 알림 화면을 탐색하고 해석할 수 있다
- 각 개념의 보안 관점에서의 위험과 대응 방안을 분석할 수 있다
- OpsClaw를 활용하여 실습 작업을 자동화하고 증적을 관리할 수 있다
- 실제 보안 사고 사례와 연결하여 학습 내용을 적용할 수 있다


## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`


## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---


---

## 용어 해설 (보안관제/SOC 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC** | Security Operations Center | 보안 관제 센터 (24/7 모니터링) | 경찰 112 상황실 |
| **관제** | Monitoring/Surveillance | 보안 이벤트를 실시간 감시하는 활동 | CCTV 관제 |
| **경보** | Alert | 보안 이벤트가 탐지 규칙에 매칭되어 발생한 알림 | 화재 경보기 울림 |
| **이벤트** | Event | 시스템에서 발생한 모든 활동 기록 | 일어난 일 하나하나 |
| **인시던트** | Incident | 보안 정책을 위반한 이벤트 (실제 위협) | 실제 화재 발생 |
| **오탐** | False Positive | 정상 활동을 공격으로 잘못 탐지 | 화재 경보기가 요리 연기에 울림 |
| **미탐** | False Negative | 실제 공격을 놓침 | 도둑이 CCTV에 안 잡힘 |
| **TTD** | Time to Detect | 공격 발생~탐지까지 걸리는 시간 | 화재 발생~경보 울림 시간 |
| **TTR** | Time to Respond | 탐지~대응까지 걸리는 시간 | 경보~소방차 도착 시간 |
| **SIGMA** | SIGMA | SIEM 벤더에 무관한 범용 탐지 룰 포맷 | 국제 표준 수배서 양식 |
| **Tier 1/2/3** | SOC Tiers | 관제 인력 수준 (L1:모니터링, L2:분석, L3:전문가) | 일반의→전문의→교수 |
| **트리아지** | Triage | 경보를 우선순위별로 분류하는 작업 | 응급실 환자 분류 |
| **플레이북** | Playbook (IR) | 인시던트 유형별 대응 절차 매뉴얼 | 화재 대응 매뉴얼 |
| **포렌식** | Forensics | 사이버 범죄 수사를 위한 증거 수집·분석 | 범죄 현장 감식 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 도메인, 해시) | 수배범의 지문, 차량번호 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술·기법·절차 | 범인의 범행 수법 |
| **위협 헌팅** | Threat Hunting | 탐지 룰에 걸리지 않는 위협을 능동적으로 찾는 활동 | 잠복 수사 |
| **syslog** | syslog | 시스템 로그를 원격 전송하는 프로토콜 (UDP 514) | 모든 부서 보고서를 본사로 모으는 시스템 |


# 본 강의 내용

# Week 04: Wazuh 관제 환경

## 학습 목표

- Wazuh SIEM의 아키텍처를 이해한다
- Wazuh Dashboard에 접속하여 알림을 확인할 수 있다
- 에이전트 관리 방법을 익힌다
- 주요 알림 화면을 탐색하고 해석할 수 있다

---

## 1. Wazuh 개요

### 1.1 Wazuh란?

Wazuh는 **오픈소스 SIEM/XDR** 플랫폼이다.

- **SIEM**: Security Information and Event Management
- **XDR**: Extended Detection and Response
- 무료, 오픈소스 (GPLv2)
- 상용 SIEM(Splunk, QRadar 등)의 대안

### 1.2 핵심 기능

| 기능 | 설명 |
|------|------|
| 로그 수집 | 에이전트에서 로그를 중앙 수집 |
| 침입 탐지 | 규칙 기반 이상 행위 탐지 |
| 취약점 탐지 | CVE 기반 취약점 스캔 |
| 파일 무결성 모니터링 | 중요 파일 변경 탐지 |
| 보안 설정 감사 | CIS Benchmark 기반 점검 |
| 인시던트 대응 | 능동 대응 (Active Response) |

### 1.3 아키텍처

```
[에이전트(Agent)]  →  [매니저(Manager)]  →  [인덱서(Indexer)]  →  [대시보드(Dashboard)]
  opsclaw              siem                  siem                 siem
  secu                 10.20.30.100          10.20.30.100         10.20.30.100:443
  web
```

| 구성 요소 | 역할 | 위치 |
|-----------|------|------|
| Agent | 로그 수집, 이벤트 전송 | 각 서버 |
| Manager | 이벤트 분석, 규칙 매칭 | siem (192.168.208.152) |
| Indexer | 데이터 저장/검색 (OpenSearch) | siem |
| Dashboard | 웹 UI (OpenSearch Dashboards) | siem:443 |

---

## 2. Wazuh Dashboard 접속

### 2.1 접속 방법

```
URL: https://192.168.208.152:443
사용자: admin
비밀번호: (수업 시간에 안내)
```

> 자체 서명 인증서를 사용하므로 브라우저에서 "안전하지 않음" 경고가 나타난다.
> "고급" → "계속 진행"을 클릭한다.

### 2.2 Dashboard 주요 메뉴

| 메뉴 | 기능 |
|------|------|
| Overview | 전체 현황 대시보드 |
| Security Events | 보안 이벤트 목록 |
| Integrity Monitoring | 파일 변경 탐지 |
| Vulnerabilities | 취약점 스캔 결과 |
| MITRE ATT&CK | ATT&CK 매핑 |
| Agents | 에이전트 관리 |
| Management > Rules | 탐지 규칙 관리 |

---

## 3. 에이전트 관리

### 3.1 에이전트 상태 확인

```bash
# Wazuh Manager에서 에이전트 목록 확인
sshpass -p1 ssh user@192.168.208.152 "/var/ossec/bin/agent_control -l 2>/dev/null"

# 에이전트 상태 요약
sshpass -p1 ssh user@192.168.208.152 "/var/ossec/bin/agent_control -s 2>/dev/null || echo 'agent_control 없음'"
```

### 3.2 각 서버의 에이전트 상태

```bash
# opsclaw 서버
sshpass -p1 ssh user@192.168.208.142 "systemctl status wazuh-agent 2>/dev/null | head -5 || echo 'Agent 미설치'"

# secu 서버
sshpass -p1 ssh user@192.168.208.150 "systemctl status wazuh-agent 2>/dev/null | head -5 || echo 'Agent 미설치'"

# web 서버
sshpass -p1 ssh user@192.168.208.151 "systemctl status wazuh-agent 2>/dev/null | head -5 || echo 'Agent 미설치'"
```

### 3.3 에이전트 설정 확인

```bash
# 에이전트 설정 파일
sshpass -p1 ssh user@192.168.208.142 "cat /var/ossec/etc/ossec.conf 2>/dev/null | head -30"

# 에이전트가 모니터링하는 로그 파일
sshpass -p1 ssh user@192.168.208.142 "grep '<location>' /var/ossec/etc/ossec.conf 2>/dev/null"
```

### 3.4 Wazuh API 사용

```bash
# Wazuh API로 에이전트 목록 조회
# API: https://192.168.208.152:55000
# 먼저 토큰 발급
TOKEN=$(sshpass -p1 ssh user@192.168.208.152 "curl -s -k -u wazuh:wazuh -X POST 'https://localhost:55000/security/user/authenticate?raw=true' 2>/dev/null")
echo "Token: ${TOKEN:0:20}..."

# 에이전트 목록
sshpass -p1 ssh user@192.168.208.152 "curl -s -k -H 'Authorization: Bearer $TOKEN' 'https://localhost:55000/agents?pretty=true' 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30"
```

---

## 4. 알림(Alert) 확인

### 4.1 알림 레벨

| 레벨 | 의미 | 예시 |
|------|------|------|
| 0~3 | 낮음 | 시스템 이벤트, 정보성 |
| 4~7 | 보통 | 정책 위반, 인증 실패 |
| 8~11 | 높음 | 무차별 대입, 파일 변경 |
| 12~15 | 치명적 | rootkit 탐지, 심각한 침해 |

### 4.2 실습: 알림 로그 분석

```bash
# 전체 알림 수
sshpass -p1 ssh user@192.168.208.152 "wc -l /var/ossec/logs/alerts/alerts.json 2>/dev/null"

# 레벨별 통계
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
levels = Counter()
for line in sys.stdin:
    try:
        a = json.loads(line)
        levels[a.get('rule',{}).get('level',0)] += 1
    except: pass
print('레벨 | 건수')
print('-----|-----')
for l in sorted(levels.keys()):
    bar = '#' * min(levels[l], 50)
    print(f'  {l:2d} | {levels[l]:5d} {bar}')
\" 2>/dev/null"
```

```bash
# 최근 고위험 알림 (레벨 8 이상) 상세
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule', {})
        if r.get('level', 0) >= 8:
            print(f'[{a.get(\"timestamp\",\"\")}] Level {r[\"level\"]}')
            print(f'  Rule: {r.get(\"id\",\"\")} - {r.get(\"description\",\"\")}')
            print(f'  Agent: {a.get(\"agent\",{}).get(\"name\",\"\")}')
            src = a.get('data',{}).get('srcip','')
            if src: print(f'  Source: {src}')
            print()
    except: pass
\" 2>/dev/null | tail -30"
```

### 4.3 규칙(Rule) ID 이해

```bash
# 주요 규칙 ID
# 5501~5599: SSH 관련
# 5710~5720: SSH 무차별 대입
# 31100~31199: 웹 공격
# 550~559: 파일 무결성

# 특정 규칙 ID의 알림 검색
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        rid = r.get('id','')
        if rid.startswith('57'):  # SSH 무차별 대입 관련
            print(f'  {a.get(\"timestamp\",\"\")} [{rid}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -10"
```

---

## 5. 규칙 관리

### 5.1 Wazuh 규칙 구조

```bash
# 기본 규칙 디렉토리
sshpass -p1 ssh user@192.168.208.152 "ls /var/ossec/ruleset/rules/ 2>/dev/null | head -20"

# SSH 관련 규칙 확인
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/ruleset/rules/0095-sshd_rules.xml 2>/dev/null | head -30"

# 사용자 정의 규칙
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/etc/rules/local_rules.xml 2>/dev/null"
```

### 5.2 규칙 형식

```xml
<rule id="5710" level="5">
  <if_matched_sid>5503</if_matched_sid>
  <match>Failed password</match>
  <description>sshd: Attempt to login using a non-existent user</description>
  <group>authentication_failed</group>
</rule>
```

| 필드 | 의미 |
|------|------|
| id | 규칙 고유 번호 |
| level | 알림 레벨 (0~15) |
| if_matched_sid | 부모 규칙 ID |
| match | 로그 매칭 패턴 |
| description | 설명 |
| group | 분류 그룹 |

---

## 6. 파일 무결성 모니터링 (FIM)

### 6.1 FIM 설정 확인

```bash
# FIM 설정 (syscheck)
sshpass -p1 ssh user@192.168.208.142 "grep -A10 '<syscheck>' /var/ossec/etc/ossec.conf 2>/dev/null | head -15"

# 모니터링 대상 디렉토리
sshpass -p1 ssh user@192.168.208.142 "grep '<directories' /var/ossec/etc/ossec.conf 2>/dev/null"
```

### 6.2 FIM 알림 확인

```bash
# 파일 무결성 관련 알림
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if 'syscheck' in str(r.get('groups',[])):
            print(f'  {a.get(\"timestamp\",\"\")} - {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -10"
```

---

## 7. Active Response (능동 대응)

### 7.1 개념

Wazuh는 특정 알림 발생 시 **자동으로 대응 조치**를 실행할 수 있다.

예시:
- SSH 5회 실패 → 자동 IP 차단
- 웹 공격 탐지 → 자동 IP 차단

### 7.2 설정 확인

```bash
# Active Response 설정
sshpass -p1 ssh user@192.168.208.152 "grep -A15 '<active-response>' /var/ossec/etc/ossec.conf 2>/dev/null"

# 차단 스크립트
sshpass -p1 ssh user@192.168.208.152 "ls /var/ossec/active-response/bin/ 2>/dev/null"
```

---

## 8. 실전 관제 워크플로우

### 8.1 SOC 분석원의 일일 업무

```
1. 대시보드 확인 (Overview)
   - 전체 알림 현황
   - 고위험 알림 유무

2. 고위험 알림 분석 (Level 8+)
   - 상세 로그 확인
   - 출발지 IP 조사
   - ATT&CK 매핑

3. 에이전트 상태 확인
   - 모든 에이전트 연결 상태
   - 로그 수집 정상 여부

4. 트렌드 분석
   - 알림 수 추이
   - 새로운 패턴 유무
```

### 8.2 실습: 일일 관제 보고 데이터 수집

```bash
echo "========================================"
echo " 일일 보안 관제 현황 - $(date '+%Y-%m-%d')"
echo "========================================"

echo ""
echo "[에이전트 상태]"
sshpass -p1 ssh user@192.168.208.152 "/var/ossec/bin/agent_control -l 2>/dev/null | head -10"

echo ""
echo "[알림 통계 (오늘)]"
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
from datetime import date
today = date.today().isoformat()
levels = Counter()
total = 0
for line in sys.stdin:
    try:
        a = json.loads(line)
        if today in a.get('timestamp',''):
            total += 1
            levels[a.get('rule',{}).get('level',0)] += 1
    except: pass
print(f'  총 알림: {total}건')
for l in sorted(levels.keys(), reverse=True):
    print(f'  Level {l}: {levels[l]}건')
\" 2>/dev/null"

echo ""
echo "[고위험 알림 (Level 10+)]"
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 10:
            print(f'  [{r[\"level\"]}] {r.get(\"description\",\"\")} (Agent: {a.get(\"agent\",{}).get(\"name\",\"\")})')
    except: pass
\" 2>/dev/null | tail -5"
```

---

## 9. 핵심 정리

1. **Wazuh** = 오픈소스 SIEM/XDR (Agent → Manager → Indexer → Dashboard)
2. **Dashboard** = https://siem:443에서 웹 UI로 알림 확인
3. **알림 레벨** = 0~3(낮음), 4~7(보통), 8~11(높음), 12~15(치명적)
4. **FIM** = 중요 파일 변경을 자동 탐지
5. **Active Response** = 특정 알림 시 자동 차단/대응

---

## 과제

1. Wazuh Dashboard에 접속하여 Overview 화면을 캡처하시오
2. 알림 레벨별 통계를 수집하고 상위 5개 알림 규칙을 분석하시오
3. 에이전트 상태를 확인하고, 미연결 에이전트가 있다면 원인을 조사하시오

---

## 참고 자료

- Wazuh Documentation (https://documentation.wazuh.com)
- Wazuh Rule Syntax
- Wazuh API Reference


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 5)

이 주차에서 다루는 기술의 동작 방식을 단계별로 분해하여 이해한다.

```
[1단계] 입력/요청 → 시스템이 데이터를 수신
[2단계] 처리 → 내부 로직에 의한 데이터 처리
[3단계] 출력/응답 → 결과 반환 또는 상태 변경
[4단계] 기록 → 로그/증적 생성
```

> **왜 이 순서가 중요한가?**
> 각 단계에서 보안 검증이 누락되면 취약점이 발생한다.
> 1단계: 입력값 검증 미흡 → Injection
> 2단계: 인가 확인 누락 → Broken Access Control
> 3단계: 에러 정보 노출 → Information Disclosure
> 4단계: 로깅 실패 → Monitoring Failures

#### 개념 2: 보안 관점에서의 위험 분석

| 위험 요소 | 발생 조건 | 영향도 | 대응 방안 |
|----------|---------|--------|---------|
| 설정 미흡 | 기본 설정 사용 | 높음 | 보안 하드닝 가이드 적용 |
| 패치 누락 | 업데이트 미적용 | 높음 | 정기 패치 관리 프로세스 |
| 접근 제어 부재 | 인증/인가 미구현 | 매우 높음 | RBAC, MFA 적용 |
| 로깅 미흡 | 감사 로그 미수집 | 중간 | SIEM 연동, 로그 정책 |

#### 개념 3: 실제 사례 분석

**사례 1: 유사 취약점이 실제 피해로 이어진 경우**

실제 보안 사고에서 이 주차의 주제가 어떻게 악용되었는지 살펴본다.
공격자는 동일한 기법을 사용하여 대규모 데이터 유출, 서비스 장애, 금전적 피해를 초래하였다.

**교훈:**
- 기본적인 보안 조치의 중요성
- 탐지 체계의 필수성
- 사고 대응 절차의 사전 수립 필요성

### 도구 비교표

| 도구 | 용도 | 장점 | 단점 | 라이선스 |
|------|------|------|------|---------|
| 도구 A | 기본 점검 | 간편, 빠름 | 기능 제한 | 오픈소스 |
| 도구 B | 심층 분석 | 상세 결과 | 학습 곡선 | 상용/무료 |
| 도구 C | 자동화 | CI/CD 연동 | 오탐 가능 | 오픈소스 |


---

## 보충 실습

### 보충 실습 1: 기본 동작 확인

이론에서 배운 내용을 직접 확인하는 기초 실습이다.

```bash
# Step 1: 현재 상태 확인
echo "=== 현재 상태 ==="
# (해당 주차에 맞는 확인 명령)

# Step 2: 설정/변경 적용
echo "=== 변경 적용 ==="
# (해당 주차에 맞는 실습 명령)

# Step 3: 결과 검증
echo "=== 결과 확인 ==="
# (변경 결과 확인 명령)
```

> **트러블슈팅:**
> - 명령이 실패하면: 권한(sudo), 경로, 서비스 상태를 먼저 확인
> - 예상과 다른 결과: 이전 실습의 설정이 남아있을 수 있으므로 초기화 후 재시도
> - 타임아웃: 네트워크 연결 또는 서비스 가동 상태 확인

### 보충 실습 2: 탐지/모니터링 관점

공격자가 아닌 **방어자 관점**에서 동일한 활동을 모니터링하는 실습이다.

```bash
# siem 서버에서 관련 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo cat /var/ossec/logs/alerts/alerts.json | tail -5" 2>/dev/null

# Suricata 알림 확인 (해당 시)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tail -20 /var/log/suricata/fast.log" 2>/dev/null
```

> **왜 방어자 관점도 배우는가?**
> 공격 기법만 알면 "스크립트 키디"에 불과하다.
> 공격이 어떻게 탐지되는지 이해해야 진정한 보안 전문가이다.
> 이 과목의 모든 공격 실습에는 대응하는 탐지/방어 관점이 포함된다.

### 보충 실습 3: OpsClaw 자동화

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화한다.

```bash
# 프로젝트 생성 (이번 주차용)
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"weekXX-lab","request_text":"이번 주차 실습 자동화","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 실습 태스크 실행 (해당 주차에 맞게 수정)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"실습 태스크 1","instruction_prompt":"echo 실습1","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"실습 태스크 2","instruction_prompt":"echo 실습2","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }'

# Evidence 확인
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 04: Wazuh 관제 환경"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **보안관제 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 로그 분석의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **인시던트 대응 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

**Q4.** OpsClaw를 통해 실습을 실행하는 가장 큰 이점은?
- (a) 속도  (b) **모든 실행의 자동 증적(evidence) 기록**  (c) 무료  (d) 간편함

**Q5.** 이 주제의 보안 위험이 높은 이유는?
- (a) 비용이 많이 들어서  (b) 복잡해서  (c) **악용 시 시스템/데이터에 직접적 피해**  (d) 법적 문제

**Q6.** 방어/대응의 핵심 원칙은?
- (a) 모든 트래픽 차단  (b) **최소 권한 + 탐지 + 대응의 조합**  (c) 서버 재시작  (d) 비밀번호 변경

**Q7.** 실습 결과를 분석할 때 가장 먼저 확인해야 하는 것은?
- (a) 서버 이름  (b) **exit_code (성공/실패 여부)**  (c) 파일 크기  (d) 날짜

**Q8.** 이 주제와 관련된 MITRE ATT&CK 전술은?
- (a) Impact만  (b) Reconnaissance만  (c) **주제에 해당하는 전술(들)**  (d) 해당 없음

**Q9.** 실무에서 이 기법/도구를 사용할 때 가장 주의할 점은?
- (a) 속도  (b) **법적 허가와 범위 준수**  (c) 비용  (d) 보고서 양식

**Q10.** 다음 주차와의 연결 포인트는?
- (a) 관련 없음  (b) **이번 주 결과를 다음 주에서 활용/심화**  (c) 완전히 다른 주제  (d) 복습만

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:c, Q6:b, Q7:b, Q8:c, Q9:b, Q10:b

---

## 과제 (다음 주까지)

### 과제 1: 이론 정리 보고서 (30점)

이번 주차의 핵심 개념을 자신의 말로 정리하라.

| 항목 | 배점 |
|------|------|
| 핵심 개념 정의 및 설명 | 10점 |
| 실습 결과 캡처 및 해석 | 10점 |
| 보안 관점 분석 (공격↔방어) | 10점 |

### 과제 2: 실습 수행 보고서 (40점)

이번 주차의 모든 실습을 수행하고 결과를 보고서로 작성하라.

| 항목 | 배점 |
|------|------|
| 실습 명령어 및 실행 결과 캡처 | 15점 |
| 결과 해석 및 보안 의미 분석 | 15점 |
| 트러블슈팅 경험 (있는 경우) | 10점 |

### 과제 3: OpsClaw 자동화 (30점)

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화하라.

| 항목 | 배점 |
|------|------|
| 프로젝트 생성 + stage 전환 | 5점 |
| execute-plan 태스크 설계 (3개 이상) | 10점 |
| evidence/summary 결과 | 5점 |
| replay 타임라인 결과 | 5점 |
| 자동화의 이점 분석 (직접 실행 대비) | 5점 |

**제출:** 보고서(PDF 또는 MD) + OpsClaw project_id


---

## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:

- [ ] 이론 강의 내용 이해 (핵심 용어 설명 가능)
- [ ] 기본 실습 모두 수행 완료
- [ ] 보충 실습 1 (기본 동작 확인) 완료
- [ ] 보충 실습 2 (탐지/모니터링 관점) 수행
- [ ] 보충 실습 3 (OpsClaw 자동화) 수행
- [ ] 자가 점검 퀴즈 8/10 이상 정답
- [ ] 과제 1 (이론 정리) 작성
- [ ] 과제 2 (실습 보고서) 작성
- [ ] 과제 3 (OpsClaw 자동화) 완료

