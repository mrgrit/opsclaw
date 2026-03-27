# Week 09: Wazuh SIEM (1) — 설치와 구성 (상세 버전)

## 학습 목표
- SIEM의 역할과 필요성을 이해한다
- Wazuh의 Manager/Agent 아키텍처를 파악한다
- Wazuh 대시보드의 기본 기능을 사용할 수 있다
- Agent를 등록하고 연결 상태를 확인할 수 있다


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

## 용어 해설 (보안 솔루션 운영 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단하는 시스템 | 건물 출입 통제 시스템 |
| **체인** | Chain (nftables) | 패킷 처리 규칙의 묶음 (input, forward, output) | 심사 단계 |
| **룰/규칙** | Rule | 특정 조건의 트래픽을 어떻게 처리할지 정의 | "택배 기사만 출입 허용" |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 (IPS/AV) | 수배범 얼굴 사진 |
| **NFQUEUE** | Netfilter Queue | 커널에서 사용자 영역으로 패킷을 넘기는 큐 | 의심 택배를 별도 검사대로 보내는 것 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크 기반) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 로그를 파싱하여 구조화하는 규칙 | 외국어 통역사 |
| **CRS** | Core Rule Set (ModSecurity) | 범용 웹 공격 탐지 규칙 모음 | 표준 보안 검사 매뉴얼 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 정보 (IOC, TTPs) | 범죄 정보 공유 시스템 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인 등) | 수배범의 지문, 차량번호 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 포맷 | 범죄 보고서 표준 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | CTI 자동 교환 프로토콜 | 경찰서 간 수배 정보 공유 시스템 |
| **NAT** | Network Address Translation | 내부 IP를 외부 IP로 변환 | 회사 대표번호 (내선→외선) |
| **masquerade** | masquerade (nftables) | 나가는 패킷의 소스 IP를 게이트웨이 IP로 변환 | 회사 이름으로 편지 보내기 |


---

# Week 09: Wazuh SIEM (1) — 설치와 구성

## 학습 목표

- SIEM의 역할과 필요성을 이해한다
- Wazuh의 Manager/Agent 아키텍처를 파악한다
- Wazuh 대시보드의 기본 기능을 사용할 수 있다
- Agent를 등록하고 연결 상태를 확인할 수 있다

---

## 1. SIEM이란?

SIEM(Security Information and Event Management)은 보안 이벤트를 **수집, 분석, 상관분석, 시각화**하는 통합 보안 관제 플랫폼이다.

### 1.1 SIEM의 핵심 기능

| 기능 | 설명 |
|------|------|
| 로그 수집 | 다양한 소스에서 로그를 중앙 집중 수집 |
| 정규화 | 서로 다른 형식의 로그를 통일된 형식으로 변환 |
| 상관분석 | 여러 이벤트를 연결하여 위협 식별 |
| 알림 | 위협 탐지 시 알림 발생 |
| 대시보드 | 보안 상태 시각화 |
| 컴플라이언스 | PCI-DSS, GDPR 등 규정 준수 보고 |

### 1.2 왜 SIEM이 필요한가?

```
방화벽 로그 ──┐
IPS 로그 ─────┤
WAF 로그 ─────┼──→  SIEM  ──→ 종합 분석 → 위협 탐지
서버 로그 ────┤               상관분석     알림
인증 로그 ────┘               대시보드     보고서
```

개별 장비의 로그만으로는 전체 그림을 볼 수 없다. SIEM이 모든 로그를 모아서 **상관분석**한다.

---

## 2. Wazuh 아키텍처

Wazuh 4.11.2는 3개 컴포넌트로 구성된다:

```
┌─────────────────────────────────────────────┐
│              Wazuh Dashboard                │
│        (웹 UI, Kibana 기반)                  │
│           https://10.20.30.100              │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────┴──────────────────────────┐
│              Wazuh Indexer                   │
│        (로그 저장, OpenSearch 기반)            │
│           :9200                              │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────┴──────────────────────────┐
│              Wazuh Manager                   │
│        (분석 엔진, 룰 처리)                    │
│           :1514 (agent), :1515 (register)    │
│           :55000 (API)                       │
└──────────────────┬──────────────────────────┘
          ┌────────┼────────┐
          │        │        │
     ┌────┴──┐ ┌───┴──┐ ┌──┴────┐
     │Agent 1│ │Agent 2│ │Agent 3│
     │ secu  │ │  web  │ │ siem  │
     └───────┘ └───────┘ └───────┘
```

| 컴포넌트 | 역할 | 포트 |
|----------|------|------|
| Manager | 이벤트 분석, 룰 매칭, Agent 관리 | 1514, 1515, 55000 |
| Indexer | 이벤트 저장, 검색 (OpenSearch) | 9200 |
| Dashboard | 웹 UI (시각화, 관리) | 443 |
| Agent | 호스트에서 로그 수집, 전송 | (아웃바운드) |

---

## 3. 실습 환경 접속

### 3.1 siem 서버 접속

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100
```

### 3.2 Wazuh 서비스 상태 확인

```bash
echo 1 | sudo -S systemctl status wazuh-manager
```

**예상 출력:**
```
● wazuh-manager.service - Wazuh manager
     Loaded: loaded (/lib/systemd/system/wazuh-manager.service; enabled; ...)
     Active: active (running) since ...
```

```bash
echo 1 | sudo -S systemctl status wazuh-indexer
echo 1 | sudo -S systemctl status wazuh-dashboard
```

### 3.3 Wazuh 버전 확인

```bash
echo 1 | sudo -S /var/ossec/bin/wazuh-control info
```

**예상 출력:**
```
WAZUH_VERSION="v4.11.2"
WAZUH_REVISION="40112"
WAZUH_TYPE="server"
```

---

## 4. 핵심 디렉터리 구조

```bash
echo 1 | sudo -S ls /var/ossec/
```

| 디렉터리 | 설명 |
|----------|------|
| `/var/ossec/etc/` | 설정 파일 (ossec.conf) |
| `/var/ossec/rules/` | 탐지 룰 |
| `/var/ossec/decoders/` | 로그 디코더 |
| `/var/ossec/logs/` | Wazuh 로그 |
| `/var/ossec/logs/alerts/` | 알림 로그 |
| `/var/ossec/bin/` | 실행 파일 |
| `/var/ossec/queue/` | 큐 디렉터리 |

---

## 5. 핵심 설정 파일 (ossec.conf)

### 5.1 설정 파일 확인

```bash
echo 1 | sudo -S cat /var/ossec/etc/ossec.conf | head -50
```

### 5.2 주요 설정 항목

**로그 수집 설정:**

```xml
<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/syslog</location>
</localfile>

<localfile>
  <log_format>json</log_format>
  <location>/var/log/suricata/eve.json</location>
</localfile>

<localfile>
  <log_format>apache</log_format>
  <location>/var/log/apache2/access.log</location>
</localfile>
```

**Agent 연결 설정 (Manager측):**

```xml
<remote>
  <connection>secure</connection>
  <port>1514</port>
  <protocol>tcp</protocol>
</remote>
```

**알림 설정:**

```xml
<alerts>
  <log_alert_level>3</log_alert_level>
  <email_alert_level>12</email_alert_level>
</alerts>
```

> `log_alert_level`: 이 레벨 이상의 알림만 기록 (1~16, 기본: 3)

---

## 6. Wazuh API

### 6.1 API 인증 토큰 획득

```bash
# 기본 관리자 계정으로 토큰 획득
TOKEN=$(curl -s -u wazuh-wui:wazuh-wui -k -X POST \
  "https://10.20.30.100:55000/security/user/authenticate?raw=true")
echo $TOKEN | head -c 50
```

### 6.2 Manager 정보 조회

```bash
curl -s -k -X GET "https://10.20.30.100:55000/" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**예상 출력:**
```json
{
    "data": {
        "title": "Wazuh API REST",
        "api_version": "4.11.2",
        "revision": 40112,
        "license_name": "GPL 2.0",
        "hostname": "siem",
        "timestamp": "2026-03-27T10:00:00Z"
    }
}
```

### 6.3 Agent 목록 조회

```bash
curl -s -k -X GET "https://10.20.30.100:55000/agents?pretty=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -40
```

**예상 출력:**
```json
{
    "data": {
        "affected_items": [
            {
                "id": "000",
                "name": "siem",
                "status": "active",
                "manager": "siem",
                "node_name": "node01",
                "ip": "127.0.0.1",
                "version": "Wazuh v4.11.2"
            }
        ],
        "total_affected_items": 1
    }
}
```

---

## 7. Agent 등록 및 관리

### 7.1 Agent 등록 (API 방식)

secu 서버를 Agent로 등록:

```bash
# siem 서버에서 Agent 등록
curl -s -k -X POST "https://10.20.30.100:55000/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"secu","ip":"10.20.30.1"}' | python3 -m json.tool
```

**예상 출력:**
```json
{
    "data": {
        "id": "001",
        "key": "MDAxIHNlY3UgMTAuMjAuMzAuMSBhYmNkZWYxMjM0NTY3ODkw..."
    }
}
```

### 7.2 Agent 측 설정

secu 서버에 접속하여 Agent를 설정:

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1

# Agent 설치 확인
echo 1 | sudo -S /var/ossec/bin/wazuh-control info

# Agent 설정 파일 확인
echo 1 | sudo -S cat /var/ossec/etc/ossec.conf | grep -A 5 "<server>"
```

**Agent ossec.conf의 서버 연결 설정:**

```xml
<client>
  <server>
    <address>10.20.30.100</address>
    <port>1514</port>
    <protocol>tcp</protocol>
  </server>
</client>
```

### 7.3 Agent 시작 및 확인

```bash
# Agent 서비스 시작
echo 1 | sudo -S systemctl restart wazuh-agent
echo 1 | sudo -S systemctl status wazuh-agent
```

### 7.4 Manager에서 Agent 상태 확인

```bash
# siem 서버에서
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100

echo 1 | sudo -S /var/ossec/bin/agent_control -l
```

**예상 출력:**
```
Wazuh agent_control. List of available agents:
   ID: 000, Name: siem (server), IP: 127.0.0.1, Active/Local
   ID: 001, Name: secu, IP: 10.20.30.1, Active
   ID: 002, Name: web, IP: 10.20.30.80, Active
```

---

## 8. 알림 로그 확인

### 8.1 실시간 알림

```bash
echo 1 | sudo -S tail -f /var/ossec/logs/alerts/alerts.json | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        rule = e.get('rule', {})
        agent = e.get('agent', {})
        print(f\"[{e.get('timestamp','')}] Level:{rule.get('level','')} Rule:{rule.get('id','')} {rule.get('description','')}\")
        print(f\"  Agent: {agent.get('name','local')} ({agent.get('ip','127.0.0.1')})\")
    except: pass
" &
```

Ctrl+C로 종료.

### 8.2 최근 알림 확인

```bash
echo 1 | sudo -S tail -10 /var/ossec/logs/alerts/alerts.json | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        r = e.get('rule',{})
        print(f\"Level {r.get('level','?'):>2} | Rule {r.get('id','?'):>6} | {r.get('description','?')}\")
    except: pass
"
```

**예상 출력:**
```
Level  5 | Rule   5715 | sshd: authentication success.
Level  3 | Rule    530 | Wazuh agent started.
Level  7 | Rule   5710 | sshd: attempt to login using a denied user.
```

### 8.3 알림 레벨 의미

| 레벨 | 설명 | 예시 |
|------|------|------|
| 0~2 | 무시 | 시스템 정보 |
| 3~5 | 낮음 | 로그인 성공, 서비스 시작 |
| 6~8 | 중간 | 인증 실패, 설정 변경 |
| 9~11 | 높음 | 다수 인증 실패, 무결성 변경 |
| 12~15 | **심각** | **루트킷 탐지, 침입 시도** |

---

## 9. Wazuh Dashboard

### 9.1 대시보드 접속

웹 브라우저에서 다음 URL 접속:

```
https://10.20.30.100
```

- 기본 계정: `admin` / `admin` (또는 설치 시 설정한 계정)

### 9.2 주요 메뉴

| 메뉴 | 설명 |
|------|------|
| Overview | 전체 보안 현황 대시보드 |
| Agents | Agent 목록 및 상태 |
| Security Events | 보안 이벤트 검색 |
| Integrity Monitoring | 파일 무결성 모니터링 |
| Vulnerabilities | 취약점 스캔 결과 |
| MITRE ATT&CK | 공격 기법 매핑 |
| SCA | 보안 설정 평가 |

### 9.3 이벤트 검색 예시

대시보드에서 다음을 검색해보라:

```
rule.level >= 7
```

```
agent.name:secu AND rule.groups:authentication_failed
```

---

## 10. Suricata 로그 연동

Suricata의 eve.json을 Wazuh가 수집하도록 설정:

### 10.1 Agent 측 설정 (secu 서버)

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1

# ossec.conf에 Suricata 로그 수집 추가
echo 1 | sudo -S tee -a /var/ossec/etc/ossec.conf << 'XMLEOF'
<ossec_config>
  <localfile>
    <log_format>json</log_format>
    <location>/var/log/suricata/eve.json</location>
  </localfile>
</ossec_config>
XMLEOF

# Agent 재시작
echo 1 | sudo -S systemctl restart wazuh-agent
```

### 10.2 연동 확인

```bash
# siem 서버에서 Suricata 알림 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100

echo 1 | sudo -S cat /var/ossec/logs/alerts/alerts.json | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        if 'suricata' in str(e.get('rule',{}).get('groups',[])):
            r = e['rule']
            print(f\"[Suricata] Level {r['level']} | {r['description']}\")
    except: pass
" | tail -5
```

---

## 11. 실습 과제

### 과제 1: 서비스 확인

1. Wazuh Manager, Indexer, Dashboard가 모두 동작하는지 확인
2. API로 Manager 버전 정보를 조회
3. 등록된 Agent 목록을 조회

### 과제 2: Agent 상태

1. secu, web 서버의 Agent가 Active 상태인지 확인
2. 비활성 Agent가 있으면 원인을 파악하고 재시작

### 과제 3: 알림 분석

1. 최근 1시간 내 Level 7 이상 알림을 조회
2. 가장 많이 발생한 알림 Rule ID를 확인
3. 특정 Agent(secu)의 알림만 필터링

---

## 12. 핵심 정리

| 개념 | 설명 |
|------|------|
| SIEM | 보안 이벤트 통합 관제 플랫폼 |
| Wazuh Manager | 분석 엔진, 룰 매칭 (1514, 55000) |
| Wazuh Indexer | 이벤트 저장/검색 (OpenSearch) |
| Wazuh Dashboard | 웹 시각화 (443) |
| Agent | 호스트 로그 수집, Manager로 전송 |
| ossec.conf | 핵심 설정 파일 |
| alerts.json | 알림 로그 |
| Rule Level | 1~15 (높을수록 심각) |
| API | REST API (55000 포트) |

---

## 다음 주 예고

Week 10에서는 Wazuh 탐지 룰을 다룬다:
- local_rules.xml에 커스텀 룰 작성
- 디코더 작성
- logtest로 룰 검증


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 09: Wazuh SIEM (1) — 설치와 구성"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안 솔루션 운영의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. SIEM이란?"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. Wazuh 아키텍처"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안 솔루션 운영 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. 실습 환경 접속"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 올바른 설정의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 보안 솔루션 운영 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---
