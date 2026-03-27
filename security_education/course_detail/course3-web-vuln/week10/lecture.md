# Week 10: 암호화 / 통신 보안 점검 (상세 버전)

## 학습 목표
- HTTPS의 동작 원리와 TLS 핸드셰이크를 이해한다
- SSL/TLS 인증서를 점검하고 문제를 식별할 수 있다
- 약한 암호 스위트(Cipher Suite)를 판별할 수 있다
- 웹 애플리케이션의 암호화 구현을 점검한다
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

# Week 10: 암호화 / 통신 보안 점검

## 학습 목표
- HTTPS의 동작 원리와 TLS 핸드셰이크를 이해한다
- SSL/TLS 인증서를 점검하고 문제를 식별할 수 있다
- 약한 암호 스위트(Cipher Suite)를 판별할 수 있다
- 웹 애플리케이션의 암호화 구현을 점검한다

## 전제 조건
- HTTP vs HTTPS 차이 이해
- 공개키/대칭키 암호화 기본 개념

---

## 1. HTTPS와 TLS 개요 (20분)

### 1.1 HTTPS가 보호하는 것

| 보호 항목 | 설명 | 위협 |
|----------|------|------|
| **기밀성** | 통신 내용 암호화 | 도청 (Eavesdropping) |
| **무결성** | 데이터 변조 방지 | 중간자 공격 (MITM) |
| **인증** | 서버 신원 확인 | 피싱, DNS 스푸핑 |

### 1.2 TLS 핸드셰이크 과정

```
클라이언트                              서버
    │                                    │
    │─── ClientHello (지원 암호목록) ──→  │
    │                                    │
    │←── ServerHello (선택 암호) ────── │
    │←── Certificate (인증서) ──────── │
    │←── ServerHelloDone ──────────── │
    │                                    │
    │─── ClientKeyExchange ──────────→  │
    │─── ChangeCipherSpec ───────────→  │
    │─── Finished ───────────────────→  │
    │                                    │
    │←── ChangeCipherSpec ──────────── │
    │←── Finished ──────────────────── │
    │                                    │
    │══════ 암호화된 통신 시작 ══════════│
```

### 1.3 TLS 버전별 보안

| 버전 | 상태 | 비고 |
|------|------|------|
| SSL 2.0 | 폐기 | 심각한 취약점 |
| SSL 3.0 | 폐기 | POODLE 공격 |
| TLS 1.0 | 폐기 | BEAST 공격 |
| TLS 1.1 | 폐기 | 약한 암호 |
| **TLS 1.2** | **사용** | 현재 최소 기준 |
| **TLS 1.3** | **권장** | 최신, 가장 안전 |

---

## 2. 실습 환경 통신 보안 점검 (20분)

### 2.1 HTTP/HTTPS 지원 확인

```bash
# JuiceShop - HTTP
echo "=== JuiceShop (포트 3000) ==="
curl -s -o /dev/null -w "HTTP: %{http_code}\n" http://10.20.30.80:3000

# JuiceShop - HTTPS 시도
curl -sk -o /dev/null -w "HTTPS: %{http_code}\n" https://10.20.30.80:3000 2>/dev/null || echo "HTTPS: 미지원"

# Apache - HTTP
echo ""
echo "=== Apache (포트 80) ==="
curl -s -o /dev/null -w "HTTP: %{http_code}\n" http://10.20.30.80:80

# Apache - HTTPS (포트 443)
curl -sk -o /dev/null -w "HTTPS: %{http_code}\n" https://10.20.30.80:443 2>/dev/null || echo "HTTPS: 미지원"
```

### 2.2 HTTP → HTTPS 리다이렉트 확인

```bash
# HTTP 요청 시 HTTPS로 리다이렉트하는지 확인
echo "=== 리다이렉트 확인 ==="
curl -sI http://10.20.30.80:80 | grep -i "location"
curl -sI http://10.20.30.80:3000 | grep -i "location"

# 리다이렉트가 없으면 → 평문 통신 가능 (취약)
```

### 2.3 HSTS(HTTP Strict Transport Security) 점검

```bash
# HSTS 헤더 확인
echo "=== HSTS 헤더 ==="
curl -sI http://10.20.30.80:80 | grep -i "strict-transport"
curl -sI http://10.20.30.80:3000 | grep -i "strict-transport"

# HSTS가 없으면:
# - 사용자가 http://로 접속하면 평문 통신
# - SSL 스트리핑 공격에 취약
```

---

## 3. SSL/TLS 인증서 점검 (30분)

### 3.1 openssl로 인증서 분석

```bash
# 실습 서버가 HTTPS를 지원하는 경우 인증서 분석
# (실습 서버가 HTTP만 지원하면 외부 사이트로 개념 학습)

# 인증서 기본 정보 확인
echo "=== 실습 서버 인증서 확인 ==="
echo | openssl s_client -connect 10.20.30.80:443 -servername 10.20.30.80 2>/dev/null | openssl x509 -noout -text 2>/dev/null | head -30 || echo "TLS 미지원 - 외부 사이트로 실습"

# 개념 학습용: 공개 사이트 인증서 분석
echo ""
echo "=== 공개 사이트 인증서 분석 (학습용) ==="
echo | openssl s_client -connect www.google.com:443 -servername www.google.com 2>/dev/null | openssl x509 -noout -subject -issuer -dates 2>/dev/null
```

### 3.2 인증서 점검 항목

| 점검 항목 | 정상 | 취약 |
|----------|------|------|
| 유효기간 | 만료 전 | 만료됨 |
| 발급자 | 신뢰 CA (DigiCert, Let's Encrypt 등) | 자체 서명 |
| CN/SAN | 도메인 일치 | 불일치 |
| 키 길이 | RSA 2048+ / ECDSA 256+ | RSA 1024 이하 |
| 서명 알고리즘 | SHA-256+ | SHA-1, MD5 |
| 인증서 체인 | 완전한 체인 | 중간 인증서 누락 |

### 3.3 인증서 점검 스크립트

```bash
# 인증서 종합 점검 스크립트 (HTTPS 지원 사이트 대상)
python3 << 'PYEOF'
import subprocess, re, sys
from datetime import datetime

target = "www.google.com"  # HTTPS 지원 사이트
port = 443

print(f"=== {target}:{port} 인증서 점검 ===\n")

# 인증서 정보 추출
cmd = f"echo | openssl s_client -connect {target}:{port} -servername {target} 2>/dev/null"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

# 인증서 상세 정보
cmd2 = f"{cmd} | openssl x509 -noout -subject -issuer -dates -serial -fingerprint"
result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
print(result2.stdout)

# 키 길이 확인
cmd3 = f"{cmd} | openssl x509 -noout -text | grep 'Public-Key'"
result3 = subprocess.run(cmd3, shell=True, capture_output=True, text=True)
print(f"키 길이: {result3.stdout.strip()}")

# TLS 버전 확인
cmd4 = f"echo | openssl s_client -connect {target}:{port} 2>/dev/null | grep 'Protocol'"
result4 = subprocess.run(cmd4, shell=True, capture_output=True, text=True)
print(f"TLS 버전: {result4.stdout.strip()}")

# 서명 알고리즘
cmd5 = f"{cmd} | openssl x509 -noout -text | grep 'Signature Algorithm' | head -1"
result5 = subprocess.run(cmd5, shell=True, capture_output=True, text=True)
print(f"서명 알고리즘: {result5.stdout.strip()}")
PYEOF
```

---

## 4. 암호 스위트 점검 (30분)

### 4.1 Cipher Suite란?

Cipher Suite는 TLS 통신에서 사용되는 암호화 알고리즘의 조합이다.

```
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
│    │      │       │    │    │    │
│    │      │       │    │    │    └─ MAC (무결성)
│    │      │       │    │    └────── 해시 크기
│    │      │       │    └─────────── 블록 모드
│    │      │       └──────────────── 암호화 알고리즘
│    │      └──────────────────────── 인증
│    └─────────────────────────────── 키 교환
└──────────────────────────────────── 프로토콜
```

### 4.2 약한 암호 스위트 목록

| 암호 | 문제 | 권장 |
|------|------|------|
| RC4 | 바이어스 공격 | 사용 금지 |
| DES / 3DES | 짧은 키 길이 | 사용 금지 |
| MD5 | 충돌 공격 | SHA-256+ 사용 |
| SHA-1 | 충돌 공격 (2017) | SHA-256+ 사용 |
| CBC 모드 | BEAST, Lucky13 | GCM 모드 사용 |
| RSA 키 교환 | PFS 미지원 | ECDHE 사용 |
| NULL 암호화 | 암호화 안함 | 절대 사용 금지 |

### 4.3 서버의 암호 스위트 점검

```bash
# 서버가 지원하는 암호 스위트 확인 (HTTPS 사이트 대상)
echo "=== 지원 암호 스위트 확인 ==="

# nmap을 이용한 점검 (설치되어 있다면)
which nmap > /dev/null 2>&1 && \
  nmap --script ssl-enum-ciphers -p 443 www.google.com 2>/dev/null | head -40 || \
  echo "nmap 미설치 - openssl로 수동 점검"

# openssl로 특정 암호 스위트 테스트
echo ""
echo "=== 약한 암호 스위트 개별 테스트 ==="

WEAK_CIPHERS=("RC4" "DES" "3DES" "NULL" "EXPORT" "MD5")
for cipher in "${WEAK_CIPHERS[@]}"; do
  result=$(echo | openssl s_client -connect www.google.com:443 -cipher "$cipher" 2>&1 | head -1)
  if echo "$result" | grep -q "CONNECTED"; then
    echo "[취약] $cipher 지원됨!"
  else
    echo "[양호] $cipher 미지원"
  fi
done
```

### 4.4 TLS 버전별 지원 확인

```bash
# 각 TLS 버전 지원 여부 확인
echo "=== TLS 버전 지원 확인 (google.com) ==="

for version in ssl3 tls1 tls1_1 tls1_2 tls1_3; do
  result=$(echo | openssl s_client -connect www.google.com:443 -$version 2>&1 | grep "Protocol")
  if echo "$result" | grep -qi "protocol"; then
    echo "[지원] $version: $result"
  else
    echo "[미지원] $version"
  fi
done 2>/dev/null
```

---

## 5. 웹 애플리케이션 암호화 점검 (20분)

### 5.1 비밀번호 저장 방식

```bash
# JuiceShop 사용자 비밀번호 해시 확인
# SQLi로 해시 추출 (Week 05에서 학습)
curl -s "http://10.20.30.80:3000/rest/products/search?q=test'))UNION+SELECT+email,password,3,4,5,6,7,8,9+FROM+Users+LIMIT+3--" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin).get('data', [])
    for item in data:
        name = str(item.get('name', ''))
        desc = str(item.get('description', ''))
        if '@' in name:
            # 해시 형식 분석
            hash_val = desc
            if len(hash_val) == 32:
                algo = 'MD5 (취약!)'
            elif len(hash_val) == 40:
                algo = 'SHA-1 (취약!)'
            elif len(hash_val) == 64:
                algo = 'SHA-256'
            elif hash_val.startswith('\$2'):
                algo = 'bcrypt (양호)'
            else:
                algo = f'알 수 없음 (길이={len(hash_val)})'
            print(f'{name}: {hash_val[:20]}... → {algo}')
except:
    print('데이터 추출 실패')
" 2>/dev/null
```

### 5.2 민감 정보 평문 전송 확인

```bash
# 로그인 요청이 HTTP(평문)로 전송되는지 확인
echo "=== 로그인 API 프로토콜 ==="
echo "현재 로그인 URL: http://10.20.30.80:3000/rest/user/login"
echo "프로토콜: HTTP (암호화 안됨)"
echo ""
echo "문제: 비밀번호가 네트워크에서 평문으로 전송됨"
echo "권고: HTTPS 적용 필수"

# API 응답에 민감 정보가 포함되는지 확인
echo ""
echo "=== API 응답 민감 정보 확인 ==="
TOKEN=$(curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['authentication']['token'])" 2>/dev/null)

# 로그인 응답에 비밀번호 해시가 포함되는지
curl -s -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@test.com","password":"Test1234!"}' | python3 -c "
import sys, json
data = json.load(sys.stdin)
auth = data.get('authentication', {})
print('로그인 응답 필드:')
for key in auth.keys():
    val = str(auth[key])
    if key == 'token':
        val = val[:30] + '...'
    print(f'  {key}: {val}')
" 2>/dev/null
```

### 5.3 쿠키 보안 속성

```bash
echo "=== 쿠키 보안 속성 점검 ==="
curl -sI http://10.20.30.80:3000 | grep -i "set-cookie" | while read -r line; do
  echo "쿠키: $line"
  echo "$line" | grep -qi "secure" && echo "  Secure: 설정됨" || echo "  Secure: 미설정 (HTTP로 전송 가능)"
  echo "$line" | grep -qi "httponly" && echo "  HttpOnly: 설정됨" || echo "  HttpOnly: 미설정 (JS 접근 가능)"
  echo "$line" | grep -qi "samesite" && echo "  SameSite: 설정됨" || echo "  SameSite: 미설정 (CSRF 위험)"
  echo ""
done
```

---

## 6. 실습 과제

### 과제 1: 통신 보안 점검
1. 실습 서버(JuiceShop, Apache)의 HTTP/HTTPS 지원 현황을 정리하라
2. HSTS, 리다이렉트 설정 여부를 확인하라
3. 점검 결과를 기반으로 통신 보안 개선 권고를 작성하라

### 과제 2: 인증서 분석
1. 공개 웹사이트 3개의 인증서를 분석하라 (발급자, 유효기간, 키 길이, 서명 알고리즘)
2. 분석 결과를 비교표로 정리하라
3. 인증서 관련 모범 사례(Best Practice)를 3가지 이상 서술하라

### 과제 3: 암호화 종합 점검
1. JuiceShop의 비밀번호 해시 알고리즘을 확인하라
2. 쿠키의 보안 속성(Secure, HttpOnly, SameSite)을 점검하라
3. 민감 정보가 평문으로 전송/저장되는 곳을 찾아 보고하라

---

## 7. 요약

| 점검 항목 | 도구 | 양호 기준 |
|----------|------|----------|
| HTTPS 지원 | curl | 모든 페이지 HTTPS 필수 |
| TLS 버전 | openssl | TLS 1.2 이상만 허용 |
| 인증서 | openssl | 신뢰 CA, 유효기간 내, SHA-256+ |
| 암호 스위트 | nmap, openssl | RC4/DES/NULL 미사용 |
| HSTS | curl -I | 헤더 설정됨 |
| 비밀번호 해시 | SQLi 결과 분석 | bcrypt/scrypt/Argon2 |
| 쿠키 보안 | curl -I | Secure+HttpOnly+SameSite |

**다음 주 예고**: Week 11 - 에러 처리/정보 노출. 스택 트레이스, 디버그 모드, 디렉터리 리스팅을 학습한다.


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

**Q1.** 이번 주차 "Week 10: 암호화 / 통신 보안 점검"의 핵심 목적은 무엇인가?
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

