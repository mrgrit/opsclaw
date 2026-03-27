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
