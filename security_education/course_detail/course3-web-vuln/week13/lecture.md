# Week 13: 자동화 점검 도구 활용 (상세 버전)

## 학습 목표
- OWASP ZAP을 사용한 자동 취약점 스캔을 수행한다
- nikto를 활용한 웹서버 보안 점검을 수행한다
- 자동화 도구의 한계와 수동 점검의 필요성을 이해한다
- 스캔 결과를 분석하고 오탐을 필터링한다
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

## 용어 해설 (웹취약점 점검 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **취약점 점검** | Vulnerability Assessment | 시스템의 보안 약점을 체계적으로 찾는 활동 | 건물 안전 진단 |
| **모의해킹** | Penetration Testing | 실제 공격자처럼 취약점을 악용하여 검증 | 소방 훈련 (실제로 불을 피워봄) |
| **CVSS** | Common Vulnerability Scoring System | 취약점 심각도 0~10점 (9.0+ Critical) | 질병 위험 등급표 |
| **SQLi** | SQL Injection | SQL 쿼리에 악성 입력 삽입 | 주문서에 가짜 지시를 끼워넣기 |
| **XSS** | Cross-Site Scripting | 웹페이지에 악성 스크립트 삽입 | 게시판에 함정 쪽지 붙이기 |
| **CSRF** | Cross-Site Request Forgery | 사용자 모르게 요청을 위조 | 누군가 내 이름으로 송금 요청 |
| **SSRF** | Server-Side Request Forgery | 서버가 내부 자원에 요청하도록 조작 | 직원에게 기밀 문서를 가져오라 속이기 |
| **LFI** | Local File Inclusion | 서버의 로컬 파일을 읽는 취약점 | 사무실 서류함을 몰래 열람 |
| **RFI** | Remote File Inclusion | 외부 파일을 서버에 로드하는 취약점 | 외부에서 악성 서류를 사무실에 반입 |
| **RCE** | Remote Code Execution | 원격에서 서버 코드 실행 | 전화로 사무실 컴퓨터 조작 |
| **WAF 우회** | WAF Bypass | 웹 방화벽의 탐지를 피하는 기법 | 보안 검색대를 우회하는 비밀 통로 |
| **인코딩** | Encoding | 데이터를 다른 형식으로 변환 (URL, Base64 등) | 택배 재포장 (내용물은 같음) |
| **난독화** | Obfuscation | 코드를 읽기 어렵게 변환 (탐지 회피) | 범인이 변장하는 것 |
| **세션** | Session | 서버가 사용자를 식별하는 상태 정보 | 카페 단골 인식표 |
| **쿠키** | Cookie | 브라우저에 저장되는 작은 데이터 | 가게에서 받은 스탬프 카드 |
| **Burp Suite** | Burp Suite | 웹 보안 점검 프록시 도구 (PortSwigger) | 우편물 검사 장비 |
| **OWASP ZAP** | OWASP ZAP | 오픈소스 웹 보안 스캐너 | 무료 보안 검사 장비 |
| **점검 보고서** | Assessment Report | 발견된 취약점과 대응 방안을 정리한 문서 | 건물 안전 진단 보고서 |


# 본 강의 내용

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


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 3)

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

**Q1.** 이번 주차 "Week 13: 자동화 점검 도구 활용"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **웹 취약점 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 OWASP의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **점검 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

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

