# Week 10: 인시던트 대응 (1) - 웹 공격 (상세 버전)

## 학습 목표
- SQL Injection 공격의 탐지부터 대응까지 전 과정을 수행한다
- 웹 로그에서 공격 증거를 수집하고 분석한다
- WAF/IPS를 활용한 차단 조치를 수행한다
- 웹 공격 인시던트 대응 보고서를 작성한다
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


---

# Week 10: 인시던트 대응 (1) - 웹 공격

## 학습 목표

- SQL Injection 공격의 탐지부터 대응까지 전 과정을 수행한다
- 웹 로그에서 공격 증거를 수집하고 분석한다
- WAF/IPS를 활용한 차단 조치를 수행한다
- 웹 공격 인시던트 대응 보고서를 작성한다

---

## 1. 시나리오: JuiceShop 웹 공격

### 1.1 환경

- **대상**: web 서버 (10.20.30.80) - OWASP JuiceShop
- **방어**: BunkerWeb WAF, Suricata IPS (secu), Wazuh SIEM
- JuiceShop은 **의도적으로 취약한** 웹 애플리케이션이다

### 1.2 공격 시나리오

```
공격자 → [Suricata IPS] → [BunkerWeb WAF] → [JuiceShop]
                  ↓                ↓                ↓
              fast.log        access.log        app.log
                  ↓                ↓                ↓
              [Wazuh SIEM] ← 로그 수집 ← [Wazuh Agent]
```

---

## 2. 탐지 (Detection)

### 2.1 Suricata에서 탐지

```bash
# SQL Injection 관련 Suricata 알림
sshpass -p1 ssh secu@10.20.30.1 "grep -iE 'sql|injection|sqli' /var/log/suricata/fast.log 2>/dev/null | tail -10"

# 웹 공격 전체 알림
sshpass -p1 ssh secu@10.20.30.1 "grep -iE 'web|http|xss|rfi|lfi' /var/log/suricata/fast.log 2>/dev/null | tail -10"

# eve.json에서 HTTP 이벤트
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert':
            a = e.get('alert',{})
            cat = a.get('category','')
            if 'web' in cat.lower() or 'sql' in cat.lower() or 'xss' in cat.lower():
                print(f'  [{a.get(\"severity\",\"\")}] {a.get(\"signature\",\"\")}')
                print(f'    {e.get(\"src_ip\",\"\")}:{e.get(\"src_port\",\"\")} -> {e.get(\"dest_ip\",\"\")}:{e.get(\"dest_port\",\"\")}')
    except: pass
\" 2>/dev/null | tail -20"
```

### 2.2 WAF에서 탐지

```bash
# WAF 차단 로그 (403 응답)
sshpass -p1 ssh web@10.20.30.80 "grep ' 403 ' /var/log/nginx/access.log 2>/dev/null | tail -10"
sshpass -p1 ssh web@10.20.30.80 "grep ' 403 ' /var/log/bunkerweb/access.log 2>/dev/null | tail -10"

# WAF 에러 로그
sshpass -p1 ssh web@10.20.30.80 "tail -10 /var/log/nginx/error.log 2>/dev/null"
```

### 2.3 웹 로그에서 탐지

```bash
# SQL Injection 패턴 검색
sshpass -p1 ssh web@10.20.30.80 "grep -iE \"union.*select|or.*1=1|'.*or.*'|drop.*table|insert.*into|sleep\(|benchmark\(\" \
  /var/log/nginx/access.log 2>/dev/null | tail -10"

# XSS 패턴 검색
sshpass -p1 ssh web@10.20.30.80 "grep -iE '<script|javascript:|onerror=|onload=|alert\(' \
  /var/log/nginx/access.log 2>/dev/null | tail -10"

# Path Traversal 패턴 검색
sshpass -p1 ssh web@10.20.30.80 "grep -iE '\.\.\/|%2e%2e|/etc/passwd|/etc/shadow' \
  /var/log/nginx/access.log 2>/dev/null | tail -10"
```

---

## 3. 분석 (Analysis)

### 3.1 공격자 식별

```bash
# 공격 요청을 보낸 IP 목록
sshpass -p1 ssh web@10.20.30.80 "grep -iE 'union|select|script|alert|\.\./' /var/log/nginx/access.log 2>/dev/null | \
  awk '{print \$1}' | sort | uniq -c | sort -rn | head -5"
```

### 3.2 공격 타임라인 구성

```bash
# 특정 공격자 IP의 전체 활동 추적
ATTACKER_IP="10.0.0.1"  # 실제 발견된 IP로 변경

echo "=== $ATTACKER_IP 활동 타임라인 ==="

echo "[웹 접근]"
sshpass -p1 ssh web@10.20.30.80 "grep '$ATTACKER_IP' /var/log/nginx/access.log 2>/dev/null | head -20"

echo ""
echo "[IPS 탐지]"
sshpass -p1 ssh secu@10.20.30.1 "grep '$ATTACKER_IP' /var/log/suricata/fast.log 2>/dev/null"

echo ""
echo "[Wazuh 알림]"
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        if '$ATTACKER_IP' in str(a):
            r = a.get('rule',{})
            print(f'  {a.get(\"timestamp\",\"\")} [{r.get(\"level\",0)}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null"
```

### 3.3 공격 성공 여부 판단

```bash
# 공격 요청의 응답 코드 분석
sshpass -p1 ssh web@10.20.30.80 "grep -iE 'union|select|script' /var/log/nginx/access.log 2>/dev/null | \
  awk '{print \$9}' | sort | uniq -c | sort -rn"

# 200 응답 = 공격 성공 가능성
# 403 응답 = WAF에 의해 차단
# 500 응답 = 서버 오류 (공격이 부분적으로 작동)
```

### 3.4 공격 영향 분석

```bash
# 데이터베이스 접근 여부 확인 (JuiceShop SQLite)
sshpass -p1 ssh web@10.20.30.80 "find / -name '*.sqlite' -o -name '*.db' 2>/dev/null | head -5"

# 서버 리소스 영향
sshpass -p1 ssh web@10.20.30.80 "uptime; free -h | grep Mem; df -h / | tail -1"
```

---

## 4. 격리/억제 (Containment)

### 4.1 공격자 IP 차단

```bash
# 방화벽에서 차단 (secu 서버)
echo "=== IP 차단 명령 (시연) ==="
echo "sshpass -p1 ssh secu@10.20.30.1 'sudo nft add rule inet filter input ip saddr $ATTACKER_IP drop'"
echo ""
echo "현재 차단 규칙:"
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null | grep 'drop' | head -5"
```

### 4.2 WAF 규칙 강화

```bash
# BunkerWeb/nginx WAF 설정 확인
sshpass -p1 ssh web@10.20.30.80 "cat /etc/nginx/conf.d/*.conf 2>/dev/null | head -20"
sshpass -p1 ssh web@10.20.30.80 "ls /etc/bunkerweb/ 2>/dev/null"
```

### 4.3 웹 서비스 상태 확인

```bash
# 웹 서비스 정상 동작 확인
sshpass -p1 ssh web@10.20.30.80 "curl -s -o /dev/null -w '%{http_code}' http://localhost/ 2>/dev/null"
```

---

## 5. 근절 및 복구

### 5.1 근절

```bash
# 웹셸 여부 확인 (의심 파일 검색)
sshpass -p1 ssh web@10.20.30.80 "find /var/www -name '*.php' -newer /etc/hostname -type f 2>/dev/null"
sshpass -p1 ssh web@10.20.30.80 "find /tmp -type f -executable 2>/dev/null"

# 서버 프로세스 확인 (비정상 프로세스)
sshpass -p1 ssh web@10.20.30.80 "ps aux | grep -E 'nc |ncat |python.*http|perl.*socket' | grep -v grep"
```

### 5.2 복구

```bash
# 서비스 상태 확인
sshpass -p1 ssh web@10.20.30.80 "systemctl status nginx bunkerweb 2>/dev/null | grep Active"

# 로그 수집 정상 확인
sshpass -p1 ssh web@10.20.30.80 "systemctl is-active wazuh-agent 2>/dev/null"
```

---

## 6. 증거 수집 및 보존

```bash
# 증거 보존 (타임스탬프 포함 복사)
EVIDENCE="/tmp/web_incident_$(date +%Y%m%d_%H%M)"

echo "증거 수집: $EVIDENCE"

# 웹 로그
sshpass -p1 ssh web@10.20.30.80 "cat /var/log/nginx/access.log" 2>/dev/null > /tmp/web_access_evidence.txt

# IPS 로그
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/fast.log" 2>/dev/null > /tmp/suricata_evidence.txt

# Wazuh 알림
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json" 2>/dev/null > /tmp/wazuh_evidence.txt

# 해시값 생성
sha256sum /tmp/*_evidence.txt 2>/dev/null
```

---

## 7. ATT&CK 매핑

| 단계 | ATT&CK 전술 | 기법 | 증거 |
|------|------------|------|------|
| 정찰 | TA0043 | T1595 Active Scanning | 대량 404, 디렉토리 스캔 |
| 초기접근 | TA0001 | T1190 Exploit Public-Facing App | SQLi 요청 |
| 실행 | TA0002 | T1059 Command and Script Interpreter | SQL 명령 실행 |
| 자격증명 | TA0006 | T1212 Exploitation for Credential Access | DB에서 인증정보 추출 |
| 유출 | TA0010 | T1048 Exfiltration Over Alternative Protocol | HTTP 응답으로 데이터 유출 |

---

## 8. 인시던트 대응 보고서

```
=== 웹 공격 인시던트 대응 보고서 ===

1. 인시던트 요약
   - 유형: SQL Injection
   - 대상: JuiceShop (10.20.30.80)
   - 공격자: X.X.X.X
   - 발생: 2026-XX-XX XX:XX
   - 탐지: 2026-XX-XX XX:XX (Suricata/Wazuh)
   - 격리: 2026-XX-XX XX:XX (방화벽 차단)
   - 종료: 2026-XX-XX XX:XX

2. 공격 타임라인
   - XX:XX 디렉토리 스캐닝 시작
   - XX:XX SQL Injection 시도 시작
   - XX:XX Suricata에서 탐지
   - XX:XX SOC 분석원 확인
   - XX:XX 방화벽에서 IP 차단

3. 영향 분석
   - 공격 성공 여부:
   - 데이터 유출:
   - 서비스 영향:

4. 조치 내역
   - 격리: IP 차단
   - 근절: (해당 사항)
   - 복구: 서비스 정상 확인

5. 재발 방지
   - WAF 규칙 강화
   - 입력값 검증
   - 정기 취약점 점검

6. ATT&CK 매핑
   (위 표 참조)
```

---

## 9. 핵심 정리

1. **웹 공격 탐지** = Suricata + WAF + 웹 로그 3중 확인
2. **분석** = 공격자 식별, 타임라인, 성공 여부 판단
3. **격리** = 방화벽 차단, WAF 강화
4. **증거 보존** = 로그 복사 + 해시값으로 무결성 보장
5. **ATT&CK 매핑** = T1190(Exploit Public-Facing App)이 핵심

---

## 과제

1. 웹 서버 로그에서 공격 시도를 탐지하고 공격자 IP를 식별하시오
2. 공격 타임라인을 구성하시오
3. 인시던트 대응 보고서를 작성하시오

---

## 참고 자료

- OWASP Top 10 2021
- OWASP JuiceShop Solutions
- SANS Web Application Incident Handling


---

---

## 심화: 보안관제(SOC) 실무 보충

### 경보 분석 워크플로

```
[1단계] 경보 수신
    → Wazuh Dashboard에서 경보 확인
    → 심각도(level), 출처(src), 대상(dst) 즉시 파악

[2단계] 초기 분류 (Triage, 5분 이내)
    → 오탐(False Positive)인가? → 기존 사례와 비교
    → 실제 위협인가? → IOC 확인 (악성 IP, 해시)
    → 긴급도 결정: P1(즉시) / P2(4시간) / P3(24시간) / P4(일반)

[3단계] 심층 분석 (Investigation)
    → 관련 로그 추가 수집 (시간 범위 확대)
    → ATT&CK 기법 매핑
    → 영향 범위 파악 (어떤 서버, 어떤 데이터)

[4단계] 대응 (Response)
    → 격리: 감염 서버 네트워크 분리
    → 차단: 공격자 IP 방화벽 차단
    → 복구: 백업에서 복원, 패치 적용

[5단계] 사후 분석 (Post-Incident)
    → 타임라인 작성 (attack→detect→respond→recover)
    → 탐지 룰 개선
    → 보고서 작성
```

### Wazuh 로그 분석 실습

```bash
# siem 서버에서 최근 경보 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 "
  echo '=== 최근 경보 (level >= 7) ==='
  sudo cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | \
    python3 -c '
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line.strip())
        if a.get("rule",{}).get("level",0) >= 7:
            print(f"[{a[\"rule\"][\"level\"]}] {a[\"rule\"].get(\"description\",\"?\")[:60]} src={a.get(\"srcip\",\"?\")}")
    except: pass
' 2>/dev/null | tail -10
" 2>/dev/null
```

### SIGMA 룰 작성 가이드

```yaml
# SIGMA 룰 기본 구조
title: SSH Brute Force Detection     # 룰 이름
id: 12345678-abcd-efgh-...           # 고유 ID (UUID)
status: experimental                  # experimental/test/stable
description: |                        # 상세 설명
    5분 내 동일 IP에서 10회 이상 SSH 인증 실패 탐지
author: Student Name                  # 작성자
date: 2026/03/27                      # 작성일

logsource:                            # 어떤 로그를 볼 것인가
    product: linux
    service: sshd

detection:                            # 어떤 패턴을 찾을 것인가
    selection:
        eventid: 4625                 # 또는 sshd 실패 이벤트
    filter:                           # 제외 조건
        srcip: "10.20.30.*"           # 내부 IP는 제외
    condition: selection and not filter
    timeframe: 5m                     # 시간 범위
    count: 10                         # 최소 횟수

level: high                           # 심각도
tags:                                 # ATT&CK 매핑
    - attack.credential_access
    - attack.t1110.001
falsepositives:                       # 오탐 가능성
    - 자동화 스크립트의 반복 접속
    - 비밀번호 정책 변경 후 재접속
```

### TTD/TTR 측정 실습

```bash
# 공격→탐지 시간(TTD) 측정 시나리오
echo "=== 공격 시작 시각 기록 ==="
ATTACK_TIME=$(date +%s)
echo "공격 시작: $(date)"

# (여기서 공격 실행)

echo "=== SIEM 경보 확인 ==="
# (경보 발생 시각 확인)
DETECT_TIME=$(date +%s)
TTD=$((DETECT_TIME - ATTACK_TIME))
echo "TTD (탐지 소요 시간): ${TTD}초"
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 10: 인시던트 대응 (1) - 웹 공격"의 핵심 목적은 무엇인가?
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


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


