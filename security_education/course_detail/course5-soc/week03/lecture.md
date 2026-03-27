# Week 03: 로그 이해 (2) - 네트워크/웹 로그 (상세 버전)

## 학습 목표
- Apache/nginx 웹 로그의 구조를 분석할 수 있다
- Suricata IPS 로그를 읽고 해석할 수 있다
- nftables 방화벽 로그를 분석할 수 있다
- 네트워크/웹 로그에서 공격 패턴을 식별할 수 있다
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

# Week 03: 로그 이해 (2) - 네트워크/웹 로그

## 학습 목표

- Apache/nginx 웹 로그의 구조를 분석할 수 있다
- Suricata IPS 로그를 읽고 해석할 수 있다
- nftables 방화벽 로그를 분석할 수 있다
- 네트워크/웹 로그에서 공격 패턴을 식별할 수 있다

---

## 1. 웹 서버 로그

### 1.1 Apache/nginx 접근 로그 형식

**Common Log Format (CLF)**:
```
호스트 식별자 사용자 [시간] "요청" 상태코드 크기
```

**Combined Log Format** (가장 일반적):
```
호스트 식별자 사용자 [시간] "요청" 상태코드 크기 "Referer" "User-Agent"
```

예시:
```
192.168.208.1 - - [27/Mar/2026:10:15:03 +0900] "GET /api/users HTTP/1.1" 200 1234 "-" "Mozilla/5.0"
```

| 필드 | 의미 | SOC 관심 포인트 |
|------|------|----------------|
| 호스트 | 클라이언트 IP | 공격 출발지 |
| 시간 | 요청 시각 | 공격 시간대 |
| 요청 | HTTP 메서드 + URI | SQLi, XSS, 경로 탐색 |
| 상태코드 | 응답 결과 | 403(차단), 500(서버 오류) |
| User-Agent | 클라이언트 정보 | 봇, 스캐너 식별 |

### 1.2 HTTP 상태코드와 보안

| 코드 | 의미 | 보안 관련 |
|------|------|----------|
| 200 | 성공 | 정상 (또는 공격 성공) |
| 301/302 | 리다이렉트 | 오픈 리다이렉트 공격 |
| 400 | 잘못된 요청 | 비정상 요청, 스캐닝 |
| 401 | 인증 필요 | 무차별 대입 |
| 403 | 금지 | 접근 차단 (WAF 등) |
| 404 | 미발견 | 디렉토리 탐색, 스캐닝 |
| 500 | 서버 오류 | SQLi 등 공격 시도 |

### 1.3 실습: 웹 로그 분석

```bash
# web 서버의 웹 로그 확인
sshpass -p1 ssh web@10.20.30.80 "ls -la /var/log/nginx/ /var/log/apache2/ /var/log/apache2/ 2>/dev/null"

# 접근 로그 최근 내용
sshpass -p1 ssh web@10.20.30.80 "tail -20 /var/log/nginx/access.log 2>/dev/null || \
  tail -20 /var/log/apache2/access.log 2>/dev/null || \
  echo '웹 로그 경로 확인 필요'"

# 에러 로그 확인
sshpass -p1 ssh web@10.20.30.80 "tail -10 /var/log/nginx/error.log 2>/dev/null || \
  tail -10 /var/log/apache2/error.log 2>/dev/null"
```

### 1.4 실습: 웹 공격 패턴 식별

```bash
# SQL Injection 시도 탐지 (UNION, SELECT, OR 1=1 등)
sshpass -p1 ssh web@10.20.30.80 "grep -iE 'union|select|or.1=1|drop.table|insert.into' /var/log/nginx/access.log 2>/dev/null | tail -10"

# XSS 시도 탐지 (<script>, alert, onerror 등)
sshpass -p1 ssh web@10.20.30.80 "grep -iE 'script|alert|onerror|onload' /var/log/nginx/access.log 2>/dev/null | tail -10"

# 디렉토리 탐색 시도 (../ 또는 %2e%2e)
sshpass -p1 ssh web@10.20.30.80 "grep -iE '\.\./|%2e%2e|/etc/passwd' /var/log/nginx/access.log 2>/dev/null | tail -10"

# 대량 404 에러 (디렉토리 스캐닝 의심)
sshpass -p1 ssh web@10.20.30.80 "grep ' 404 ' /var/log/nginx/access.log 2>/dev/null | \
  awk '{print \$1}' | sort | uniq -c | sort -rn | head -5"

# 대량 요청 IP (DDoS/스캐닝 의심)
sshpass -p1 ssh web@10.20.30.80 "awk '{print \$1}' /var/log/nginx/access.log 2>/dev/null | \
  sort | uniq -c | sort -rn | head -10"
```

### 1.5 실습: User-Agent 분석

```bash
# 비정상 User-Agent 확인 (스캐너, 봇)
sshpass -p1 ssh web@10.20.30.80 "awk -F'\"' '{print \$6}' /var/log/nginx/access.log 2>/dev/null | \
  sort | uniq -c | sort -rn | head -10"

# 알려진 스캐너 도구 탐지
sshpass -p1 ssh web@10.20.30.80 "grep -iE 'nikto|sqlmap|nmap|dirbuster|gobuster|burp' /var/log/nginx/access.log 2>/dev/null | tail -5"
```

---

## 2. Suricata IPS 로그

### 2.1 Suricata 로그 파일

| 파일 | 내용 |
|------|------|
| /var/log/suricata/fast.log | 알림 요약 (한 줄 형식) |
| /var/log/suricata/eve.json | JSON 형식 상세 로그 |
| /var/log/suricata/stats.log | 성능 통계 |

### 2.2 fast.log 형식

```
03/27/2026-10:15:03.123456  [**] [1:2001219:20] ET SCAN Potential SSH Scan [**]
  [Classification: Attempted Information Leak] [Priority: 2]
  {TCP} 10.0.0.1:54321 -> 10.20.30.1:22
```

| 필드 | 의미 |
|------|------|
| 날짜/시간 | 탐지 시각 |
| SID:Rev | 규칙 ID와 버전 |
| 메시지 | 탐지된 위협 설명 |
| Classification | 위협 분류 |
| Priority | 우선순위 (1=높음, 4=낮음) |
| 프로토콜 | TCP/UDP/ICMP |
| 출발지→목적지 | IP:Port 정보 |

### 2.3 실습: Suricata fast.log 분석

```bash
# fast.log 최근 내용
sshpass -p1 ssh secu@10.20.30.1 "tail -20 /var/log/suricata/fast.log 2>/dev/null"

# 알림 유형별 통계
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/fast.log 2>/dev/null | \
  grep -oP '\[\*\*\].*?\[\*\*\]' | sort | uniq -c | sort -rn | head -10"

# 우선순위별 통계
sshpass -p1 ssh secu@10.20.30.1 "grep -oP 'Priority: [0-9]+' /var/log/suricata/fast.log 2>/dev/null | \
  sort | uniq -c | sort -rn"

# 출발지 IP별 통계 (공격자 식별)
sshpass -p1 ssh secu@10.20.30.1 "grep -oP '\\{\\w+\\} [0-9.]+' /var/log/suricata/fast.log 2>/dev/null | \
  awk '{print \$2}' | sort | uniq -c | sort -rn | head -10"
```

### 2.4 실습: eve.json 분석

```bash
# eve.json 최근 이벤트 (JSON 형식)
sshpass -p1 ssh secu@10.20.30.1 "tail -3 /var/log/suricata/eve.json 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30"

# 이벤트 유형별 통계
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
types = Counter()
for line in sys.stdin:
    try:
        e = json.loads(line)
        types[e.get('event_type', 'unknown')] += 1
    except: pass
for t, c in types.most_common(10):
    print(f'  {t}: {c}')
\" 2>/dev/null"

# alert 이벤트만 추출
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert':
            a = e.get('alert', {})
            print(f'  [{a.get(\"severity\",\"?\")}] {a.get(\"signature\",\"\")} | {e.get(\"src_ip\",\"\")} -> {e.get(\"dest_ip\",\"\")}')
    except: pass
\" 2>/dev/null | tail -10"
```

---

## 3. nftables 방화벽 로그

### 3.1 방화벽 로그 설정

nftables는 `log` 액션을 사용하여 차단/허용 이벤트를 기록할 수 있다.

```
# nftables 규칙 예시
nft add rule inet filter input tcp dport 22 log prefix "SSH-ACCEPT: " accept
nft add rule inet filter input log prefix "DROPPED: " drop
```

### 3.2 실습: 방화벽 규칙 및 로그 확인

```bash
# 현재 방화벽 규칙 확인
sshpass -p1 ssh secu@10.20.30.1 "sudo nft list ruleset 2>/dev/null"

# 방화벽 로그 확인 (커널 로그에 기록됨)
sshpass -p1 ssh secu@10.20.30.1 "grep -i 'nft\|DROPPED\|REJECT\|firewall' /var/log/kern.log 2>/dev/null | tail -10"
sshpass -p1 ssh secu@10.20.30.1 "dmesg 2>/dev/null | grep -i 'nft\|DROP\|REJECT' | tail -10"

# iptables 로그 (레거시 환경)
sshpass -p1 ssh secu@10.20.30.1 "grep 'iptables\|nftables' /var/log/syslog 2>/dev/null | tail -10"
```

### 3.3 방화벽 로그 분석 포인트

| 분석 항목 | 목적 |
|-----------|------|
| 차단된 IP 목록 | 공격 시도 출발지 식별 |
| 차단된 포트 목록 | 포트 스캔 탐지 |
| 시간대별 차단 횟수 | DDoS 패턴 파악 |
| 동일 IP 반복 차단 | 지속적 공격 식별 |

---

## 4. 웹 WAF 로그

### 4.1 Apache+ModSecurity WAF 로그

```bash
# Apache+ModSecurity 로그 확인
sshpass -p1 ssh web@10.20.30.80 "ls -la /var/log/apache2/ 2>/dev/null"
sshpass -p1 ssh web@10.20.30.80 "journalctl -u apache2 --no-pager | tail -20 2>/dev/null | tail -20 || echo 'docker 로그 확인 필요'"

# WAF에 의해 차단된 요청
sshpass -p1 ssh web@10.20.30.80 "grep ' 403 ' /var/log/apache2/access.log 2>/dev/null | tail -10 || \
  grep ' 403 ' /var/log/nginx/access.log 2>/dev/null | tail -10"
```

---

## 5. 로그 통합 분석

### 5.1 시간 기반 상관 분석

같은 시간대에 여러 로그에서 관련 이벤트를 찾는다:

```bash
# 특정 시간대의 로그를 여러 소스에서 수집
TARGET_TIME="Mar 27 10:1"

echo "=== auth.log ==="
sshpass -p1 ssh opsclaw@10.20.30.201 "grep '$TARGET_TIME' /var/log/auth.log 2>/dev/null | head -5"

echo "=== Suricata ==="
sshpass -p1 ssh secu@10.20.30.1 "grep '03/27/2026-10:1' /var/log/suricata/fast.log 2>/dev/null | head -5"

echo "=== 웹 로그 ==="
sshpass -p1 ssh web@10.20.30.80 "grep '27/Mar/2026:10:1' /var/log/nginx/access.log 2>/dev/null | head -5"
```

### 5.2 IP 기반 상관 분석

특정 IP의 활동을 여러 로그에서 추적한다:

```bash
SUSPECT_IP="192.168.208.1"  # 의심 IP (실제 발견된 IP로 변경)

echo "=== $SUSPECT_IP 활동 추적 ==="

echo "[SSH 시도]"
sshpass -p1 ssh opsclaw@10.20.30.201 "grep '$SUSPECT_IP' /var/log/auth.log 2>/dev/null | tail -5"

echo "[IPS 탐지]"
sshpass -p1 ssh secu@10.20.30.1 "grep '$SUSPECT_IP' /var/log/suricata/fast.log 2>/dev/null | tail -5"

echo "[웹 접근]"
sshpass -p1 ssh web@10.20.30.80 "grep '$SUSPECT_IP' /var/log/nginx/access.log 2>/dev/null | tail -5"
```

---

## 6. 로그 분석 도구

### 6.1 커맨드라인 도구 요약

| 도구 | 용도 | 예시 |
|------|------|------|
| grep | 패턴 검색 | `grep 'Failed' auth.log` |
| awk | 필드 추출/처리 | `awk '{print $1}' access.log` |
| sort/uniq | 정렬/중복 제거/통계 | `sort \| uniq -c \| sort -rn` |
| wc | 행 수 세기 | `wc -l` |
| cut | 필드 분리 | `cut -d' ' -f1` |
| jq/python3 | JSON 파싱 | `python3 -m json.tool` |

### 6.2 자주 쓰는 조합

```bash
# Top 10 접근 IP
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10

# 시간대별 요청 수
awk '{print $4}' access.log | cut -d: -f1,2 | sort | uniq -c | sort -rn

# 특정 상태코드 필터링
awk '$9 == 403 {print $1, $7}' access.log | sort | uniq -c | sort -rn
```

---

## 7. 핵심 정리

1. **웹 로그** = 접근 IP, 요청 URI, 상태코드, User-Agent 분석
2. **Suricata** = fast.log(요약), eve.json(상세), SID/Priority 기반 분류
3. **방화벽 로그** = 차단 이벤트, 포트 스캔 탐지
4. **상관 분석** = 시간/IP 기준으로 여러 로그를 연결
5. **공격 패턴** = SQLi, XSS, 디렉토리 탐색, 스캐닝, 무차별 대입

---

## 과제

1. web 서버의 웹 로그에서 공격 시도를 5가지 이상 찾아 보고하시오
2. Suricata fast.log에서 상위 5개 알림 유형을 분석하시오
3. 특정 IP를 선택하여 SSH/IPS/웹 로그에서 해당 IP의 전체 활동을 추적하시오

---

## 참고 자료

- Apache HTTP Server Log Files Documentation
- Suricata Documentation: EVE JSON Output
- nftables Logging Guide


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

**Q1.** 이번 주차 "Week 03: 로그 이해 (2) - 네트워크/웹 로그"의 핵심 목적은 무엇인가?
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


