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
