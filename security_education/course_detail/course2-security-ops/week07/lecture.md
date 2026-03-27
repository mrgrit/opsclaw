# Week 07: BunkerWeb WAF — 웹 애플리케이션 방화벽 (상세 버전)

## 학습 목표
- WAF의 역할과 동작 원리를 이해한다
- ModSecurity Core Rule Set (CRS)의 구조를 파악한다
- 커스텀 WAF 룰을 작성할 수 있다
- 오탐 예외 처리를 수행할 수 있다
- curl을 사용하여 WAF 동작을 테스트할 수 있다
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

## 용어 해설 (보안 솔루션 운영 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단하는 시스템 | 건물 출입 통제 시스템 |
| **체인** | Chain (nftables) | 패킷 처리 규칙의 묶음 (input, forward, output) | 심사 단계 |
| **룰/규칙** | Rule | 특정 조건의 트래픽을 어떻게 처리할지 정의 | "택배 기사만 출입 허용" |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 (IPS/AV) | 수배범 얼굴 사진 |
| **NFQUEUE** | Netfilter Queue | 커널에서 사용자 영역으로 패킷을 넘기는 큐 | 의심 택배를 별도 검사대로 보내는 것 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크 기반) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 로그를 파싱하여 구조화하는 규칙 | 외국어 통역사 |
| **CRS** | Core Rule Set (ModSecurity) | 범용 웹 공격 탐지 규칙 모음 | 표준 보안 검사 매뉴얼 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 정보 (IOC, TTPs) | 범죄 정보 공유 시스템 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인 등) | 수배범의 지문, 차량번호 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 포맷 | 범죄 보고서 표준 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | CTI 자동 교환 프로토콜 | 경찰서 간 수배 정보 공유 시스템 |
| **NAT** | Network Address Translation | 내부 IP를 외부 IP로 변환 | 회사 대표번호 (내선→외선) |
| **masquerade** | masquerade (nftables) | 나가는 패킷의 소스 IP를 게이트웨이 IP로 변환 | 회사 이름으로 편지 보내기 |


# 본 강의 내용

# Week 07: BunkerWeb WAF — 웹 애플리케이션 방화벽

## 학습 목표

- WAF의 역할과 동작 원리를 이해한다
- ModSecurity Core Rule Set (CRS)의 구조를 파악한다
- 커스텀 WAF 룰을 작성할 수 있다
- 오탐 예외 처리를 수행할 수 있다
- curl을 사용하여 WAF 동작을 테스트할 수 있다

---

## 1. WAF란?

WAF(Web Application Firewall)는 HTTP/HTTPS 트래픽을 검사하여 웹 공격을 차단하는 보안 솔루션이다.

**네트워크 방화벽 vs WAF:**

| 구분 | 네트워크 방화벽 (nftables) | WAF (BunkerWeb) |
|------|---------------------------|-----------------|
| 계층 | L3/L4 (IP, 포트) | **L7 (HTTP 내용)** |
| 검사 대상 | IP, 포트, 프로토콜 | URL, 헤더, 쿠키, 본문 |
| 탐지 가능 | 포트 스캔, DoS | **SQL Injection, XSS, CSRF** |
| 배치 위치 | 네트워크 경계 | 웹 서버 앞단 |

---

## 2. BunkerWeb 구조

BunkerWeb은 Nginx + ModSecurity 기반의 오픈소스 WAF이다.

```
    클라이언트 요청
         │
         ▼
    ┌──────────┐
    │ BunkerWeb │ (Nginx + ModSecurity)
    │   :80     │
    └────┬─────┘
         │ ModSecurity CRS 검사
         │  ├─ 정상 → 통과
         │  └─ 공격 → 차단 (403)
         ▼
    ┌──────────┐
    │ JuiceShop│ (백엔드 앱)
    │   :3000  │
    └──────────┘
```

실습 환경: web 서버(10.20.30.80)

---

## 3. 실습 환경 접속

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80
```

### 3.1 BunkerWeb 상태 확인

```bash
echo 1 | sudo -S docker ps | grep bunkerweb
```

**예상 출력:**
```
abc123  bunkerio/bunkerweb:1.5  ...  Up 2 days  0.0.0.0:80->8080/tcp  bunkerweb
```

### 3.2 ModSecurity 활성화 확인

```bash
echo 1 | sudo -S docker exec bunkerweb cat /etc/nginx/modsecurity.conf 2>/dev/null | head -10
```

또는 환경 변수 확인:

```bash
echo 1 | sudo -S docker inspect bunkerweb | python3 -c "
import sys, json
data = json.load(sys.stdin)
env = data[0]['Config']['Env']
for e in sorted(env):
    if 'MODSEC' in e.upper() or 'WAF' in e.upper() or 'SECURITY' in e.upper():
        print(e)
"
```

---

## 4. ModSecurity Core Rule Set (CRS)

CRS는 OWASP에서 관리하는 범용 WAF 룰셋이다.

### 4.1 CRS 구조

| 파일 범위 | 내용 |
|-----------|------|
| 900-xxx | 설정/초기화 |
| 910-xxx | IP 평판 검사 |
| 920-xxx | 프로토콜 위반 검사 |
| 930-xxx | 로컬 파일 포함 (LFI) |
| 931-xxx | 원격 파일 포함 (RFI) |
| 932-xxx | 원격 코드 실행 (RCE) |
| 933-xxx | PHP 공격 |
| 934-xxx | Node.js 공격 |
| 941-xxx | **XSS (Cross-Site Scripting)** |
| 942-xxx | **SQL Injection** |
| 943-xxx | 세션 고정 |
| 944-xxx | Java 공격 |
| 949-xxx | 인바운드 차단 판정 |
| 950-xxx | 아웃바운드 (데이터 유출) |

### 4.2 Anomaly Scoring

CRS는 **이상 점수(Anomaly Score)** 방식으로 동작한다:

1. 각 룰이 매칭되면 점수를 누적한다
2. 총 점수가 임계값을 초과하면 차단한다

| 심각도 | 점수 | 예 |
|--------|------|---|
| CRITICAL | 5 | SQL Injection |
| ERROR | 4 | 원격 코드 실행 |
| WARNING | 3 | 의심스러운 문자열 |
| NOTICE | 2 | 프로토콜 위반 |

**기본 차단 임계값: 5점** (CRITICAL 1개로 즉시 차단)

---

## 5. WAF 동작 테스트

secu 서버 또는 로컬에서 web 서버로 공격 테스트를 수행한다:

### 5.1 정상 요청

```bash
# 정상 요청 (200 OK)
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://10.20.30.80/
```

**예상 출력:**
```
HTTP 200
```

### 5.2 SQL Injection 테스트

```bash
# SQL Injection (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/?id=1%20OR%201=1"
```

**예상 출력:**
```
HTTP 403
```

### 5.3 XSS 테스트

```bash
# XSS (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/?q=<script>alert(1)</script>"
```

**예상 출력:**
```
HTTP 403
```

### 5.4 디렉터리 트래버설 테스트

```bash
# Path Traversal (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/../../etc/passwd"
```

### 5.5 명령 주입 테스트

```bash
# Command Injection (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  "http://10.20.30.80/?cmd=;cat%20/etc/passwd"
```

### 5.6 User-Agent 스캐너 테스트

```bash
# 스캐너 User-Agent (403 차단 예상)
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  -A "sqlmap/1.0" \
  "http://10.20.30.80/"
```

### 5.7 차단 응답 확인

```bash
# 차단 시 응답 본문 확인
curl -s "http://10.20.30.80/?id=1%20UNION%20SELECT%201"
```

**예상 출력:**
```html
<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
</body>
</html>
```

---

## 6. WAF 로그 분석

### 6.1 ModSecurity 감사 로그

```bash
# BunkerWeb 컨테이너 내 로그 확인
echo 1 | sudo -S docker exec bunkerweb cat /var/log/bunkerweb/error.log | \
  grep "ModSecurity" | tail -10
```

### 6.2 Nginx 접근 로그

```bash
echo 1 | sudo -S docker exec bunkerweb cat /var/log/bunkerweb/access.log | tail -20
```

### 6.3 차단된 요청 필터링

```bash
# 403 응답만 추출
echo 1 | sudo -S docker exec bunkerweb cat /var/log/bunkerweb/access.log | \
  awk '$9 == 403' | tail -10
```

---

## 7. 커스텀 WAF 룰

### 7.1 ModSecurity 룰 문법

```
SecRule VARIABLES "OPERATOR" "ACTIONS"
```

| 부분 | 설명 | 예시 |
|------|------|------|
| VARIABLES | 검사 대상 | `REQUEST_URI`, `ARGS`, `REQUEST_HEADERS` |
| OPERATOR | 비교 연산 | `@rx` (정규식), `@contains`, `@eq` |
| ACTIONS | 동작 | `deny`, `log`, `id:xxx` |

### 7.2 커스텀 룰 작성

BunkerWeb에서 커스텀 ModSecurity 룰을 추가하는 방법:

```bash
# 커스텀 룰 파일 생성
echo 1 | sudo -S tee /tmp/custom-waf-rules.conf << 'EOF'
# 관리자 페이지 외부 접근 차단
SecRule REQUEST_URI "@beginsWith /admin" \
  "id:10001,phase:1,deny,status:403,log,msg:'Admin access blocked'"

# 특정 파일 확장자 업로드 차단
SecRule FILES_NAMES "@rx \.(exe|bat|cmd|sh|php)$" \
  "id:10002,phase:2,deny,status:403,log,msg:'Dangerous file upload blocked'"

# 요청 본문 크기 제한 (10MB)
SecRule REQUEST_BODY_LENGTH "@gt 10485760" \
  "id:10003,phase:2,deny,status:413,log,msg:'Request body too large'"

# 특정 국가 차단 (GeoIP 필요)
# SecRule GEO:COUNTRY_CODE "@rx ^(CN|RU|KP)$" \
#   "id:10004,phase:1,deny,status:403,log,msg:'Country blocked'"
EOF
```

### 7.3 BunkerWeb에 룰 적용

BunkerWeb은 Docker 환경 변수 또는 설정 파일로 커스텀 룰을 적용한다:

```bash
# BunkerWeb 설정 디렉터리 확인
echo 1 | sudo -S ls /opt/bunkerweb/configs/ 2>/dev/null || \
echo 1 | sudo -S ls /etc/bunkerweb/ 2>/dev/null || \
echo "설정 디렉터리를 확인하세요"
```

---

## 8. 예외 처리 (False Positive)

### 8.1 예외가 필요한 경우

- 정상적인 API 요청이 SQL Injection으로 오인될 때
- 관리 도구의 요청이 차단될 때
- 특정 경로에서 파일 업로드가 필요할 때

### 8.2 예외 룰 작성

```bash
# 특정 경로에서 SQL Injection 룰 비활성화
echo 1 | sudo -S tee /tmp/waf-exceptions.conf << 'EOF'
# /api/ 경로에서 SQL Injection 룰 예외
SecRule REQUEST_URI "@beginsWith /api/" \
  "id:10010,phase:1,pass,nolog,ctl:ruleRemoveById=942100-942999"

# 특정 파라미터에서 XSS 룰 예외
SecRule ARGS_NAMES "@eq search_query" \
  "id:10011,phase:1,pass,nolog,ctl:ruleRemoveTargetById=941100-941999;ARGS:search_query"

# 특정 IP에서 모든 룰 예외 (모니터링 서버)
SecRule REMOTE_ADDR "@eq 10.20.30.100" \
  "id:10012,phase:1,pass,nolog,ctl:ruleEngine=Off"
EOF
```

### 8.3 예외 적용 시 주의사항

1. **최소 권한 원칙**: 가능한 좁은 범위로 예외를 설정한다
2. **특정 룰 ID만 제외**: 전체 비활성화보다 특정 ID만 제외한다
3. **로그 기록 유지**: 예외 적용해도 로그는 남기는 것을 권장한다
4. **정기적 재검토**: 예외가 여전히 필요한지 주기적으로 확인한다

---

## 9. Anomaly Score 조정

### 9.1 차단 임계값 변경

```bash
# 임계값을 10으로 높이기 (더 관대하게)
# BunkerWeb 환경 변수 방식:
# MODSECURITY_INBOUND_ANOMALY_SCORE_THRESHOLD=10
```

### 9.2 Paranoia Level 조정

| 레벨 | 설명 | 오탐 가능성 |
|------|------|-------------|
| PL 1 | 기본 (보수적) | 낮음 |
| PL 2 | 추가 룰 활성화 | 중간 |
| PL 3 | 공격적 탐지 | 높음 |
| PL 4 | 최대 탐지 | 매우 높음 |

```bash
# Paranoia Level 설정
# MODSECURITY_SEC_RULE_ENGINE=On
# CRS_PARANOIA_LEVEL=1
```

---

## 10. 종합 테스트 스크립트

다양한 공격을 한번에 테스트하는 스크립트:

```bash
cat << 'TESTEOF' > /tmp/waf_test.sh
#!/bin/bash
TARGET="http://10.20.30.80"
echo "=== WAF 테스트 시작 ==="

tests=(
  "정상 요청|/"
  "SQL Injection (OR)|/?id=1 OR 1=1"
  "SQL Injection (UNION)|/?id=1 UNION SELECT 1,2,3"
  "XSS (script)|/?q=<script>alert(1)</script>"
  "XSS (onerror)|/?q=<img src=x onerror=alert(1)>"
  "LFI (traversal)|/../../etc/passwd"
  "RCE (cmd injection)|/?cmd=;ls -la"
  "Scanner (sqlmap)|/ -A sqlmap/1.0"
)

for test in "${tests[@]}"; do
  IFS='|' read -r name path <<< "$test"
  if [[ "$name" == *"Scanner"* ]]; then
    code=$(curl -s -o /dev/null -w "%{http_code}" -A "sqlmap/1.0" "${TARGET}/")
  else
    code=$(curl -s -o /dev/null -w "%{http_code}" "${TARGET}${path}")
  fi
  if [ "$code" == "403" ]; then
    result="BLOCKED"
  elif [ "$code" == "200" ]; then
    result="PASSED"
  else
    result="HTTP $code"
  fi
  printf "%-30s %s (%s)\n" "$name" "$result" "$code"
done

echo "=== 테스트 완료 ==="
TESTEOF
chmod +x /tmp/waf_test.sh
bash /tmp/waf_test.sh
```

**예상 출력:**
```
=== WAF 테스트 시작 ===
정상 요청                       PASSED (200)
SQL Injection (OR)             BLOCKED (403)
SQL Injection (UNION)          BLOCKED (403)
XSS (script)                   BLOCKED (403)
XSS (onerror)                  BLOCKED (403)
LFI (traversal)                BLOCKED (403)
RCE (cmd injection)            BLOCKED (403)
Scanner (sqlmap)               BLOCKED (403)
=== 테스트 완료 ===
```

---

## 11. 실습 과제

### 과제 1: WAF 동작 확인

1. 위 테스트 스크립트를 실행하여 모든 공격이 차단되는지 확인하라
2. 차단된 요청의 로그를 분석하라
3. 응답 본문에 어떤 내용이 포함되어 있는지 확인하라

### 과제 2: 커스텀 룰 작성

1. `/backup` 경로 접근을 차단하는 룰을 작성하라
2. `.sql` 파일 다운로드를 차단하는 룰을 작성하라
3. 작성한 룰을 테스트하라

### 과제 3: 예외 처리

1. `/api/search` 경로에서 `q` 파라미터의 XSS 룰을 예외 처리하라
2. 예외 처리 후 정상적인 검색이 가능한지 확인하라
3. 동시에 다른 경로에서는 여전히 XSS가 차단되는지 확인하라

---

## 12. 핵심 정리

| 개념 | 설명 |
|------|------|
| WAF | L7 계층 웹 공격 차단 |
| ModSecurity | 오픈소스 WAF 엔진 |
| CRS | OWASP 핵심 룰셋 |
| Anomaly Score | 이상 점수 누적 방식 |
| Paranoia Level | 탐지 민감도 (1~4) |
| SecRule | ModSecurity 룰 문법 |
| ctl:ruleRemoveById | 특정 룰 예외 처리 |
| 403 Forbidden | WAF 차단 응답 |

---

## 다음 주 예고

Week 08은 **중간고사**이다:
- nftables 방화벽 + Suricata IPS를 조합하여
- 실제 보안 인프라를 구성하는 실기 시험


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 2)

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

**Q1.** 이번 주차 "Week 07: BunkerWeb WAF — 웹 애플리케이션 방화벽"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **보안 솔루션 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 방화벽/IPS의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **SIEM 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

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

