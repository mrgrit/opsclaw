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
