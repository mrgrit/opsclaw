# Week 15: 기말고사 - 모의 인증 심사 (상세 버전)

## 학습 목표

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

# Week 15: 기말고사 - 모의 인증 심사

## 시험 개요

- **유형**: 팀 실기 시험 (2~3인 1조)
- **시간**: 180분
- **배점**: 100점
- **역할**: 심사팀(1조) / 피심사 조직(1조)을 번갈아 수행
- **기준**: ISO 27001:2022 + ISMS-P 통합

---

## 시험 구성

| 파트 | 내용 | 배점 | 시간 |
|------|------|------|------|
| Part A | 심사 준비 (피심사 역할) | 30점 | 60분 |
| Part B | 모의 심사 실시 | 40점 | 80분 |
| Part C | 심사 보고서 작성 | 30점 | 40분 |

---

## Part A: 심사 준비 - 피심사 조직 역할 (30점)

### 과제

실습 환경 4개 서버에 대해 인증 심사를 받을 준비를 하시오.

### A-1. SoA 완성 (10점)

A.8 기술적 통제 34개 항목에 대한 적용성 보고서를 작성하시오.

```bash
# 점검을 위한 기본 정보 수집
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "========== $ip =========="
  sshpass -p1 ssh user@$ip "
    hostname
    echo '--- 서비스 ---'
    systemctl list-units --type=service --state=running --no-pager | wc -l
    echo '--- 포트 ---'
    ss -tlnp 2>/dev/null | grep LISTEN | wc -l
  " 2>/dev/null
done
```

### A-2. 증적 수집 (10점)

최소 10개 통제 항목에 대한 증적을 수집하시오.

```bash
# 증적 수집 가이드
EVIDENCE="/tmp/exam_evidence"
mkdir -p $EVIDENCE

# [A.8.2] 특수접근권한 증적
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh user@$ip "
    echo 'Server: $ip'
    echo 'PermitRootLogin:'
    grep PermitRootLogin /etc/ssh/sshd_config | grep -v '^#'
    echo 'sudo users:'
    getent group sudo
  " 2>/dev/null >> $EVIDENCE/A8.2_evidence.txt
done

# [A.8.5] 보안인증 증적
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh user@$ip "
    echo 'Server: $ip'
    grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS' /etc/login.defs | grep -v '^#'
    echo 'MaxAuthTries:'
    grep MaxAuthTries /etc/ssh/sshd_config | grep -v '^#'
  " 2>/dev/null >> $EVIDENCE/A8.5_evidence.txt
done

# [A.8.15] 로깅 증적
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh user@$ip "
    echo 'Server: $ip'
    echo 'rsyslog:'
    systemctl is-active rsyslog
    echo 'log files:'
    ls -lh /var/log/syslog /var/log/auth.log 2>/dev/null
  " 2>/dev/null >> $EVIDENCE/A8.15_evidence.txt
done

# [A.8.16] 모니터링 증적
sshpass -p1 ssh user@192.168.208.152 "
  echo 'Wazuh Manager:'
  systemctl is-active wazuh-manager
  echo 'Agent count:'
  /var/ossec/bin/agent_control -l 2>/dev/null | wc -l
  echo 'Recent alerts:'
  wc -l /var/ossec/logs/alerts/alerts.json
" 2>/dev/null > $EVIDENCE/A8.16_evidence.txt

# [A.8.20] 네트워크보안 증적
sshpass -p1 ssh user@192.168.208.150 "
  echo 'Firewall rules:'
  sudo nft list ruleset
  echo 'Suricata:'
  systemctl is-active suricata
" 2>/dev/null > $EVIDENCE/A8.20_evidence.txt

# [A.8.24] 암호화 증적
sshpass -p1 ssh user@192.168.208.152 "
  echo 'TLS version:'
  echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol
" 2>/dev/null > $EVIDENCE/A8.24_evidence.txt

echo "=== 수집된 증적 ==="
ls -la $EVIDENCE/
```

### A-3. 심사 답변 준비 (10점)

다음 질문에 대한 답변을 준비하시오:

1. "정보보안 관리체계의 범위는 어디까지입니까?"
2. "리스크 평가 결과를 보여주십시오."
3. "접근통제 정책과 실제 구현이 일치합니까?"
4. "보안 사고 탐지 및 대응 체계를 설명해 주십시오."
5. "변경 관리 절차는 어떻게 운영됩니까?"
6. "패치 관리 현황을 보여주십시오."
7. "백업 및 복구 절차가 있습니까?"
8. "로그 보관 기간은 얼마입니까?"

---

## Part B: 모의 심사 실시 (40점)

### B-1. 심사팀 역할 (20점)

상대 조의 환경을 심사한다.

**심사 영역 (택 5개)**:

#### 영역 1: 접근통제 심사

```bash
# 심사 명령어
echo "=== 접근통제 심사 ==="

# 1. 사용자 계정 관리
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip: 계정 ---"
  sshpass -p1 ssh user@$ip "awk -F: '\$3>=1000 && \$3<65534 {print \$1,\$3,\$7}' /etc/passwd"
done

# 2. 권한 관리
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip: sudo ---"
  sshpass -p1 ssh user@$ip "getent group sudo"
done

# 3. SSH 설정
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip: SSH ---"
  sshpass -p1 ssh user@$ip "grep -E 'PermitRootLogin|PasswordAuthentication|MaxAuthTries|AllowUsers' /etc/ssh/sshd_config | grep -v '^#'"
done
```

#### 영역 2: 로깅 및 모니터링 심사

```bash
echo "=== 로깅/모니터링 심사 ==="

# 1. 로그 서비스 동작 여부
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip ---"
  sshpass -p1 ssh user@$ip "systemctl is-active rsyslog auditd 2>/dev/null; ls -lh /var/log/auth.log /var/log/syslog 2>/dev/null"
done

# 2. SIEM 통합 모니터링
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null"
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | wc -l"

# 3. 로그 보관 기간
sshpass -p1 ssh user@192.168.208.142 "cat /etc/logrotate.conf | grep -E 'rotate|weekly'"
```

#### 영역 3: 네트워크 보안 심사

```bash
echo "=== 네트워크 보안 심사 ==="

# 방화벽 규칙
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null"

# IPS 상태
sshpass -p1 ssh user@192.168.208.150 "systemctl is-active suricata 2>/dev/null"

# 열린 포트 (불필요 서비스)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip ---"
  sshpass -p1 ssh user@$ip "ss -tlnp | grep LISTEN"
done
```

#### 영역 4: 암호화 심사

```bash
echo "=== 암호화 심사 ==="

# TLS 버전
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep -E 'Protocol|Cipher'"

# SSH 알고리즘
sshpass -p1 ssh user@192.168.208.142 "grep -E 'Ciphers|MACs|KexAlgorithms' /etc/ssh/sshd_config | grep -v '^#'"

# 파일 권한
sshpass -p1 ssh user@192.168.208.142 "stat -c '%a %n' /etc/shadow /etc/ssh/ssh_host_*_key 2>/dev/null"
```

#### 영역 5: 사고 대응 심사

```bash
echo "=== 사고 대응 심사 ==="

# 탐지 체계
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null"
sshpass -p1 ssh user@192.168.208.150 "systemctl is-active suricata 2>/dev/null"

# 격리/차단 능력
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | grep -c 'drop'"

# 최근 고위험 이벤트 대응 기록
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 12:
            print(f'{a.get(\"timestamp\",\"\")} Level {r[\"level\"]}: {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -5"
```

### B-2. 피심사 조직 역할 (20점)

심사팀의 질문에 답변하고, 요청받은 증적을 즉시 제시한다.

**평가 기준**:
- 질문에 대한 정확한 답변 (5점)
- 증적의 즉시 제시 (5점)
- 기술적 설명의 정확성 (5점)
- 부적합 사항에 대한 인정과 개선 의지 (5점)

---

## Part C: 심사 보고서 작성 (30점)

### 보고서 양식

```
================================================================
모의 인증 심사 보고서
================================================================

1. 심사 개요
   - 심사일: 2026-XX-XX
   - 심사 기준: ISO 27001:2022, ISMS-P
   - 심사 범위: 서버 4대 (opsclaw, secu, web, siem)
   - 심사팀: (이름)
   - 피심사 조직: (팀명)

2. 심사 결과 요약
   | 구분 | 건수 |
   |------|------|
   | 중대 부적합 (Major) | ? |
   | 경미 부적합 (Minor) | ? |
   | 관찰 사항 (OFI) | ? |
   | 적합 | ? |

3. 상세 발견사항

   [부적합 NC-001]
   - 통제 항목: A.X.XX
   - 발견 내용: (구체적 기술)
   - 증거: (명령어 실행 결과)
   - 심각도: Major / Minor
   - 권고 조치: (구체적 개선 방안)

   [부적합 NC-002]
   ...

   [관찰사항 OFI-001]
   ...

4. 영역별 평가

   | 영역 | 점검 항목 수 | 적합 | 부적합 | 평가 |
   |------|------------|------|--------|------|
   | 접근통제 | ? | ? | ? | 양호/미흡 |
   | 로깅 | ? | ? | ? | 양호/미흡 |
   | 네트워크 | ? | ? | ? | 양호/미흡 |
   | 암호화 | ? | ? | ? | 양호/미흡 |
   | 사고대응 | ? | ? | ? | 양호/미흡 |

5. 종합 의견
   (인증 가능/조건부 인증/인증 불가 판정과 사유)

6. 시정 조치 계획 (피심사 조직 작성)
   | NC 번호 | 시정 조치 | 담당 | 완료 예정일 |
   |---------|----------|------|-----------|
   | NC-001 | ... | ... | ... |
================================================================
```

---

## 채점 기준

### Part A: 심사 준비 (30점)

| 항목 | 우수 | 보통 | 미흡 |
|------|------|------|------|
| SoA 완성도 | 34개 항목 전체, 사유 충분 | 20개 이상 | 20개 미만 |
| 증적 수집 | 10개 이상 항목, 해시 포함 | 7개 이상 | 7개 미만 |
| 답변 준비 | 8개 질문 모두 준비 | 5개 이상 | 5개 미만 |

### Part B: 모의 심사 (40점)

| 항목 | 우수 | 보통 | 미흡 |
|------|------|------|------|
| 심사 수행 | 5개 영역, 적절한 질문 | 3개 영역 | 2개 이하 |
| 발견사항 도출 | 정확한 부적합 도출 | 일부 정확 | 부정확 |
| 피심사 대응 | 즉시 증적 제시, 정확한 답변 | 부분적 | 미흡 |

### Part C: 보고서 (30점)

| 항목 | 우수 | 보통 | 미흡 |
|------|------|------|------|
| 구조 | 양식 완비 | 일부 누락 | 구조 미흡 |
| 정확성 | 증거 기반 판정 | 일부 주관적 | 근거 없음 |
| 실용성 | 구체적 시정조치 제시 | 추상적 | 미제시 |

---

## 시험 전 체크리스트

```bash
# 서버 접속 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 user@$ip "hostname" 2>/dev/null \
    && echo "$ip: OK" || echo "$ip: FAIL"
done

# Wazuh 상태 확인
sshpass -p1 ssh user@192.168.208.152 "systemctl is-active wazuh-manager 2>/dev/null"
```

---

## 참고

- 오픈 북 시험: Week 02~14 강의 자료, 인터넷 검색 가능
- 팀 구성: 수업 시작 시 발표
- 제출물: 심사 보고서 (md 또는 txt 파일)
- 이 시험은 학기 전체 내용을 종합하는 실전 연습이다


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 4)

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

**Q1.** 이번 주차 "Week 15: 기말고사 - 모의 인증 심사"의 핵심 목적은 무엇인가?
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

