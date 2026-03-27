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
