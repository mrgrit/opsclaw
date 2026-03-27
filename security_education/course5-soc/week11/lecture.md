# Week 11: 인시던트 대응 (2) - 악성코드

## 학습 목표

- 의심 파일과 프로세스를 식별하는 방법을 익힌다
- 프로세스 조사 및 네트워크 활동 분석을 수행한다
- 악성코드 인시던트의 격리/근절/복구 절차를 실습한다
- 파일 해시를 활용한 IOC(Indicator of Compromise) 확인 방법을 이해한다

---

## 1. 악성코드 인시던트 개요

### 1.1 악성코드 유형

| 유형 | 설명 | 주요 영향 |
|------|------|----------|
| 랜섬웨어 | 파일 암호화 후 몸값 요구 | 가용성 |
| 트로이목마 | 정상 프로그램 위장, 백도어 | 기밀성 |
| 웜 | 네트워크 전파 | 가용성, 무결성 |
| 크립토마이너 | 암호화폐 채굴 | 성능 저하 |
| 웹셸 | 웹 서버에 설치된 원격 제어 | 기밀성, 무결성 |
| 루트킷 | 시스템 수준 은폐 | 탐지 회피 |

### 1.2 감염 경로

```
피싱 이메일 → 악성 첨부파일/링크 → 다운로드 → 실행
취약한 서비스 → 원격 코드 실행 → 페이로드 설치
공급망 공격 → 정상 업데이트에 악성코드 삽입
```

---

## 2. 탐지: 의심 프로세스 조사

### 2.1 프로세스 목록 분석

```bash
# 전체 프로세스 목록 (CPU 사용량 순)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "========== $ip =========="
  sshpass -p1 ssh user@$ip "ps aux --sort=-%cpu | head -15"
done
```

### 2.2 의심 프로세스 식별 기준

| 의심 기준 | 확인 방법 |
|-----------|----------|
| 이름이 이상함 | 랜덤 문자열, 시스템 프로세스 위장 |
| CPU/메모리 과다 | top, ps aux --sort=-%cpu |
| 비정상 경로에서 실행 | /tmp, /dev/shm, /var/tmp에서 실행 |
| 네트워크 연결 | 외부 IP로 지속적 연결 |
| 실행 시간이 이상 | 서버 시작 전부터 실행 중 |

```bash
# 의심 경로에서 실행되는 프로세스
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 의심 경로 프로세스 ==="
  sshpass -p1 ssh user@$ip "ls -la /proc/*/exe 2>/dev/null | grep -E '/tmp/|/dev/shm/|/var/tmp/' | head -5"
done

# /tmp에서 실행 가능 파일
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "find /tmp /dev/shm /var/tmp -type f -executable 2>/dev/null"
done
```

### 2.3 프로세스 상세 조사

```bash
# 특정 프로세스 상세 정보 (PID를 알고 있을 때)
# PID=12345  # 의심 PID로 변경
sshpass -p1 ssh user@192.168.208.142 "
  # 프로세스 정보
  echo '=== 프로세스 정보 ==='
  ps -p \$(pgrep -n python3 2>/dev/null || echo 1) -o pid,ppid,user,%cpu,%mem,start,args 2>/dev/null | head -5

  # 열린 파일
  echo '=== 열린 파일 ==='
  lsof -p \$(pgrep -n python3 2>/dev/null || echo 1) 2>/dev/null | head -10

  # 네트워크 연결
  echo '=== 네트워크 연결 ==='
  ss -tnp 2>/dev/null | head -10
"
```

---

## 3. 탐지: 의심 파일 조사

### 3.1 최근 생성/변경된 파일

```bash
# 최근 24시간 내 생성된 실행 파일
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 최근 생성 파일 ==="
  sshpass -p1 ssh user@$ip "find / -type f -mtime -1 \( -perm -100 -o -name '*.sh' -o -name '*.py' -o -name '*.pl' \) 2>/dev/null | grep -v '/proc\|/sys\|/run' | head -10"
done

# /etc 아래 변경된 파일
sshpass -p1 ssh user@192.168.208.142 "find /etc -type f -mtime -1 2>/dev/null | head -10"
```

### 3.2 파일 해시 확인

```bash
# 의심 파일의 해시 생성
sshpass -p1 ssh user@192.168.208.142 "
  echo '=== /tmp 내 파일 해시 ==='
  find /tmp -type f -maxdepth 2 2>/dev/null | while read f; do
    sha256sum \"\$f\" 2>/dev/null
  done | head -10
"
```

### 3.3 IOC 확인

파일 해시를 VirusTotal 등에서 조회하여 악성 여부를 확인한다:

```bash
# 해시를 VirusTotal API로 조회 (API 키 필요)
# curl -s "https://www.virustotal.com/api/v3/files/{hash}" -H "x-apikey: {key}"

# OpenCTI에서 IOC 검색 (실습 환경)
# 브라우저: http://192.168.208.152:9400
echo "OpenCTI 접속: http://192.168.208.152:9400"
echo "IOC 검색: 해시값 또는 IP 주소로 검색"
```

---

## 4. 탐지: 네트워크 활동 분석

### 4.1 외부 연결 확인

```bash
# ESTABLISHED 연결 (외부 통신)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: 외부 연결 ==="
  sshpass -p1 ssh user@$ip "ss -tnp state established 2>/dev/null | grep -v '192.168.208\|10.20.30\|127.0.0' | head -10"
done
```

### 4.2 비정상 리스닝 포트

```bash
# 알려지지 않은 리스닝 포트
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "ss -tlnp | grep LISTEN"
done
```

### 4.3 DNS 쿼리 분석

```bash
# DNS 트래픽 확인 (비정상 DNS = C2 가능)
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/eve.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
domains = Counter()
for line in sys.stdin:
    try:
        e = json.loads(line)
        if e.get('event_type') == 'dns':
            d = e.get('dns',{}).get('rrname','')
            if d: domains[d] += 1
    except: pass
print('=== Top 10 DNS 쿼리 ===')
for d, c in domains.most_common(10):
    print(f'  {c:4d}: {d}')
\" 2>/dev/null"
```

---

## 5. Wazuh에서의 악성코드 탐지

### 5.1 파일 무결성 모니터링 (FIM) 알림

```bash
# 파일 변경 탐지 알림
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        groups = str(r.get('groups',[]))
        if 'syscheck' in groups or 'integrity' in groups:
            print(f'  {a.get(\"timestamp\",\"\")} [{r.get(\"level\",0)}] {r.get(\"description\",\"\")}')
            syscheck = a.get('syscheck',{})
            if syscheck.get('path'):
                print(f'    파일: {syscheck[\"path\"]}')
    except: pass
\" 2>/dev/null | tail -20"
```

### 5.2 rootcheck 결과

```bash
# rootkit/malware 탐지 결과
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if 'rootcheck' in str(r.get('groups',[])) or 'rootkit' in str(r.get('description','')).lower():
            print(f'  [{r.get(\"level\",0)}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -10"
```

---

## 6. 격리 및 근절

### 6.1 프로세스 종료

```bash
# 의심 프로세스 종료 (시연)
echo "=== 프로세스 종료 명령 (시연) ==="
echo "kill -9 <PID>        # 특정 프로세스 종료"
echo "pkill -f '<pattern>' # 패턴으로 종료"
echo "주의: 정상 프로세스를 종료하지 않도록 반드시 확인 후 실행"
```

### 6.2 악성 파일 제거

```bash
# 격리 (삭제 전 보존)
echo "=== 악성 파일 격리 절차 ==="
echo "1. mkdir -p /tmp/quarantine"
echo "2. cp suspicious_file /tmp/quarantine/"
echo "3. sha256sum /tmp/quarantine/suspicious_file > /tmp/quarantine/hash.txt"
echo "4. rm suspicious_file"
```

### 6.3 지속성 메커니즘 제거

```bash
# cron 작업 확인 (백도어 가능)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: cron ==="
  sshpass -p1 ssh user@$ip "crontab -l 2>/dev/null; ls -la /etc/cron.d/ /etc/cron.daily/ 2>/dev/null | head -5"
done

# systemd 서비스 확인 (의심 서비스)
sshpass -p1 ssh user@192.168.208.142 "systemctl list-unit-files --type=service | grep enabled | grep -v 'system\|network\|ssh\|cron\|rsyslog\|wazuh'"

# authorized_keys 확인 (SSH 백도어)
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "cat /home/*/.ssh/authorized_keys /root/.ssh/authorized_keys 2>/dev/null || echo '없음'"
done

# .bashrc 등 쉘 시작 파일 확인
sshpass -p1 ssh user@192.168.208.142 "tail -5 /home/*/.bashrc /root/.bashrc 2>/dev/null"
```

---

## 7. ATT&CK 매핑

| 관찰 내용 | 전술 | 기법 |
|-----------|------|------|
| 악성 파일 다운로드 | TA0002 Execution | T1059 Command Interpreter |
| /tmp에서 실행 | TA0005 Defense Evasion | T1036 Masquerading |
| cron 등록 | TA0003 Persistence | T1053 Scheduled Task |
| 외부 IP 연결 | TA0011 C2 | T1071 Application Layer Protocol |
| SSH 키 추가 | TA0003 Persistence | T1098 Account Manipulation |
| 로그 삭제 | TA0005 Defense Evasion | T1070 Indicator Removal |

---

## 8. 종합 점검 스크립트

```bash
#!/bin/bash
echo "============================================"
echo " 악성코드 인시던트 조사 - $(date)"
echo "============================================"

IP=$1
if [ -z "$IP" ]; then echo "Usage: $0 <IP>"; exit 1; fi

echo "[1] 의심 프로세스 (CPU Top 5)"
sshpass -p1 ssh user@$IP "ps aux --sort=-%cpu | head -6"

echo ""
echo "[2] /tmp 실행 파일"
sshpass -p1 ssh user@$IP "find /tmp /dev/shm /var/tmp -type f -executable 2>/dev/null"

echo ""
echo "[3] 외부 네트워크 연결"
sshpass -p1 ssh user@$IP "ss -tnp state established 2>/dev/null | grep -v '192.168\|10.20\|127.0'"

echo ""
echo "[4] 비정상 리스닝 포트"
sshpass -p1 ssh user@$IP "ss -tlnp 2>/dev/null | grep LISTEN"

echo ""
echo "[5] 최근 변경 파일 (24h)"
sshpass -p1 ssh user@$IP "find /etc /usr/local -type f -mtime -1 2>/dev/null | head -10"

echo ""
echo "[6] cron 작업"
sshpass -p1 ssh user@$IP "crontab -l 2>/dev/null; cat /etc/crontab 2>/dev/null | grep -v '^#' | grep -v '^$'"

echo ""
echo "[7] SSH authorized_keys"
sshpass -p1 ssh user@$IP "cat ~/.ssh/authorized_keys 2>/dev/null || echo '없음'"
```

---

## 9. 핵심 정리

1. **프로세스 조사** = CPU/메모리, 실행 경로, 네트워크 연결
2. **파일 조사** = 최근 변경 파일, 해시, IOC 확인
3. **네트워크 조사** = 외부 연결, 비정상 포트, DNS 분석
4. **지속성 제거** = cron, systemd, SSH 키, 쉘 시작 파일
5. **증거 보존** = 삭제 전 복사 + 해시 기록

---

## 과제

1. 4개 서버에서 의심 프로세스/파일/네트워크 활동을 조사하시오
2. 발견한 이상 징후를 ATT&CK 기법에 매핑하시오
3. 악성코드 인시던트 대응 보고서를 작성하시오

---

## 참고 자료

- SANS Malware Analysis Cheat Sheet
- Linux Forensics for Incident Responders
- VirusTotal (https://www.virustotal.com)
