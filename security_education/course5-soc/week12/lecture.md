# Week 12: 인시던트 대응 (3) - 내부 위협

## 학습 목표

- 내부자 위협(Insider Threat)의 유형과 탐지 방법을 이해한다
- sudo 남용, 비인가 접근, 데이터 유출을 탐지할 수 있다
- 내부자 위협에 대한 인시던트 대응 절차를 수행한다
- 로그 기반 내부자 행위 분석을 실습한다

---

## 1. 내부자 위협 개요

### 1.1 유형

| 유형 | 동기 | 예시 |
|------|------|------|
| 악의적 내부자 | 금전, 불만, 경쟁사 이직 | 데이터 유출, 시스템 파괴 |
| 부주의한 내부자 | 실수, 무지 | 설정 오류, 비밀번호 공유 |
| 침해된 내부자 | 계정 탈취 | 공격자가 직원 계정 사용 |

### 1.2 내부자 위협이 위험한 이유

- **이미 접근 권한이 있음** → 방화벽으로 막을 수 없음
- **정상 행위와 구분이 어려움** → FP가 매우 높음
- **탐지까지 평균 77일** (Ponemon 연구)

---

## 2. 탐지: sudo 남용

### 2.1 sudo 사용 패턴 분석

```bash
# 전체 sudo 사용 이력
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "========== $ip =========="
  sshpass -p1 ssh user@$ip "grep 'COMMAND=' /var/log/auth.log 2>/dev/null | \
    awk -F'COMMAND=' '{print \$2}' | sort | uniq -c | sort -rn | head -10"
done
```

### 2.2 위험한 sudo 명령 탐지

```bash
# 위험 명령 패턴
DANGER_CMDS="rm -rf|chmod 777|chown root|passwd|useradd|userdel|visudo|cat /etc/shadow|dd if=|mkfs|fdisk"

for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 위험 sudo 명령 ==="
  sshpass -p1 ssh user@$ip "grep 'COMMAND=' /var/log/auth.log 2>/dev/null | \
    grep -iE '$DANGER_CMDS'" 2>/dev/null
done
```

### 2.3 비인가 sudo 시도

```bash
# sudoers에 없는 사용자의 sudo 시도
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "grep 'NOT in sudoers' /var/log/auth.log 2>/dev/null"
done

# sudo 인증 실패
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "grep 'authentication failure.*sudo' /var/log/auth.log 2>/dev/null"
done
```

---

## 3. 탐지: 비인가 접근

### 3.1 비정상 시간대 접근

```bash
# 업무 외 시간 로그인 (22:00~06:00)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 야간 로그인 ==="
  sshpass -p1 ssh user@$ip "grep 'Accepted\|session opened' /var/log/auth.log 2>/dev/null | \
    awk '{
      split(\$3,t,\":\");
      h=int(t[1]);
      if(h>=22 || h<=5) print
    }' | head -5"
done
```

### 3.2 비정상 출발지 접근

```bash
# 평소와 다른 IP에서의 로그인
sshpass -p1 ssh user@192.168.208.142 "grep 'Accepted' /var/log/auth.log 2>/dev/null | \
  awk '{for(i=1;i<=NF;i++) if(\$i==\"from\") print \$(i+1)}' | sort | uniq -c | sort -rn"
```

### 3.3 권한 변경 탐지

```bash
# 그룹 변경 (sudo 그룹에 추가)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "grep -E 'usermod|groupmod|useradd.*sudo|gpasswd' /var/log/auth.log 2>/dev/null"
done

# /etc/sudoers 변경
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        sc = a.get('syscheck',{})
        if sc.get('path','') in ['/etc/sudoers', '/etc/passwd', '/etc/shadow', '/etc/group']:
            print(f'  {a.get(\"timestamp\",\"\")} - {sc[\"path\"]} 변경')
    except: pass
\" 2>/dev/null | tail -5"
```

---

## 4. 탐지: 데이터 유출

### 4.1 대량 파일 접근

```bash
# 대량 파일 읽기 패턴 (auditd가 있는 경우)
sshpass -p1 ssh user@192.168.208.142 "cat /var/log/audit/audit.log 2>/dev/null | \
  grep 'type=SYSCALL' | grep 'success=yes' | grep -E 'open|read' | tail -10"

# 대용량 파일 복사/전송 흔적
sshpass -p1 ssh user@192.168.208.142 "grep -E 'scp|rsync|curl.*upload|wget' /var/log/auth.log 2>/dev/null"
```

### 4.2 외부 전송 탐지

```bash
# 대량 외부 데이터 전송
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 외부 연결 ==="
  sshpass -p1 ssh user@$ip "ss -tnp state established 2>/dev/null | \
    grep -v '192.168.208\|10.20.30\|127.0.0' | head -5"
done

# Suricata에서 대량 데이터 전송 탐지
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'flow':
            f = e.get('flow',{})
            bytes_out = f.get('bytes_toserver',0)
            if bytes_out > 1000000:  # 1MB 이상 전송
                print(f'  {e.get(\"timestamp\",\"\")} {e.get(\"src_ip\",\"\")} -> {e.get(\"dest_ip\",\"\")} : {bytes_out} bytes')
    except: pass
\" 2>/dev/null | tail -10"
```

### 4.3 USB/이동매체 사용 탐지

```bash
# USB 장치 연결 로그
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: USB ==="
  sshpass -p1 ssh user@$ip "dmesg | grep -i 'usb.*storage\|usb.*mass' 2>/dev/null | tail -3"
  sshpass -p1 ssh user@$ip "journalctl -k | grep -i 'usb' 2>/dev/null | tail -3"
done
```

---

## 5. 사용자 행위 분석 (UBA)

### 5.1 사용자별 활동 프로파일

```bash
# 각 사용자의 활동 통계
sshpass -p1 ssh user@192.168.208.142 "
echo '=== 사용자별 로그인 횟수 ==='
grep 'session opened' /var/log/auth.log 2>/dev/null | \
  awk '{for(i=1;i<=NF;i++) if(\$i==\"for\" && \$(i+1)==\"user\") print \$(i+2)}' | \
  sort | uniq -c | sort -rn

echo ''
echo '=== 사용자별 sudo 횟수 ==='
grep 'COMMAND=' /var/log/auth.log 2>/dev/null | \
  awk '{for(i=1;i<=NF;i++) if(\$i ~ /^user=/) print \$i}' | \
  sort | uniq -c | sort -rn

echo ''
echo '=== 사용자별 SSH 실패 ==='
grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{for(i=1;i<=NF;i++) if(\$i==\"for\") {if(\$(i+1)==\"invalid\") print \$(i+3); else print \$(i+1)}}' | \
  sort | uniq -c | sort -rn | head -5
"
```

### 5.2 비정상 행위 지표

| 지표 | 설명 | 탐지 방법 |
|------|------|----------|
| 접근 시간 이상 | 업무 외 시간 접근 | 시간대별 로그인 분석 |
| 접근 빈도 이상 | 평소보다 많은 접근 | 일별 로그인 통계 비교 |
| 접근 대상 이상 | 업무와 무관한 서버 접근 | 서버별 접근 패턴 |
| 데이터 양 이상 | 대량 다운로드/복사 | 네트워크 트래픽 분석 |
| 권한 행사 이상 | 불필요한 sudo 사용 | sudo 로그 분석 |

---

## 6. 대응 절차

### 6.1 내부자 위협 대응의 특수성

| 외부 위협 대응 | 내부자 위협 대응 |
|---------------|----------------|
| 즉시 차단 가능 | 법적/HR 절차 필요 |
| 기술적 격리 | 사회적 고려 필요 |
| 증거 수집 간단 | 프라이버시 이슈 |
| IP 차단 | 계정 관리 (즉시 잠금이 어려울 수 있음) |

### 6.2 대응 단계

```
1. 탐지 → 의심 행위 식별
2. 비밀 조사 → 증거 수집 (당사자 모르게)
3. HR/법무 협의 → 법적 절차 확인
4. 증거 보존 → 포렌식 이미지 생성
5. 대응 조치 → 계정 잠금, 접근 차단
6. 조사 완료 → 징계/법적 조치
7. 재발 방지 → 정책 강화
```

### 6.3 실습: 증거 보존

```bash
# 내부자 조사 시 증거 수집
echo "=== 증거 수집 (의심 사용자: user) ==="

TARGET_USER="user"
IP="192.168.208.142"

echo "[1] 로그인 이력"
sshpass -p1 ssh user@$IP "last $TARGET_USER 2>/dev/null | head -20"

echo ""
echo "[2] sudo 이력"
sshpass -p1 ssh user@$IP "grep '$TARGET_USER' /var/log/auth.log 2>/dev/null | grep COMMAND | tail -20"

echo ""
echo "[3] 파일 접근 이력 (최근 수정)"
sshpass -p1 ssh user@$IP "find /home/$TARGET_USER -type f -mtime -7 2>/dev/null | head -20"

echo ""
echo "[4] 네트워크 활동"
sshpass -p1 ssh user@$IP "ss -tnp 2>/dev/null | grep -v '127.0.0'"

echo ""
echo "[5] 프로세스"
sshpass -p1 ssh user@$IP "ps -u $TARGET_USER -o pid,start,etime,args 2>/dev/null"
```

---

## 7. ATT&CK 매핑

| 내부자 행위 | 전술 | 기법 |
|------------|------|------|
| 비인가 데이터 접근 | TA0009 Collection | T1005 Data from Local System |
| sudo 권한 남용 | TA0004 Privilege Escalation | T1548 Abuse Elevation Control |
| 계정 정보 열람 | TA0006 Credential Access | T1003 OS Credential Dumping |
| USB로 데이터 복사 | TA0010 Exfiltration | T1052 Exfiltration Over Physical Medium |
| 네트워크로 전송 | TA0010 Exfiltration | T1048 Exfiltration Over Alternative Protocol |
| 로그 삭제 | TA0005 Defense Evasion | T1070 Indicator Removal |
| 백도어 계정 생성 | TA0003 Persistence | T1136 Create Account |

---

## 8. 예방 대책

### 8.1 기술적 대책

```bash
# 1. 최소 권한 원칙 확인
echo "=== sudo 권한 사용자 ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "$ip: $(sshpass -p1 ssh user@$ip 'getent group sudo 2>/dev/null')"
done

# 2. 세션 타임아웃 설정 확인
echo "=== TMOUT 설정 ==="
sshpass -p1 ssh user@192.168.208.142 "grep TMOUT /etc/profile /etc/bash.bashrc 2>/dev/null || echo '미설정'"

# 3. 로그 중앙 수집 확인
echo "=== Wazuh Agent ==="
for ip in 192.168.208.142 192.168.208.150 192.168.208.151; do
  echo -n "$ip: "
  sshpass -p1 ssh user@$ip "systemctl is-active wazuh-agent 2>/dev/null || echo 'N/A'"
done
```

### 8.2 관리적 대책

| 대책 | 내용 |
|------|------|
| 접근 권한 정기 검토 | 분기별 권한 리뷰 |
| 직무 분리 | 중요 작업은 2인 승인 |
| 퇴직 절차 | 퇴직 당일 계정 즉시 비활성화 |
| 보안 교육 | 내부자 위협 인식 교육 |
| 감사 로그 | auditd로 상세 행위 기록 |

---

## 9. 핵심 정리

1. **내부자 위협** = 악의적/부주의/침해된 내부자 3유형
2. **탐지 어려움** = 정상 행위와 구분이 어려움, FP 높음
3. **sudo 분석** = 위험 명령, 비인가 시도, 사용 패턴
4. **데이터 유출** = 네트워크 전송, USB, 대량 파일 접근
5. **법적 절차** = HR/법무 협의 후 조치 (기술 대응만으로 부족)

---

## 과제

1. 4개 서버에서 sudo 사용 이력을 분석하고 위험 명령을 보고하시오
2. 야간 시간대(22:00~06:00) 로그인을 탐지하시오
3. 내부자 위협 탐지를 위한 SIGMA 규칙을 1개 작성하시오

---

## 참고 자료

- CERT Insider Threat Guide (Carnegie Mellon)
- MITRE ATT&CK for Enterprise: Insider Threat
- SANS Insider Threat Detection Techniques
