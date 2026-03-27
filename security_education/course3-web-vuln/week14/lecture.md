# Week 14: 취약점 점검 보고서 작성법

## 학습 목표
- CVSS v3.1 점수 체계를 이해하고 취약점에 적용할 수 있다
- 재현 가능한 취약점 증명(PoC) 절차를 작성할 수 있다
- 전문적인 취약점 점검 보고서를 작성할 수 있다
- 권고사항을 위험도와 구현 난이도 기준으로 우선순위화한다

## 전제 조건
- Week 01~13 취약점 점검 실습 완료
- 기본적인 보고서 작성 경험

---

## 1. 취약점 점검 보고서 구조 (15분)

### 1.1 표준 보고서 구성

```
1. 표지 (프로젝트명, 일시, 점검 범위, 점검자)
2. 요약 (Executive Summary)
   - 점검 결과 요약 (통계)
   - 주요 발견사항 (Top 3)
   - 전체 위험도 평가
3. 점검 범위 및 방법론
   - 대상 시스템 목록
   - 사용 도구
   - 점검 방법론 (OWASP Testing Guide)
4. 발견사항 상세
   - 취약점별 상세 기술
5. 권고사항 (우선순위별)
6. 부록 (도구 출력, 스크린샷, 참고자료)
```

### 1.2 좋은 보고서 vs 나쁜 보고서

| 항목 | 좋은 보고서 | 나쁜 보고서 |
|------|-----------|-----------|
| 재현성 | 단계별 재현 가능 | "취약점 있음"만 기술 |
| 증거 | 스크린샷 + 요청/응답 | 도구 출력 복사 |
| 영향 | 비즈니스 영향 설명 | 기술 용어만 나열 |
| 권고사항 | 구체적 코드/설정 제시 | "보안 강화 필요" |
| 대상 독자 | 경영진 + 개발팀 분리 | 단일 기술 문서 |

---

## 2. CVSS v3.1 점수 체계 (25분)

### 2.1 CVSS 기본 지표 (Base Metrics)

| 지표 | 값 | 설명 |
|------|-----|------|
| Attack Vector (AV) | N/A/L/P | 네트워크/인접/로컬/물리 |
| Attack Complexity (AC) | L/H | 낮음/높음 |
| Privileges Required (PR) | N/L/H | 없음/낮음/높음 |
| User Interaction (UI) | N/R | 없음/필요 |
| Scope (S) | U/C | 변경없음/변경됨 |
| Confidentiality (C) | N/L/H | 없음/낮음/높음 |
| Integrity (I) | N/L/H | 없음/낮음/높음 |
| Availability (A) | N/L/H | 없음/낮음/높음 |

### 2.2 심각도 등급

| 점수 | 등급 | 색상 |
|------|------|------|
| 0.0 | None | - |
| 0.1 - 3.9 | Low | 녹색 |
| 4.0 - 6.9 | Medium | 황색 |
| 7.0 - 8.9 | High | 주황 |
| 9.0 - 10.0 | Critical | 적색 |

### 2.3 실습: JuiceShop 취약점 CVSS 산출

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
# CVSS v3.1 간이 계산기
def cvss_score(av, ac, pr, ui, scope, c, i, a):
    """CVSS v3.1 Base Score 간이 계산"""
    av_val = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
    ac_val = {"L": 0.77, "H": 0.44}

    # Scope Unchanged
    pr_u = {"N": 0.85, "L": 0.62, "H": 0.27}
    # Scope Changed
    pr_c = {"N": 0.85, "L": 0.68, "H": 0.50}

    ui_val = {"N": 0.85, "R": 0.62}
    cia_val = {"N": 0, "L": 0.22, "H": 0.56}

    pr_val = pr_c if scope == "C" else pr_u

    exploitability = 8.22 * av_val[av] * ac_val[ac] * pr_val[pr] * ui_val[ui]
    impact_sub = 1 - ((1 - cia_val[c]) * (1 - cia_val[i]) * (1 - cia_val[a]))

    if scope == "U":
        impact = 6.42 * impact_sub
    else:
        impact = 7.52 * (impact_sub - 0.029) - 3.25 * (impact_sub - 0.02) ** 15

    if impact <= 0:
        return 0.0

    if scope == "U":
        score = min(impact + exploitability, 10)
    else:
        score = min(1.08 * (impact + exploitability), 10)

    import math
    return math.ceil(score * 10) / 10

# JuiceShop 취약점별 CVSS 산출
vulns = [
    {
        "name": "SQL Injection (로그인 우회)",
        "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
        "params": ("N", "L", "N", "N", "U", "H", "H", "N"),
    },
    {
        "name": "Stored XSS (상품 리뷰)",
        "vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:R/S:C/C:L/I:L/A:N",
        "params": ("N", "L", "L", "R", "C", "L", "L", "N"),
    },
    {
        "name": "IDOR (주문 정보 접근)",
        "vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N",
        "params": ("N", "L", "L", "N", "U", "H", "N", "N"),
    },
    {
        "name": "보안 헤더 누락 (CSP)",
        "vector": "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:L/A:N",
        "params": ("N", "H", "N", "R", "U", "L", "L", "N"),
    },
]

print(f"{'취약점':<35} {'CVSS':<6} {'등급':<10}")
print("-" * 55)

for v in vulns:
    score = cvss_score(*v["params"])
    if score >= 9.0: grade = "Critical"
    elif score >= 7.0: grade = "High"
    elif score >= 4.0: grade = "Medium"
    elif score > 0: grade = "Low"
    else: grade = "None"
    print(f"{v['name']:<35} {score:<6.1f} {grade:<10}")
    print(f"  Vector: {v['vector']}")

PYEOF
ENDSSH
```

---

## 3. 취약점 상세 기술 작성 (25분)

### 3.1 취약점 카드 템플릿

```
[V-XXX] 취약점 제목
================================================================
심각도: Critical / High / Medium / Low
CVSS: X.X (벡터 문자열)
CWE: CWE-XXX (분류명)
OWASP: A01:2021 - 카테고리명
================================================================

1. 설명
   (취약점의 기술적 설명, 2-3문장)

2. 영향
   (비즈니스/기술적 영향, 구체적으로)

3. 재현 절차
   Step 1: ...
   Step 2: ...
   Step 3: ...

4. 증거
   (요청/응답 원문, 스크린샷)

5. 권고사항
   (구체적 수정 방법, 코드 예시 포함)

6. 참고자료
   (CWE, OWASP, CVE 링크)
================================================================
```

### 3.2 실습: SQL Injection 취약점 카드 작성

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
echo "=== 취약점 카드 작성 실습 ==="

# 재현 증거 수집
echo "--- Step 1: 정상 로그인 시도 ---"
curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"wrongpassword"}' | python3 -m json.tool 2>/dev/null || echo "JSON 파싱 실패"

echo ""
echo "--- Step 2: SQLi 페이로드 로그인 ---"
RESULT=$(curl -s -X POST http://localhost:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR 1=1--\",\"password\":\"x\"}")
echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"

echo ""
echo "--- Step 3: 응답 분석 ---"
echo "$RESULT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    if 'authentication' in d:
        auth = d['authentication']
        print(f'인증 토큰 발급됨: {auth.get(\"token\",\"\")[:50]}...')
        print(f'사용자 이메일: {auth.get(\"umail\",\"N/A\")}')
        print('=> SQL Injection으로 인증 우회 확인')
    else:
        print(f'응답: {str(d)[:200]}')
except:
    print('응답 파싱 불가')
" 2>/dev/null
ENDSSH
```

### 3.3 보고서 자동 생성 스크립트

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
from datetime import datetime

report = f"""
================================================================
        웹 취약점 점검 보고서
================================================================
프로젝트: JuiceShop 보안 점검
점검 일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}
점검 대상: http://localhost:3000 (OWASP JuiceShop)
점검 방법: OWASP Testing Guide v4.2
점검 도구: curl, Python, 수동 점검
================================================================

1. 요약 (Executive Summary)
----------------------------------------------------------------
총 발견 취약점: 5건
  - Critical: 1건
  - High:     1건
  - Medium:   2건
  - Low:      1건

주요 발견사항:
  1) SQL Injection을 통한 인증 우회 (Critical)
  2) 저장형 XSS 공격 가능 (High)
  3) 불충분한 접근제어 (Medium)

전체 위험도 평가: 높음
  → SQL Injection으로 전체 데이터 유출 및 관리자 접근 가능

2. 점검 범위
----------------------------------------------------------------
  - 웹 애플리케이션: JuiceShop (Node.js + Angular)
  - API: REST API (/rest/*, /api/*)
  - 인증/세션 관리
  - 입력값 검증
  - 접근제어
  - 보안 설정

3. 발견사항 상세
----------------------------------------------------------------
[V-001] SQL Injection - 로그인 인증 우회
  심각도: Critical (CVSS 9.8)
  CWE: CWE-89 (SQL Injection)
  OWASP: A03:2021 - Injection

  설명: 로그인 API의 email 파라미터에서 SQL Injection이
  가능하여 인증을 우회할 수 있다.

  영향: 임의의 사용자(관리자 포함) 계정으로 로그인 가능.
  전체 고객 데이터, 주문 정보, 결제 정보 유출 위험.

  재현 절차:
    1. POST /rest/user/login
    2. Body: {{"email":"' OR 1=1--","password":"x"}}
    3. 결과: 인증 토큰 발급됨

  권고사항:
    - Parameterized Query(PreparedStatement) 사용
    - ORM 활용 (Sequelize 등)
    - 입력값 화이트리스트 검증

[V-002] Stored XSS - 상품 리뷰
  심각도: High (CVSS 6.1)
  CWE: CWE-79 (Cross-site Scripting)
  OWASP: A03:2021 - Injection

  설명: 상품 리뷰 작성 시 HTML/JavaScript 코드가
  필터링 없이 저장되어 다른 사용자에게 실행된다.

  권고사항:
    - 출력 시 HTML 엔티티 인코딩
    - CSP 헤더 적용
    - DOMPurify 라이브러리 적용

================================================================
보고서 끝
================================================================
"""

print(report)

# 파일로 저장
with open("/tmp/vuln_report.txt", "w") as f:
    f.write(report)
print("보고서 저장: /tmp/vuln_report.txt")

PYEOF
ENDSSH
```

---

## 4. 권고사항 작성과 우선순위화 (20분)

### 4.1 권고사항 우선순위 매트릭스

```
           구현 난이도
        낮음        높음
    ┌──────────┬──────────┐
높  │  즉시    │  계획    │  위험도
음  │  시행    │  수립    │
    ├──────────┼──────────┤
낮  │  일반    │  장기    │
음  │  개선    │  과제    │
    └──────────┴──────────┘
```

### 4.2 권고사항 상세 작성 실습

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
recommendations = [
    {
        "vuln": "V-001 SQL Injection",
        "priority": "즉시 시행",
        "risk": "Critical",
        "effort": "Low",
        "recommendation": "Parameterized Query 적용",
        "code_before": "db.query('SELECT * FROM users WHERE email=\"' + email + '\"')",
        "code_after": "db.query('SELECT * FROM users WHERE email = ?', [email])",
    },
    {
        "vuln": "V-002 Stored XSS",
        "priority": "즉시 시행",
        "risk": "High",
        "effort": "Low",
        "recommendation": "출력 인코딩 + CSP 헤더",
        "code_before": "element.innerHTML = userReview",
        "code_after": "element.textContent = userReview  // 또는 DOMPurify.sanitize()",
    },
    {
        "vuln": "V-003 IDOR",
        "priority": "계획 수립",
        "risk": "Medium",
        "effort": "Medium",
        "recommendation": "서버사이드 권한 검증",
        "code_before": "GET /api/orders/:id  (id만 확인)",
        "code_after": "GET /api/orders/:id  (id + 세션 사용자 소유 확인)",
    },
]

print("=" * 70)
print("권고사항 상세")
print("=" * 70)

for idx, r in enumerate(recommendations, 1):
    print(f"\n[R-{idx:03d}] {r['vuln']}")
    print(f"  우선순위: {r['priority']}")
    print(f"  위험도: {r['risk']} / 구현 난이도: {r['effort']}")
    print(f"  권고: {r['recommendation']}")
    print(f"  수정 전: {r['code_before']}")
    print(f"  수정 후: {r['code_after']}")

PYEOF
ENDSSH
```

---

## 5. LLM을 활용한 보고서 자동화 (20분)

### 5.1 취약점 설명 자동 생성

```bash
# Ollama LLM으로 취약점 설명 자동 생성
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 컨설턴트입니다. 취약점 점검 보고서를 작성합니다. 한국어로 전문적이고 간결하게 작성하세요."},
      {"role": "user", "content": "다음 취약점의 보고서 항목을 작성하세요:\n\n취약점: SQL Injection\n위치: POST /rest/user/login (email 파라미터)\n페이로드: {\"email\":\"'"'"' OR 1=1--\",\"password\":\"x\"}\n결과: 인증 토큰 발급 (관리자 계정 포함)\n\n[설명], [영향], [권고사항]을 각각 2-3문장으로 작성하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 5.2 권고사항 코드 자동 생성

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Node.js/Express 보안 전문가입니다. 취약점 수정 코드를 제시합니다."},
      {"role": "user", "content": "SQL Injection 취약점이 있는 로그인 코드를 Sequelize ORM으로 안전하게 수정하는 코드를 보여주세요.\n\n취약한 코드:\nconst query = \"SELECT * FROM Users WHERE email = '"'"'\" + req.body.email + \"'"'"'\";\ndb.query(query)\n\n수정된 코드를 작성하세요."}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. 보고서 품질 체크리스트 (10분)

### 6.1 자가 점검 항목

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'ENDSSH'
python3 << 'PYEOF'
checklist = [
    ("표지", "프로젝트명, 일시, 점검 범위, 점검자 정보"),
    ("요약", "비기술 경영진도 이해할 수 있는 수준"),
    ("통계", "심각도별 취약점 수 그래프/표"),
    ("재현성", "모든 취약점에 단계별 재현 절차"),
    ("증거", "요청/응답 원문 또는 스크린샷 첨부"),
    ("CVSS", "모든 취약점에 CVSS 벡터 + 점수"),
    ("CWE", "모든 취약점에 CWE ID 부여"),
    ("영향", "비즈니스 관점 영향 분석"),
    ("권고", "구체적 코드/설정 수정 방법 제시"),
    ("우선순위", "위험도 + 난이도 기반 우선순위"),
    ("참고자료", "OWASP, CWE, CVE 링크"),
    ("맞춤법", "전문 용어 통일, 오타 없음"),
]

print("취약점 점검 보고서 품질 체크리스트")
print("=" * 55)
for idx, (item, desc) in enumerate(checklist, 1):
    print(f"  [ ] {idx:2d}. {item:<10} - {desc}")

print(f"\n총 {len(checklist)}개 항목")

PYEOF
ENDSSH
```

---

## 핵심 정리

1. 취약점 보고서는 재현성, 증거, 비즈니스 영향이 핵심이다
2. CVSS v3.1로 객관적 심각도를 산출하고 우선순위를 결정한다
3. 권고사항은 구체적 코드/설정 수준으로 제시해야 한다
4. 경영진용(요약)과 개발팀용(상세)을 분리하여 작성한다
5. LLM을 활용하면 보고서 초안 작성 효율을 높일 수 있다
6. 품질 체크리스트로 보고서 완성도를 검증한다

---

## 다음 주 예고
- Week 15: 기말 종합 웹취약점 점검 프로젝트
