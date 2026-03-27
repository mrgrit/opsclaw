# Week 06: ISMS-P (2) - 점검 항목 실습 (상세 버전)

## 학습 목표
- ISMS-P 보호대책 중 핵심 20개 항목을 실제 서버에서 점검한다
- 점검 스크립트를 작성하고 실행한다
- 점검 결과를 ISMS-P 양식에 맞게 문서화한다
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


# 본 강의 내용

# Week 06: ISMS-P (2) - 점검 항목 실습

## 학습 목표

- ISMS-P 보호대책 중 핵심 20개 항목을 실제 서버에서 점검한다
- 점검 스크립트를 작성하고 실행한다
- 점검 결과를 ISMS-P 양식에 맞게 문서화한다

---

## 1. 점검 방법론

### 1.1 점검 유형

| 유형 | 방법 | 예시 |
|------|------|------|
| 서류 점검 | 정책/절차 문서 확인 | 보안 정책서, 접근통제 절차서 |
| 기술 점검 | 시스템 설정 확인 | SSH 설정, 방화벽 규칙 |
| 인터뷰 | 담당자 면담 | 보안 교육 이수 여부 |
| 현장 확인 | 물리적 확인 | 서버실 출입 통제 |

### 1.2 점검 결과 판정

| 판정 | 의미 |
|------|------|
| 적합 | 기준을 충족함 |
| 부분적합 | 일부 미흡한 점이 있음 |
| 부적합 | 기준을 충족하지 못함 |
| 해당없음 | 해당 항목이 적용되지 않음 |

---

## 2. 점검 항목 1~5: 정책 및 조직

### 2.1 [2.1.1] 정책의 유지관리

**점검 내용**: 정보보안 정책이 문서화되어 있는가?

```bash
# 보안 관련 문서/설정 파일 존재 확인
sshpass -p1 ssh user@192.168.208.142 "ls -la /etc/security/ 2>/dev/null"
sshpass -p1 ssh user@192.168.208.142 "ls -la /etc/pam.d/ | head -10"
```

### 2.2 [2.1.3] 정보자산 관리

**점검 내용**: 정보자산 목록이 관리되고 있는가?

```bash
# 서버 인벤토리 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "hostname; cat /etc/machine-id; lscpu | grep 'Model name'; free -h | grep Mem"
done
```

### 2.3 [2.2.1] 주요 직무자 지정 및 관리

```bash
# sudo 권한 사용자 확인 (주요 직무자)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "getent group sudo 2>/dev/null; getent group wheel 2>/dev/null"
done
```

### 2.4 [2.2.4] 보안 서약서

**점검 내용**: 직원이 보안 서약서에 서명했는가? (서류 점검 - 실습에서는 스킵)

### 2.5 [2.2.5] 보안 인식 교육

**점검 내용**: 연 1회 이상 보안 교육을 실시했는가? (서류 점검)

---

## 3. 점검 항목 6~10: 인증 및 접근통제

### 3.1 [2.5.1] 사용자 계정 관리

```bash
# 점검: 불필요한 계정, 기본 계정, 미사용 계정
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 사용자 계정 ==="
  sshpass -p1 ssh user@$ip "awk -F: '\$3 >= 1000 && \$3 < 65534 {print \$1, \$6, \$7}' /etc/passwd"
  echo "--- 최근 로그인 ---"
  sshpass -p1 ssh user@$ip "lastlog 2>/dev/null | awk 'NR>1 && \$2 != \"Never\" {print}' | head -5"
done
```

### 3.2 [2.5.2] 사용자 식별

```bash
# 점검: 공용 계정 사용 여부 (같은 계정으로 다수 접속)
sshpass -p1 ssh user@192.168.208.142 "who"
sshpass -p1 ssh user@192.168.208.142 "last | head -20"
```

### 3.3 [2.5.3] 사용자 인증

```bash
# 비밀번호 정책 점검
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 비밀번호 정책 ==="
  sshpass -p1 ssh user@$ip "grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_MIN_LEN|PASS_WARN_AGE' /etc/login.defs"
  echo "--- pwquality ---"
  sshpass -p1 ssh user@$ip "cat /etc/security/pwquality.conf 2>/dev/null | grep -v '^#' | grep -v '^$' || echo '미설정'"
done
```

**ISMS-P 기준**:
- 최소 8자 이상 (영문+숫자+특수문자 중 2종 이상)
- 90일 이내 변경
- 최근 2회 이내 동일 비밀번호 사용 불가

### 3.4 [2.5.4] 비밀번호 관리

```bash
# 각 사용자의 비밀번호 만료일 확인
sshpass -p1 ssh user@192.168.208.142 "sudo chage -l user 2>/dev/null"
```

### 3.5 [2.6.1] 네트워크 접근

```bash
# 방화벽 규칙 점검
echo "=== secu 서버 방화벽 ==="
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null"

# 기본 정책 확인 (DROP이어야 함)
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | grep 'policy'"
```

---

## 4. 점검 항목 11~15: 시스템 보안

### 4.1 [2.6.2] 정보시스템 접근

```bash
# SSH 접근 제한 설정 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: SSH 설정 ==="
  sshpass -p1 ssh user@$ip "grep -E 'PermitRootLogin|PasswordAuthentication|MaxAuthTries|AllowUsers|AllowGroups|LoginGraceTime' /etc/ssh/sshd_config | grep -v '^#'"
done
```

### 4.2 [2.6.6] 서버 보안

```bash
# 불필요한 서비스 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 불필요 서비스 ==="
  sshpass -p1 ssh user@$ip "systemctl list-units --type=service --state=running --no-pager | grep -E 'cups|avahi|bluetooth|rpcbind|telnet|ftp' || echo '해당 없음'"
done

# SUID 파일 점검
sshpass -p1 ssh user@192.168.208.142 "find /usr -perm -4000 -type f 2>/dev/null | wc -l"
```

### 4.3 [2.7.1] 암호정책 적용

```bash
# 전송 구간 암호화 확인
echo "=== Wazuh Dashboard TLS ==="
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep -E 'Protocol|Cipher'"

echo "=== SSH 암호 알고리즘 ==="
sshpass -p1 ssh user@192.168.208.142 "ssh -Q cipher 2>/dev/null | head -10"
```

### 4.4 [2.9.1] 변경관리

```bash
# 최근 패키지 변경 이력
sshpass -p1 ssh user@192.168.208.142 "cat /var/log/dpkg.log 2>/dev/null | tail -10"
sshpass -p1 ssh user@192.168.208.142 "cat /var/log/apt/history.log 2>/dev/null | tail -20"
```

### 4.5 [2.9.3] 보안시스템 운영

```bash
# IPS 상태 확인
sshpass -p1 ssh user@192.168.208.150 "systemctl status suricata 2>/dev/null | head -5"

# WAF 상태 확인
sshpass -p1 ssh user@192.168.208.151 "systemctl status bunkerweb 2>/dev/null | head -5 || docker ps 2>/dev/null | grep bunkerweb"

# SIEM 상태 확인
sshpass -p1 ssh user@192.168.208.152 "systemctl status wazuh-manager 2>/dev/null | head -5"
```

---

## 5. 점검 항목 16~20: 로그 및 사고 대응

### 5.1 [2.10.4] 로그 및 접속기록 관리

```bash
# 로그 보존 설정
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 로그 보존 ==="
  sshpass -p1 ssh user@$ip "cat /etc/logrotate.conf 2>/dev/null | grep -E 'rotate|weekly|monthly|daily'"
  echo "--- 로그 파일 크기 ---"
  sshpass -p1 ssh user@$ip "ls -lh /var/log/syslog /var/log/auth.log 2>/dev/null"
done
```

**ISMS-P 기준**: 접근 기록 최소 **6개월** 이상 보관

### 5.2 [2.10.5] 시간 동기화

```bash
# NTP 설정 확인 (로그 시간 정확성)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "timedatectl 2>/dev/null | grep -E 'Time zone|NTP|synchronized'"
done
```

### 5.3 [2.10.7] 패치관리

```bash
# 보안 패치 현황
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 패치 현황 ==="
  sshpass -p1 ssh user@$ip "apt list --upgradable 2>/dev/null | wc -l"
done
```

### 5.4 [2.11.1] 사고 예방 및 대응체계 구축

```bash
# Wazuh 에이전트 설치 및 동작 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151; do
  echo "=== $ip: Wazuh Agent ==="
  sshpass -p1 ssh user@$ip "systemctl is-active wazuh-agent 2>/dev/null || echo 'N/A'"
done

# Wazuh Manager 알림 수집 확인
sshpass -p1 ssh user@192.168.208.152 "ls -la /var/ossec/logs/alerts/ 2>/dev/null | tail -3"
```

### 5.5 [2.11.4] 사고 분석 및 공유

```bash
# 최근 보안 이벤트 확인
sshpass -p1 ssh user@192.168.208.152 "tail -5 /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30"
```

---

## 6. 통합 점검 스크립트

다음은 위 20개 항목을 한 번에 실행하는 스크립트이다:

```bash
#!/bin/bash
# ISMS-P 핵심 20개 항목 자동 점검 스크립트
SERVERS="192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152"

echo "=========================================="
echo " ISMS-P 핵심 점검 실행: $(date)"
echo "=========================================="

for ip in $SERVERS; do
  echo ""
  echo "########## $ip ##########"

  echo "[2.5.1] 사용자 계정:"
  sshpass -p1 ssh -o StrictHostKeyChecking=no user@$ip \
    "awk -F: '\$3>=1000 && \$3<65534{print \$1}' /etc/passwd" 2>/dev/null

  echo "[2.5.3] 비밀번호 정책:"
  sshpass -p1 ssh user@$ip \
    "grep PASS_MAX_DAYS /etc/login.defs 2>/dev/null | grep -v '^#'" 2>/dev/null

  echo "[2.6.2] SSH 접근 제한:"
  sshpass -p1 ssh user@$ip \
    "grep -E 'PermitRootLogin|MaxAuthTries' /etc/ssh/sshd_config | grep -v '^#'" 2>/dev/null

  echo "[2.10.4] 로그 보존:"
  sshpass -p1 ssh user@$ip \
    "ls -lh /var/log/auth.log 2>/dev/null || echo 'N/A'" 2>/dev/null

  echo "[2.10.5] NTP 동기화:"
  sshpass -p1 ssh user@$ip \
    "timedatectl 2>/dev/null | grep synchronized" 2>/dev/null

  echo "[2.10.7] 패치 현황:"
  sshpass -p1 ssh user@$ip \
    "apt list --upgradable 2>/dev/null | wc -l" 2>/dev/null
done
```

---

## 7. 점검 결과 보고서 양식

```
=============================================
ISMS-P 점검 결과 보고서
점검일: 2026-03-27
점검자: (이름)
대상: 실습 환경 4개 서버
=============================================

| No | 항목번호 | 항목명 | 대상서버 | 점검결과 | 판정 | 비고 |
|----|---------|--------|---------|---------|------|------|
| 1 | 2.5.1 | 사용자계정관리 | 전체 | ... | 적합/부적합 | ... |
| 2 | 2.5.3 | 사용자인증 | 전체 | ... | 적합/부적합 | ... |
| ... | ... | ... | ... | ... | ... | ... |

[부적합 항목 개선 계획]
- 항목번호:
- 현황:
- 개선 방안:
- 완료 예정일:
```

---

## 8. 핵심 정리

1. **20개 핵심 항목** = 계정/인증/접근통제/암호화/로깅/패치/사고대응
2. **점검 유형** = 서류 + 기술 + 인터뷰 + 현장
3. **판정 기준** = 적합, 부분적합, 부적합, 해당없음
4. **자동화** = 기술 점검은 스크립트로 반복 수행 가능
5. **문서화** = 점검 결과는 반드시 증적으로 보관

---

## 과제

1. 위 통합 점검 스크립트를 실행하고 결과를 보고서 양식에 맞게 작성하시오
2. 부적합 판정된 항목에 대한 개선 방안을 제시하시오
3. 점검 항목을 3개 추가하여 스크립트를 확장하시오

---

## 참고 자료

- KISA ISMS-P 인증기준 해설서
- KISA 주요정보통신기반시설 기술적 취약점 분석 가이드
- 정보보호 컴플라이언스 점검 실무 가이드


---

---

## 심화: 표준/인증 실무 보충

### 보안 통제 구현 패턴

실무에서 통제 항목을 구현할 때의 일반적 패턴을 이해한다.

```
[1] 정책(Policy) 수립
    → "무엇을 해야 하는가?" 를 문서로 정의
    예: "모든 서버는 90일마다 패스워드를 변경한다"

[2] 절차(Procedure) 작성
    → "어떻게 하는가?" 를 단계별로 정리
    예: "1. passwd 명령 실행 2. 복잡도 확인 3. 변경 로그 기록"

[3] 기술적 구현(Technical Implementation)
    → 실제 시스템에 적용
    예: /etc/login.defs에 PASS_MAX_DAYS=90 설정

[4] 증적(Evidence) 수집
    → 구현되었음을 증명하는 자료 확보
    예: login.defs 캡처, 변경 로그, OpsClaw evidence
```

### 증적 수집 실습

```bash
# ISO 27001 A.8.5 (안전한 인증) 점검 증적 수집
echo "=== 패스워드 정책 확인 ==="
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80 "
  echo '--- login.defs ---' && grep -E 'PASS_MAX|PASS_MIN|PASS_WARN' /etc/login.defs
  echo '--- pam 설정 ---' && grep pam_pwquality /etc/pam.d/common-password 2>/dev/null || echo 'pam_pwquality 미설정'
  echo '--- sudo 설정 ---' && sudo -l 2>/dev/null | head -5
" 2>/dev/null

# 결과를 OpsClaw evidence로 기록
# (OpsClaw dispatch 사용)
```

### GAP 분석 워크시트 예시

| 통제 ID | 통제 항목 | 현재 상태 | 목표 | GAP | 우선순위 |
|---------|---------|---------|------|-----|---------|
| A.5.1 | 정보보안 정책 | 문서 없음 | 승인된 정책 문서 | 정책 수립 필요 | 높음 |
| A.8.2 | 접근 권한 관리 | sudo NOPASSWD:ALL | 최소 권한 | sudo 제한 필요 | 긴급 |
| A.8.5 | 안전한 인증 | 단순 비밀번호 | 복잡도+MFA | 정책 변경 | 높음 |
| A.12.4 | 로깅 | 부분 수집 | 전체 수집+SIEM | Wazuh 연동 | 중간 |

### 인증 심사 대비 FAQ

| 질문 | 준비 방법 |
|------|---------|
| "이 통제의 증적을 보여주세요" | OpsClaw evidence/replay로 실행 이력 제시 |
| "리스크 평가를 어떻게 했나요?" | 리스크 평가 워크시트 + 기준 설명 |
| "부적합 사항은 어떻게 처리했나요?" | 시정 조치 계획서 + 완료 증적 |
| "경영진의 검토는?" | 검토 회의록 + 서명 |

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

**Q1.** 이번 주차 "Week 06: ISMS-P (2) - 점검 항목 실습"의 핵심 목적은 무엇인가?
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

