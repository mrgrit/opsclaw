# Week 08: 중간고사 - ISO 27001 기반 보안 점검 체크리스트

## 시험 개요

- **유형**: 실기 시험 (실습 환경 점검 + 보고서 작성)
- **시간**: 120분
- **배점**: 100점
- **범위**: ISO 27001 Annex A 기술적 통제 중심

---

## 시험 구성

| 파트 | 내용 | 배점 |
|------|------|------|
| Part A | 보안 점검 체크리스트 작성 | 20점 |
| Part B | 4개 서버 기술 점검 실행 | 40점 |
| Part C | 점검 결과 분석 및 보고서 작성 | 30점 |
| Part D | 개선 방안 제시 | 10점 |

---

## Part A: 보안 점검 체크리스트 작성 (20점)

### 과제

ISO 27001:2022 Annex A 기술적 통제(A.8)를 기반으로, 우리 실습 환경에 적합한 **보안 점검 체크리스트**를 작성하시오.

### 요구사항

최소 15개 항목을 포함하며, 각 항목에 다음을 명시하시오:

| 필드 | 설명 |
|------|------|
| 항목 번호 | ISO 27001 통제 번호 (예: A.8.5) |
| 항목명 | 점검 내용 요약 |
| 점검 명령 | 실제 실행할 Linux 명령어 |
| 기대 결과 | 적합 판정 기준 |
| 대상 서버 | 해당 서버 IP |

### 템플릿

```
| No | 통제번호 | 항목명 | 점검 명령 | 기대 결과 | 대상서버 |
|----|---------|--------|----------|----------|---------|
| 1 | A.8.2 | root 직접 로그인 차단 | grep PermitRootLogin /etc/ssh/sshd_config | no | 전체 |
| 2 | A.8.5 | 비밀번호 최대 사용일 | grep PASS_MAX_DAYS /etc/login.defs | <=90 | 전체 |
| ... | ... | ... | ... | ... | ... |
```

---

## Part B: 기술 점검 실행 (40점)

### 과제

Part A에서 작성한 체크리스트를 실제 4개 서버에서 실행하고 결과를 기록하시오.

### 서버 접속 정보

```bash
# opsclaw (Control Plane)
sshpass -p1 ssh user@192.168.208.142

# secu (방화벽/IPS)
sshpass -p1 ssh user@192.168.208.150

# web (WAF/웹앱)
sshpass -p1 ssh user@192.168.208.151

# siem (SIEM)
sshpass -p1 ssh user@192.168.208.152
```

### 필수 점검 항목 (최소 이것은 수행할 것)

#### 1. 계정 관리 (A.8.2)

```bash
# 각 서버에서 실행
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "========== $ip =========="

  echo "[1] 일반 사용자 계정 목록:"
  sshpass -p1 ssh user@$ip "awk -F: '\$3>=1000 && \$3<65534{print \$1,\$6,\$7}' /etc/passwd"

  echo "[2] sudo 권한 사용자:"
  sshpass -p1 ssh user@$ip "getent group sudo 2>/dev/null"

  echo "[3] root 직접 로그인 설정:"
  sshpass -p1 ssh user@$ip "grep '^PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null || echo '기본값'"
done
```

#### 2. 인증 설정 (A.8.5)

```bash
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "========== $ip =========="

  echo "[4] 비밀번호 정책:"
  sshpass -p1 ssh user@$ip "grep -E 'PASS_MAX_DAYS|PASS_MIN_DAYS|PASS_MIN_LEN' /etc/login.defs | grep -v '^#'"

  echo "[5] SSH 최대 인증 시도:"
  sshpass -p1 ssh user@$ip "grep 'MaxAuthTries' /etc/ssh/sshd_config | grep -v '^#' || echo '기본값(6)'"

  echo "[6] 비밀번호 복잡도:"
  sshpass -p1 ssh user@$ip "cat /etc/security/pwquality.conf 2>/dev/null | grep -v '^#' | grep -v '^$' || echo '미설정'"
done
```

#### 3. 로깅 (A.8.15)

```bash
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "========== $ip =========="

  echo "[7] syslog 서비스:"
  sshpass -p1 ssh user@$ip "systemctl is-active rsyslog 2>/dev/null || systemctl is-active syslog-ng 2>/dev/null"

  echo "[8] 로그 파일 존재:"
  sshpass -p1 ssh user@$ip "ls -lh /var/log/syslog /var/log/auth.log 2>/dev/null"

  echo "[9] auditd 상태:"
  sshpass -p1 ssh user@$ip "systemctl is-active auditd 2>/dev/null || echo '미설치'"

  echo "[10] Wazuh Agent:"
  sshpass -p1 ssh user@$ip "systemctl is-active wazuh-agent 2>/dev/null || echo 'N/A'"
done
```

#### 4. 네트워크 보안 (A.8.20~A.8.22)

```bash
# secu 서버 방화벽
echo "[11] 방화벽 기본 정책:"
sshpass -p1 ssh user@192.168.208.150 "sudo nft list ruleset 2>/dev/null | grep policy"

echo "[12] 열린 포트:"
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "--- $ip ---"
  sshpass -p1 ssh user@$ip "ss -tlnp 2>/dev/null | grep LISTEN"
done

# IPS 상태
echo "[13] Suricata IPS:"
sshpass -p1 ssh user@192.168.208.150 "systemctl is-active suricata 2>/dev/null"
```

#### 5. 암호화 (A.8.24)

```bash
echo "[14] TLS 버전 (Wazuh Dashboard):"
sshpass -p1 ssh user@192.168.208.152 "echo | openssl s_client -connect localhost:443 2>/dev/null | grep Protocol"

echo "[15] SSH 프로토콜 버전:"
sshpass -p1 ssh user@192.168.208.142 "ssh -V 2>&1"
```

#### 6. 시스템 설정 (A.8.9)

```bash
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "========== $ip =========="

  echo "[16] 커널 보안 파라미터:"
  sshpass -p1 ssh user@$ip "sysctl net.ipv4.ip_forward net.ipv4.conf.all.accept_redirects 2>/dev/null"

  echo "[17] NTP 동기화:"
  sshpass -p1 ssh user@$ip "timedatectl 2>/dev/null | grep -E 'synchronized|NTP'"

  echo "[18] 패치 현황:"
  sshpass -p1 ssh user@$ip "apt list --upgradable 2>/dev/null | wc -l"
done
```

---

## Part C: 점검 결과 분석 및 보고서 (30점)

### 보고서 구조

```
=== 보안 점검 결과 보고서 ===

1. 개요
   - 점검 목적
   - 점검 범위 (대상 서버 4대)
   - 점검 기준 (ISO 27001:2022 Annex A)
   - 점검 일시

2. 점검 결과 요약
   | 판정 | 항목 수 |
   |------|---------|
   | 적합 | ? |
   | 부분적합 | ? |
   | 부적합 | ? |

3. 상세 점검 결과
   (각 항목별 실제 결과와 판정)

4. 주요 발견사항
   - 미준수 항목과 위험도
   - 즉시 조치가 필요한 사항

5. 결론
```

### 평가 기준

| 항목 | 배점 |
|------|------|
| 보고서 구조 완성도 | 5점 |
| 점검 결과 정확성 | 10점 |
| 분석의 깊이 | 10점 |
| 문서 품질 | 5점 |

---

## Part D: 개선 방안 (10점)

### 과제

부적합으로 판정된 항목에 대해 다음을 제시하시오:

1. **즉시 조치 항목** (1주 이내 가능한 것)
2. **단기 개선 항목** (1개월 이내)
3. **중장기 개선 항목** (3개월 이상)

### 예시

```
[부적합 항목: A.8.5 비밀번호 정책]
- 현황: PASS_MAX_DAYS = 99999 (만료 없음)
- 위험도: 높음
- 즉시 조치: /etc/login.defs에서 PASS_MAX_DAYS를 90으로 변경
- 단기: pwquality.conf 설정으로 복잡도 강화
- 중장기: 키 기반 인증으로 전환, 비밀번호 관리자 도입
```

---

## 채점 기준 상세

| 평가 항목 | 우수 (100%) | 보통 (70%) | 미흡 (40%) |
|-----------|------------|------------|------------|
| 체크리스트 | 15개 이상, 명령어 정확 | 10개 이상 | 10개 미만 |
| 점검 실행 | 4대 서버 전체 수행 | 2~3대 수행 | 1대만 수행 |
| 결과 분석 | 정확한 판정+근거 | 판정만 기재 | 부정확 |
| 보고서 | 구조 완비, 논리적 | 구조 미흡 | 단편적 |
| 개선방안 | 구체적, 실현가능 | 추상적 | 미제출 |

---

## 시험 전 체크사항

```bash
# 서버 접속 확인
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 user@$ip "hostname" 2>/dev/null \
    && echo "$ip: OK" || echo "$ip: FAIL"
done
```

---

## 참고

- 오픈 북 시험: Week 02~07 강의 자료 참고 가능
- 인터넷 검색 가능 (다만 다른 학생과 동일한 답안은 감점)
- 결과 파일을 제출 (txt 또는 md 형식)
