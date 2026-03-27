# Week 12: API 보안 점검 (상세 버전)

## 학습 목표
- REST API의 보안 위협을 이해한다
- API 인증/인가를 점검할 수 있다
- Rate Limiting의 필요성과 점검 방법을 익힌다
- Swagger/OpenAPI 문서 노출의 위험을 파악한다
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

# Week 12: API 보안 점검

## 학습 목표
- REST API의 보안 위협을 이해한다
- API 인증/인가를 점검할 수 있다
- Rate Limiting의 필요성과 점검 방법을 익힌다
- Swagger/OpenAPI 문서 노출의 위험을 파악한다

## 전제 조건
- REST API 기본 개념 (HTTP 메서드, JSON)
- JWT 인증 (Week 04)

---

## 1. API 보안 개요 (15분)

### 1.1 OWASP API Security Top 10 (2023)

| 순위 | 위협 | 설명 |
|------|------|------|
| API1 | Broken Object Level Authorization | IDOR (Week 09) |
| API2 | Broken Authentication | 인증 우회 |
| API3 | Broken Object Property Level Authorization | 과도한 데이터 노출 |
| API4 | Unrestricted Resource Consumption | Rate Limit 부재 |
| API5 | Broken Function Level Authorization | 권한 상승 |
| API6 | Unrestricted Access to Sensitive Business Flows | 비즈니스 로직 악용 |
| API7 | Server Side Request Forgery | SSRF |
| API8 | Security Misconfiguration | 설정 오류 |
| API9 | Improper Inventory Management | API 문서 관리 부재 |
| API10 | Unsafe Consumption of APIs | 외부 API 신뢰 |

### 1.2 API vs 웹 페이지 점검 차이

| 항목 | 웹 페이지 | API |
|------|----------|-----|
| 인터페이스 | HTML 폼, 브라우저 | JSON/XML, 직접 호출 |
| 인증 | 세션 쿠키 | API Key, JWT, OAuth |
| 입력 | 폼 필드 | JSON body, Query params |
| 문서 | 사용자 매뉴얼 | Swagger/OpenAPI |
| Rate Limit | 덜 중요 | 매우 중요 |

---

## 2. JuiceShop API 구조 파악 (20분)

### 2.1 API 엔드포인트 전체 탐색

```bash
# JuiceShop API 엔드포인트 목록 수집
echo "=== API 엔드포인트 탐색 ==="

# HTML/JS에서 API 경로 추출
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*main[^"]*\.js"' | head -1 | sed 's/src="//;s/"//')
if [ -n "$MAIN_JS" ]; then
  echo "JS에서 발견된 API 경로:"
  curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -oE '"/api/[^"]*"|"/rest/[^"]*"' | sort -u | head -30
fi

echo ""
echo "=== 직접 탐색 ==="
# REST API 엔드포인트
ENDPOINTS=(
  "api/Products" "api/Products/1" "api/Users" "api/Users/1"
  "api/Feedbacks" "api/Feedbacks/1" "api/Challenges" "api/Complaints"
  "api/Recycles" "api/SecurityQuestions" "api/Quantitys"
  "rest/products/search?q=test" "rest/user/login" "rest/user/whoami"
  "rest/user/change-password" "rest/basket/1" "rest/track-order/1"
  "rest/saveLoginIp" "rest/deluxe-membership" "rest/memories"
  "rest/chatbot/status" "rest/chatbot/respond" "rest/languages"
  "rest/repeat-notification" "rest/continue-code" "rest/continue-code/apply"
  "rest/wallet/balance" "rest/order-history"
  "b2b/v2/orders" "profile" "file-upload"
  "promotion" "video" "redirect" "snippets"
)

printf "%-45s %s\n" "엔드포인트" "코드"
printf "%-45s %s\n" "---" "---"
for ep in "${ENDPOINTS[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$ep")
  if [ "$code" != "404" ]; then
    printf "%-45s %s\n" "/$ep" "$code"
  fi
done
```

### 2.2 HTTP 메서드별 응답 확인

```bash
# 각 API의 지원 메서드 확인
echo "=== Products API 메서드 ==="
for method in GET POST PUT DELETE PATCH OPTIONS; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" http://10.20.30.80:3000/api/Products/)
  echo "  $method: HTTP $code"
done

echo ""
echo "=== Users API 메서드 ==="
for method in GET POST PUT DELETE PATCH OPTIONS; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" http://10.20.30.80:3000/api/Users/)
  echo "  $method: HTTP $code"
done
```

---

## 3. API 인증 점검 (30분)

### 3.1 인증 없는 접근 테스트

```bash
# 인증 토큰 없이 각 API 호출
echo "=== 인증 없는 접근 테스트 ==="
python3 << 'PYEOF'
import requests

BASE = "http://10.20.30.80:3000"
endpoints = {
    "GET /api/Products": f"{BASE}/api/Products",
    "GET /api/Users": f"{BASE}/api/Users",
    "GET /api/Feedbacks": f"{BASE}/api/Feedbacks",
    "GET /api/Challenges": f"{BASE}/api/Challenges",
    "GET /api/Complaints": f"{BASE}/api/Complaints",
    "GET /rest/user/whoami": f"{BASE}/rest/user/whoami",
    "GET /rest/basket/1": f"{BASE}/rest/basket/1",
    "GET /rest/wallet/balance": f"{BASE}/rest/wallet/balance",
    "GET /rest/order-history": f"{BASE}/rest/order-history",
    "POST /api/Feedbacks": f"{BASE}/api/Feedbacks",
}

print(f"{'API':<35} {'인증없음':>10} {'결과':>10}")
print("-" * 60)

for name, url in endpoints.items():
    method = name.split()[0]
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json={}, timeout=5)
        status = "공개" if r.status_code == 200 else "보호"
        print(f"{name:<35} {r.status_code:>10} {status:>10}")
    except Exception as e:
        print(f"{name:<35} {'ERROR':>10}")
PYEOF
```

### 3.2 토큰 조작 테스트

```bash
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

echo "=== 토큰 조작 테스트 ==="

# 정상 토큰
echo "정상 토큰:"
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('user',{}).get('email','실패'))" 2>/dev/null

# 만료된 토큰 (한 글자 변경)
TAMPERED="${TOKEN:0:-5}XXXXX"
echo "변조 토큰:"
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Bearer $TAMPERED" | head -3

# 빈 토큰
echo "빈 토큰:"
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Bearer " | head -3

# 다른 인증 스킴
echo "Basic 인증 시도:"
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Basic YWRtaW46YWRtaW4=" | head -3
```

### 3.3 API 키 노출 점검

```bash
# 소스 코드에서 API 키/시크릿 패턴 검색
echo "=== 소스 코드 내 시크릿 검색 ==="
if [ -n "$MAIN_JS" ]; then
  curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -oiE \
    "(api[_-]?key|secret|token|password|auth)['\"]?\s*[:=]\s*['\"][^'\"]{8,}" | head -10
fi

# HTML에서 시크릿 검색
curl -s http://10.20.30.80:3000 | grep -oiE \
  "(api[_-]?key|secret|token)['\"]?\s*[:=]\s*['\"][^'\"]{8,}" | head -5
```

---

## 4. Rate Limiting 점검 (25분)

### 4.1 Rate Limiting이란?

Rate Limiting은 특정 시간 내 요청 수를 제한하여 무차별 대입, DoS, 스크래핑을 방지한다.

### 4.2 로그인 API Rate Limiting 테스트

```bash
echo "=== 로그인 API Rate Limiting 테스트 ==="
echo "30회 연속 잘못된 로그인 시도:"

for i in $(seq 1 30); do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"password\":\"wrong$i\"}")
  if [ "$code" = "429" ]; then
    echo "시도 $i: HTTP $code (Rate Limited!)"
    echo "Rate Limiting 활성화됨 ($i 회째에서 차단)"
    break
  elif [ "$i" -eq 10 ] || [ "$i" -eq 20 ] || [ "$i" -eq 30 ]; then
    echo "시도 $i: HTTP $code"
  fi
done

echo ""
echo "30회 모두 401이면 → Rate Limiting 없음 (취약)"
echo "429가 나오면 → Rate Limiting 있음 (양호)"
```

### 4.3 검색 API Rate Limiting 테스트

```bash
echo "=== 검색 API Rate Limiting 테스트 ==="
echo "50회 연속 검색 요청:"

blocked=0
for i in $(seq 1 50); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/rest/products/search?q=test$i")
  if [ "$code" = "429" ]; then
    echo "시도 $i: Rate Limited!"
    blocked=1
    break
  fi
done

if [ $blocked -eq 0 ]; then
  echo "50회 모두 정상 응답 → Rate Limiting 없음"
fi
```

### 4.4 Rate Limiting 우회 시도

```bash
# X-Forwarded-For 헤더로 IP 위장
echo "=== Rate Limiting 우회 (IP 위장) ==="
for i in $(seq 1 5); do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: 1.2.3.$i" \
    -d '{"email":"admin@juice-sh.op","password":"wrong"}')
  echo "IP 1.2.3.$i: HTTP $code"
done
```

---

## 5. Swagger / OpenAPI 문서 노출 (20분)

### 5.1 Swagger UI 탐색

```bash
# Swagger/OpenAPI 문서 경로 탐색
echo "=== Swagger/API 문서 탐색 ==="
for path in \
  "swagger" "swagger-ui" "swagger-ui.html" "swagger.json" "swagger.yaml" \
  "api-docs" "api/docs" "v1/api-docs" "v2/api-docs" "v3/api-docs" \
  "openapi.json" "openapi.yaml" "docs" "redoc" \
  "graphql" "graphiql" "playground" \
  "api/swagger" "api/openapi" "_api" "api/v1" "api/v2"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$path")
  if [ "$code" != "404" ]; then
    echo "[$code] /$path"
  fi
done
```

### 5.2 Swagger 문서가 노출된 경우의 위험

API 문서가 외부에 노출되면:

1. **모든 API 엔드포인트가 공개됨** → 공격 표면 확대
2. **파라미터/데이터 타입이 공개됨** → 정밀한 공격 가능
3. **인증 방식이 공개됨** → 우회 시도 용이
4. **숨겨진 관리자 API도 노출 가능** → 권한 상승 위험

### 5.3 API 문서에서 공격 대상 추출

```bash
# Swagger JSON이 있다면 파싱하여 엔드포인트 추출
SWAGGER_URL="http://10.20.30.80:3000/swagger.json"
result=$(curl -s -o /dev/null -w "%{http_code}" "$SWAGGER_URL")

if [ "$result" = "200" ]; then
  echo "Swagger 문서 발견! 엔드포인트 추출:"
  curl -s "$SWAGGER_URL" | python3 -c "
import sys, json
doc = json.load(sys.stdin)
paths = doc.get('paths', {})
for path, methods in paths.items():
    for method in methods:
        if method.upper() in ['GET','POST','PUT','DELETE','PATCH']:
            auth = '인증필요' if any('security' in str(methods[method]) for _ in [1]) else '공개'
            print(f'  {method.upper():6} {path}')
" 2>/dev/null
else
  echo "Swagger 문서 없음 (HTTP $result)"
fi
```

---

## 6. 데이터 과다 노출 점검 (20분)

### 6.1 불필요한 필드 노출

```bash
# API 응답에 불필요한 민감 정보가 포함되는지 확인
echo "=== 데이터 과다 노출 점검 ==="

TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# Users API 응답 분석
echo "=== /api/Users/1 응답 필드 ==="
curl -s http://10.20.30.80:3000/api/Users/1 \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin).get('data', {})
    sensitive_keywords = ['password', 'hash', 'secret', 'token', 'ssn', 'card', 'credit']
    print('포함된 필드:')
    for key, val in data.items():
        is_sensitive = any(k in key.lower() for k in sensitive_keywords)
        marker = ' <<< 민감 정보!' if is_sensitive else ''
        print(f'  {key}: {str(val)[:60]}{marker}')
except Exception as e:
    print(f'파싱 실패: {e}')
" 2>/dev/null

echo ""
echo "=== /api/Products/1 응답 필드 ==="
curl -s http://10.20.30.80:3000/api/Products/1 | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin).get('data', {})
    print('포함된 필드:')
    for key, val in data.items():
        print(f'  {key}: {str(val)[:60]}')
except:
    print('파싱 실패')
" 2>/dev/null
```

### 6.2 대량 데이터 조회 (Pagination 부재)

```bash
# 전체 데이터 조회 시 페이지네이션 여부
echo "=== 페이지네이션 점검 ==="

# 전체 사용자 조회
result=$(curl -s http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $TOKEN")
count=$(echo "$result" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
echo "Users API: ${count}건 반환 (제한 없이 전체?)"

# 전체 상품 조회
result=$(curl -s http://10.20.30.80:3000/api/Products/)
count=$(echo "$result" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
echo "Products API: ${count}건 반환"
```

---

## 7. 실습 과제

### 과제 1: API 인벤토리 작성
1. JuiceShop의 모든 API 엔드포인트를 탐색하여 목록을 작성하라
2. 각 API의 지원 메서드(GET/POST/PUT/DELETE)를 확인하라
3. 인증 필요 여부를 표시하라

### 과제 2: Rate Limiting 점검
1. 로그인 API에 대한 Rate Limiting 존재 여부를 확인하라
2. 검색, 회원가입 등 다른 API에도 Rate Limiting이 있는지 테스트하라
3. Rate Limiting이 없는 API에서 가능한 공격 시나리오를 서술하라

### 과제 3: API 보안 종합 보고서
1. JuiceShop API의 인증, 인가, Rate Limiting, 데이터 노출을 종합 점검하라
2. OWASP API Security Top 10 기준으로 취약점을 분류하라
3. 각 취약점에 대한 개선 권고를 작성하라

---

## 8. 요약

| 점검 항목 | 도구 | 기대 결과 |
|----------|------|----------|
| API 인증 | curl (토큰 제외) | 인증 필요 API → 401/403 |
| Rate Limiting | curl 반복 호출 | 과도한 요청 → 429 |
| Swagger 노출 | 경로 탐색 | 404 (비공개) |
| 데이터 과다 노출 | 응답 필드 분석 | 최소 필드만 반환 |
| HTTP 메서드 | 메서드 변경 | 불필요 메서드 → 405 |

**다음 주 예고**: Week 13 - OWASP ZAP 자동화 점검. ZAP 자동 스캔, 보고서 생성을 학습한다.


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

**Q1.** 이번 주차 "Week 12: API 보안 점검"의 핵심 목적은 무엇인가?
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

