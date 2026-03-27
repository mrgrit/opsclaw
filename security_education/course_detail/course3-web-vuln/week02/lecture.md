# Week 02: 점검 도구 환경 구축 (상세 버전)

## 학습 목표
- 웹 취약점 점검에 사용되는 대표 도구의 역할과 차이를 이해한다
- OWASP ZAP 프록시의 기본 동작 원리를 파악한다
- nikto, sqlmap, curl을 실습 환경에서 직접 설치하고 실행한다
- curl 고급 옵션을 활용하여 HTTP 요청을 세밀하게 제어할 수 있다
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

# Week 02: 점검 도구 환경 구축

## 학습 목표
- 웹 취약점 점검에 사용되는 대표 도구의 역할과 차이를 이해한다
- OWASP ZAP 프록시의 기본 동작 원리를 파악한다
- nikto, sqlmap, curl을 실습 환경에서 직접 설치하고 실행한다
- curl 고급 옵션을 활용하여 HTTP 요청을 세밀하게 제어할 수 있다

## 전제 조건
- SSH로 실습 서버 접속 가능 (Week 01 완료)
- HTTP 요청/응답의 기본 구조를 이해함

---

## 1. 웹 취약점 점검 도구 개요 (20분)

### 1.1 도구 분류

| 분류 | 도구 | 역할 |
|------|------|------|
| **프록시 도구** | Burp Suite, OWASP ZAP | 브라우저↔서버 사이에서 요청/응답 가로채기 |
| **스캐너** | nikto, Nessus | 알려진 취약점 자동 탐지 |
| **특화 도구** | sqlmap, XSSer | 특정 취약점(SQLi, XSS) 자동 공격 |
| **범용 도구** | curl, wget, httpie | 수동 HTTP 요청 전송 |

### 1.2 점검 워크플로우

```
1. 정보수집 (nikto, curl)
   ↓
2. 프록시 설정 (ZAP/Burp)
   ↓
3. 수동 점검 (프록시로 요청 변조)
   ↓
4. 자동 점검 (sqlmap, ZAP Scanner)
   ↓
5. 결과 분석 및 보고서 작성
```

### 1.3 합법적 점검의 원칙

> **중요**: 취약점 점검은 반드시 **허가된 대상**에서만 수행한다.
> 이 수업에서는 실습 전용 서버(JuiceShop)만 대상으로 한다.

- 점검 전 서면 동의서 확보 (실무)
- 점검 범위와 시간을 명확히 정의
- 발견된 취약점은 책임 있게 보고 (Responsible Disclosure)

---

## 2. 실습 환경 접속 확인 (10분)

### 2.1 web 서버 접속

```bash
# opsclaw 서버에서 web 서버로 SSH 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80
```

### 2.2 JuiceShop 동작 확인

```bash
# JuiceShop 프로세스 확인
curl -s http://10.20.30.80:3000 | head -20

# HTTP 응답 코드 확인
curl -o /dev/null -s -w "%{http_code}" http://10.20.30.80:3000
# 예상 결과: 200
```

### 2.3 Apache + ModSecurity 확인

```bash
# Apache 상태 확인
curl -s -o /dev/null -w "%{http_code}" http://10.20.30.80:80

# 서버 헤더 확인
curl -sI http://10.20.30.80:80 | grep -i server
```

---

## 3. Burp Suite 개념 이해 (15분)

### 3.1 Burp Suite란?

Burp Suite는 PortSwigger사에서 만든 웹 취약점 점검의 표준 도구이다.
Community Edition(무료)과 Professional Edition(유료)이 있다.

**핵심 기능:**

| 기능 | 설명 |
|------|------|
| **Proxy** | 브라우저 트래픽 가로채기 (Intercept) |
| **Repeater** | 요청을 수정하여 재전송 |
| **Intruder** | 페이로드 자동 삽입 (무차별 대입) |
| **Scanner** | 자동 취약점 스캔 (Pro 전용) |
| **Decoder** | 인코딩/디코딩 변환 |

### 3.2 프록시 동작 원리

```
[브라우저] → [프록시:8080] → [웹서버]
                  ↑
            요청을 가로채서
            확인/수정 후 전달
```

- 브라우저의 프록시 설정을 `127.0.0.1:8080`으로 변경
- HTTPS 트래픽 가로채기 위해 Burp CA 인증서 설치 필요
- **이 수업에서는 설치하지 않고 개념만 이해** (대신 ZAP과 curl 사용)

---

## 4. OWASP ZAP 설치 및 사용 (30분)

### 4.1 OWASP ZAP이란?

OWASP Zed Attack Proxy(ZAP)는 무료 오픈소스 웹 보안 점검 도구이다.
Burp Suite의 무료 대안으로, 자동 스캔 기능이 무료로 제공된다.

### 4.2 ZAP CLI 설치 (실습 서버)

```bash
# opsclaw 서버에서 실행
# ZAP은 GUI 도구이지만, CLI/API 모드로도 사용 가능

# Python 기반 ZAP CLI 도구 확인
pip3 install python-owasp-zap-v2.4 2>/dev/null || echo "이미 설치됨"
```

### 4.3 ZAP을 활용한 기본 스캔 (개념)

```
# ZAP daemon 모드 실행 (GUI 없는 서버에서)
# zap.sh -daemon -port 8090 -config api.key=zap-api-key

# API로 스캔 시작
# curl "http://localhost:8090/JSON/spider/action/scan/?url=http://10.20.30.80:3000&apikey=zap-api-key"

# 이 수업에서는 Week 13에서 자동화 스캔을 본격적으로 다룸
# 지금은 수동 도구(curl, nikto)부터 익히자
```

---

## 5. nikto 설치 및 사용 (30분)

### 5.1 nikto란?

nikto는 웹 서버의 알려진 취약점, 기본 파일, 잘못된 설정을 스캔하는 도구이다.
6,700개 이상의 위험한 파일/프로그램을 검사한다.

### 5.2 설치

```bash
# opsclaw 서버에서 실행
which nikto || echo "1" | sudo -S apt-get install -y nikto
```

### 5.3 기본 스캔

```bash
# JuiceShop 대상 nikto 스캔 (기본)
nikto -h http://10.20.30.80:3000 -maxtime 60s

# 출력 예시:
# + Server: Express
# + /: The anti-clickjacking X-Frame-Options header is not present.
# + /: The X-Content-Type-Options header is not set.
# + No CGI Directories found
```

### 5.4 주요 옵션

```bash
# 특정 포트 지정
nikto -h 10.20.30.80 -p 3000

# 출력을 파일로 저장 (HTML 형식)
nikto -h http://10.20.30.80:3000 -o /tmp/nikto_juice.html -Format html

# 출력을 CSV 형식으로 저장
nikto -h http://10.20.30.80:3000 -o /tmp/nikto_juice.csv -Format csv

# SSL 사이트 스캔 (참고용)
# nikto -h https://example.com -ssl

# 특정 튜닝 옵션 (점검 항목 선택)
# 1=흥미로운 파일, 2=잘못된 설정, 3=정보 노출, 4=XSS
nikto -h http://10.20.30.80:3000 -Tuning 1234 -maxtime 60s
```

### 5.5 결과 해석

nikto 결과에서 주의할 항목:

| 표시 | 의미 |
|------|------|
| `+` | 정보성 메시지 |
| `OSVDB-XXXX` | Open Source Vulnerability Database 항목 |
| `X-Frame-Options not set` | 클릭재킹 취약 가능 |
| `X-Content-Type-Options not set` | MIME 스니핑 가능 |
| `Server: Express` | 서버 기술 스택 노출 |

---

## 6. sqlmap 설치 및 기본 사용 (20분)

### 6.1 sqlmap이란?

sqlmap은 SQL Injection 취약점 탐지 및 공격 자동화 도구이다.
다양한 DBMS(MySQL, PostgreSQL, SQLite 등)를 지원한다.

### 6.2 설치

```bash
# 설치 확인
which sqlmap || echo "1" | sudo -S apt-get install -y sqlmap

# 버전 확인
sqlmap --version
```

### 6.3 기본 사용법 (맛보기, Week 05에서 상세 학습)

```bash
# URL의 파라미터에 SQLi 테스트
# --batch: 모든 질문에 기본값으로 자동 응답
sqlmap -u "http://10.20.30.80:3000/rest/products/search?q=test" --batch --level=1 --risk=1

# 주의: JuiceShop는 NoSQL 기반이므로 전통적 SQLi와 다를 수 있음
# Week 05에서 다양한 SQLi 기법을 상세히 학습한다
```

---

## 7. curl 고급 활용 (40분)

### 7.1 curl 기본 복습

```bash
# GET 요청
curl http://10.20.30.80:3000

# 응답 헤더만 보기
curl -I http://10.20.30.80:3000

# 헤더 + 본문 모두 보기
curl -i http://10.20.30.80:3000
```

### 7.2 POST 요청 보내기

```bash
# JSON 데이터로 로그인 시도 (JuiceShop)
curl -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op","password":"wrong"}'

# 응답 확인 - 에러 메시지에 정보 노출이 있는지 확인
```

### 7.3 쿠키 다루기

```bash
# 쿠키 저장
curl -c /tmp/cookies.txt http://10.20.30.80:3000

# 저장된 쿠키로 요청
curl -b /tmp/cookies.txt http://10.20.30.80:3000/rest/basket/1

# 쿠키 직접 지정
curl -b "token=abc123" http://10.20.30.80:3000/rest/basket/1
```

### 7.4 HTTP 헤더 조작

```bash
# User-Agent 변경
curl -H "User-Agent: Mozilla/5.0 (Security Scanner)" http://10.20.30.80:3000

# Referer 위조
curl -H "Referer: http://10.20.30.80:3000/admin" http://10.20.30.80:3000

# 여러 헤더 동시 설정
curl -H "Accept: application/json" \
     -H "Authorization: Bearer fake-token" \
     http://10.20.30.80:3000/api/Products/1
```

### 7.5 상세 정보 출력

```bash
# 요청/응답 전체 과정 출력 (-v verbose)
curl -v http://10.20.30.80:3000/rest/products/search?q=apple 2>&1 | head -30

# 응답 시간 측정
curl -o /dev/null -s -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" http://10.20.30.80:3000

# 리다이렉트 따라가기
curl -L http://10.20.30.80:3000
```

### 7.6 파일 업로드 테스트

```bash
# 테스트 파일 생성
echo "test file content" > /tmp/test_upload.txt

# multipart form 업로드
curl -X POST http://10.20.30.80:3000/file-upload \
  -F "file=@/tmp/test_upload.txt" \
  -v 2>&1 | tail -20
```

### 7.7 curl을 이용한 간이 스캐닝

```bash
# 여러 경로를 순회하며 존재 여부 확인
for path in admin robots.txt .env .git/config sitemap.xml; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$path")
  echo "$code - /$path"
done
```

---

## 8. 실습 과제

### 과제 1: nikto 스캔 결과 분석
1. nikto로 JuiceShop(포트 3000)을 스캔하라
2. 결과를 `/tmp/nikto_result.txt`로 저장하라
3. 발견된 항목 중 보안상 의미 있는 3가지를 골라 설명하라

### 과제 2: curl로 JuiceShop 탐색
1. JuiceShop의 REST API 엔드포인트 5개를 찾아라 (힌트: `/api/`, `/rest/`)
2. 각 엔드포인트의 응답 코드와 Content-Type을 기록하라
3. 로그인 API에 잘못된 인증 정보를 보내고 에러 응답을 분석하라

### 과제 3: HTTP 헤더 보안 점검
1. curl -I로 JuiceShop의 응답 헤더를 확인하라
2. 다음 보안 헤더의 존재 여부를 확인하라:
   - `X-Frame-Options`
   - `X-Content-Type-Options`
   - `Content-Security-Policy`
   - `Strict-Transport-Security`
3. 누락된 헤더가 있으면 어떤 공격에 취약한지 서술하라

---

## 9. 요약

| 도구 | 용도 | 이번 수업 실습 |
|------|------|----------------|
| Burp Suite | 프록시 + 수동점검 | 개념 이해 |
| OWASP ZAP | 프록시 + 자동스캔 | 설치 확인 |
| nikto | 웹서버 취약점 스캔 | 기본 스캔 실행 |
| sqlmap | SQL Injection 자동화 | 설치 확인 (Week 05 상세) |
| curl | 수동 HTTP 요청 | 고급 옵션 실습 |

**다음 주 예고**: Week 03 - 정보수집 점검. 디렉터리 스캐닝, 기술 스택 식별, SSL/TLS 점검을 학습한다.


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

**Q1.** 이번 주차 "Week 02: 점검 도구 환경 구축"의 핵심 목적은 무엇인가?
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

