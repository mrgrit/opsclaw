# Week 03: 정보수집 점검 (상세 버전)

## 학습 목표
- 웹 애플리케이션 점검의 첫 단계인 정보수집의 중요성을 이해한다
- 디렉터리/파일 스캐닝 기법을 curl 기반으로 실습한다
- 대상 서버의 기술 스택을 식별하는 방법을 익힌다
- SSL/TLS 설정을 점검하고 취약한 구성을 판별할 수 있다


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

# Week 03: 정보수집 점검

## 학습 목표
- 웹 애플리케이션 점검의 첫 단계인 정보수집의 중요성을 이해한다
- 디렉터리/파일 스캐닝 기법을 curl 기반으로 실습한다
- 대상 서버의 기술 스택을 식별하는 방법을 익힌다
- SSL/TLS 설정을 점검하고 취약한 구성을 판별할 수 있다

## 전제 조건
- Week 02 도구 환경 구축 완료
- curl 기본 사용법 숙지

---

## 1. 정보수집이 중요한 이유 (15분)

### 1.1 점검 프로세스에서의 위치

```
[정보수집] → 취약점 탐색 → 취약점 검증 → 보고서 작성
  ↑ 지금 여기
```

정보수집(Reconnaissance)은 공격 표면(Attack Surface)을 파악하는 단계이다.
무엇이 있는지 모르면 무엇을 점검할지도 모른다.

### 1.2 수집 대상

| 항목 | 예시 | 활용 |
|------|------|------|
| 디렉터리/파일 구조 | /admin, /api, /.env | 숨겨진 기능, 설정 파일 노출 |
| 기술 스택 | Node.js, Express, Angular | 알려진 취약점 검색 |
| HTTP 헤더 | Server, X-Powered-By | 버전 정보 → CVE 매핑 |
| 에러 메시지 | Stack trace, DB 에러 | 내부 구조 유추 |
| robots.txt, sitemap | 크롤링 제외 경로 | 민감한 경로 힌트 |

### 1.3 수동 vs 자동 정보수집

| 방식 | 장점 | 단점 |
|------|------|------|
| 수동 (curl) | 정밀, 은밀, 맞춤형 | 느림, 경험 필요 |
| 자동 (dirb, gobuster) | 빠름, 대량 스캔 | 노이즈 많음, 탐지 쉬움 |

---

## 2. robots.txt / sitemap 분석 (15분)

### 2.1 robots.txt 확인

```bash
# JuiceShop의 robots.txt 확인
curl -s http://10.20.30.80:3000/robots.txt

# Apache의 robots.txt 확인
curl -s http://10.20.30.80:80/robots.txt
```

**보안 관점**: robots.txt에 `Disallow`로 지정된 경로는 오히려 민감한 페이지의 힌트가 된다.
검색엔진 크롤러는 지시를 따르지만 공격자는 따르지 않는다.

### 2.2 sitemap.xml 확인

```bash
curl -s http://10.20.30.80:3000/sitemap.xml
curl -s http://10.20.30.80:80/sitemap.xml
```

### 2.3 .well-known 디렉터리

```bash
# 보안 관련 공개 정보
curl -s http://10.20.30.80:3000/.well-known/security.txt
curl -s http://10.20.30.80:3000/.well-known/openid-configuration
```

---

## 3. 디렉터리 스캐닝 (40분)

### 3.1 개념: dirb/gobuster

**dirb**와 **gobuster**는 사전 파일(wordlist)을 이용해 웹 서버의 숨겨진 디렉터리와 파일을 찾는 도구이다.

```
# dirb 동작 원리 (개념)
# wordlist의 각 단어를 URL에 붙여서 요청 → 200/301/403 등 확인
# /admin → 200 OK (존재!)
# /secret → 404 Not Found (없음)
# /backup → 403 Forbidden (접근 차단 = 존재함!)
```

### 3.2 curl 기반 디렉터리 스캐닝 (직접 구현)

도구 설치 없이 curl과 wordlist로 같은 효과를 낼 수 있다.

```bash
# 기본 wordlist 생성
cat > /tmp/webdirs.txt << 'WORDLIST'
admin
api
login
register
console
debug
backup
test
.env
.git
.git/config
.git/HEAD
config
robots.txt
sitemap.xml
swagger
api-docs
graphql
rest
ftp
WORDLIST

# curl 기반 디렉터리 스캔 스크립트
while IFS= read -r path; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$path")
  if [ "$code" != "404" ]; then
    echo "[${code}] /$path"
  fi
done < /tmp/webdirs.txt
```

### 3.3 JuiceShop 숨겨진 경로 탐색

```bash
# JuiceShop에 특화된 경로 목록
for path in \
  "ftp" \
  "api/Products/1" \
  "rest/products/search?q=test" \
  "rest/user/whoami" \
  "api/SecurityQuestions" \
  "api/Challenges" \
  "api/Complaints" \
  "api/Feedbacks" \
  "api/Quantitys" \
  "rest/languages" \
  "rest/memories" \
  "rest/chatbot/status" \
  "metrics" \
  "promotion" \
  "video" \
  "encryptionkeys" \
  "assets/public/images/uploads"; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$path")
  size=$(curl -o /dev/null -s -w "%{size_download}" "http://10.20.30.80:3000/$path")
  echo "[${code}] (${size}B) /$path"
done
```

### 3.4 FTP 디렉터리 탐색

```bash
# JuiceShop의 /ftp 디렉터리는 파일 목록을 노출할 수 있다
curl -s http://10.20.30.80:3000/ftp/ | python3 -m json.tool 2>/dev/null || \
  curl -s http://10.20.30.80:3000/ftp/

# FTP에 있는 파일 다운로드 시도
curl -s http://10.20.30.80:3000/ftp/legal.md
curl -s http://10.20.30.80:3000/ftp/acquisitions.md
```

### 3.5 디렉터리 스캔 결과 분석

| 응답 코드 | 의미 | 점검 시 행동 |
|-----------|------|-------------|
| 200 | 정상 접근 | 내용 확인, 민감 정보 여부 |
| 301/302 | 리다이렉트 | 리다이렉트 대상 확인 |
| 403 | 접근 거부 | 존재 확인됨, 우회 시도 가능 |
| 404 | 미존재 | 무시 |
| 500 | 서버 에러 | 에러 메시지에 정보 노출 가능 |

---

## 4. 기술 스택 식별 (30분)

### 4.1 HTTP 응답 헤더 분석

```bash
# 응답 헤더에서 기술 스택 정보 추출
echo "=== JuiceShop (포트 3000) ==="
curl -sI http://10.20.30.80:3000 | grep -iE "server|x-powered|x-generator|x-aspnet|set-cookie"

echo ""
echo "=== Apache (포트 80) ==="
curl -sI http://10.20.30.80:80 | grep -iE "server|x-powered|x-generator|x-aspnet|set-cookie"
```

### 4.2 쿠키 분석

```bash
# 쿠키 이름으로 기술 스택 추측
curl -sI http://10.20.30.80:3000 | grep -i set-cookie

# 쿠키 이름 → 기술 스택 매핑
# PHPSESSID → PHP
# JSESSIONID → Java (Tomcat/Spring)
# ASP.NET_SessionId → ASP.NET
# connect.sid → Node.js (Express)
# token → JWT 기반 인증
```

### 4.3 에러 페이지 분석

```bash
# 존재하지 않는 경로로 404 에러 유도
curl -s http://10.20.30.80:3000/nonexistent_path_12345

# 잘못된 API 요청으로 에러 유도
curl -s http://10.20.30.80:3000/api/Products/abc

# 에러 메시지에서 기술 정보 추출
# - Express 버전
# - Node.js 버전
# - 스택 트레이스(stack trace) 중 파일 경로
```

### 4.4 JavaScript 소스 분석

```bash
# HTML에서 JS 파일 경로 추출
curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*\.js"' | head -10

# main.js 등에서 API 엔드포인트 추출
MAIN_JS=$(curl -s http://10.20.30.80:3000 | grep -oE 'src="[^"]*main[^"]*\.js"' | head -1 | sed 's/src="//;s/"//')
if [ -n "$MAIN_JS" ]; then
  echo "Main JS: $MAIN_JS"
  curl -s "http://10.20.30.80:3000/$MAIN_JS" | grep -oE '/api/[a-zA-Z/]+|/rest/[a-zA-Z/]+' | sort -u | head -20
fi
```

### 4.5 기술 스택 정리 템플릿

```
대상: http://10.20.30.80:3000
---
웹 서버: Express (Node.js)
프레임워크: Angular (프론트엔드)
DB: SQLite (JuiceShop 기본)
인증 방식: JWT (Bearer Token)
추가 정보:
- /ftp 디렉터리 노출
- robots.txt 존재
```

---

## 5. SSL/TLS 점검 (20분)

### 5.1 TLS의 중요성

| 항목 | HTTP | HTTPS |
|------|------|-------|
| 데이터 암호화 | X | O |
| 서버 인증 | X | O |
| 무결성 보장 | X | O |
| 중간자 공격 | 취약 | 방어 |

### 5.2 openssl을 이용한 TLS 점검

```bash
# TLS 연결 테스트 (대상이 HTTPS를 지원하는 경우)
# 실습 서버는 HTTP이므로, 개념 이해용 명령
# openssl s_client -connect example.com:443 -servername example.com < /dev/null 2>/dev/null | head -20

# 인증서 정보 확인
# openssl s_client -connect example.com:443 < /dev/null 2>/dev/null | openssl x509 -noout -dates -subject

# 지원 프로토콜 확인
# openssl s_client -connect example.com:443 -tls1_2 < /dev/null 2>&1 | grep "Protocol"
```

### 5.3 curl로 TLS 정보 확인

```bash
# HTTPS 사이트의 인증서 정보 (참고용 외부 사이트)
# curl -vI https://www.google.com 2>&1 | grep -E "SSL|TLS|subject|expire|issuer"

# HTTP 전용 서버에 HTTPS 시도 (에러 확인)
curl -vI https://10.20.30.80:3000 2>&1 | head -10
# 예상: SSL 관련 에러 → HTTPS 미지원 확인
```

### 5.4 점검 체크리스트

```
[ ] HTTPS 지원 여부
[ ] HTTP → HTTPS 리다이렉트 여부
[ ] TLS 1.2 이상만 허용하는지
[ ] 인증서 유효기간
[ ] 인증서 발급자 (자체 서명 여부)
[ ] 취약한 암호 스위트 (RC4, DES, 3DES 등)
[ ] HSTS 헤더 설정 여부
```

---

## 6. 종합 실습: 정보수집 보고서 작성 (30분)

### 6.1 보고서 템플릿

```bash
cat > /tmp/recon_report.md << 'EOF'
# 정보수집 보고서

## 1. 대상 정보
- URL: http://10.20.30.80:3000
- 서비스: OWASP JuiceShop
- 점검 일시: $(date)

## 2. 기술 스택
- 웹 서버:
- 프레임워크:
- 데이터베이스:
- 인증 방식:

## 3. 발견된 디렉터리/파일
| 경로 | 응답코드 | 설명 |
|------|---------|------|
| / | 200 | 메인 페이지 |
| /ftp | | |
| /api | | |

## 4. 보안 헤더 점검
| 헤더 | 존재여부 | 값 |
|------|---------|-----|
| X-Frame-Options | | |
| X-Content-Type-Options | | |
| Content-Security-Policy | | |

## 5. TLS 설정
- HTTPS 지원:
- HSTS 설정:

## 6. 정보 노출 항목
(에러 메시지, 버전 정보 등)

## 7. 요약 및 다음 단계
EOF

echo "보고서 템플릿이 /tmp/recon_report.md에 생성되었습니다."
```

---

## 7. 실습 과제

### 과제 1: 디렉터리 스캐닝
1. 제공된 wordlist로 JuiceShop의 숨겨진 경로를 모두 찾아라
2. 발견된 각 경로의 내용을 확인하고 위험도를 평가하라
3. `/ftp` 디렉터리에서 다운로드 가능한 파일 목록을 작성하라

### 과제 2: 기술 스택 식별
1. JuiceShop의 기술 스택을 모두 식별하라 (서버, 프레임워크, DB, 인증)
2. Apache(포트 80)의 기술 스택도 동일하게 식별하라
3. 두 서비스의 보안 헤더를 비교 분석하라

### 과제 3: 정보수집 보고서
1. 위 템플릿을 기반으로 JuiceShop 정보수집 보고서를 완성하라
2. 발견된 정보 중 공격에 활용될 수 있는 항목을 3가지 이상 서술하라

---

## 8. 요약

| 기법 | 도구/명령 | 발견 가능한 것 |
|------|----------|----------------|
| robots.txt 분석 | curl | 숨겨진 경로 힌트 |
| 디렉터리 스캐닝 | curl + wordlist | 숨겨진 페이지, 파일 |
| 헤더 분석 | curl -I | 서버 종류, 버전 |
| 에러 분석 | curl + 잘못된 요청 | 내부 구조, 파일 경로 |
| TLS 점검 | openssl, curl -v | 암호화 설정 |

**다음 주 예고**: Week 04 - 인증/세션 관리 점검. 비밀번호 정책, 세션 타임아웃, JWT 검증을 학습한다.


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 03: 정보수집 점검"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **웹 취약점 점검의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "전제 조건"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "1. 정보수집이 중요한 이유 (15분)"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **웹 취약점 점검 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "2. robots.txt / sitemap 분석 (15분)"의 실무 활용 방안은?
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
