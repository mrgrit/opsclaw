# Week 11: 에러 처리 / 정보 노출 점검 (상세 버전)

## 학습 목표
- 부적절한 에러 처리가 보안에 미치는 영향을 이해한다
- 스택 트레이스, 디버그 모드에서 노출되는 정보를 분석한다
- 디렉터리 리스팅 취약점을 점검한다
- 정보 노출의 다양한 경로를 체계적으로 점검할 수 있다
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

# Week 11: 에러 처리 / 정보 노출 점검

## 학습 목표
- 부적절한 에러 처리가 보안에 미치는 영향을 이해한다
- 스택 트레이스, 디버그 모드에서 노출되는 정보를 분석한다
- 디렉터리 리스팅 취약점을 점검한다
- 정보 노출의 다양한 경로를 체계적으로 점검할 수 있다

## 전제 조건
- HTTP 응답 코드 이해 (200, 404, 500 등)
- curl 사용법

---

## 1. 정보 노출의 위험 (15분)

### 1.1 OWASP에서의 위치

**A05:2021 Security Misconfiguration** 카테고리.
잘못된 설정으로 인한 정보 노출은 공격의 첫 단추가 된다.

### 1.2 노출 가능한 정보

| 정보 유형 | 노출 경로 | 위험 |
|----------|----------|------|
| 서버 버전 | HTTP 헤더 | CVE 검색 → 공격 |
| 파일 경로 | 스택 트레이스 | 내부 구조 파악 |
| DB 정보 | SQL 에러 | SQLi 공격 보조 |
| 소스 코드 | 디버그 모드 | 로직 분석 |
| 사용자 목록 | 열거 공격 | 무차별 대입 대상 |
| API 키/토큰 | 소스 코드, 설정 파일 | 인증 우회 |

---

## 2. 스택 트레이스 / 에러 메시지 (30분)

### 2.1 에러 유도 기법

```bash
# 1. 존재하지 않는 경로 (404)
echo "=== 404 에러 ==="
curl -s http://10.20.30.80:3000/nonexistent_path_xyz123 | head -10
echo ""

# 2. 잘못된 파라미터 타입
echo "=== 타입 에러 ==="
curl -s http://10.20.30.80:3000/api/Products/abc | python3 -m json.tool 2>/dev/null
echo ""

# 3. SQL 문법 오류 유도
echo "=== SQL 에러 ==="
curl -s "http://10.20.30.80:3000/rest/products/search?q='" | head -20
echo ""

# 4. 빈 JSON body
echo "=== 빈 요청 에러 ==="
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool 2>/dev/null
echo ""

# 5. 잘못된 Content-Type
echo "=== Content-Type 에러 ==="
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: text/plain" \
  -d 'not json' | head -10
echo ""

# 6. 매우 긴 입력
echo "=== 과도한 입력 ==="
LONG_INPUT=$(python3 -c "print('A'*10000)")
curl -s "http://10.20.30.80:3000/rest/products/search?q=$LONG_INPUT" | head -5
```

### 2.2 스택 트레이스 분석

```bash
# 에러 응답에서 민감 정보 추출
curl -s "http://10.20.30.80:3000/rest/products/search?q='" | python3 -c "
import sys, json

data = sys.stdin.read()
try:
    parsed = json.loads(data)
    error = parsed.get('error', {})
    if isinstance(error, dict):
        message = error.get('message', '')
        stack = error.get('stack', '')
    else:
        message = str(error)
        stack = ''
except:
    message = data[:500]
    stack = ''

print('=== 에러 메시지 분석 ===')
print(f'메시지: {message[:200]}')

if stack:
    print(f'\n스택 트레이스 (처음 5줄):')
    for i, line in enumerate(stack.split('\n')[:5]):
        print(f'  {line.strip()}')

# 노출된 정보 식별
info_found = []
full_text = message + stack
if 'SQLITE' in full_text.upper() or 'sqlite' in full_text:
    info_found.append('DB 종류: SQLite')
if '/app/' in full_text or '/home/' in full_text:
    info_found.append('파일 경로 노출')
if 'node_modules' in full_text:
    info_found.append('Node.js 사용 확인')
if 'at ' in full_text and '.js:' in full_text:
    info_found.append('JS 파일명 + 줄번호')

print(f'\n노출된 정보: {info_found if info_found else \"없음\"}')" 2>/dev/null
```

### 2.3 에러 응답 비교 (JuiceShop vs Apache)

```bash
echo "=== JuiceShop 에러 응답 ==="
curl -sI http://10.20.30.80:3000/nonexistent | head -5
echo ""
curl -s http://10.20.30.80:3000/nonexistent | head -5

echo ""
echo "=== Apache 에러 응답 ==="
curl -sI http://10.20.30.80:80/nonexistent | head -5
echo ""
curl -s http://10.20.30.80:80/nonexistent | head -10

# Apache 에러 페이지에 버전 정보가 노출되는지 확인
curl -s http://10.20.30.80:80/nonexistent | grep -i "apache\|server at\|port"
```

---

## 3. 디버그 모드 점검 (20분)

### 3.1 디버그 엔드포인트 탐색

```bash
# 일반적인 디버그/상태 엔드포인트
echo "=== 디버그 엔드포인트 탐색 ==="
for path in \
  "debug" "console" "status" "health" "healthcheck" \
  "info" "env" "config" "metrics" "trace" \
  "actuator" "actuator/env" "actuator/health" \
  "_debug" "__debug__" "phpinfo.php" \
  "server-status" "server-info" \
  "elmah.axd" "trace.axd" \
  ".env" "config.json" "package.json"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$path")
  if [ "$code" != "404" ]; then
    echo "[$code] /$path"
  fi
done
```

### 3.2 JuiceShop 메트릭 엔드포인트

```bash
# /metrics 엔드포인트가 노출되면 내부 정보 확인 가능
echo "=== /metrics 내용 ==="
curl -s http://10.20.30.80:3000/metrics | head -30

# 메트릭에서 추출 가능한 정보:
# - 요청 수, 에러 수
# - 메모리 사용량
# - Node.js 버전
# - 프로세스 정보
```

### 3.3 소스맵 파일 노출

```bash
# Angular 앱의 소스맵(.map) 파일이 노출되는지 확인
# 소스맵이 있으면 프론트엔드 원본 소스 코드를 복원할 수 있음
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*main[^"]*\.js"' | head -1 | sed 's/src="//;s/"//')
if [ -n "$MAIN_JS" ]; then
  echo "JS 파일: $MAIN_JS"
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/${MAIN_JS}.map")
  echo "소스맵 ($MAIN_JS.map): HTTP $code"
  if [ "$code" = "200" ]; then
    echo "소스맵 노출됨! 소스 코드 복원 가능"
    curl -s "http://10.20.30.80:3000/${MAIN_JS}.map" | python3 -c "
import sys, json
data = json.load(sys.stdin)
sources = data.get('sources', [])
print(f'소스 파일 수: {len(sources)}')
for s in sources[:10]:
    print(f'  {s}')
if len(sources) > 10:
    print(f'  ... 외 {len(sources)-10}개')
" 2>/dev/null
  fi
fi
```

---

## 4. 디렉터리 리스팅 (25분)

### 4.1 디렉터리 리스팅이란?

디렉터리 리스팅은 웹 서버가 디렉터리의 파일 목록을 보여주는 기능이다.
개발/테스트 환경에서는 편리하지만, 운영 환경에서는 보안 위험이다.

### 4.2 디렉터리 리스팅 점검

```bash
# JuiceShop 디렉터리 리스팅
echo "=== JuiceShop 디렉터리 리스팅 ==="
for dir in "/" "/ftp" "/ftp/" "/assets" "/assets/" "/public" "/encryptionkeys"; do
  result=$(curl -s "http://10.20.30.80:3000$dir" | head -3)
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$dir")
  echo "[$code] $dir"
  if echo "$result" | grep -qi "index of\|listing\|directory"; then
    echo "  → 디렉터리 리스팅 활성화!"
  fi
done

echo ""
echo "=== Apache 디렉터리 리스팅 ==="
for dir in "/" "/icons/" "/manual/" "/cgi-bin/"; do
  result=$(curl -s "http://10.20.30.80:80$dir" | head -5)
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:80$dir")
  echo "[$code] $dir"
  if echo "$result" | grep -qi "index of\|listing\|directory"; then
    echo "  → 디렉터리 리스팅 활성화!"
  fi
done
```

### 4.3 JuiceShop /ftp 상세 탐색

```bash
# /ftp 디렉터리의 파일 목록과 내용 확인
echo "=== /ftp 파일 목록 ==="
curl -s http://10.20.30.80:3000/ftp/ | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        for f in data:
            print(f'  {f}')
    elif isinstance(data, dict):
        for f in data.get('data', data.get('files', [])):
            if isinstance(f, str):
                print(f'  {f}')
            else:
                print(f'  {f.get(\"name\", f)}')
except:
    print(sys.stdin.read()[:500])
" 2>/dev/null

# 각 파일 내용 확인
echo ""
echo "=== 주요 파일 내용 ==="
for file in "legal.md" "acquisitions.md" "package.json.bak" "coupons_2013.md.bak" "eastere.gg"; do
  echo "--- $file ---"
  curl -s "http://10.20.30.80:3000/ftp/$file" 2>/dev/null | head -5
  echo ""
done
```

---

## 5. 사용자 열거 (User Enumeration) (20분)

### 5.1 열거 공격이란?

에러 메시지의 차이를 이용하여 유효한 사용자명/이메일을 알아내는 공격이다.

```
존재하는 계정: "비밀번호가 틀렸습니다" ← 계정 존재 확인!
미존재 계정: "계정을 찾을 수 없습니다" ← 계정 없음 확인!

안전한 메시지: "이메일 또는 비밀번호가 올바르지 않습니다"
                (존재 여부를 알 수 없음)
```

### 5.2 JuiceShop 사용자 열거 테스트

```bash
# 로그인 에러 메시지 비교
echo "=== 사용자 열거 테스트 ==="

# 존재하는 이메일 + 잘못된 비밀번호
echo "존재하는 계정:"
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrong"}' | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('error','')[:100])" 2>/dev/null

# 존재하지 않는 이메일
echo "미존재 계정:"
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"nobody@nowhere.com","password":"wrong"}' | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('error','')[:100])" 2>/dev/null

echo ""
echo "두 메시지가 다르면 → 사용자 열거 가능 (취약)"
echo "두 메시지가 같으면 → 사용자 열거 불가 (양호)"
```

### 5.3 회원가입에서의 열거

```bash
# 이미 존재하는 이메일로 가입 시도
echo ""
echo "=== 회원가입 열거 ==="
echo "존재하는 이메일:"
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' | python3 -c "import sys; data=sys.stdin.read(); print(data[:150])" 2>/dev/null

echo ""
echo "새 이메일:"
curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"brand_new_user@test.com","password":"Test1234!","passwordRepeat":"Test1234!","securityQuestion":{"id":1},"securityAnswer":"a"}' | python3 -c "import sys; data=sys.stdin.read(); print(data[:150])" 2>/dev/null
```

### 5.4 비밀번호 찾기에서의 열거

```bash
# 비밀번호 재설정 기능에서 열거
echo ""
echo "=== 비밀번호 재설정 열거 ==="
echo "존재하는 이메일:"
curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","answer":"wrong","new":"Test1234!","repeat":"Test1234!"}' | head -3

echo ""
echo "미존재 이메일:"
curl -s -X POST http://10.20.30.80:3000/rest/user/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email":"nobody@test.com","answer":"wrong","new":"Test1234!","repeat":"Test1234!"}' | head -3
```

---

## 6. 종합 정보 노출 점검 스크립트 (20분)

```bash
# 자동 점검 스크립트
python3 << 'PYEOF'
import requests, json

BASE = "http://10.20.30.80:3000"
findings = []

print("=" * 60)
print("정보 노출 종합 점검")
print("=" * 60)

# 1. 서버 헤더
r = requests.head(BASE, timeout=5)
for header in ["Server", "X-Powered-By", "X-AspNet-Version", "X-Generator"]:
    val = r.headers.get(header)
    if val:
        findings.append(f"헤더 정보 노출: {header}: {val}")
        print(f"[!] {header}: {val}")

# 2. 보안 헤더 미설정
for header in ["X-Frame-Options", "X-Content-Type-Options",
               "Content-Security-Policy", "Strict-Transport-Security"]:
    if header not in r.headers:
        findings.append(f"보안 헤더 미설정: {header}")
        print(f"[-] {header}: 미설정")

# 3. 에러 정보 노출
r = requests.get(f"{BASE}/rest/products/search?q='", timeout=5)
try:
    err = r.json()
    if "error" in err:
        error_msg = str(err["error"])
        if "SQLITE" in error_msg.upper() or "stack" in error_msg.lower():
            findings.append("에러 메시지에 DB/스택 정보 노출")
            print(f"[!] 에러에 내부 정보 포함")
except:
    pass

# 4. 디렉터리/파일 노출
sensitive_paths = ["ftp", "metrics", ".env", "package.json", "encryptionkeys"]
for path in sensitive_paths:
    r = requests.get(f"{BASE}/{path}", timeout=5)
    if r.status_code == 200:
        findings.append(f"민감 경로 접근 가능: /{path}")
        print(f"[!] /{path}: 접근 가능 (HTTP {r.status_code})")

# 5. 요약
print(f"\n{'=' * 60}")
print(f"총 발견 사항: {len(findings)}건")
for i, f in enumerate(findings, 1):
    print(f"  {i}. {f}")
PYEOF
```

---

## 7. 실습 과제

### 과제 1: 에러 메시지 분석
1. 다양한 방법으로 JuiceShop에 에러를 유발하라 (최소 5가지)
2. 각 에러 응답에서 노출되는 정보를 분석하라
3. 가장 많은 정보를 노출하는 에러 패턴을 보고하라

### 과제 2: 정보 노출 점검
1. JuiceShop과 Apache의 디렉터리 리스팅 상태를 비교하라
2. 디버그/상태 엔드포인트를 모두 탐색하라
3. 소스맵 파일 노출 여부를 확인하라

### 과제 3: 사용자 열거
1. 로그인, 회원가입, 비밀번호 재설정에서 사용자 열거가 가능한지 테스트하라
2. 열거 가능/불가능한 기능을 구분하고 에러 메시지를 비교하라
3. 안전한 에러 메시지 예시를 제안하라

---

## 8. 요약

| 취약점 | 확인 방법 | 위험도 | 방어 |
|--------|----------|--------|------|
| 스택 트레이스 노출 | 에러 유도 | 중 | 운영 환경 에러 숨김 |
| 서버 버전 노출 | 헤더 확인 | 하 | 헤더 제거/변경 |
| 디렉터리 리스팅 | 디렉터리 URL 접근 | 중 | Options -Indexes |
| 디버그 모드 | 엔드포인트 탐색 | 상 | 운영 환경 비활성화 |
| 소스맵 노출 | .map 파일 접근 | 중 | 운영 빌드에서 제거 |
| 사용자 열거 | 에러 메시지 비교 | 중 | 일관된 에러 메시지 |

**다음 주 예고**: Week 12 - API 보안 점검. REST API 인증, Rate Limiting, Swagger 노출을 학습한다.


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

**Q1.** 이번 주차 "Week 11: 에러 처리 / 정보 노출 점검"의 핵심 목적은 무엇인가?
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

