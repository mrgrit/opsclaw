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
