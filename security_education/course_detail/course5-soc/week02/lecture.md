# Week 02: 로그 이해 (1) - 시스템 로그 (상세 버전)

## 학습 목표
- Linux 시스템 로그의 종류와 위치를 이해한다
- syslog, auth.log, journal의 구조를 분석할 수 있다
- auditd를 활용한 상세 감사 로깅을 이해한다
- 로그에서 보안 관련 이벤트를 식별할 수 있다


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

## 용어 해설 (보안관제/SOC 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC** | Security Operations Center | 보안 관제 센터 (24/7 모니터링) | 경찰 112 상황실 |
| **관제** | Monitoring/Surveillance | 보안 이벤트를 실시간 감시하는 활동 | CCTV 관제 |
| **경보** | Alert | 보안 이벤트가 탐지 규칙에 매칭되어 발생한 알림 | 화재 경보기 울림 |
| **이벤트** | Event | 시스템에서 발생한 모든 활동 기록 | 일어난 일 하나하나 |
| **인시던트** | Incident | 보안 정책을 위반한 이벤트 (실제 위협) | 실제 화재 발생 |
| **오탐** | False Positive | 정상 활동을 공격으로 잘못 탐지 | 화재 경보기가 요리 연기에 울림 |
| **미탐** | False Negative | 실제 공격을 놓침 | 도둑이 CCTV에 안 잡힘 |
| **TTD** | Time to Detect | 공격 발생~탐지까지 걸리는 시간 | 화재 발생~경보 울림 시간 |
| **TTR** | Time to Respond | 탐지~대응까지 걸리는 시간 | 경보~소방차 도착 시간 |
| **SIGMA** | SIGMA | SIEM 벤더에 무관한 범용 탐지 룰 포맷 | 국제 표준 수배서 양식 |
| **Tier 1/2/3** | SOC Tiers | 관제 인력 수준 (L1:모니터링, L2:분석, L3:전문가) | 일반의→전문의→교수 |
| **트리아지** | Triage | 경보를 우선순위별로 분류하는 작업 | 응급실 환자 분류 |
| **플레이북** | Playbook (IR) | 인시던트 유형별 대응 절차 매뉴얼 | 화재 대응 매뉴얼 |
| **포렌식** | Forensics | 사이버 범죄 수사를 위한 증거 수집·분석 | 범죄 현장 감식 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 도메인, 해시) | 수배범의 지문, 차량번호 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술·기법·절차 | 범인의 범행 수법 |
| **위협 헌팅** | Threat Hunting | 탐지 룰에 걸리지 않는 위협을 능동적으로 찾는 활동 | 잠복 수사 |
| **syslog** | syslog | 시스템 로그를 원격 전송하는 프로토콜 (UDP 514) | 모든 부서 보고서를 본사로 모으는 시스템 |


---

# Week 02: 로그 이해 (1) - 시스템 로그

## 학습 목표

- Linux 시스템 로그의 종류와 위치를 이해한다
- syslog, auth.log, journal의 구조를 분석할 수 있다
- auditd를 활용한 상세 감사 로깅을 이해한다
- 로그에서 보안 관련 이벤트를 식별할 수 있다

---

## 1. 시스템 로그 개요

### 1.1 왜 로그가 중요한가?

보안관제(SOC)에서 로그는 **모든 것의 시작**이다.

```
공격 발생 → 로그에 흔적 남김 → SOC 분석원이 로그로 탐지/분석
```

- 사고 탐지의 **1차 데이터 소스**
- 포렌식 조사의 핵심 증거
- 컴플라이언스 요구사항 (ISMS-P 2.10.4: 로그 6개월 보관)

### 1.2 Linux 로그 시스템 구조

```
[애플리케이션] → [rsyslog/systemd-journal] → [로그 파일]
                                              → [원격 SIEM (Wazuh)]
```

| 구성 요소 | 역할 |
|-----------|------|
| rsyslog | 전통적 로그 수집 데몬 |
| systemd-journald | systemd 기반 로그 수집 |
| logrotate | 로그 순환(rotation) 관리 |
| Wazuh Agent | 원격 SIEM으로 로그 전송 |

---

## 2. 주요 로그 파일

### 2.1 로그 파일 위치와 용도

| 파일 | 용도 | SOC 관련 |
|------|------|---------|
| /var/log/syslog | 시스템 전반 이벤트 | 서비스 이상, 커널 오류 |
| /var/log/auth.log | 인증 관련 (SSH, sudo, su) | 무차별 대입, 권한 상승 |
| /var/log/kern.log | 커널 메시지 | 하드웨어 오류, 보안 모듈 |
| /var/log/dpkg.log | 패키지 설치/제거 | 비인가 소프트웨어 설치 |
| /var/log/cron.log | cron 작업 실행 | 비인가 예약 작업 |
| /var/log/faillog | 로그인 실패 기록 | 무차별 대입 공격 |

### 2.2 실습: 로그 파일 확인

```bash
# 각 서버의 로그 파일 확인
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "========== $ip =========="
  sshpass -p1 ssh user@$ip "ls -lh /var/log/syslog /var/log/auth.log /var/log/kern.log 2>/dev/null"
done
```

---

## 3. syslog 분석

### 3.1 syslog 메시지 형식

```
<날짜> <호스트명> <프로세스[PID]>: <메시지>
```

예시:
```
Mar 27 10:15:03 opsclaw sshd[12345]: Accepted password for user from 192.168.208.1 port 54321 ssh2
```

| 필드 | 값 | 의미 |
|------|-----|------|
| 날짜 | Mar 27 10:15:03 | 이벤트 발생 시각 |
| 호스트 | opsclaw | 로그를 생성한 서버 |
| 프로세스 | sshd[12345] | 프로세스명과 PID |
| 메시지 | Accepted password... | 이벤트 상세 |

### 3.2 syslog 심각도 (Severity)

| 코드 | 이름 | 의미 |
|------|------|------|
| 0 | Emergency | 시스템 사용 불가 |
| 1 | Alert | 즉시 조치 필요 |
| 2 | Critical | 치명적 상황 |
| 3 | Error | 오류 발생 |
| 4 | Warning | 경고 |
| 5 | Notice | 정상이지만 주목할 사항 |
| 6 | Info | 정보성 메시지 |
| 7 | Debug | 디버그 메시지 |

### 3.3 실습: syslog 분석

```bash
# 최근 syslog 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "tail -20 /var/log/syslog"

# 오류 메시지만 필터링
sshpass -p1 ssh opsclaw@10.20.30.201 "grep -i 'error\|fail\|critical' /var/log/syslog | tail -10"

# 특정 서비스의 로그만 추출
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'sshd' /var/log/syslog | tail -10"

# rsyslog 설정 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "cat /etc/rsyslog.conf | grep -v '^#' | grep -v '^$' | head -20"
```

---

## 4. auth.log 분석

### 4.1 auth.log의 중요성

auth.log는 SOC 분석원이 **가장 먼저 확인**하는 로그이다.

기록 내용:
- SSH 로그인 성공/실패
- sudo 명령 실행
- su (사용자 전환) 시도
- PAM 인증 이벤트

### 4.2 실습: SSH 로그인 분석

```bash
# SSH 로그인 성공
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Accepted' /var/log/auth.log | tail -10"

# SSH 로그인 실패
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log | tail -10"

# 실패한 사용자명 통계
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{for(i=1;i<=NF;i++) if(\$i==\"for\") print \$(i+1)}' | sort | uniq -c | sort -rn | head -10"

# 실패한 출발지 IP 통계
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -10"
```

### 4.3 실습: sudo 사용 분석

```bash
# sudo 명령 실행 이력
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'sudo:' /var/log/auth.log | tail -10"

# sudo 실패 (권한 없는 사용자의 시도)
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'NOT in sudoers' /var/log/auth.log 2>/dev/null"

# su 명령 사용 이력
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'su:' /var/log/auth.log | tail -5"
```

### 4.4 실습: 무차별 대입 공격 패턴 식별

```bash
# 1분 내 동일 IP에서 5회 이상 실패 = 무차별 대입 의심
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$1,\$2,substr(\$3,1,5),\$(NF-3)}' | sort | uniq -c | sort -rn | head -10"

# 존재하지 않는 사용자로 시도 (Invalid user)
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Invalid user' /var/log/auth.log 2>/dev/null | tail -10"
```

---

## 5. systemd journal 분석

### 5.1 journalctl 기본 사용법

```bash
# 최근 로그 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "journalctl --no-pager | tail -20"

# 특정 서비스의 로그
sshpass -p1 ssh opsclaw@10.20.30.201 "journalctl -u sshd --no-pager | tail -10"

# 시간 범위로 필터링
sshpass -p1 ssh opsclaw@10.20.30.201 "journalctl --since '1 hour ago' --no-pager | tail -20"

# 부팅 이후 로그
sshpass -p1 ssh opsclaw@10.20.30.201 "journalctl -b --no-pager | tail -10"

# 우선순위별 필터링 (err 이상)
sshpass -p1 ssh opsclaw@10.20.30.201 "journalctl -p err --no-pager | tail -10"

# 커널 메시지만
sshpass -p1 ssh opsclaw@10.20.30.201 "journalctl -k --no-pager | tail -10"
```

### 5.2 journal vs syslog 비교

| 항목 | syslog (rsyslog) | journal (systemd) |
|------|-----------------|-------------------|
| 형식 | 텍스트 파일 | 바이너리 |
| 조회 | grep, awk | journalctl |
| 구조화 | 비구조화 | 구조화 (필드) |
| 보관 | logrotate | 자체 관리 |
| 장점 | 단순, 호환성 | 검색 강력, 메타데이터 풍부 |

### 5.3 실습: journal 고급 검색

```bash
# JSON 형식으로 출력 (필드 확인)
sshpass -p1 ssh opsclaw@10.20.30.201 "journalctl -u sshd -o json --no-pager | tail -1 | python3 -m json.tool 2>/dev/null"

# 특정 PID의 로그
sshpass -p1 ssh opsclaw@10.20.30.201 "journalctl _PID=1 --no-pager | tail -5"

# 디스크 사용량 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "journalctl --disk-usage 2>/dev/null"
```

---

## 6. auditd (감사 로깅)

### 6.1 auditd란?

Linux Audit System은 **커널 수준**에서 시스템 호출(syscall)을 감시한다.
일반 로그보다 훨씬 상세한 정보를 기록할 수 있다.

- 파일 접근 감시
- 시스템 호출 추적
- 사용자 명령 기록
- 네트워크 연결 추적

### 6.2 실습: auditd 상태 확인

```bash
# auditd 설치 여부 확인
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "systemctl is-active auditd 2>/dev/null || echo 'auditd 미설치'"
  sshpass -p1 ssh user@$ip "which auditctl 2>/dev/null || echo 'auditctl 없음'"
done
```

### 6.3 auditd 규칙 예시

만약 auditd가 설치되어 있다면:

```bash
# 현재 감사 규칙 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "sudo auditctl -l 2>/dev/null || echo '규칙 없음 또는 auditd 미설치'"

# /etc/passwd 파일 변경 감시 규칙 (예시)
# sudo auditctl -w /etc/passwd -p wa -k passwd_changes

# /etc/shadow 파일 접근 감시 규칙 (예시)
# sudo auditctl -w /etc/shadow -p r -k shadow_access

# audit 로그 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "tail -10 /var/log/audit/audit.log 2>/dev/null || echo 'audit 로그 없음'"
```

### 6.4 auditd 로그 형식

```
type=SYSCALL msg=audit(1648389600.123:456): arch=c000003e syscall=2
  success=yes exit=3 a0=7fff5a8b4e90 ... pid=12345 uid=0 ...
  comm="cat" exe="/usr/bin/cat" key="shadow_access"
```

| 필드 | 의미 |
|------|------|
| type | 이벤트 유형 (SYSCALL, PATH 등) |
| msg | 타임스탬프와 시리얼 번호 |
| syscall | 시스템 호출 번호 |
| pid | 프로세스 ID |
| uid | 사용자 ID |
| comm | 실행 명령 |
| key | 감사 규칙의 태그 |

---

## 7. 로그 분석 실전

### 7.1 종합 분석 스크립트

```bash
#!/bin/bash
# 시스템 로그 보안 분석 스크립트
echo "============================================"
echo " 시스템 로그 보안 분석 - $(date)"
echo "============================================"

IP=$1
if [ -z "$IP" ]; then IP=10.20.30.201; fi

echo ""
echo "[1] SSH 로그인 통계"
echo "  성공: $(sshpass -p1 ssh user@$IP 'grep -c "Accepted" /var/log/auth.log 2>/dev/null || echo 0')"
echo "  실패: $(sshpass -p1 ssh user@$IP 'grep -c "Failed password" /var/log/auth.log 2>/dev/null || echo 0')"

echo ""
echo "[2] 무차별 대입 의심 IP (10회 이상 실패)"
sshpass -p1 ssh user@$IP "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | awk '\$1>=10 {print \"  \" \$1 \"회: \" \$2}'"

echo ""
echo "[3] sudo 사용 현황"
sshpass -p1 ssh user@$IP "grep 'sudo:' /var/log/auth.log 2>/dev/null | wc -l | xargs -I{} echo '  총 {}건'"

echo ""
echo "[4] 시스템 오류"
sshpass -p1 ssh user@$IP "grep -i 'error\|critical\|emergency' /var/log/syslog 2>/dev/null | wc -l | xargs -I{} echo '  총 {}건'"

echo ""
echo "[5] 최근 패키지 변경"
sshpass -p1 ssh user@$IP "tail -5 /var/log/dpkg.log 2>/dev/null || echo '  dpkg 로그 없음'"
```

### 7.2 실습: 4개 서버 로그 비교 분석

```bash
# 모든 서버에서 로그 요약 수집
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "========== $ip =========="
  echo -n "SSH 실패: "
  sshpass -p1 ssh user@$ip "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo '0'"
  echo -n "SSH 성공: "
  sshpass -p1 ssh user@$ip "grep -c 'Accepted' /var/log/auth.log 2>/dev/null || echo '0'"
  echo -n "sudo 사용: "
  sshpass -p1 ssh user@$ip "grep -c 'sudo:' /var/log/auth.log 2>/dev/null || echo '0'"
  echo -n "에러 수: "
  sshpass -p1 ssh user@$ip "grep -ci 'error' /var/log/syslog 2>/dev/null || echo '0'"
done
```

---

## 8. 핵심 정리

1. **auth.log** = SOC 분석의 최우선 로그 (SSH, sudo, 인증)
2. **syslog** = 시스템 전반 이벤트 (서비스 장애, 커널)
3. **journalctl** = systemd 기반 구조화된 로그 검색
4. **auditd** = 커널 수준 상세 감사 (syscall, 파일 접근)
5. **패턴 식별** = 무차별 대입, 권한 상승, 비정상 접근

---

## 과제

1. 4개 서버의 auth.log를 분석하여 무차별 대입 공격 의심 IP를 보고하시오
2. journalctl을 사용하여 최근 1시간의 경고(warning) 이상 이벤트를 수집하시오
3. 로그 분석 스크립트를 작성하여 4개 서버의 보안 상태를 한눈에 파악할 수 있게 하시오

---

## 참고 자료

- Linux System Administration: Log Management
- SANS Logging Cheat Sheet
- auditd Configuration Guide


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 02: 로그 이해 (1) - 시스템 로그"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안관제/SOC의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. 시스템 로그 개요"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. 주요 로그 파일"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안관제/SOC 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. syslog 분석"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 탐지/대응의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 보안관제/SOC 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---

## 과제 (다음 주까지)


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


