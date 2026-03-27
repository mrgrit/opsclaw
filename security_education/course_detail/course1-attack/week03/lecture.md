# Week 03: 웹 애플리케이션 구조 이해 (상세 버전)

## 학습 목표
- HTTP 프로토콜의 요청/응답 구조를 이해한다
- HTTP 메서드, 상태 코드, 헤더의 의미를 파악한다
- HTTPS와 TLS 핸드셰이크의 기본 원리를 이해한다
- 쿠키, 세션, JWT 토큰의 차이와 동작 원리를 실습한다
- REST API 구조를 이해하고 직접 호출한다
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

## 용어 해설 (이 과목에서 자주 나오는 용어)

> 대학 1~2학년이 처음 접할 수 있는 보안/IT 용어를 정리한다.
> 강의 중 모르는 용어가 나오면 이 표를 참고하라.

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **페이로드** | Payload | 공격에 사용되는 실제 데이터/코드. 예: `' OR 1=1--` | 미사일의 탄두 |
| **익스플로잇** | Exploit | 취약점을 악용하는 기법 또는 코드 | 열쇠 없이 문을 여는 방법 |
| **셸** | Shell | 운영체제와 사용자를 연결하는 명령어 해석기 (bash, sh 등) | OS에게 말 걸 수 있는 창구 |
| **리버스 셸** | Reverse Shell | 대상 서버가 공격자에게 역방향 연결을 맺는 것 | 도둑이 집에서 밖으로 전화를 거는 것 |
| **포트** | Port | 서버에서 특정 서비스를 식별하는 번호 (0~65535) | 아파트 호수 |
| **데몬** | Daemon | 백그라운드에서 실행되는 서비스 프로그램 | 24시간 근무하는 경비원 |
| **패킷** | Packet | 네트워크로 전송되는 데이터의 단위 | 택배 상자 하나 |
| **프록시** | Proxy | 클라이언트와 서버 사이에서 중개하는 서버 | 대리인, 중간 거래자 |
| **해시** | Hash | 임의 길이 데이터를 고정 길이 값으로 변환하는 함수 (SHA-256 등) | 지문 (고유하지만 원본 복원 불가) |
| **토큰** | Token | 인증 정보를 담은 문자열 (JWT, API Key 등) | 놀이공원 입장권 |
| **JWT** | JSON Web Token | Base64로 인코딩된 JSON 기반 인증 토큰 | 이름·권한이 적힌 입장권 |
| **Base64** | Base64 | 바이너리 데이터를 텍스트로 인코딩하는 방법 | 암호가 아닌 "포장" (누구나 풀 수 있음) |
| **CORS** | Cross-Origin Resource Sharing | 다른 도메인에서의 API 호출 허용 설정 | "외부인 출입 허용" 표지판 |
| **API** | Application Programming Interface | 프로그램 간 통신 규약 | 식당의 메뉴판 (주문 양식) |
| **REST** | Representational State Transfer | URL + HTTP 메서드로 자원을 조작하는 API 스타일 | 도서관 대출 시스템 (책 이름으로 검색/대출/반납) |
| **SSH** | Secure Shell | 원격 서버에 안전하게 접속하는 프로토콜 | 암호화된 전화선 |
| **sudo** | SuperUser DO | 관리자(root) 권한으로 명령 실행 | "사장님 권한으로 실행" |
| **SUID** | Set User ID | 실행 시 파일 소유자 권한으로 실행되는 특수 권한 | 다른 사람의 사원증을 빌려 출입 |
| **IPS** | Intrusion Prevention System | 네트워크 침입 방지 시스템 (악성 트래픽 차단) | 공항 보안 검색대 |
| **SIEM** | Security Information and Event Management | 보안 로그를 수집·분석하는 통합 관제 시스템 | CCTV 관제실 |
| **WAF** | Web Application Firewall | 웹 공격을 탐지·차단하는 방화벽 | 웹사이트 전용 경비원 |
| **nftables** | nftables | Linux 커널 방화벽 프레임워크 (iptables 후계) | 건물 출입구 차단기 |
| **Suricata** | Suricata | 오픈소스 IDS/IPS 엔진 | 공항 X-ray 검색기 |
| **Wazuh** | Wazuh | 오픈소스 SIEM 플랫폼 | CCTV + AI 관제 시스템 |
| **ATT&CK** | MITRE ATT&CK | 실제 공격 전술·기법을 분류한 데이터베이스 | 범죄 수법 백과사전 |
| **OWASP** | Open Web Application Security Project | 웹 보안 취약점 연구 국제 단체 | 웹 보안의 표준 기관 |
| **CVSS** | Common Vulnerability Scoring System | 취약점 심각도 점수 (0~10점) | 질병 위험도 등급 |
| **CVE** | Common Vulnerabilities and Exposures | 취약점 고유 식별 번호 | 질병의 고유 코드 (예: COVID-19) |
| **OpsClaw** | OpsClaw | 보안 작업 자동화·증적 관리 플랫폼 (이 수업에서 사용) | 보안 작업 일지 + 자동화 시스템 |


---

# Week 03: 웹 애플리케이션 구조 이해

## 학습 목표

- HTTP 프로토콜의 요청/응답 구조를 이해한다
- HTTP 메서드, 상태 코드, 헤더의 의미를 파악한다
- HTTPS와 TLS 핸드셰이크의 기본 원리를 이해한다
- 쿠키, 세션, JWT 토큰의 차이와 동작 원리를 실습한다
- REST API 구조를 이해하고 직접 호출한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| opsclaw | 10.20.30.201 | 실습 기지 |
| web | 10.20.30.80 | JuiceShop:3000, Apache:80 |

---

## 1. HTTP 프로토콜 기초

HTTP(HyperText Transfer Protocol)는 웹 브라우저와 웹 서버가 통신하는 규약이다. 모든 웹 해킹의 기반이므로 반드시 이해해야 한다.

### 1.1 HTTP 요청(Request) 구조

브라우저가 서버에 보내는 메시지의 형태:

```
[메서드] [경로] HTTP/[버전]
[헤더1]: [값1]
[헤더2]: [값2]
(빈 줄)
[본문 - POST 등에서 사용]
```

**실제 예시:**
```
GET /api/Products HTTP/1.1
Host: 10.20.30.80:3000
User-Agent: curl/7.88.1
Accept: */*
```

### 1.2 HTTP 응답(Response) 구조

서버가 브라우저에 보내는 메시지:

```
HTTP/[버전] [상태코드] [상태메시지]
[헤더1]: [값1]
[헤더2]: [값2]
(빈 줄)
[본문 - HTML, JSON 등]
```

### 1.3 직접 확인하기

```bash
# -v 옵션으로 요청과 응답 헤더를 모두 볼 수 있다
curl -v http://10.20.30.80:3000/ 2>&1 | head -40
```

**예상 출력:**
```
> GET / HTTP/1.1
> Host: 10.20.30.80:3000
> User-Agent: curl/7.88.1
> Accept: */*
>
< HTTP/1.1 200 OK
< X-Powered-By: Express
< Content-Type: text/html; charset=utf-8
< Content-Length: 6541
< ETag: W/"1985-..."
< X-Content-Type-Options: nosniff
< X-Frame-Options: SAMEORIGIN
<
<!DOCTYPE html>
<html lang="en">
...
```

> `>`로 시작하는 줄은 **요청**, `<`로 시작하는 줄은 **응답**이다.

---

## 2. HTTP 메서드

HTTP 메서드는 서버에게 "무엇을 하라"고 알려주는 동사(verb)다.

| 메서드 | 용도 | 예시 |
|--------|------|------|
| **GET** | 데이터 조회 | 웹 페이지 열기, API 데이터 가져오기 |
| **POST** | 데이터 생성 | 회원가입, 로그인, 글 작성 |
| **PUT** | 데이터 전체 수정 | 프로필 업데이트 |
| **PATCH** | 데이터 일부 수정 | 비밀번호만 변경 |
| **DELETE** | 데이터 삭제 | 계정 삭제 |
| **OPTIONS** | 허용 메서드 확인 | CORS 프리플라이트 |
| **HEAD** | 헤더만 조회 (본문 없음) | 파일 존재 여부 확인 |

### 실습: 다양한 메서드 사용

```bash
# GET - 제품 목록 조회
curl -s http://10.20.30.80:3000/api/Products | python3 -m json.tool | head -20

# HEAD - 헤더만 확인
curl -I http://10.20.30.80:3000/api/Products

# OPTIONS - 허용된 메서드 확인
curl -X OPTIONS -v http://10.20.30.80:3000/api/Products 2>&1 | grep -i "allow\|access-control"

# POST - 사용자 등록 (JSON 본문 전송)
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234","passwordRepeat":"test1234","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"test"}' \
  | python3 -m json.tool
```

**POST 예상 출력:**
```json
{
    "status": "success",
    "data": {
        "id": 22,
        "email": "test@test.com",
        "password": "...(해시됨)...",
        "createdAt": "2026-03-27T09:00:00.000Z",
        "updatedAt": "2026-03-27T09:00:00.000Z"
    }
}
```

---

## 3. HTTP 상태 코드

서버가 요청 처리 결과를 숫자로 알려준다.

| 범위 | 의미 | 예시 |
|------|------|------|
| **1xx** | 정보 | 100 Continue |
| **2xx** | 성공 | 200 OK, 201 Created |
| **3xx** | 리다이렉트 | 301 Moved Permanently, 302 Found |
| **4xx** | 클라이언트 오류 | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| **5xx** | 서버 오류 | 500 Internal Server Error |

### 실습: 다양한 상태 코드 만들어보기

```bash
# 200 OK - 정상 응답
curl -o /dev/null -s -w "%{http_code}\n" http://10.20.30.80:3000/

# 404 Not Found - Apache에서 존재하지 않는 경로
curl -o /dev/null -s -w "%{http_code}\n" http://10.20.30.80:80/nonexistent_page
# → 404 (Apache는 전통적 웹서버라 없는 페이지에 404를 반환)

# 참고: JuiceShop은 SPA(Single Page Application)라서 없는 경로에도 200을 반환한다
curl -o /dev/null -s -w "%{http_code}\n" http://10.20.30.80:3000/nonexistent
# → 200 (SPA는 모든 경로를 프론트엔드에서 처리하므로 항상 200)

# 401 Unauthorized - 인증 필요한 API (admin 전용)
curl -o /dev/null -s -w "%{http_code}\n" -X POST http://10.20.30.80:3000/api/Products/
# → 401 (POST로 제품 생성 시 인증 필요)

# 500 Internal Server Error - SQLi로 서버 오류 유발
curl -o /dev/null -s -w "%{http_code}\n" -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"'","password":"x"}'
# → 500 (SQL 구문 오류 발생)
```

> **보안 관점**: 에러 메시지에 내부 정보(스택 트레이스, DB 쿼리 등)가 포함되면 공격자에게 힌트를 준다.

---

## 4. HTTP 헤더 상세 분석

### 4.1 주요 요청 헤더

| 헤더 | 용도 | 보안 관련성 |
|------|------|-------------|
| `Host` | 대상 서버 지정 | 가상 호스트 구분 |
| `User-Agent` | 클라이언트 정보 | 브라우저 위장 가능 |
| `Cookie` | 세션 정보 전송 | 세션 하이재킹 대상 |
| `Authorization` | 인증 토큰 | Bearer JWT 등 |
| `Content-Type` | 본문 형식 | MIME 타입 조작 가능 |
| `Referer` | 이전 페이지 URL | 정보 유출 가능 |

### 4.2 주요 응답 헤더

| 헤더 | 용도 | 보안 설정 |
|------|------|-----------|
| `Server` | 서버 소프트웨어 | 버전 노출 위험 |
| `Set-Cookie` | 쿠키 설정 | HttpOnly, Secure 플래그 |
| `X-Powered-By` | 프레임워크 | 제거 권장 |
| `X-Frame-Options` | 클릭재킹 방지 | DENY 또는 SAMEORIGIN |
| `X-Content-Type-Options` | MIME 스니핑 방지 | nosniff |
| `Content-Security-Policy` | XSS 방지 | 스크립트 소스 제한 |

### 실습: 헤더 분석

```bash
# JuiceShop 응답 헤더 상세 분석
curl -v http://10.20.30.80:3000/ 2>&1 | grep "< "
```

```bash
# User-Agent 변경해서 요청 보내기 (브라우저로 위장)
curl -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0" \
  -I http://10.20.30.80:3000/
```

---

## 5. HTTPS와 TLS

### 5.1 HTTP vs HTTPS

| 항목 | HTTP | HTTPS |
|------|------|-------|
| 포트 | 80 | 443 |
| 암호화 | 없음 (평문) | TLS로 암호화 |
| 도청 가능 | 가능 | 불가능 |
| URL 시작 | http:// | https:// |

### 5.2 TLS 핸드셰이크 (간소화)

HTTPS 연결이 시작될 때 클라이언트와 서버가 암호화 방법을 협상하는 과정이다:

```
1. 클라이언트 → 서버: "안녕, 나는 이런 암호화를 지원해" (ClientHello)
2. 서버 → 클라이언트: "이 방법으로 하자, 내 인증서야" (ServerHello + Certificate)
3. 클라이언트: 인증서 검증 후, 비밀 키 교환
4. 양쪽: 공유된 키로 암호화 통신 시작
```

### 실습: TLS 인증서 확인

우리 인프라에서 HTTPS를 사용하는 서비스는 **Wazuh Dashboard** (siem:443)이다.

```bash
# Wazuh Dashboard의 TLS 인증서 확인
curl -vk https://10.20.30.100:443/ 2>&1 | grep -A5 "Server certificate"

# openssl로 상세 확인
echo | openssl s_client -connect 10.20.30.100:443 2>/dev/null | openssl x509 -noout -subject -dates

# 인증서 발급자와 주체 확인
echo | openssl s_client -connect 10.20.30.100:443 2>/dev/null | openssl x509 -noout -issuer -subject
```

**예상 출력:**
```
subject=C = US, L = California, O = Wazuh, OU = Wazuh, CN = wazuh-dashboard
notBefore=Mar 24 05:23:34 2026 GMT
notAfter=Mar 21 05:23:34 2036 GMT
```

> **분석 포인트:**
> - `CN = wazuh-dashboard`: 인증서의 Common Name (도메인 대신 이름)
> - 유효기간: 10년 (자체 서명 인증서에서 흔한 설정)
> - 자체 서명(self-signed) 인증서이므로 브라우저에서 "안전하지 않음" 경고 발생
> - `-k` 옵션은 인증서 검증을 무시 (실습 환경에서만 사용, 실무에서는 위험)
>
> **참고:** JuiceShop(:3000)과 Apache(:80)는 HTTP만 사용하며 HTTPS 미설정이다.

---

## 6. 쿠키(Cookie)와 세션(Session)

### 6.1 쿠키란?

쿠키는 서버가 브라우저에 저장하는 작은 데이터 조각이다. 브라우저는 같은 서버에 요청할 때마다 쿠키를 자동으로 함께 보낸다.

**쿠키 동작 흐름:**
```
1. 브라우저 → 서버: 로그인 요청 (ID/PW)
2. 서버 → 브라우저: "로그인 성공! 이 쿠키를 저장해" (Set-Cookie 헤더)
3. 브라우저 → 서버: 이후 모든 요청에 쿠키 자동 첨부
```

### 6.2 쿠키 속성

| 속성 | 의미 | 보안 영향 |
|------|------|-----------|
| `HttpOnly` | JavaScript에서 접근 불가 | XSS로 쿠키 탈취 방지 |
| `Secure` | HTTPS에서만 전송 | 네트워크 도청 방지 |
| `SameSite` | 동일 사이트에서만 전송 | CSRF 공격 방지 |
| `Path` | 특정 경로에서만 전송 | 범위 제한 |
| `Expires/Max-Age` | 만료 시간 | 세션 수명 관리 |

### 실습: JuiceShop 쿠키 확인

```bash
# 로그인하고 쿠키 확인 (-c: 쿠키 저장, -v: 상세 출력)
curl -v -c /tmp/cookies.txt -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"admin123"}' 2>&1

# 저장된 쿠키 확인
cat /tmp/cookies.txt
```

**예상 출력 (쿠키 파일):**
```
# Netscape HTTP Cookie File
10.20.30.80	FALSE	/	FALSE	0	token	eyJhbGciOiJ...
```

> 아직 admin 비밀번호를 모르므로 로그인이 실패할 수 있다. Week 04에서 SQL Injection으로 우회하는 방법을 배운다.

### 6.3 세션(Session)

세션은 서버 측에서 사용자 상태를 관리하는 방식이다:

- **쿠키 기반 인증**: 세션 ID를 쿠키에 저장, 서버가 세션 데이터 보유
- **토큰 기반 인증**: JWT 토큰을 쿠키 또는 헤더에 저장, 토큰 자체에 정보 포함

---

## 7. JWT (JSON Web Token)

### 7.1 JWT란?

JWT는 JSON 형식의 자가 포함형(self-contained) 인증 토큰이다. 서버가 세션을 저장할 필요 없이, 토큰 자체에 사용자 정보가 들어 있다.

### 7.2 JWT 구조

JWT는 점(.)으로 구분된 3개 부분으로 구성된다:

```
[헤더].[페이로드].[서명]
eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJhZG1pbkBqdWljZS1zaC5vcCJ9.xxxxx
```

각 부분은 Base64URL로 인코딩되어 있다.

**헤더 (Header):**
```json
{
  "alg": "RS256",   // 서명 알고리즘
  "typ": "JWT"      // 토큰 타입
}
```

**페이로드 (Payload):**
```json
{
  "sub": "1",                          // 사용자 ID
  "email": "admin@juice-sh.op",       // 이메일
  "role": "admin",                     // 역할
  "iat": 1711526400,                   // 발급 시간
  "exp": 1711612800                    // 만료 시간
}
```

**서명 (Signature):**
```
RSASHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), privateKey)
```

### 7.3 JWT 디코딩 실습

JWT는 암호화가 아니라 **인코딩**이므로, 누구나 내용을 읽을 수 있다. 서명은 **위변조 방지**를 위한 것이다.

```bash
# JWT를 직접 디코딩하는 방법
# 먼저 JuiceShop에서 계정을 만들고 로그인
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!","passwordRepeat":"Student123!","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"test"}'

# 로그인해서 토큰 받기
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")

echo "JWT Token: $TOKEN"

# JWT 디코딩 (Base64)
echo "$TOKEN" | cut -d. -f1 | base64 -d 2>/dev/null; echo
echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null; echo
```

**예상 출력 (페이로드 디코딩):**
```json
{"status":"success","data":{"id":22,"email":"student@test.com","password":"..."},"iat":1711526400}
```

> **보안 관점**: JWT 페이로드는 누구나 읽을 수 있으므로, 민감한 정보(비밀번호, 주민번호 등)를 넣으면 안 된다.

### 7.4 JWT를 사용한 API 호출

```bash
# 인증이 필요한 API에 JWT를 사용하여 접근
curl -s http://10.20.30.80:3000/api/Feedbacks \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool | head -20

# 인증 없이 같은 API 호출 (401 에러 예상)
curl -s -o /dev/null -w "%{http_code}\n" http://10.20.30.80:3000/api/Feedbacks
```

---

## 8. REST API 구조

### 8.1 REST란?

REST(Representational State Transfer)는 웹 API 설계 규칙이다. URL로 **자원(Resource)**을 표현하고, HTTP 메서드로 **행위(Action)**를 표현한다.

| 행위 | HTTP 메서드 | URL 예시 | 설명 |
|------|-------------|----------|------|
| 조회 | GET | /api/Products | 전체 목록 |
| 조회 | GET | /api/Products/1 | 특정 항목 |
| 생성 | POST | /api/Products | 새 항목 생성 |
| 수정 | PUT | /api/Products/1 | 항목 수정 |
| 삭제 | DELETE | /api/Products/1 | 항목 삭제 |

### 8.2 JuiceShop REST API 탐색

```bash
# 제품 전체 목록
curl -s http://10.20.30.80:3000/api/Products | python3 -m json.tool | head -30

# 특정 제품 조회
curl -s http://10.20.30.80:3000/api/Products/1 | python3 -m json.tool

# 사용자 목록 (인증 필요)
curl -s http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool | head -30

# 리뷰(Feedback) 목록
curl -s http://10.20.30.80:3000/api/Feedbacks | python3 -m json.tool | head -20

# 챌린지 목록 (JuiceShop 특수 API)
curl -s http://10.20.30.80:3000/api/Challenges | python3 -m json.tool | head -30

# 검색 기능
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" | python3 -m json.tool
```

### 8.3 API 응답 구조 분석

JuiceShop API의 일관된 응답 패턴:

```json
{
    "status": "success",
    "data": [ ... ]    // 또는 단일 객체 { ... }
}
```

에러 시:
```json
{
    "error": {
        "message": "...",
        "name": "..."
    }
}
```

---

## 9. 종합 실습: JuiceShop 완전 분석

### Step 1: 모든 API 엔드포인트 탐색

```bash
# JuiceShop 메인 페이지 소스에서 API 경로 추출
curl -s http://10.20.30.80:3000/ | grep -oE '"/[a-zA-Z/]+"' | sort -u

# JavaScript 파일에서 API 경로 찾기
curl -s http://10.20.30.80:3000/main.js 2>/dev/null | grep -oE '/api/[A-Za-z/]+' | sort -u
curl -s http://10.20.30.80:3000/main.js 2>/dev/null | grep -oE '/rest/[A-Za-z/]+' | sort -u
```

### Step 2: 인증 토큰 분석

```bash
# 로그인 후 토큰 저장
RESPONSE=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}')

echo "$RESPONSE" | python3 -m json.tool

# 토큰에서 사용자 정보 추출
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")

# 페이로드 디코딩
echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
payload = sys.stdin.read().strip()
# Base64 패딩 추가
payload += '=' * (4 - len(payload) % 4)
decoded = base64.urlsafe_b64decode(payload)
print(json.dumps(json.loads(decoded), indent=2))
"
```

### Step 3: 응답 헤더 보안 분석

```bash
# 보안 관련 헤더 확인
curl -sI http://10.20.30.80:3000/ | grep -iE "x-frame|x-content|x-powered|content-security|strict-transport|x-xss"
```

**분석 체크리스트:**
- [  ] `X-Frame-Options`이 설정되어 있는가?
- [  ] `X-Content-Type-Options: nosniff`가 있는가?
- [  ] `X-Powered-By`가 노출되고 있는가? (위험)
- [  ] `Content-Security-Policy`가 있는가?
- [  ] `Strict-Transport-Security`가 있는가?

---

## 10. OpsClaw로 웹 분석 자동화

```bash
# OpsClaw로 웹 서버 분석 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week03-http-analysis","request_text":"JuiceShop HTTP 분석","master_mode":"external"}' \
  | python3 -m json.tool

# Stage 전환 후 헤더 수집 자동화
# (프로젝트 ID를 실제 값으로 교체)
curl -s -X POST http://localhost:8000/projects/{프로젝트ID}/plan \
  -H "X-API-Key: opsclaw-api-key-2026"
curl -s -X POST http://localhost:8000/projects/{프로젝트ID}/execute \
  -H "X-API-Key: opsclaw-api-key-2026"

curl -s -X POST http://localhost:8000/projects/{프로젝트ID}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"curl -sI http://10.20.30.80:3000/", "risk_level":"low"},
      {"order":2, "instruction_prompt":"curl -s http://10.20.30.80:3000/api/Products | head -100", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

---

## 과제

1. JuiceShop에 계정을 생성하고 로그인하여 JWT 토큰을 획득하라
2. JWT 토큰을 디코딩하여 포함된 정보(이메일, ID, 역할 등)를 정리하라
3. JuiceShop의 REST API 엔드포인트를 최소 5개 찾아서 각각 호출 결과를 기록하라
4. 응답 헤더를 분석하여 보안상 문제가 되는 헤더를 식별하고 이유를 설명하라

---

## 핵심 요약

- HTTP는 **요청(Request)**과 **응답(Response)**으로 구성되며, 메서드/상태코드/헤더를 이해해야 한다
- **HTTPS**는 TLS를 통해 HTTP를 암호화한 것이며, 인증서로 서버 신원을 검증한다
- **쿠키**는 서버가 브라우저에 저장하는 데이터로, HttpOnly/Secure 플래그가 중요하다
- **JWT**는 Base64 인코딩된 JSON 토큰으로, 누구나 내용을 읽을 수 있다 (서명으로 위변조만 방지)
- **REST API**는 URL + HTTP 메서드로 자원을 조작하며, curl로 직접 호출할 수 있다

> **다음 주 예고**: Week 04에서는 OWASP Top 10의 첫 번째 취약점인 SQL Injection을 배우고, JuiceShop에서 관리자 로그인을 우회한다.


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** HTTP 요청에서 데이터를 서버에 전송할 때 주로 사용하는 메서드는?
- (a) GET  (b) **POST**  (c) DELETE  (d) HEAD

**Q2.** HTTP 상태 코드 403의 의미는?
- (a) 성공  (b) 리다이렉트  (c) **접근 금지(Forbidden)**  (d) 서버 오류

**Q3.** HTTPS에서 데이터를 암호화하는 프로토콜은?
- (a) SSH  (b) **TLS**  (c) FTP  (d) SMTP

**Q4.** 쿠키(Cookie)가 저장되는 위치는?
- (a) 서버 메모리  (b) 데이터베이스  (c) **클라이언트(브라우저)**  (d) DNS 서버

**Q5.** JWT 토큰의 세 부분은?
- (a) ID, PW, Token  (b) **Header, Payload, Signature**  (c) Key, Value, Hash  (d) User, Role, Time

**Q6.** REST API에서 리소스를 삭제하는 HTTP 메서드는?
- (a) POST  (b) PUT  (c) GET  (d) **DELETE**

**Q7.** `Access-Control-Allow-Origin: *`가 보안 이슈인 이유는?
- (a) 속도 저하  (b) **모든 도메인에서 API 호출 가능**  (c) 암호화 비활성화  (d) 로그 미생성

**Q8.** HTTP 상태 코드 500은 어떤 종류의 오류인가?
- (a) 클라이언트 오류  (b) 리다이렉트  (c) **서버 내부 오류**  (d) 인증 실패

**Q9.** `curl -X POST`에서 `-X POST`의 의미는?
- (a) 프록시 설정  (b) 타임아웃 설정  (c) **HTTP 메서드를 POST로 지정**  (d) 출력 형식 설정

**Q10.** 세션 ID가 URL에 노출되면 어떤 공격이 가능한가?
- (a) SQLi  (b) **세션 하이재킹**  (c) DDoS  (d) 버퍼 오버플로

**정답:** Q1:b, Q2:c, Q3:b, Q4:c, Q5:b, Q6:d, Q7:b, Q8:c, Q9:c, Q10:b

---

## 과제 (다음 주까지)


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


