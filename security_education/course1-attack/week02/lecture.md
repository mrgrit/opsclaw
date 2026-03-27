# Week 02: 정보수집과 정찰 (Reconnaissance)

## 학습 목표

- 침투 테스트의 첫 단계인 **정보수집(Reconnaissance)**의 개념을 이해한다
- nmap을 사용하여 네트워크 스캔을 수행하고 결과를 해석할 수 있다
- DNS 조회 도구(dig, host, nslookup)를 활용할 수 있다
- 웹 서버의 기술 스택을 파악하는 방법을 익힌다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| opsclaw | 10.20.30.201 | 실습 기지 (여기서 명령 실행) |
| secu | 10.20.30.1 | 방화벽/IPS 서버 |
| web | 10.20.30.80 | 웹 서버 (JuiceShop:3000, Apache:80) |
| siem | 10.20.30.100 | Wazuh SIEM |

SSH 접속:
```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.201
```

---

## 1. 정보수집이란?

침투 테스트(Penetration Test)는 크게 5단계로 진행된다:

1. **정보수집 (Reconnaissance)** <-- 이번 주 주제
2. 취약점 분석 (Vulnerability Analysis)
3. 공격 (Exploitation)
4. 후속 활동 (Post-Exploitation)
5. 보고서 작성 (Reporting)

정보수집은 대상 시스템에 대해 최대한 많은 정보를 수집하는 단계다. 실제 공격 전에 어떤 서비스가 열려 있는지, 어떤 소프트웨어를 사용하는지 파악해야 효과적인 공격 계획을 세울 수 있다.

### 수동 정찰 vs 능동 정찰

| 구분 | 수동 정찰 (Passive) | 능동 정찰 (Active) |
|------|---------------------|---------------------|
| 정의 | 대상에 직접 접촉하지 않고 정보 수집 | 대상에 직접 패킷을 보내서 정보 수집 |
| 예시 | Google 검색, WHOIS, DNS 조회 | nmap 포트 스캔, 배너 그래빙 |
| 탐지 가능성 | 낮음 | 높음 (IDS/IPS에 탐지될 수 있음) |

---

## 2. nmap - 네트워크 스캔의 핵심 도구

nmap(Network Mapper)은 네트워크 탐색과 보안 감사를 위한 오픈소스 도구다. 포트가 열려 있는지, 어떤 서비스가 실행 중인지, 운영체제가 무엇인지 알 수 있다.

### 2.1 기본 개념: 포트(Port)란?

컴퓨터에서 네트워크 서비스는 **포트 번호**로 구분된다. 포트는 0~65535 범위의 숫자다.

| 포트 | 서비스 | 설명 |
|------|--------|------|
| 22 | SSH | 원격 접속 |
| 80 | HTTP | 웹 서버 |
| 443 | HTTPS | 암호화된 웹 서버 |
| 3000 | 사용자 정의 | JuiceShop 등 |
| 3306 | MySQL | 데이터베이스 |

### 2.2 기본 스캔

```bash
# 가장 기본적인 스캔 - 상위 1000개 포트를 TCP Connect 방식으로 스캔
nmap 10.20.30.80
```

**예상 출력:**
```
Starting Nmap 7.94 ( https://nmap.org )
Nmap scan report for 10.20.30.80
Host is up (0.0010s latency).
Not shown: 996 closed tcp ports (conn-refused)
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
443/tcp  open  https
3000/tcp open  ppp

Nmap done: 1 IP address (1 host up) scanned in 1.23 seconds
```

> **해석**: web 서버에 SSH(22), HTTP(80), HTTPS(443), 그리고 3000번 포트가 열려 있다. 3000번은 JuiceShop이 실행 중인 포트다.

### 2.3 SYN 스캔 (-sS): 스텔스 스캔

TCP의 3-way handshake를 완료하지 않고 SYN 패킷만 보내서 응답을 확인한다. 연결을 완전히 맺지 않으므로 로그에 남기 어렵다.

```bash
# SYN 스캔 (root 권한 필요)
sudo nmap -sS 10.20.30.80
```

**TCP 3-way handshake 복습:**
```
정상 연결:  클라이언트 --SYN-->     서버
            클라이언트 <--SYN/ACK-- 서버
            클라이언트 --ACK-->     서버  (연결 완료)

SYN 스캔:   클라이언트 --SYN-->     서버
            클라이언트 <--SYN/ACK-- 서버  (포트 열림 확인!)
            클라이언트 --RST-->     서버  (연결 끊기 - 로그 안 남음)
```

### 2.4 서비스 버전 탐지 (-sV)

열린 포트에서 실행 중인 소프트웨어의 **정확한 이름과 버전**을 알아낸다.

```bash
nmap -sV 10.20.30.80
```

**예상 출력:**
```
PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 9.2p1 Debian 2+deb12u2 (protocol 2.0)
80/tcp   open  http     Apache httpd 2.4.59 ((Debian))
443/tcp  open  ssl/http Apache httpd 2.4.59
3000/tcp open  http     Node.js Express framework
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

> **핵심**: 버전 정보는 공격자에게 매우 중요하다. 예를 들어 "Apache 2.4.59"를 알면 해당 버전의 알려진 취약점(CVE)을 검색할 수 있다.

### 2.5 OS 탐지 (-O)

TCP/IP 스택의 특성을 분석하여 운영체제를 추측한다.

```bash
sudo nmap -O 10.20.30.80
```

**예상 출력:**
```
OS details: Linux 5.10 - 6.1
Network Distance: 1 hop
```

### 2.6 종합 스캔 (-A)

`-A` 옵션은 OS 탐지(-O), 버전 탐지(-sV), 스크립트 스캔(-sC), traceroute를 한 번에 실행한다.

```bash
sudo nmap -A 10.20.30.80
```

**예상 출력 (일부):**
```
PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 9.2p1 Debian
| ssh-hostkey:
|   256 aa:bb:cc:dd:... (ECDSA)
|_  256 ee:ff:00:11:... (ED25519)
80/tcp   open  http     Apache httpd 2.4.59 ((Debian))
|_http-title: Apache2 Debian Default Page
|_http-server-header: Apache/2.4.59 (Debian)
3000/tcp open  http     Node.js Express framework
|_http-title: OWASP Juice Shop
```

### 2.7 nmap 스크립트 엔진 (NSE)

nmap에는 수백 개의 자동화 스크립트가 내장되어 있다. `--script` 옵션으로 사용한다.

```bash
# 기본 스크립트 실행 (-sC와 동일)
nmap --script=default 10.20.30.80

# HTTP 관련 정보 수집
nmap --script=http-headers -p 80 10.20.30.80

# 특정 취약점 검사
nmap --script=http-vuln* -p 80,3000 10.20.30.80

# 사용 가능한 스크립트 목록 확인
ls /usr/share/nmap/scripts/ | head -20
```

**http-headers 스크립트 예상 출력:**
```
PORT   STATE SERVICE
80/tcp open  http
| http-headers:
|   Date: Thu, 27 Mar 2026 09:00:00 GMT
|   Server: Apache/2.4.59 (Debian)
|   Content-Type: text/html
|_  (Request type: HEAD)
```

### 2.8 전체 포트 스캔

기본 스캔은 상위 1000개 포트만 검사한다. 모든 포트를 검사하려면:

```bash
# 전체 65535 포트 스캔 (시간이 오래 걸림)
nmap -p- 10.20.30.80

# 특정 포트 범위 스캔
nmap -p 1-1000 10.20.30.80

# 특정 포트만 스캔
nmap -p 22,80,443,3000,8080 10.20.30.80
```

---

## 3. DNS 정보 수집

DNS(Domain Name System)는 도메인 이름을 IP 주소로 변환하는 시스템이다. DNS 조회를 통해 대상의 인프라 구조를 파악할 수 있다.

### 3.1 host 명령

가장 간단한 DNS 조회 도구다.

```bash
# 기본 조회
host 10.20.30.80

# 역방향 조회 (IP → 이름)
host 10.20.30.80
```

**예상 출력:**
```
80.30.20.10.in-addr.arpa domain name pointer web.
```

### 3.2 nslookup 명령

대화형 DNS 조회 도구다.

```bash
# 기본 조회
nslookup 10.20.30.80

# 특정 DNS 서버 지정
nslookup 10.20.30.80 10.20.30.1
```

### 3.3 dig 명령 (가장 상세)

DNS 전문가용 도구로, 가장 상세한 정보를 제공한다.

```bash
# 기본 조회
dig @10.20.30.1 web

# 역방향 조회
dig -x 10.20.30.80

# 모든 레코드 타입 조회
dig @10.20.30.1 web ANY

# 짧은 출력
dig +short @10.20.30.1 web
```

**dig 출력 구조:**
```
;; QUESTION SECTION:    <-- 질의 내용
;; ANSWER SECTION:      <-- 응답 (IP 주소 등)
;; AUTHORITY SECTION:   <-- 권한 있는 네임서버
;; ADDITIONAL SECTION:  <-- 추가 정보
```

---

## 4. 웹 서버 핑거프린팅

웹 서버가 사용하는 기술 스택(웹 서버, 프레임워크, 언어 등)을 파악하는 기법이다.

### 4.1 HTTP 헤더 분석 (curl)

curl은 HTTP 요청을 보내는 명령줄 도구다. 응답 헤더에 서버 정보가 포함되어 있다.

```bash
# 헤더만 가져오기 (-I: HEAD 요청)
curl -I http://10.20.30.80
```

**예상 출력:**
```
HTTP/1.1 200 OK
Date: Thu, 27 Mar 2026 09:00:00 GMT
Server: Apache/2.4.59 (Debian)
Content-Type: text/html; charset=UTF-8
```

```bash
# JuiceShop 헤더 확인
curl -I http://10.20.30.80:3000
```

**예상 출력:**
```
HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: text/html; charset=utf-8
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
```

> **분석**: `X-Powered-By: Express`를 통해 Node.js Express 프레임워크를 사용한다는 것을 알 수 있다. 이 헤더는 보안상 제거하는 것이 좋다.

```bash
# 응답 본문도 함께 보기 (-v: verbose)
curl -v http://10.20.30.80:3000 2>&1 | head -30
```

### 4.2 whatweb - 자동화된 웹 기술 탐지

whatweb은 웹사이트가 사용하는 기술을 자동으로 탐지하는 도구다.

```bash
# 기본 스캔
whatweb http://10.20.30.80

# JuiceShop 스캔
whatweb http://10.20.30.80:3000

# 상세 모드
whatweb -v http://10.20.30.80:3000
```

**예상 출력:**
```
http://10.20.30.80:3000 [200 OK] Country[RESERVED][ZZ],
Express, HTML5, HTTPServer[Express], IP[10.20.30.80],
Script, Title[OWASP Juice Shop], X-Frame-Options[SAMEORIGIN],
X-Powered-By[Express]
```

### 4.3 robots.txt 분석

`robots.txt`는 검색 엔진 크롤러에게 접근하면 안 되는 경로를 알려주는 파일이다. 하지만 공격자에게는 **숨겨진 경로의 목록**이 될 수 있다.

```bash
# Apache의 robots.txt 확인
curl http://10.20.30.80/robots.txt

# JuiceShop의 robots.txt 확인
curl http://10.20.30.80:3000/robots.txt
```

**JuiceShop 예상 출력:**
```
User-agent: *
Disallow: /ftp
```

> **분석**: `/ftp` 경로를 숨기려 하고 있다. 이는 공격자에게 "여기에 뭔가 흥미로운 것이 있다"는 신호다. 나중에 이 경로를 탐색할 것이다.

### 4.4 sitemap.xml 분석

```bash
# sitemap.xml 확인
curl http://10.20.30.80/sitemap.xml
curl http://10.20.30.80:3000/sitemap.xml
```

> sitemap.xml이 없으면 404 응답이 온다. 이것도 정보다 -- sitemap을 제공하지 않는다는 뜻이다.

---

## 5. 종합 실습: web 서버 완전 분석

### 실습 과제

web 서버(10.20.30.80)에 대해 종합적인 정보수집을 수행하고, 결과를 정리하라.

### Step 1: 포트 스캔

```bash
# 주요 포트 빠른 스캔
nmap -sV -p 1-10000 10.20.30.80
```

**기록할 내용:**
- 열린 포트 번호와 서비스 이름
- 각 서비스의 소프트웨어 버전

### Step 2: OS 탐지

```bash
sudo nmap -O 10.20.30.80
```

### Step 3: 웹 서버 헤더 분석

```bash
# Apache (포트 80)
curl -I http://10.20.30.80

# JuiceShop (포트 3000)
curl -I http://10.20.30.80:3000
```

### Step 4: 숨겨진 경로 탐색

```bash
# robots.txt
curl http://10.20.30.80:3000/robots.txt

# 발견한 /ftp 경로 접근
curl http://10.20.30.80:3000/ftp
```

**예상 출력 (/ftp):**
```json
["acquisitions.md","coupons_2013.md.bak","eastere.gg",
"incident-support.kdbx","legal.md","package.json.bak",
"quarantine","suspicious_errors.yml"]
```

> **분석**: `/ftp` 디렉토리에 백업 파일(.bak), 비밀번호 데이터베이스(.kdbx), 에러 로그 등 민감한 파일이 노출되어 있다. 이는 심각한 보안 문제다.

### Step 5: JuiceShop API 탐색

```bash
# JuiceShop REST API 엔드포인트 확인
curl -s http://10.20.30.80:3000/api/Products | python3 -m json.tool | head -30
```

**예상 출력:**
```json
{
    "status": "success",
    "data": [
        {
            "id": 1,
            "name": "Apple Juice (1000ml)",
            "description": "The all-time classic.",
            "price": 1.99,
            ...
        }
    ]
}
```

### Step 6: NSE 스크립트로 추가 정보 수집

```bash
# HTTP 관련 스크립트 실행
nmap --script=http-enum -p 80,3000 10.20.30.80
```

### Step 7: 다른 서버들도 스캔

```bash
# 방화벽 서버
nmap -sV 10.20.30.1

# SIEM 서버
nmap -sV 10.20.30.100
```

---

## 6. OpsClaw로 스캔 자동화

OpsClaw Manager API를 사용하면 스캔 작업을 자동화하고 결과를 기록할 수 있다.

```bash
# 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week02-recon","request_text":"web 서버 정보수집","master_mode":"external"}' \
  | python3 -m json.tool

# 프로젝트 ID를 확인하고 (예: proj_xxx)
# Stage 전환
curl -s -X POST http://localhost:8000/projects/{프로젝트ID}/plan \
  -H "X-API-Key: opsclaw-api-key-2026"
curl -s -X POST http://localhost:8000/projects/{프로젝트ID}/execute \
  -H "X-API-Key: opsclaw-api-key-2026"

# nmap 스캔 실행 (web 서버의 SubAgent를 통해)
curl -s -X POST http://localhost:8000/projects/{프로젝트ID}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"nmap -sV -p 1-10000 10.20.30.80", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 결과 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/{프로젝트ID}/evidence/summary \
  | python3 -m json.tool
```

---

## 7. 정보수집 결과 정리 템플릿

실습 후 다음 형식으로 결과를 정리하라:

| 항목 | 발견 내용 |
|------|-----------|
| 대상 IP | 10.20.30.80 |
| 열린 포트 | 22, 80, 443, 3000 |
| OS | Linux (Debian) |
| 웹 서버 (80) | Apache 2.4.59 |
| 웹 앱 (3000) | OWASP Juice Shop (Node.js Express) |
| 숨겨진 경로 | /ftp (민감 파일 노출) |
| 노출된 API | /api/Products, /rest/... |
| 보안 문제 | X-Powered-By 헤더 노출, /ftp 디렉토리 리스팅 |

---

## 8. 보안 관점: 정보수집 방어

공격자의 정보수집을 어렵게 만드는 방법:

1. **불필요한 포트 닫기**: 사용하지 않는 서비스는 중지
2. **배너 숨기기**: 서버 버전 정보를 응답 헤더에서 제거
3. **방화벽 설정**: 스캔 트래픽을 탐지하고 차단
4. **IDS/IPS**: Suricata 같은 도구로 포트 스캔 탐지 (secu 서버에 설치됨)
5. **robots.txt 최소화**: 민감한 경로를 robots.txt에 넣지 않기

---

## 과제

1. web 서버(10.20.30.80)의 포트 1-10000을 스캔하고, 발견한 모든 서비스와 버전을 정리하라
2. JuiceShop의 `/ftp` 디렉토리에서 접근 가능한 파일 목록을 작성하라
3. secu 서버(10.20.30.1)와 siem 서버(10.20.30.100)도 스캔하여 비교하라
4. nmap NSE 스크립트 중 `http-enum`을 사용하여 JuiceShop의 숨겨진 경로를 추가로 탐색하라

---

## 핵심 요약

- **nmap**은 침투 테스트의 필수 도구이며, 다양한 스캔 방식(-sS, -sV, -O, -A)을 상황에 맞게 선택한다
- **DNS 도구**(dig, host, nslookup)로 도메인과 IP의 관계를 파악한다
- **웹 핑거프린팅**(curl, whatweb)으로 서버의 기술 스택을 식별한다
- **robots.txt, /ftp** 등 숨겨진 경로에서 민감한 정보가 노출될 수 있다
- 정보수집 결과를 체계적으로 정리하는 것이 효과적인 침투 테스트의 기본이다

> **다음 주 예고**: Week 03에서는 HTTP 프로토콜의 구조를 깊이 있게 이해하고, JuiceShop의 쿠키, 세션, JWT 토큰을 직접 분석한다.
