# Week 11: 보안 정책 수립 (상세 버전)

## 학습 목표
- 보안 정책의 구조와 작성 원칙을 이해한다
- 접근통제 정책, 비밀번호 정책, 사고대응 정책을 작성할 수 있다
- 정책을 실제 시스템 설정으로 구현할 수 있다
- 정책과 기술적 구현 사이의 관계를 이해한다
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

## 용어 해설 (보안 표준/컴플라이언스 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **컴플라이언스** | Compliance | 법/규정/표준을 준수하는 것 | 교통법규 준수 |
| **인증** | Certification | 외부 심사 기관이 표준 준수를 확인하는 절차 | 운전면허 시험 합격 |
| **통제 항목** | Control | 보안 목표를 달성하기 위한 구체적 조치 | 건물 소방 설비 하나하나 |
| **SoA** | Statement of Applicability | 적용 가능한 통제 항목 선언서 | "우리 건물에 필요한 소방 설비 목록" |
| **리스크 평가** | Risk Assessment | 위험을 식별·분석·평가하는 과정 | 건물의 화재/지진 위험도 평가 |
| **리스크 처리** | Risk Treatment | 평가된 위험에 대한 대응 결정 (수용/회피/감소/전가) | 보험 가입, 소방 설비 설치 |
| **PDCA** | Plan-Do-Check-Act | ISO 표준의 지속적 개선 사이클 | 계획→실행→점검→개선 반복 |
| **ISMS** | Information Security Management System | 정보보안 관리 체계 | 회사의 보안 관리 시스템 전체 |
| **ISMS-P** | ISMS + Privacy | 한국의 정보보호 + 개인정보보호 인증 | 한국판 ISO 27001 + 개인정보 |
| **ISO 27001** | ISO/IEC 27001 | 국제 정보보안 관리체계 표준 | 국제 보안 면허증 |
| **ISO 27002** | ISO/IEC 27002 | ISO 27001의 통제 항목 상세 가이드 | 면허 시험 교재 |
| **NIST CSF** | NIST Cybersecurity Framework | 미국 국립표준기술연구소의 사이버보안 프레임워크 | 미국판 보안 가이드 |
| **GDPR** | General Data Protection Regulation | EU 개인정보보호 규정 | EU의 개인정보 보호법 |
| **SOC 2** | Service Organization Control 2 | 클라우드 서비스 보안 인증 (미국) | 클라우드 업체의 보안 성적표 |
| **증적** | Evidence (Audit) | 통제가 실행되었음을 증명하는 자료 | 출석부, 영수증 |
| **심사원** | Auditor | 인증 심사를 수행하는 전문가 | 감독관, 시험관 |
| **부적합** | Non-conformity | 심사에서 표준 미충족 판정 | 시험 불합격 항목 |
| **GAP 분석** | Gap Analysis | 현재 상태와 목표 기준의 차이 분석 | 현재 실력과 합격선의 차이 |


---

# Week 11: 보안 정책 수립

## 학습 목표

- 보안 정책의 구조와 작성 원칙을 이해한다
- 접근통제 정책, 비밀번호 정책, 사고대응 정책을 작성할 수 있다
- 정책을 실제 시스템 설정으로 구현할 수 있다
- 정책과 기술적 구현 사이의 관계를 이해한다

---

## 1. 보안 정책이란?

### 1.1 정의

보안 정책은 조직이 정보 자산을 보호하기 위해 수립한 **공식 문서화된 규칙**이다.

### 1.2 정책 계층 구조

```
정보보안 정책 (Policy)          ← 최상위: "무엇을" 해야 하는가
    ↓
보안 표준/기준 (Standard)       ← "어떤 수준으로" 해야 하는가
    ↓
보안 절차 (Procedure)           ← "어떻게" 해야 하는가
    ↓
보안 가이드라인 (Guideline)     ← "권장" 사항
```

### 1.3 좋은 정책의 특징

| 특징 | 설명 |
|------|------|
| 명확성 | 모호하지 않은 표현 |
| 강제성 | "~해야 한다" (SHALL/MUST) |
| 측정 가능 | 준수 여부를 객관적으로 판단 가능 |
| 현실성 | 실제로 이행 가능한 수준 |
| 최신성 | 정기적으로 검토/갱신 |

---

## 2. 접근통제 정책

### 2.1 정책 작성

```
========================================
접근통제 정책 (Access Control Policy)
========================================
버전: 1.0
작성일: 2026-03-27
승인자: (CISO)

1. 목적
   본 정책은 정보시스템에 대한 접근을 통제하여
   비인가 접근을 방지하고 정보 자산을 보호하는 것을 목적으로 한다.

2. 적용 범위
   본 정책은 모든 정보시스템(서버, 네트워크, 데이터베이스, 애플리케이션)에 적용된다.

3. 원칙
   3.1 최소 권한 원칙: 업무 수행에 필요한 최소한의 권한만 부여한다.
   3.2 직무 분리: 핵심 업무는 2인 이상이 분담한다.
   3.3 필요 기반 접근(Need-to-Know): 업무상 필요한 정보만 접근한다.

4. 세부 기준
   4.1 사용자 계정
       - 개인별 고유 계정을 사용한다 (공용 계정 사용 금지)
       - 퇴직자/전환자 계정은 당일 비활성화한다
       - 90일 이상 미사용 계정은 자동 잠금한다
   4.2 관리자 권한
       - root/sudo 접근은 지정된 관리자에게만 부여한다
       - 관리자 작업은 개인 계정으로 로그인 후 sudo로 수행한다
       - root 직접 로그인은 금지한다
   4.3 원격 접근
       - SSH 키 기반 인증을 기본으로 한다
       - SSH 포트는 기본 포트(22)에서 변경을 권장한다
       - 접근 허용 IP를 방화벽으로 제한한다
   4.4 네트워크 접근
       - 기본 정책은 모두 차단(Default Deny)이다
       - 허용할 서비스만 명시적으로 개방한다
       - DMZ와 내부 네트워크를 분리한다

5. 위반 시 조치
   본 정책 위반 시 징계 절차에 따라 조치한다.

6. 검토 주기
   본 정책은 연 1회 이상 검토하고 필요 시 개정한다.
```

### 2.2 실습: 접근통제 정책 구현

```bash
# 정책 4.2: root 직접 로그인 금지 — 현재 설정 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "grep '^PermitRootLogin' /etc/ssh/sshd_config || echo 'PermitRootLogin: 기본값'"
done

# 정책 4.1: 미사용 계정 확인
sshpass -p1 ssh user@192.168.208.142 "lastlog 2>/dev/null | awk 'NR>1 && \$2==\"Never\" {print \$1}'"

# 정책 4.4: 방화벽 기본 정책 확인
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | grep 'policy'"
```

---

## 3. 비밀번호 정책

### 3.1 정책 작성

```
========================================
비밀번호 정책 (Password Policy)
========================================
버전: 1.0

1. 비밀번호 복잡도
   - 최소 12자 이상
   - 영문 대문자, 소문자, 숫자, 특수문자 중 3종 이상 포함
   - 사전에 있는 단어 사용 금지
   - 연속된 문자/숫자 3자 이상 사용 금지 (예: abc, 123)

2. 비밀번호 변경
   - 최대 사용 기간: 90일
   - 최소 사용 기간: 1일 (즉시 원래대로 되돌리기 방지)
   - 최근 5개 비밀번호 재사용 금지

3. 계정 잠금
   - 5회 연속 실패 시 계정 잠금
   - 잠금 시간: 30분
   - 관리자 해제도 가능

4. 초기/임시 비밀번호
   - 초기 비밀번호는 최초 로그인 시 즉시 변경
   - 임시 비밀번호 유효기간: 24시간

5. 비밀번호 저장
   - 평문 저장 금지
   - 단방향 해시(SHA-256 이상) + 솔트 적용
```

### 3.2 실습: 비밀번호 정책 구현

```bash
# 현재 설정 확인
sshpass -p1 ssh user@192.168.208.142 "grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_MIN_LEN|PASS_WARN_AGE' /etc/login.defs | grep -v '^#'"

# pwquality 설정 확인
sshpass -p1 ssh user@192.168.208.142 "cat /etc/security/pwquality.conf 2>/dev/null | grep -v '^#' | grep -v '^$'"

# 정책에 맞게 설정하려면 (예시 - 실제 변경은 주의):
# /etc/login.defs:
#   PASS_MAX_DAYS   90
#   PASS_MIN_DAYS   1
#   PASS_MIN_LEN    12
#   PASS_WARN_AGE   14
#
# /etc/security/pwquality.conf:
#   minlen = 12
#   dcredit = -1
#   ucredit = -1
#   lcredit = -1
#   ocredit = -1
#   maxrepeat = 3

# PAM 계정 잠금 설정 확인
sshpass -p1 ssh user@192.168.208.142 "grep -E 'pam_faillock|pam_tally' /etc/pam.d/common-auth 2>/dev/null || echo '계정 잠금 미설정'"

# 비밀번호 해시 알고리즘 확인
sshpass -p1 ssh user@192.168.208.142 "grep '^ENCRYPT_METHOD' /etc/login.defs"
```

---

## 4. 사고 대응 정책

### 4.1 정책 작성

```
========================================
정보보안 사고 대응 정책 (Incident Response Policy)
========================================
버전: 1.0

1. 목적
   정보보안 사고 발생 시 피해를 최소화하고
   신속하게 복구하기 위한 절차를 정의한다.

2. 사고 분류
   등급 1 (Critical): 개인정보 유출, 핵심 시스템 침해, 랜섬웨어
   등급 2 (High): 비인가 접근 탐지, 악성코드 감염, DDoS
   등급 3 (Medium): 정책 위반, 비정상 트래픽, 취약점 발견
   등급 4 (Low): 바이러스 경고, 스팸, 포트 스캔

3. 대응 절차
   3.1 탐지 및 보고 (30분 이내)
       - 보안 관제 시스템(Wazuh)에서 자동 탐지
       - 발견자는 즉시 보안 담당자에게 보고
   3.2 초기 분석 (2시간 이내)
       - 사고 범위 파악
       - 영향도 평가
       - 사고 등급 결정
   3.3 격리 및 억제 (등급에 따라)
       - 등급 1~2: 즉시 격리 (네트워크 차단, 계정 잠금)
       - 등급 3~4: 모니터링 강화
   3.4 근본 원인 분석
       - 로그 분석
       - 포렌식 증거 수집
   3.5 복구
       - 정상 서비스 복원
       - 백업에서 데이터 복원
   3.6 사후 조치
       - 재발 방지 대책 수립
       - 사고 보고서 작성
       - 교훈 공유

4. 보고 체계
   발견자 → 보안 담당자 → CISO → 경영진
   (개인정보 유출 시: + 개인정보보호위원회, KISA)

5. 증거 보존
   - 모든 로그와 증거는 최소 1년간 보존
   - 디지털 증거는 무결성 보장 (해시값 기록)
```

### 4.2 실습: 사고 대응 체계 확인

```bash
# 탐지 체계 확인 (Wazuh)
echo "=== Wazuh Manager 상태 ==="
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null"

echo "=== 최근 고위험 알림 ==="
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 10:
            print(f'[Level {r[\"level\"]}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -5"

# 격리 능력 확인 (방화벽으로 IP 차단 가능 여부)
echo "=== 방화벽 차단 가능 ==="
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | head -5 && echo 'nftables 사용 가능'"

# 증거 보존 확인 (로그 보관 기간)
echo "=== 로그 보관 설정 ==="
sshpass -p1 ssh user@192.168.208.142 "cat /etc/logrotate.conf 2>/dev/null | grep -E 'rotate|weekly|monthly'"
```

---

## 5. 추가 정책: 패치 관리 정책

### 5.1 핵심 내용

```
패치 관리 정책 요약:
- 긴급 패치 (Critical): 발표 후 72시간 이내 적용
- 중요 패치 (Important): 발표 후 2주 이내 적용
- 일반 패치 (Moderate): 월 1회 정기 패치
- 패치 전 테스트 환경에서 검증 후 적용
- 패치 이력을 문서화하여 보관
```

### 5.2 실습: 패치 현황 점검

```bash
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 패치 현황 ==="
  sshpass -p1 ssh user@$ip "apt list --upgradable 2>/dev/null | head -5"
  echo "보안 패치:"
  sshpass -p1 ssh user@$ip "apt list --upgradable 2>/dev/null | grep -i security | head -3"
done
```

---

## 6. 정책과 설정의 매핑

| 정책 항목 | Linux 설정 파일 | 설정 내용 |
|-----------|----------------|----------|
| root 직접 로그인 금지 | /etc/ssh/sshd_config | PermitRootLogin no |
| 비밀번호 최대 사용 기간 90일 | /etc/login.defs | PASS_MAX_DAYS 90 |
| 비밀번호 최소 12자 | /etc/security/pwquality.conf | minlen = 12 |
| 5회 실패 시 잠금 | /etc/pam.d/common-auth | pam_faillock deny=5 |
| 세션 타임아웃 10분 | /etc/profile | TMOUT=600 |
| 기본 방화벽 정책 DROP | nftables ruleset | chain input { policy drop } |
| 로그 보관 6개월 | /etc/logrotate.conf | rotate 26 (weekly) |
| NTP 동기화 | /etc/systemd/timesyncd.conf | NTP=pool.ntp.org |

### 6.1 실습: 매핑 검증

```bash
# 정책 준수 여부 일괄 확인
echo "=== 정책 준수 점검 ==="
ip=192.168.208.142

echo "[1] root 로그인:"
sshpass -p1 ssh user@$ip "grep '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null || echo '기본값'"

echo "[2] 비밀번호 만료:"
sshpass -p1 ssh user@$ip "grep '^PASS_MAX_DAYS' /etc/login.defs"

echo "[3] 세션 타임아웃:"
sshpass -p1 ssh user@$ip "grep TMOUT /etc/profile /etc/bash.bashrc 2>/dev/null || echo '미설정'"

echo "[4] NTP:"
sshpass -p1 ssh user@$ip "timedatectl 2>/dev/null | grep synchronized"

echo "[5] 로그 보관:"
sshpass -p1 ssh user@$ip "grep '^rotate' /etc/logrotate.conf"
```

---

## 7. 정책 검토 및 개정

### 7.1 검토 주기

- **정기 검토**: 연 1회 이상
- **수시 검토**: 보안 사고 발생 시, 조직 변경 시, 법률 개정 시

### 7.2 변경 관리

```
정책 변경 절차:
1. 변경 필요성 식별
2. 변경 초안 작성
3. 관련 부서 검토
4. CISO 승인
5. 임직원 공지 및 교육
6. 시스템 반영
7. 효과성 확인
```

---

## 8. 핵심 정리

1. **정책 계층** = 정책 > 표준 > 절차 > 가이드라인
2. **접근통제 정책** = 최소 권한, 직무 분리, 필요 기반 접근
3. **비밀번호 정책** = 12자+, 90일 변경, 5회 실패 잠금
4. **사고대응 정책** = 탐지→분석→격리→복구→사후조치
5. **정책-설정 매핑** = 정책을 실제 시스템 설정으로 구현

---

## 과제

1. 실습 환경에 맞는 접근통제 정책을 작성하시오 (A4 1장 이상)
2. 비밀번호 정책의 각 항목이 현재 서버에서 준수되는지 점검하시오
3. 사고 대응 정책에 따라 "SSH 무차별 대입 공격 탐지" 시나리오의 대응 절차를 작성하시오

---

## 참고 자료

- SANS Security Policy Templates (https://www.sans.org/information-security-policy/)
- KISA 정보보안 정책 수립 가이드
- ISO 27001 A.5.1 정보보안 정책


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 11: 보안 정책 수립"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **컴플라이언스 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 ISO 27001의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **ISMS-P 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

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


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


