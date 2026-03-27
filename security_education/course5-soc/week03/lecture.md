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
sshpass -p1 ssh user@192.168.208.151 "ls -la /var/log/nginx/ /var/log/apache2/ /var/log/bunkerweb/ 2>/dev/null"

# 접근 로그 최근 내용
sshpass -p1 ssh user@192.168.208.151 "tail -20 /var/log/nginx/access.log 2>/dev/null || \
  tail -20 /var/log/bunkerweb/access.log 2>/dev/null || \
  echo '웹 로그 경로 확인 필요'"

# 에러 로그 확인
sshpass -p1 ssh user@192.168.208.151 "tail -10 /var/log/nginx/error.log 2>/dev/null || \
  tail -10 /var/log/bunkerweb/error.log 2>/dev/null"
```

### 1.4 실습: 웹 공격 패턴 식별

```bash
# SQL Injection 시도 탐지 (UNION, SELECT, OR 1=1 등)
sshpass -p1 ssh user@192.168.208.151 "grep -iE 'union|select|or.1=1|drop.table|insert.into' /var/log/nginx/access.log 2>/dev/null | tail -10"

# XSS 시도 탐지 (<script>, alert, onerror 등)
sshpass -p1 ssh user@192.168.208.151 "grep -iE 'script|alert|onerror|onload' /var/log/nginx/access.log 2>/dev/null | tail -10"

# 디렉토리 탐색 시도 (../ 또는 %2e%2e)
sshpass -p1 ssh user@192.168.208.151 "grep -iE '\.\./|%2e%2e|/etc/passwd' /var/log/nginx/access.log 2>/dev/null | tail -10"

# 대량 404 에러 (디렉토리 스캐닝 의심)
sshpass -p1 ssh user@192.168.208.151 "grep ' 404 ' /var/log/nginx/access.log 2>/dev/null | \
  awk '{print \$1}' | sort | uniq -c | sort -rn | head -5"

# 대량 요청 IP (DDoS/스캐닝 의심)
sshpass -p1 ssh user@192.168.208.151 "awk '{print \$1}' /var/log/nginx/access.log 2>/dev/null | \
  sort | uniq -c | sort -rn | head -10"
```

### 1.5 실습: User-Agent 분석

```bash
# 비정상 User-Agent 확인 (스캐너, 봇)
sshpass -p1 ssh user@192.168.208.151 "awk -F'\"' '{print \$6}' /var/log/nginx/access.log 2>/dev/null | \
  sort | uniq -c | sort -rn | head -10"

# 알려진 스캐너 도구 탐지
sshpass -p1 ssh user@192.168.208.151 "grep -iE 'nikto|sqlmap|nmap|dirbuster|gobuster|burp' /var/log/nginx/access.log 2>/dev/null | tail -5"
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
sshpass -p1 ssh user@192.168.208.150 "tail -20 /var/log/suricata/fast.log 2>/dev/null"

# 알림 유형별 통계
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/fast.log 2>/dev/null | \
  grep -oP '\[\*\*\].*?\[\*\*\]' | sort | uniq -c | sort -rn | head -10"

# 우선순위별 통계
sshpass -p1 ssh user@192.168.208.150 "grep -oP 'Priority: [0-9]+' /var/log/suricata/fast.log 2>/dev/null | \
  sort | uniq -c | sort -rn"

# 출발지 IP별 통계 (공격자 식별)
sshpass -p1 ssh user@192.168.208.150 "grep -oP '\\{\\w+\\} [0-9.]+' /var/log/suricata/fast.log 2>/dev/null | \
  awk '{print \$2}' | sort | uniq -c | sort -rn | head -10"
```

### 2.4 실습: eve.json 분석

```bash
# eve.json 최근 이벤트 (JSON 형식)
sshpass -p1 ssh user@192.168.208.150 "tail -3 /var/log/suricata/eve.json 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30"

# 이벤트 유형별 통계
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
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
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
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
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null"

# 방화벽 로그 확인 (커널 로그에 기록됨)
sshpass -p1 ssh user@192.168.208.150 "grep -i 'nft\|DROPPED\|REJECT\|firewall' /var/log/kern.log 2>/dev/null | tail -10"
sshpass -p1 ssh user@192.168.208.150 "dmesg 2>/dev/null | grep -i 'nft\|DROP\|REJECT' | tail -10"

# iptables 로그 (레거시 환경)
sshpass -p1 ssh user@192.168.208.150 "grep 'iptables\|nftables' /var/log/syslog 2>/dev/null | tail -10"
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

### 4.1 BunkerWeb WAF 로그

```bash
# BunkerWeb 로그 확인
sshpass -p1 ssh user@192.168.208.151 "ls -la /var/log/bunkerweb/ 2>/dev/null"
sshpass -p1 ssh user@192.168.208.151 "docker logs bunkerweb 2>/dev/null | tail -20 || echo 'docker 로그 확인 필요'"

# WAF에 의해 차단된 요청
sshpass -p1 ssh user@192.168.208.151 "grep ' 403 ' /var/log/bunkerweb/access.log 2>/dev/null | tail -10 || \
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
sshpass -p1 ssh user@192.168.208.142 "grep '$TARGET_TIME' /var/log/auth.log 2>/dev/null | head -5"

echo "=== Suricata ==="
sshpass -p1 ssh user@192.168.208.150 "grep '03/27/2026-10:1' /var/log/suricata/fast.log 2>/dev/null | head -5"

echo "=== 웹 로그 ==="
sshpass -p1 ssh user@192.168.208.151 "grep '27/Mar/2026:10:1' /var/log/nginx/access.log 2>/dev/null | head -5"
```

### 5.2 IP 기반 상관 분석

특정 IP의 활동을 여러 로그에서 추적한다:

```bash
SUSPECT_IP="192.168.208.1"  # 의심 IP (실제 발견된 IP로 변경)

echo "=== $SUSPECT_IP 활동 추적 ==="

echo "[SSH 시도]"
sshpass -p1 ssh user@192.168.208.142 "grep '$SUSPECT_IP' /var/log/auth.log 2>/dev/null | tail -5"

echo "[IPS 탐지]"
sshpass -p1 ssh user@192.168.208.150 "grep '$SUSPECT_IP' /var/log/suricata/fast.log 2>/dev/null | tail -5"

echo "[웹 접근]"
sshpass -p1 ssh user@192.168.208.151 "grep '$SUSPECT_IP' /var/log/nginx/access.log 2>/dev/null | tail -5"
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
