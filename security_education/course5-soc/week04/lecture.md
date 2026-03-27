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
