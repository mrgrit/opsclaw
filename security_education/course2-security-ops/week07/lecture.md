# Week 07: BunkerWeb WAF — 웹 애플리케이션 방화벽

## 학습 목표

- WAF의 역할과 동작 원리를 이해한다
- ModSecurity Core Rule Set (CRS)의 구조를 파악한다
- 커스텀 WAF 룰을 작성할 수 있다
- 오탐 예외 처리를 수행할 수 있다
- curl을 사용하여 WAF 동작을 테스트할 수 있다

---

## 1. WAF란?

WAF(Web Application Firewall)는 HTTP/HTTPS 트래픽을 검사하여 웹 공격을 차단하는 보안 솔루션이다.

**네트워크 방화벽 vs WAF:**

| 구분 | 네트워크 방화벽 (nftables) | WAF (BunkerWeb) |
|------|---------------------------|-----------------|
| 계층 | L3/L4 (IP, 포트) | **L7 (HTTP 내용)** |
| 검사 대상 | IP, 포트, 프로토콜 | URL, 헤더, 쿠키, 본문 |
| 탐지 가능 | 포트 스캔, DoS | **SQL Injection, XSS, CSRF** |
| 배치 위치 | 네트워크 경계 | 웹 서버 앞단 |

---

## 2. BunkerWeb 구조

BunkerWeb은 Nginx + ModSecurity 기반의 오픈소스 WAF이다.

```
    클라이언트 요청
         │
         ▼
    ┌──────────┐
    │ BunkerWeb │ (Nginx + ModSecurity)
    │   :80     │
    └────┬─────┘
         │ ModSecurity CRS 검사
         │  ├─ 정상 → 통과
         │  └─ 공격 → 차단 (403)
         ▼
    ┌──────────┐
    │ JuiceShop│ (백엔드 앱)
    │   :3000  │
    └──────────┘
```

실습 환경: web 서버(10.20.30.80)

---

## 3. 실습 환경 접속

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80
```

### 3.1 BunkerWeb 상태 확인

```bash
echo 1 | sudo -S docker ps | grep bunkerweb
```

**예상 출력:**
```
abc123  bunkerio/bunkerweb:1.5  ...  Up 2 days  0.0.0.0:80->8080/tcp  bunkerweb
```

### 3.2 ModSecurity 활성화 확인

```bash
echo 1 | sudo -S docker exec bunkerweb cat /etc/nginx/modsecurity.conf 2>/dev/null | head -10
```

또는 환경 변수 확인:

```bash
echo 1 | sudo -S docker inspect bunkerweb | python3 -c "
import sys, json
data = json.load(sys.stdin)
env = data[0]['Config']['Env']
for e in sorted(env):
    if 'MODSEC' in e.upper() or 'WAF' in e.upper() or 'SECURITY' in e.upper():
        print(e)
"
```

---

## 4. ModSecurity Core Rule Set (CRS)

CRS는 OWASP에서 관리하는 범용 WAF 룰셋이다.

### 4.1 CRS 구조

| 파일 범위 | 내용 |
|-----------|------|
| 900-xxx | 설정/초기화 |
| 910-xxx | IP 평판 검사 |
| 920-xxx | 프로토콜 위반 검사 |
| 930-xxx | 로컬 파일 포함 (LFI) |
| 931-xxx | 원격 파일 포함 (RFI) |
| 932-xxx | 원격 코드 실행 (RCE) |
| 933-xxx | PHP 공격 |
| 934-xxx | Node.js 공격 |
| 941-xxx | **XSS (Cross-Site Scripting)** |
| 942-xxx | **SQL Injection** |
| 943-xxx | 세션 고정 |
| 944-xxx | Java 공격 |
| 949-xxx | 인바운드 차단 판정 |
| 950-xxx | 아웃바운드 (데이터 유출) |

### 4.2 Anomaly Scoring

CRS는 **이상 점수(Anomaly Score)** 방식으로 동작한다:

1. 각 룰이 매칭되면 점수를 누적한다
2. 총 점수가 임계값을 초과하면 차단한다

| 심각도 | 점수 | 예 |
|--------|------|---|
| CRITICAL | 5 | SQL Injection |
| ERROR | 4 | 원격 코드 실행 |
| WARNING | 3 | 의심스러운 문자열 |
| NOTICE | 2 | 프로토콜 위반 |

**기본 차단 임계값: 5점** (CRITICAL 1개로 즉시 차단)

---

## 5. WAF 동작 테스트

secu 서버 또는 로컬에서 web 서버로 공격 테스트를 수행한다:

### 5.1 정상 요청

```bash
# 정상 요청 (200 OK)
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://10.20.30.80/
```

**예상 출력:**
```
HTTP 200
```

### 5.2 SQL Injection 테스트

```bash
# SQL Injection (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/?id=1%20OR%201=1"
```

**예상 출력:**
```
HTTP 403
```

### 5.3 XSS 테스트

```bash
# XSS (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/?q=<script>alert(1)</script>"
```

**예상 출력:**
```
HTTP 403
```

### 5.4 디렉터리 트래버설 테스트

```bash
# Path Traversal (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/../../etc/passwd"
```

### 5.5 명령 주입 테스트

```bash
# Command Injection (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/?cmd=;cat%20/etc/passwd"
```

### 5.6 User-Agent 스캐너 테스트

```bash
# 스캐너 User-Agent (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -A "sqlmap/1.0" \
  "http://10.20.30.80/"
```

### 5.7 차단 응답 확인

```bash
# 차단 시 응답 본문 확인
curl -s "http://10.20.30.80/?id=1%20UNION%20SELECT%201"
```

**예상 출력:**
```html
<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
</body>
</html>
```

---

## 6. WAF 로그 분석

### 6.1 ModSecurity 감사 로그

```bash
# BunkerWeb 컨테이너 내 로그 확인
echo 1 | sudo -S docker exec bunkerweb cat /var/log/bunkerweb/error.log | \
  grep "ModSecurity" | tail -10
```

### 6.2 Nginx 접근 로그

```bash
echo 1 | sudo -S docker exec bunkerweb cat /var/log/bunkerweb/access.log | tail -20
```

### 6.3 차단된 요청 필터링

```bash
# 403 응답만 추출
echo 1 | sudo -S docker exec bunkerweb cat /var/log/bunkerweb/access.log | \
  awk '$9 == 403' | tail -10
```

---

## 7. 커스텀 WAF 룰

### 7.1 ModSecurity 룰 문법

```
SecRule VARIABLES "OPERATOR" "ACTIONS"
```

| 부분 | 설명 | 예시 |
|------|------|------|
| VARIABLES | 검사 대상 | `REQUEST_URI`, `ARGS`, `REQUEST_HEADERS` |
| OPERATOR | 비교 연산 | `@rx` (정규식), `@contains`, `@eq` |
| ACTIONS | 동작 | `deny`, `log`, `id:xxx` |

### 7.2 커스텀 룰 작성

BunkerWeb에서 커스텀 ModSecurity 룰을 추가하는 방법:

```bash
# 커스텀 룰 파일 생성
echo 1 | sudo -S tee /tmp/custom-waf-rules.conf << 'EOF'
# 관리자 페이지 외부 접근 차단
SecRule REQUEST_URI "@beginsWith /admin" \
  "id:10001,phase:1,deny,status:403,log,msg:'Admin access blocked'"

# 특정 파일 확장자 업로드 차단
SecRule FILES_NAMES "@rx \.(exe|bat|cmd|sh|php)$" \
  "id:10002,phase:2,deny,status:403,log,msg:'Dangerous file upload blocked'"

# 요청 본문 크기 제한 (10MB)
SecRule REQUEST_BODY_LENGTH "@gt 10485760" \
  "id:10003,phase:2,deny,status:413,log,msg:'Request body too large'"

# 특정 국가 차단 (GeoIP 필요)
# SecRule GEO:COUNTRY_CODE "@rx ^(CN|RU|KP)$" \
#   "id:10004,phase:1,deny,status:403,log,msg:'Country blocked'"
EOF
```

### 7.3 BunkerWeb에 룰 적용

BunkerWeb은 Docker 환경 변수 또는 설정 파일로 커스텀 룰을 적용한다:

```bash
# BunkerWeb 설정 디렉터리 확인
echo 1 | sudo -S ls /opt/bunkerweb/configs/ 2>/dev/null || \
echo 1 | sudo -S ls /etc/bunkerweb/ 2>/dev/null || \
echo "설정 디렉터리를 확인하세요"
```

---

## 8. 예외 처리 (False Positive)

### 8.1 예외가 필요한 경우

- 정상적인 API 요청이 SQL Injection으로 오인될 때
- 관리 도구의 요청이 차단될 때
- 특정 경로에서 파일 업로드가 필요할 때

### 8.2 예외 룰 작성

```bash
# 특정 경로에서 SQL Injection 룰 비활성화
echo 1 | sudo -S tee /tmp/waf-exceptions.conf << 'EOF'
# /api/ 경로에서 SQL Injection 룰 예외
SecRule REQUEST_URI "@beginsWith /api/" \
  "id:10010,phase:1,pass,nolog,ctl:ruleRemoveById=942100-942999"

# 특정 파라미터에서 XSS 룰 예외
SecRule ARGS_NAMES "@eq search_query" \
  "id:10011,phase:1,pass,nolog,ctl:ruleRemoveTargetById=941100-941999;ARGS:search_query"

# 특정 IP에서 모든 룰 예외 (모니터링 서버)
SecRule REMOTE_ADDR "@eq 10.20.30.100" \
  "id:10012,phase:1,pass,nolog,ctl:ruleEngine=Off"
EOF
```

### 8.3 예외 적용 시 주의사항

1. **최소 권한 원칙**: 가능한 좁은 범위로 예외를 설정한다
2. **특정 룰 ID만 제외**: 전체 비활성화보다 특정 ID만 제외한다
3. **로그 기록 유지**: 예외 적용해도 로그는 남기는 것을 권장한다
4. **정기적 재검토**: 예외가 여전히 필요한지 주기적으로 확인한다

---

## 9. Anomaly Score 조정

### 9.1 차단 임계값 변경

```bash
# 임계값을 10으로 높이기 (더 관대하게)
# BunkerWeb 환경 변수 방식:
# MODSECURITY_INBOUND_ANOMALY_SCORE_THRESHOLD=10
```

### 9.2 Paranoia Level 조정

| 레벨 | 설명 | 오탐 가능성 |
|------|------|-------------|
| PL 1 | 기본 (보수적) | 낮음 |
| PL 2 | 추가 룰 활성화 | 중간 |
| PL 3 | 공격적 탐지 | 높음 |
| PL 4 | 최대 탐지 | 매우 높음 |

```bash
# Paranoia Level 설정
# MODSECURITY_SEC_RULE_ENGINE=On
# CRS_PARANOIA_LEVEL=1
```

---

## 10. 종합 테스트 스크립트

다양한 공격을 한번에 테스트하는 스크립트:

```bash
cat << 'TESTEOF' > /tmp/waf_test.sh
#!/bin/bash
TARGET="http://10.20.30.80"
echo "=== WAF 테스트 시작 ==="

tests=(
  "정상 요청|/"
  "SQL Injection (OR)|/?id=1 OR 1=1"
  "SQL Injection (UNION)|/?id=1 UNION SELECT 1,2,3"
  "XSS (script)|/?q=<script>alert(1)</script>"
  "XSS (onerror)|/?q=<img src=x onerror=alert(1)>"
  "LFI (traversal)|/../../etc/passwd"
  "RCE (cmd injection)|/?cmd=;ls -la"
  "Scanner (sqlmap)|/ -A sqlmap/1.0"
)

for test in "${tests[@]}"; do
  IFS='|' read -r name path <<< "$test"
  if [[ "$name" == *"Scanner"* ]]; then
    code=$(curl -s -o /dev/null -w "%{http_code}" -A "sqlmap/1.0" "${TARGET}/")
  else
    code=$(curl -s -o /dev/null -w "%{http_code}" "${TARGET}${path}")
  fi
  if [ "$code" == "403" ]; then
    result="BLOCKED"
  elif [ "$code" == "200" ]; then
    result="PASSED"
  else
    result="HTTP $code"
  fi
  printf "%-30s %s (%s)\n" "$name" "$result" "$code"
done

echo "=== 테스트 완료 ==="
TESTEOF
chmod +x /tmp/waf_test.sh
bash /tmp/waf_test.sh
```

**예상 출력:**
```
=== WAF 테스트 시작 ===
정상 요청                       PASSED (200)
SQL Injection (OR)             BLOCKED (403)
SQL Injection (UNION)          BLOCKED (403)
XSS (script)                   BLOCKED (403)
XSS (onerror)                  BLOCKED (403)
LFI (traversal)                BLOCKED (403)
RCE (cmd injection)            BLOCKED (403)
Scanner (sqlmap)               BLOCKED (403)
=== 테스트 완료 ===
```

---

## 11. 실습 과제

### 과제 1: WAF 동작 확인

1. 위 테스트 스크립트를 실행하여 모든 공격이 차단되는지 확인하라
2. 차단된 요청의 로그를 분석하라
3. 응답 본문에 어떤 내용이 포함되어 있는지 확인하라

### 과제 2: 커스텀 룰 작성

1. `/backup` 경로 접근을 차단하는 룰을 작성하라
2. `.sql` 파일 다운로드를 차단하는 룰을 작성하라
3. 작성한 룰을 테스트하라

### 과제 3: 예외 처리

1. `/api/search` 경로에서 `q` 파라미터의 XSS 룰을 예외 처리하라
2. 예외 처리 후 정상적인 검색이 가능한지 확인하라
3. 동시에 다른 경로에서는 여전히 XSS가 차단되는지 확인하라

---

## 12. 핵심 정리

| 개념 | 설명 |
|------|------|
| WAF | L7 계층 웹 공격 차단 |
| ModSecurity | 오픈소스 WAF 엔진 |
| CRS | OWASP 핵심 룰셋 |
| Anomaly Score | 이상 점수 누적 방식 |
| Paranoia Level | 탐지 민감도 (1~4) |
| SecRule | ModSecurity 룰 문법 |
| ctl:ruleRemoveById | 특정 룰 예외 처리 |
| 403 Forbidden | WAF 차단 응답 |

---

## 다음 주 예고

Week 08은 **중간고사**이다:
- nftables 방화벽 + Suricata IPS를 조합하여
- 실제 보안 인프라를 구성하는 실기 시험
