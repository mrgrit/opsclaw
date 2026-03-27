# Week 06: Suricata IPS (3) — 운영 (상세 버전)

## 학습 목표
- eve.json과 fast.log를 분석할 수 있다
- Suricata 성능을 모니터링하고 튜닝할 수 있다
- 오탐(False Positive)을 식별하고 관리할 수 있다
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


# 본 강의 내용

# Week 06: Suricata IPS (3) — 운영

## 학습 목표

- eve.json과 fast.log를 분석할 수 있다
- Suricata 성능을 모니터링하고 튜닝할 수 있다
- 오탐(False Positive)을 식별하고 관리할 수 있다

---

## 1. 로그 파일 구조

| 로그 파일 | 형식 | 용도 |
|-----------|------|------|
| `eve.json` | JSON | **핵심 로그** — 모든 이벤트를 구조화된 형식으로 기록 |
| `fast.log` | 텍스트 | 알림 한 줄 요약 (빠른 확인용) |
| `stats.log` | 텍스트 | 엔진 통계 |
| `suricata.log` | 텍스트 | 엔진 상태/오류 |

---

## 2. 실습 환경 접속

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1
```

---

## 3. fast.log 분석

### 3.1 기본 확인

```bash
echo 1 | sudo -S tail -20 /var/log/suricata/fast.log
```

**예상 출력:**
```
03/27/2026-10:15:22.456789  [**] [1:2024897:4] ET WEB_SERVER SQL Injection Attempt [**] [Classification: Web Application Attack] [Priority: 1] {TCP} 10.20.30.80:45678 -> 10.20.30.1:80
03/27/2026-10:15:23.123456  [**] [1:9000010:1] CUSTOM - SQL Injection in URI [**] [Classification: Web Application Attack] [Priority: 1] {TCP} 10.20.30.80:45679 -> 10.20.30.1:80
```

**각 필드 의미:**

```
날짜-시간  [**] [gid:sid:rev] 메시지 [**] [분류] [우선순위] {프로토콜} 출발지 -> 목적지
```

### 3.2 빈도 분석

```bash
# 가장 많이 발생한 알림 TOP 10
echo 1 | sudo -S cat /var/log/suricata/fast.log | \
  awk -F'\\]' '{print $2}' | sort | uniq -c | sort -rn | head -10
```

### 3.3 특정 SID 검색

```bash
# SID 9000010 (SQL Injection) 알림만 확인
echo 1 | sudo -S grep "9000010" /var/log/suricata/fast.log | tail -5
```

### 3.4 출발지 IP별 알림 수

```bash
echo 1 | sudo -S cat /var/log/suricata/fast.log | \
  grep -oP '\d+\.\d+\.\d+\.\d+:\d+ ->' | \
  awk -F: '{print $1}' | sort | uniq -c | sort -rn | head -10
```

---

## 4. eve.json 분석

eve.json은 구조화된 JSON 형식으로, 훨씬 풍부한 정보를 제공한다.

### 4.1 이벤트 타입 확인

```bash
# 이벤트 타입별 개수
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "
import sys, json
types = {}
for line in sys.stdin:
    try:
        e = json.loads(line)
        t = e.get('event_type','unknown')
        types[t] = types.get(t,0) + 1
    except: pass
for t,c in sorted(types.items(), key=lambda x:-x[1]):
    print(f'{c:>8}  {t}')
"
```

**예상 출력:**
```
   15234  flow
    3456  http
     892  dns
     234  alert
      45  tls
      12  stats
```

### 4.2 알림(alert) 이벤트 상세 보기

```bash
# 최근 알림 5개를 보기 좋게 출력
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "
import sys, json
alerts = []
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert':
            alerts.append(e)
    except: pass
for a in alerts[-5:]:
    al = a['alert']
    print(f\"[{a['timestamp']}] SID:{al['signature_id']} {al['signature']}\")
    print(f\"  {a.get('src_ip','?')}:{a.get('src_port','?')} -> {a.get('dest_ip','?')}:{a.get('dest_port','?')}\")
    print(f\"  Severity: {al.get('severity','?')} Category: {al.get('category','?')}\")
    if 'http' in a:
        print(f\"  HTTP: {a['http'].get('http_method','?')} {a['http'].get('hostname','?')}{a['http'].get('url','?')}\")
    print()
"
```

**예상 출력:**
```
[2026-03-27T10:15:22.456789+0000] SID:9000010 CUSTOM - SQL Injection in URI (union select)
  10.20.30.80:45678 -> 10.20.30.1:80
  Severity: 1 Category: Web Application Attack
  HTTP: GET 10.20.30.80/?q=1 union select 1,2,3
```

### 4.3 jq를 사용한 분석

```bash
# jq가 설치되어 있는 경우
echo 1 | sudo -S tail -100 /var/log/suricata/eve.json | \
  jq 'select(.event_type=="alert") | {
    time: .timestamp,
    sig: .alert.signature,
    sid: .alert.signature_id,
    src: .src_ip,
    dst: .dest_ip,
    severity: .alert.severity
  }' 2>/dev/null | head -30
```

### 4.4 HTTP 트래픽 분석

```bash
# HTTP 요청 로그 (공격과 무관한 정상 트래픽 포함)
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'http':
            h = e['http']
            print(f\"{e['timestamp'][:19]} {h.get('http_method','?'):6} {h.get('hostname','?')}{h.get('url','?')[:80]} [{h.get('status','-')}]\")
    except: pass
" | tail -20
```

---

## 5. 성능 모니터링

### 5.1 Suricata 엔진 통계

```bash
echo 1 | sudo -S cat /var/log/suricata/stats.log | tail -40
```

**주요 지표:**

| 지표 | 설명 | 정상 범위 |
|------|------|-----------|
| `capture.kernel_packets` | 커널에서 받은 패킷 | 증가 추세 |
| `capture.kernel_drops` | **커널 드롭** | 0에 가까워야 함 |
| `decoder.pkts` | 디코딩 패킷 | 증가 추세 |
| `detect.alert` | 탐지 알림 수 | 환경에 따라 다름 |
| `flow.memuse` | 플로우 메모리 사용량 | 설정된 max 이하 |
| `tcp.sessions` | TCP 세션 수 | 환경에 따라 다름 |

### 5.2 드롭 확인 (가장 중요)

```bash
# 커널 드롭 확인
echo 1 | sudo -S cat /var/log/suricata/stats.log | grep "kernel_drops" | tail -5
```

**예상 출력 (정상):**
```
capture.kernel_drops             | Total: 0        | Per min: 0
```

> 커널 드롭이 발생하면 패킷을 분석하지 못하고 놓치는 것이다. **즉시 튜닝 필요**.

### 5.3 실시간 통계 (eve.json)

```bash
echo 1 | sudo -S tail -f /var/log/suricata/eve.json | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'stats':
            s = e['stats']
            cap = s.get('capture',{})
            det = s.get('detect',{})
            print(f\"Pkts: {cap.get('kernel_packets',0):>10} Drops: {cap.get('kernel_drops',0):>6} Alerts: {det.get('alert',0):>6}\")
    except: pass
" &
```

Ctrl+C로 종료한다.

---

## 6. 성능 튜닝

### 6.1 NFQUEUE 설정 최적화

`/etc/suricata/suricata.yaml`:

```yaml
nfq:
  mode: accept
  batchcount: 20       # 한 번에 처리할 패킷 수 (기본 1, 늘리면 성능 향상)
  fail-open: yes
```

### 6.2 메모리 설정

```yaml
# 플로우 관련 메모리
flow:
  memcap: 128mb        # 플로우 메모리 상한
  hash-size: 65536
  prealloc: 10000

# 스트림 메모리
stream:
  memcap: 256mb
  reassembly:
    memcap: 256mb
    depth: 1mb         # 재조합 깊이 (줄이면 성능 향상)
```

### 6.3 룰 프로파일링

어떤 룰이 성능에 영향을 주는지 확인:

```yaml
# suricata.yaml에 추가
profiling:
  rules:
    enabled: yes
    filename: rule_perf.log
    sort: avgticks
    limit: 20
```

```bash
# 프로파일링 결과 확인 (재시작 후)
echo 1 | sudo -S cat /var/log/suricata/rule_perf.log | head -30
```

### 6.4 불필요한 프로토콜 파서 비활성화

사용하지 않는 프로토콜 파서를 끄면 성능이 향상된다:

```yaml
app-layer:
  protocols:
    ftp:
      enabled: no      # FTP 미사용 시
    smtp:
      enabled: no      # SMTP 미사용 시
    smb:
      enabled: no
```

---

## 7. 오탐(False Positive) 관리

### 7.1 오탐이란?

| 용어 | 의미 | 예시 |
|------|------|------|
| True Positive (TP) | 실제 공격을 탐지 | SQL Injection 차단 |
| **False Positive (FP)** | **정상을 공격으로 오인** | 검색어가 SQL 문법 포함 |
| False Negative (FN) | 공격을 탐지 못함 | 우회 공격 |
| True Negative (TN) | 정상을 정상으로 판단 | 일반 웹 접근 |

### 7.2 오탐 식별

```bash
# 가장 많이 발생하는 알림 확인 (오탐 후보)
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "
import sys, json
sigs = {}
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert':
            key = f\"{e['alert']['signature_id']}:{e['alert']['signature']}\"
            sigs[key] = sigs.get(key,0) + 1
    except: pass
for s,c in sorted(sigs.items(), key=lambda x:-x[1])[:10]:
    print(f'{c:>6}  {s}')
"
```

### 7.3 오탐 처리 방법

**방법 1: 룰 비활성화 (suricata-update)**

```bash
# 특정 SID 비활성화
echo "2024897" | sudo tee -a /etc/suricata/disable.conf
echo 1 | sudo -S suricata-update
echo 1 | sudo -S kill -USR2 $(pidof suricata)
```

**방법 2: suppress (특정 조건에서만 무시)**

`/etc/suricata/threshold.config`:

```bash
# 특정 IP에서 오는 특정 SID 무시
echo 'suppress gen_id 1, sig_id 2024897, track by_src, ip 10.20.30.80' | \
  sudo tee -a /etc/suricata/threshold.config
```

**방법 3: pass 룰 (특정 트래픽 허용)**

```bash
# 모니터링 도구의 트래픽을 허용
echo 'pass http 10.20.30.100 any -> any any (msg:"Allow SIEM health check"; content:"/health"; http.uri; sid:9000099; rev:1;)' | \
  sudo tee -a /etc/suricata/rules/local.rules
```

> pass 룰은 다른 룰보다 먼저 평가된다.

### 7.4 오탐 관리 워크플로우

```
1. 빈발 알림 목록 작성
2. 각 알림의 실제 트래픽 확인 (eve.json)
3. 정상 트래픽인지 공격인지 판단
4. 오탐이면:
   a. 특정 조건만 해당 → suppress
   b. 룰 자체가 불필요 → disable
   c. 일부만 허용 → pass 룰
5. 변경 후 모니터링
```

---

## 8. 로그 로테이션

### 8.1 logrotate 설정

```bash
echo 1 | sudo -S cat /etc/logrotate.d/suricata 2>/dev/null
```

설정이 없으면 생성:

```bash
echo 1 | sudo -S tee /etc/logrotate.d/suricata << 'EOF'
/var/log/suricata/*.log /var/log/suricata/*.json {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 640 root root
    postrotate
        /bin/kill -HUP $(cat /var/run/suricata.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF
```

### 8.2 디스크 사용량 확인

```bash
echo 1 | sudo -S du -sh /var/log/suricata/
echo 1 | sudo -S ls -lh /var/log/suricata/
```

---

## 9. 운영 체크리스트

일일 점검:

```bash
# 1. 서비스 상태
echo 1 | sudo -S systemctl is-active suricata

# 2. 커널 드롭 확인
echo 1 | sudo -S grep "kernel_drops" /var/log/suricata/stats.log | tail -1

# 3. 최근 24시간 알림 수
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "
import sys, json
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(hours=24)
cnt = 0
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert':
            cnt += 1
    except: pass
print(f'최근 알림 수: {cnt}')
"

# 4. 디스크 사용량
echo 1 | sudo -S du -sh /var/log/suricata/

# 5. 높은 심각도 알림
echo 1 | sudo -S cat /var/log/suricata/eve.json | \
  python3 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'alert' and e['alert'].get('severity',4) <= 2:
            print(f\"{e['timestamp'][:19]} [{e['alert']['severity']}] {e['alert']['signature']}\")
    except: pass
" | tail -10
```

---

## 10. 실습 과제

### 과제 1: 로그 분석

1. fast.log에서 가장 많이 발생한 알림 TOP 5를 구하라
2. eve.json에서 severity 1인 알림만 출력하라
3. 특정 출발지 IP의 알림 이력을 추적하라

### 과제 2: 오탐 처리

1. 실습 중 발생한 알림 중 오탐을 식별하라
2. suppress 설정으로 오탐을 처리하라
3. 처리 후 알림이 발생하지 않는 것을 확인하라

### 과제 3: 성능 확인

1. stats.log에서 커널 드롭 수를 확인하라
2. 현재 메모리 사용량을 확인하라
3. 불필요한 프로토콜 파서를 비활성화하라

---

## 11. 핵심 정리

| 개념 | 설명 |
|------|------|
| eve.json | 구조화된 JSON 이벤트 로그 (핵심) |
| fast.log | 한 줄 요약 알림 로그 |
| kernel_drops | 패킷 드롭 수 (0이어야 정상) |
| False Positive | 정상을 공격으로 오인 |
| suppress | 특정 조건에서 알림 무시 |
| disable.conf | 룰 비활성화 |
| pass 룰 | 특정 트래픽 허용 |
| batchcount | NFQUEUE 배치 크기 (성능) |
| logrotate | 로그 자동 순환 |

---

## 다음 주 예고

Week 07에서는 BunkerWeb WAF를 다룬다:
- ModSecurity Core Rule Set (CRS)
- 커스텀 WAF 룰
- 예외 처리
- web 서버(10.20.30.80)에서 실습


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 2)

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

**Q1.** 이번 주차 "Week 06: Suricata IPS (3) — 운영"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **보안 솔루션 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 방화벽/IPS의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **SIEM 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

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

