# Red Team Turn 1 - 공격 보고서
**페르소나**: Red Team (레드팀)
**시작**: 2026-03-25 01:45:11 KST
**종료**: 2026-03-25 02:01:40 KST
**소요**: ~16분
**공격 서버**: test2 (192.168.208.139, Ubuntu 22.04)
**공격 대상**: 10.20.30.0/24 내부망

---

## 정찰 결과

### 호스트 발견
| 호스트 | IP | MAC | 서비스 |
|--------|-----|-----|--------|
| secu | 10.20.30.1 | 00:0c:29:7a:07:36 | SSH,HTTP(nginx),8002,8338 |
| web | 10.20.30.80 | 00:0c:29:be:61:0e | SSH,HTTP(nginx),8002 |
| siem | 10.20.30.100 | 00:0c:29:ea:ca:fe | SSH,HTTP(nginx),443,8002 |
| opsclaw | 10.20.30.201 | 00:0c:29:c2:4e:8b | SSH,HTTP(nginx),**8000**,8002 |

### 서비스 식별
- secu:80 → Juice Shop (OWASP 취약 웹앱) ← [!] 잘못된 라우팅 발견
- web:80 → Juice Shop (BunkerWeb WAF 경유)
- opsclaw:8000 → Manager API (uvicorn)
- secu:8338 → maltrail 서버

---

## 취약점 발견 및 공격 성공 내역

### 🔴 CRITICAL-1: Juice Shop 관리자 기본 패스워드
- **위치**: http://10.20.30.80/rest/user/login
- **취약점**: 기본 자격증명 사용
- **공격**: `admin@juice-sh.op / admin123`
- **결과**: JWT 관리자 토큰 획득
  ```
  eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...
  Decoded: {email: "admin@juice-sh.op", role: "admin"}
  ```
- **영향**: 전체 사용자 21명 데이터 노출 (5명 admin 포함)

### 🔴 CRITICAL-2: FTP 디렉토리 목록 + 기밀 파일 노출
- **위치**: http://10.20.30.80/ftp/
- **취약점**: Directory Listing, 파일 접근 제어 미흡
- **노출 파일**:
  - `acquisitions.md` - **기밀 M&A 계획서** ("Do not distribute!")
  - `incident-support.kdbx` - **KeePass 패스워드 데이터베이스** (다운로드 성공)
  - `coupons_2013.md.bak`, `package.json.bak` - 구성 파일 백업
  - `encrypt.pyc`, `announcement_encrypted.md`
- **결과**: KeePass DB 로컬 저장 완료 (`/tmp/incident.kdbx`, 3246 bytes)

### 🔴 CRITICAL-3: OpsClaw API 인증 없이 RCE 달성
- **위치**: http://10.20.30.201:8000
- **취약점**: Manager API에 인증 메커니즘 없음
- **공격 단계**:
  1. `POST /projects` → 프로젝트 생성 (무인증)
  2. `POST /projects/{id}/plan` + `/execute` → 스테이지 전환
  3. `POST /projects/{id}/execute-plan` → secu SubAgent로 명령 전달
- **실행 명령**: `id; hostname; cat /etc/passwd | head -3`
- **결과**:
  ```
  uid=1000(secu) gid=1000(secu) groups=1000(secu),4(adm),24(cdrom),27(sudo)...
  secu
  root:x:0:0:root:/root:/bin/bash
  ```
- **영향**: secu 서버에 secu 유저로 임의 명령 실행 가능
  - SubAgent가 있는 모든 서버 (secu, web, siem, opsclaw) 접근 가능

### 🟡 MEDIUM-1: 내부 인프라 정보 노출
- OpsClaw `/pow/leaderboard`: 에이전트 IP 목록 노출
- OpsClaw `/projects`: 50개 운영 프로젝트 및 작업 내역 노출
- 내부망 구조 완전 파악 (4개 호스트, IP/MAC 확인)

### 🟡 MEDIUM-2: 사용자 정보 대량 노출
- `/api/Users` (관리자 토큰으로 접근): 21명 이메일/역할/비밀번호해시 노출
- 이메일 주소로 소셜엔지니어링 가능

### 🟢 LOW-1: secu:80 잘못된 서비스 노출
- secu(방화벽 서버)의 80 포트에 Juice Shop 응답 - 라우팅 오설정 가능성

---

## 실패한 공격

| 공격 | 결과 | 이유 |
|------|------|------|
| SQL Injection (login) | 실패 | WAF 또는 Juice Shop 자체 필터링 |
| XSS via Feedback | 403 Forbidden | BunkerWeb WAF 차단 |
| FTP pyc/kdbx 직접 접근 | 403 | Nginx 접근 제어 |
| SSH 연결 (패스워드) | 미시도 | 규칙: SSH 브루트포스 금지 |
| Wazuh API | 401 Unauthorized | 토큰 기반 인증 동작 중 |

---

## 사용 도구

- nmap, masscan (포트 스캔)
- whatweb (웹 핑거프린팅)
- curl (REST API 공격)
- arp-scan (호스트 탐지)
- sqlmap (SQLi 테스트)
- nikto (웹 취약점)

---

## 요약 (레드팀 판정: 공격 성공)

**3개 Critical 취약점 달성**:
1. ✅ 관리자 계정 탈취
2. ✅ 기밀 파일 다운로드 (KeePass DB 포함)
3. ✅ **RCE - 내부 서버 명령 실행**

**레드팀 승리 조건**: 30분 내 공격 성공 → **달성** (약 16분)

---

_턴을 퍼플팀에게 이관합니다._
