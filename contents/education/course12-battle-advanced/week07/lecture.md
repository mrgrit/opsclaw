# Week 07: 포렌식 기반 방어 -- 메모리 분석, 디스크 분석, 타임라인

## 학습 목표

- 디지털 포렌식의 기본 원칙, 증거 유형, Chain of Custody, 법적 요건을 체계적으로 이해한다
- Volatility 3를 설치하고 pslist/pstree/netscan/malfind/dlllist 플러그인으로 악성 프로세스를 식별한다
- dd 기반 디스크 이미지 생성, strings/grep 분석, 삭제 파일 복구, 파일시스템 타임라인 분석을 수행한다
- log2timeline/plaso로 다중 소스 통합 타임라인을 구성하고 포렌식 보고서를 작성한다
- 포렌식 결과를 기반으로 실질적인 방어 규칙을 개선할 수 있다

## 선수 지식

- 공방전 기초 과정(course11) 이수 또는 동등 수준의 보안 지식
- 운영체제 핵심 개념: 프로세스 관리, 가상 메모리, 파일시스템 구조(inode, 저널링)
- Week 02-05에서 다룬 공격 기법(Persistence, Lateral Movement, C2) 이해
- Linux 명령행 기본 조작 능력 (find, grep, awk, sort, pipe)
- 네트워크 기초 (TCP/UDP 소켓, 포트, DNS)

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 포렌식 분석 워크스테이션 | `ssh opsclaw@10.20.30.201` |
| web | 10.20.30.80 | 침해 시스템 (분석 대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | 로그 상관 분석 (Wazuh) | `sshpass -p1 ssh siem@10.20.30.100` |

> **중요**: 모든 포렌식 분석은 opsclaw 워크스테이션에서 수행한다. 침해 시스템(web)에는 증거 수집 목적으로만 최소 접근하며, 분석 작업은 절대 침해 시스템에서 직접 실행하지 않는다.

## 강의 시간 배분 (4시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:50 | Part 1: 디지털 포렌식 이론 | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:50 | Part 2: 메모리 분석 (Volatility 3) | 실습 |
| 1:50-2:00 | 휴식 | - |
| 2:00-2:50 | Part 3: 디스크 분석 | 실습 |
| 2:50-3:00 | 휴식 | - |
| 3:00-3:50 | Part 4: 타임라인 구성 + 보고서 | 실습 + 토론 |
| 3:50-4:00 | 퀴즈 + 과제 안내 | 정리 |

---

# Part 1: 디지털 포렌식 이론 (50분)

## 1.1 디지털 포렌식의 정의와 목적

디지털 포렌식(Digital Forensics)은 컴퓨터 시스템, 네트워크, 저장매체에서 법적으로 유효한 디지털 증거를 수집, 보존, 분석, 보고하는 체계적 과정이다. 단순히 "해킹당했다"는 사실을 확인하는 것을 넘어, 공격의 전체 경로를 재구성하고, 피해 범위를 산정하며, 재발 방지 대책을 수립하는 데 핵심 역할을 한다.

### 포렌식의 4대 목적

| 목적 | 설명 | 예시 |
|------|------|------|
| **사고 대응** | 침해 사고의 원인과 범위를 신속하게 파악 | APT 그룹의 초기 침투 경로 식별 |
| **법적 증거 확보** | 법정에서 인정받을 수 있는 증거를 체계적으로 수집 | 내부자 데이터 유출 소송에서 증거 제출 |
| **피해 산정** | 유출된 데이터의 종류와 양, 영향 범위를 정량화 | 개인정보 유출 건수 확인, 규제 기관 보고 |
| **방어 개선** | 공격 기법을 분석하여 탐지 규칙과 방어 체계를 강화 | 발견된 C2 패턴으로 IDS 시그니처 추가 |

### 포렌식 분석의 기본 원칙 5가지

```
1. 증거 보전 (Preservation)
   - 원본 데이터를 절대 변경하지 않는다
   - 분석은 반드시 사본(이미지)에 대해 수행한다
   - Write Blocker 또는 읽기 전용 마운트를 사용한다

2. 무결성 입증 (Integrity)
   - 증거 수집 직후 암호학적 해시(SHA-256)를 생성한다
   - 분석 전후 해시를 비교하여 변조 여부를 확인한다
   - 해시 체인을 기록하여 증거의 연속성을 보장한다

3. Chain of Custody (증거 관리 연쇄)
   - 증거가 누구 손에, 언제, 어떤 상태로 있었는지 빈틈 없이 기록한다
   - 수집자, 운송자, 보관자, 분석자 전원의 서명을 받는다
   - 한 번이라도 끊기면 법적 증거 능력을 상실한다

4. 재현 가능성 (Reproducibility)
   - 동일한 증거에 동일한 절차를 적용하면 동일한 결과가 나와야 한다
   - 분석 도구의 버전, 설정, 명령어를 모두 기록한다
   - 제3자가 검증할 수 있어야 한다

5. 최소 침습 (Minimal Footprint)
   - 증거 수집 과정에서 시스템에 미치는 영향을 최소화한다
   - 라이브 수집 시 사용하는 도구는 외부 매체에서 실행한다
   - 수집 도구 자체가 남기는 아티팩트도 문서화한다
```

## 1.2 증거 유형과 휘발성 순서

디지털 증거는 휘발성(Volatility)에 따라 수집 우선순위가 결정된다. RFC 3227 "Guidelines for Evidence Collection and Archiving"은 다음과 같은 휘발성 순서를 제시한다.

### 휘발성 순서 (Order of Volatility)

```
가장 휘발적 (즉시 수집)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1단계: CPU 레지스터, 캐시
   └─ 수명: 나노초~밀리초
   └─ 수집 방법: 거의 불가능 (실무에서 생략)

2단계: 메모리 (RAM)
   └─ 수명: 전원 차단 시 수초~수분 내 소실
   └─ 수집 방법: LiME, DumpIt, WinPmem
   └─ 포함 정보: 실행 중인 프로세스, 네트워크 연결,
                  암호화 키, 복호화된 데이터, 악성코드

3단계: 네트워크 상태
   └─ 수명: 연결 종료 시 소멸
   └─ 수집 방법: netstat, ss, conntrack, tcpdump
   └─ 포함 정보: 활성 연결, 라우팅 테이블, ARP 캐시

4단계: 실행 중인 프로세스
   └─ 수명: 프로세스 종료 시 소멸
   └─ 수집 방법: ps, /proc 파일시스템
   └─ 포함 정보: PID, 명령행, 환경변수, 열린 파일

5단계: 디스크 (비휘발성)
   └─ 수명: 덮어쓰기 전까지 유지
   └─ 수집 방법: dd, dcfldd, FTK Imager
   └─ 포함 정보: 파일시스템, 삭제 파일, 로그, 설정

6단계: 원격 로그/백업
   └─ 수명: 보존 정책에 따라 수개월~수년
   └─ 수집 방법: syslog, SIEM 쿼리, 백업 복원
   └─ 포함 정보: 집중형 로그, 백업 스냅샷
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
가장 영구적 (나중에 수집 가능)
```

> **실무 핵심**: 사고 대응 시 가장 먼저 메모리를 덤프하고, 그 다음 네트워크 상태를 기록하고, 마지막에 디스크 이미지를 생성한다. 순서를 잘못 잡으면 핵심 증거가 소실된다.

### 라이브 포렌식 vs 데드 포렌식

| 구분 | 라이브 포렌식 (Live) | 데드 포렌식 (Dead/Post-mortem) |
|------|---------------------|-------------------------------|
| **시점** | 시스템 전원이 켜진 상태 | 시스템 전원을 끈 후 |
| **대상** | 메모리, 네트워크, 프로세스 | 디스크, 저장매체 |
| **장점** | 휘발성 데이터 수집 가능 | 증거 변조 위험 최소화 |
| **단점** | 수집 과정에서 증거 변조 가능성 | 메모리 데이터 소실 |
| **우선순위** | 항상 먼저 수행 | 라이브 수집 완료 후 수행 |
| **도구** | LiME, Volatility, tcpdump | dd, Autopsy, Sleuth Kit |

## 1.3 Chain of Custody (증거 관리 연쇄)

Chain of Custody는 디지털 증거가 수집된 순간부터 법정에 제출될 때까지의 전체 이동 경로를 문서화하는 절차이다.

### Chain of Custody 기록 항목

```
┌─────────────────────────────────────────────────┐
│           증거 관리 기록서 (Evidence Log)          │
├─────────────────────────────────────────────────┤
│ 사건 번호: INC-2026-0401-001                      │
│ 증거 번호: EVD-001 (메모리 덤프)                   │
│ 증거 설명: web 서버(10.20.30.80) RAM 8GB 덤프     │
│                                                   │
│ [수집 정보]                                        │
│ 수집 일시: 2026-04-01 14:23:00 KST                │
│ 수집자: 김보안 (보안팀)                             │
│ 수집 도구: LiME v1.9.1                            │
│ 수집 방법: insmod lime.ko (USB에서 실행)           │
│ 원본 해시 (SHA-256):                              │
│   a3f2e1d4c5b6...89012345                         │
│                                                   │
│ [이동 기록]                                        │
│ 14:30 김보안 → SCP → 분석 워크스테이션              │
│ 14:35 수신 해시 검증: 일치                          │
│ 15:00 김보안 → 이포렌 (분석 담당자 교대)            │
│ 서명: _________ / _________                       │
│                                                   │
│ [보관 정보]                                        │
│ 보관 위치: 포렌식 랩 금고 #3                        │
│ 접근 권한: 김보안, 이포렌, 박관리                    │
│ 암호화: AES-256 (키는 별도 보관)                    │
└─────────────────────────────────────────────────┘
```

### Chain of Custody 단절 사례와 결과

| 단절 사례 | 법적 결과 | 예방 방법 |
|----------|----------|----------|
| 증거 USB를 잠금 없는 서랍에 보관 | 증거 능력 상실 가능 | 잠금 장치가 있는 금고 사용 |
| 해시값 기록 누락 | 무결성 입증 불가 | 수집 즉시 해시 생성 + 서명 |
| 이동 기록 없이 분석자에게 전달 | 변조 의심 여지 발생 | 이동 시마다 서명 + 시간 기록 |
| 원본 디스크에서 직접 분석 | 원본 변조 주장 가능 | 반드시 사본에서 분석 |

## 1.4 법적 요건

### 한국 법률 체계에서의 디지털 증거

```
관련 법률:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 형사소송법 제313조 (디지털 증거의 증거능력)
   - 원본 동일성 입증 필수 (해시값)
   - 전문 증거 배제 법칙 적용
   - 작성자 또는 진술자의 인정 필요

2. 정보통신망법 제48조 (침해사고 신고의무)
   - KISA 또는 관련 기관에 신고
   - 증거 보전 의무
   - 신고 기한: 인지 후 24시간 이내

3. 개인정보보호법 제34조 (유출 통지)
   - 정보주체에 72시간 이내 통지
   - 유출 항목, 시점, 대응 조치 포함
   - 1,000명 이상 시 PIPC 신고 의무

4. 전자금융거래법 제21조의3
   - 금융 분야 침해사고 금융감독원 보고
   - 포렌식 조사 보고서 제출 의무

실무 체크포인트:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ 증거 수집 시 해시값 생성 + 기록
□ Chain of Custody 기록서 작성
□ 분석 도구 버전 + 명령어 전체 기록
□ 분석 결과 보고서에 재현 절차 포함
□ 증거 보관 시 암호화 + 접근 통제
□ 관련 기관 신고 기한 준수
```

## 1.5 포렌식 도구 분류

### 목적별 도구 분류표

| 분류 | 도구 | 용도 | 라이선스 |
|------|------|------|---------|
| **메모리 수집** | LiME | Linux 메모리 덤프 (커널 모듈) | GPL |
| | WinPmem | Windows 메모리 덤프 | Apache 2.0 |
| | DumpIt | Windows 메모리 원클릭 덤프 | 무료 |
| **메모리 분석** | Volatility 3 | 크로스 플랫폼 메모리 분석 프레임워크 | GPL |
| | Rekall | Google 개발 메모리 분석 (개발 중단) | GPL |
| **디스크 수집** | dd / dcfldd | 비트 단위 디스크 이미지 생성 | GPL |
| | FTK Imager | GUI 디스크 이미징 + 미리보기 | 무료 |
| | ewfacquire | E01(Expert Witness) 포맷 이미징 | LGPL |
| **디스크 분석** | Sleuth Kit (TSK) | CLI 기반 파일시스템 분석 도구 모음 | CPL/GPL |
| | Autopsy | TSK 기반 GUI 포렌식 플랫폼 | Apache 2.0 |
| | extundelete | ext3/ext4 삭제 파일 복구 | GPL |
| | photorec | 시그니처 기반 파일 복구 (carving) | GPL |
| **타임라인** | log2timeline/plaso | 다중 소스 통합 타임라인 생성 | Apache 2.0 |
| | mactime (TSK) | MACtime 기반 타임라인 생성 | CPL |
| **네트워크** | Wireshark/tshark | 패킷 캡처 및 분석 | GPL |
| | NetworkMiner | 네트워크 포렌식 (파일 추출) | GPL |
| **통합 플랫폼** | SIFT Workstation | SANS 포렌식 배포판 (Ubuntu 기반) | 무료 |
| | CAINE | 이탈리아 포렌식 배포판 | GPL |

### ATT&CK 기법과 포렌식 아티팩트 매핑

| MITRE ATT&CK 기법 | 포렌식 아티팩트 위치 | 분석 도구 | 메모리에서 탐지 |
|-------------------|---------------------|----------|---------------|
| T1053.003 (Cron Job) | /var/spool/cron/, /etc/cron.d/ | strings, cat, fls | pstree에서 cron 자식 프로세스 |
| T1543.002 (Systemd Service) | /etc/systemd/system/, /run/systemd/ | find, stat, strings | pslist에서 systemctl 실행 |
| T1059.004 (Unix Shell) | ~/.bash_history, /var/log/auth.log | cat, grep, timeline | linux.bash 플러그인 |
| T1071.001 (Web C2) | 네트워크 소켓, 프록시 로그 | netscan, tshark | sockstat에서 외부 연결 |
| T1003.008 (/etc/shadow) | /etc/shadow, 메모리 내 해시 | strings, malfind | 메모리에서 해시 문자열 검색 |
| T1070.004 (File Deletion) | 삭제된 inode, 저널 | extundelete, fls | 프로세스가 삭제 파일 핸들 보유 |
| T1027 (Obfuscated Files) | 인코딩된 페이로드 | strings, base64 -d | malfind에서 인젝션 코드 |
| T1105 (Ingress Tool Transfer) | /tmp, 웹 루트, 다운로드 경로 | find, stat, sha256sum | pslist에서 wget/curl 프로세스 |

---

# Part 2: 메모리 분석 -- Volatility 3 (50분)

## 2.1 Volatility 3 설치

### 실습 2.1: Volatility 3 설치 및 환경 구성

**실습 목적**: Volatility 3 프레임워크를 설치하고, Linux 메모리 분석에 필요한 심볼 테이블을 준비한다.

**배우는 것**: Python 가상환경 기반 포렌식 도구 설치, ISF(Intermediate Symbol Format) 심볼 테이블 개념

```bash
# ─── Volatility 3 설치 (opsclaw 워크스테이션) ───

# 1. 포렌식 작업 디렉토리 생성
mkdir -p /home/opsclaw/forensics/{evidence,symbols,output,reports}
cd /home/opsclaw/forensics

# 2. Python 가상환경 생성 (분석 도구 격리)
python3.11 -m venv /home/opsclaw/forensics/venv-forensics
source /home/opsclaw/forensics/venv-forensics/bin/activate

# 3. Volatility 3 설치
pip install volatility3

# 4. 설치 확인
vol --help 2>&1 | head -5
# 출력 예시:
# Volatility 3 Framework 2.x.x
# usage: volatility [-h] [-c CONFIG] ...

# 5. 사용 가능한 플러그인 목록 확인 (Linux 관련)
vol --help 2>&1 | grep "linux\."
# linux.bash, linux.check_afinfo, linux.check_creds, linux.elfs,
# linux.envars, linux.iomem, linux.keyboard_notifiers,
# linux.lsmod, linux.lsof, linux.malfind, linux.proc.maps,
# linux.pslist, linux.pstree, linux.sockstat, ...

# 6. Linux 심볼 테이블 준비
# Volatility 3는 커널 심볼 테이블(ISF)이 필요하다
# 방법 A: 자동 다운로드 (인터넷 연결 시)
vol -f /tmp/test.raw linux.pslist
# → 자동으로 심볼 테이블 다운로드 시도

# 방법 B: 수동 생성 (대상 시스템의 커널 정보 필요)
# 대상 시스템에서 커널 버전 확인
ssh web@10.20.30.80 'uname -r'
# 예: 6.8.0-106-generic

# dwarf2json으로 심볼 테이블 생성
# (사전에 dwarf2json이 설치되어 있다고 가정)
# dwarf2json linux \
#   --elf /usr/lib/debug/boot/vmlinux-$(uname -r) \
#   > /home/opsclaw/forensics/symbols/linux-$(uname -r).json

# 심볼 테이블을 Volatility 검색 경로에 배치
# ls /home/opsclaw/forensics/symbols/
```

**결과 해석**:
- `vol --help`에서 `linux.*` 플러그인 목록이 출력되면 설치 성공
- ISF 심볼 테이블이 없으면 대부분의 플러그인이 "Unsatisfied requirement" 오류를 발생시킨다
- 심볼 테이블은 분석 대상 시스템의 정확한 커널 버전과 일치해야 한다

**실전 활용**: 사고 대응 키트(IR Kit)에 주요 배포판/커널 버전의 심볼 테이블을 미리 준비해 두면 긴급 상황에서 시간을 절약할 수 있다.

**트러블슈팅**:
- `pip install volatility3` 실패 시: `pip install --upgrade pip setuptools wheel` 후 재시도
- `vol` 명령이 없을 때: `python -m volatility3.cli` 로 대체 실행
- 심볼 테이블 오류: `--symbol-path` 옵션으로 심볼 디렉토리를 명시적으로 지정

## 2.2 메모리 덤프 수집

### 실습 2.2: LiME을 이용한 메모리 덤프 수집

**실습 목적**: 침해가 의심되는 시스템에서 메모리를 안전하게 수집하고, 무결성을 검증한다.

**배우는 것**: LiME 커널 모듈 사용법, 메모리 덤프 무결성 검증, 안전한 전송

```bash
# ─── 메모리 덤프 수집 (web 서버에서 실행) ───

# 1. 수집 전 시간 기록 (Chain of Custody 시작)
echo "=== Memory Acquisition Start ===" > /tmp/acquisition_log.txt
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> /tmp/acquisition_log.txt
echo "Analyst: $(whoami)" >> /tmp/acquisition_log.txt
echo "Target: $(hostname) / $(hostname -I)" >> /tmp/acquisition_log.txt
echo "Kernel: $(uname -r)" >> /tmp/acquisition_log.txt
echo "RAM: $(free -h | awk '/Mem:/{print $2}')" >> /tmp/acquisition_log.txt

# 2. LiME으로 메모리 덤프 (USB 또는 네트워크 공유에 저장)
# LiME이 이미 컴파일되어 있다고 가정
sudo insmod /opt/lime/lime-$(uname -r).ko \
  "path=/tmp/memdump.lime format=lime digest=sha256"

# 3. LiME이 없는 경우 대안: /proc/kcore (제한적)
# dd if=/proc/kcore of=/tmp/memdump.raw bs=1M count=2048
# 주의: /proc/kcore는 전체 물리 메모리를 포함하지 않을 수 있다

# 4. 또 다른 대안: AVML (Microsoft의 Linux 메모리 수집 도구)
# ./avml /tmp/memdump.raw
# AVML은 커널 모듈 없이 /proc/kcore + /dev/crash를 활용한다

# 5. 무결성 해시 생성
sha256sum /tmp/memdump.lime | tee /tmp/memdump.sha256
echo "SHA-256: $(cat /tmp/memdump.sha256)" >> /tmp/acquisition_log.txt

# 6. 수집 완료 기록
echo "Acquisition End: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> /tmp/acquisition_log.txt

# 7. 분석 워크스테이션으로 안전 전송
scp /tmp/memdump.lime opsclaw@10.20.30.201:/home/opsclaw/forensics/evidence/
scp /tmp/memdump.sha256 opsclaw@10.20.30.201:/home/opsclaw/forensics/evidence/
scp /tmp/acquisition_log.txt opsclaw@10.20.30.201:/home/opsclaw/forensics/evidence/

# ─── 무결성 검증 (opsclaw 워크스테이션에서 실행) ───

# 8. 전송 후 해시 검증
cd /home/opsclaw/forensics/evidence
sha256sum -c memdump.sha256
# 출력: memdump.lime: OK  → 무결성 확인
# 출력: memdump.lime: FAILED  → 전송 중 손상, 재수집 필요

# 9. 검증 결과 기록
echo "Verification: $(sha256sum -c memdump.sha256)" >> acquisition_log.txt
echo "Verified by: opsclaw" >> acquisition_log.txt
echo "Verification time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> acquisition_log.txt
```

**결과 해석**:
- `sha256sum -c`에서 "OK"가 출력되면 전송 중 변조 없음이 확인된다
- LiME의 `digest=sha256` 옵션은 수집 중 해시를 내장하여 이중 검증이 가능하다
- 메모리 덤프 크기는 시스템 RAM과 유사해야 한다 (8GB RAM -> 약 8GB 파일)

**명령어 해설**:
- `insmod lime.ko "path=... format=lime"`: LiME 커널 모듈을 로드하여 메모리 덤프 시작. `format=lime`은 LiME 전용 포맷, `format=raw`는 원시 포맷
- `sha256sum`: SHA-256 해시 생성. MD5는 충돌 취약성으로 법적 증거에 부적합
- `scp`: SSH 기반 보안 파일 전송. 네트워크 구간 암호화 보장

**트러블슈팅**:
- LiME 로드 실패 (`insmod: ERROR`): 커널 버전이 일치하지 않음. 대상 시스템에서 다시 컴파일 필요
- 디스크 공간 부족: 메모리 크기 이상의 여유 공간 필요. 원격 NFS/SMB 마운트 활용
- SSH 연결 문제: 포렌식 수집 전에 네트워크 연결을 미리 확인

## 2.3 Volatility 3 핵심 플러그인 분석

### 실습 2.3: pslist와 pstree -- 프로세스 분석

**실습 목적**: 메모리 덤프에서 실행 중이던 프로세스를 목록화하고, 부모-자식 관계를 분석하여 악성 프로세스를 식별한다.

**배우는 것**: 정상 프로세스와 비정상 프로세스의 구분법, 프로세스 은닉 기법 탐지

```bash
# ─── 프로세스 분석 (opsclaw 워크스테이션) ───
cd /home/opsclaw/forensics
source venv-forensics/bin/activate

EVIDENCE="/home/opsclaw/forensics/evidence/memdump.lime"
OUTPUT="/home/opsclaw/forensics/output"

# 1. pslist: 프로세스 목록 (커널 태스크 리스트 순회)
vol -f "$EVIDENCE" linux.pslist > "$OUTPUT/pslist.txt"
cat "$OUTPUT/pslist.txt"
# PID    PPID   COMM           UID    GID
# 1      0      systemd        0      0
# 2      0      kthreadd       0      0
# ...
# 1234   1      suspicious     0      0    ← 의심 프로세스

# 2. pstree: 프로세스 트리 (부모-자식 관계)
vol -f "$EVIDENCE" linux.pstree > "$OUTPUT/pstree.txt"
cat "$OUTPUT/pstree.txt"
# PID    PPID   COMM
# 1      0      systemd
# ├── 456  1    sshd
# │   └── 789  456  bash
# │       └── 1234  789  suspicious    ← ssh → bash → 악성코드
# ├── 234  1    apache2
# │   ├── 235  234  apache2
# │   └── 1337  234  sh              ← 웹쉘! apache 자식으로 sh

# 3. 의심 프로세스 상세 분석
# PPID가 비정상적인 프로세스 찾기
awk 'NR>1 && $2!=0 && $2!=1 && $2!=2' "$OUTPUT/pslist.txt"

# 4. 프로세스 이름이 정상 이름으로 위장한 경우 탐지
# 예: "kworker" 위장 (정상 커널 스레드 이름)
grep -E "kworker|kthread|migration" "$OUTPUT/pslist.txt" | \
  awk '$4 != 0 {print "WARNING: kernel thread name with non-root UID:", $0}'

# 5. pslist vs psscan 비교 (숨겨진 프로세스 탐지)
# pslist: 커널의 task_struct 연결 리스트를 따라감 → DKOM으로 숨긴 프로세스 못 봄
# psscan: 메모리 전체를 스캔하여 task_struct 패턴 검색 → 숨겨진 프로세스 탐지
vol -f "$EVIDENCE" linux.pslist > "$OUTPUT/pslist_pids.txt"
vol -f "$EVIDENCE" linux.pstree > "$OUTPUT/pstree_pids.txt"

# psscan이 더 많은 프로세스를 보여주면 → 프로세스 은닉 시도!
# 참고: Volatility 3의 linux.psscan은 버전에 따라 제공 여부가 다르다
```

**결과 해석**:
- apache2의 자식으로 `sh`나 `bash`가 있으면 웹쉘 실행을 강하게 의심
- PPID=1(systemd)인 프로세스 중 이름이 낯선 것은 독립 실행 악성코드 가능성
- UID=0(root)으로 실행 중인 비정상 프로세스는 권한 상승 성공을 의미
- pslist에 없지만 psscan에 있는 프로세스는 DKOM(Direct Kernel Object Manipulation) 은닉 기법 사용

**실전 활용**: 인시던트 대응 시 프로세스 트리를 가장 먼저 분석한다. 부모-자식 관계만으로도 공격 경로의 80%를 파악할 수 있다.

### 실습 2.4: netscan -- 네트워크 연결 분석

**실습 목적**: 메모리에서 네트워크 연결 정보를 추출하여 C2(Command & Control) 통신과 데이터 유출 채널을 식별한다.

**배우는 것**: C2 통신 패턴 식별, 비정상 포트 사용 탐지, 외부 연결 분석

```bash
# ─── 네트워크 분석 ───

# 1. 네트워크 소켓 정보 추출 (Linux)
vol -f "$EVIDENCE" linux.sockstat > "$OUTPUT/sockstat.txt"
cat "$OUTPUT/sockstat.txt"
# PID   COMM       Proto  LocalAddr       LocalPort  ForeignAddr     ForeignPort  State
# 456   sshd       TCP    0.0.0.0         22         0.0.0.0         0            LISTEN
# 789   bash       TCP    10.20.30.80     22         10.20.30.201    52341        ESTABLISHED
# 1234  suspicious TCP    10.20.30.80     443        203.0.113.50    4444         ESTABLISHED  ← C2!
# 1337  sh         TCP    10.20.30.80     80         198.51.100.10   54321        ESTABLISHED  ← 웹쉘

# 2. 외부 연결 필터링 (사설 IP 대역 제외)
grep "ESTABLISHED" "$OUTPUT/sockstat.txt" | \
  grep -v -E "10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\." | \
  grep -v "127\.0\.0\." > "$OUTPUT/external_connections.txt"
echo "=== 외부 연결 목록 ==="
cat "$OUTPUT/external_connections.txt"

# 3. 비정상 LISTEN 포트 탐지
grep "LISTEN" "$OUTPUT/sockstat.txt" | \
  grep -v -E ":(22|80|443|3306|5432|8080|8443)\b" > "$OUTPUT/unusual_ports.txt"
echo "=== 비정상 LISTEN 포트 ==="
cat "$OUTPUT/unusual_ports.txt"

# 4. 의심스러운 외부 IP에 대한 위협 인텔리전스 조회 준비
# 외부 IP 추출
awk '{print $7}' "$OUTPUT/external_connections.txt" | \
  sort -u | grep -v "0.0.0.0" > "$OUTPUT/suspicious_ips.txt"

echo "=== 위협 인텔리전스 조회 대상 IP ==="
cat "$OUTPUT/suspicious_ips.txt"
# 이 IP들을 VirusTotal, AbuseIPDB, OTX 등에서 조회

# 5. 특정 프로세스의 네트워크 활동 집중 분석
PID_SUSPICIOUS=1234
grep "$PID_SUSPICIOUS" "$OUTPUT/sockstat.txt"
```

**결과 해석**:
- ESTABLISHED 상태로 외부 IP에 연결된 비정상 프로세스는 C2 통신 강력 의심
- 고포트(4444, 5555, 8888 등)로의 아웃바운드 연결은 리버스 쉘 패턴
- 웹 서버 프로세스(apache2, nginx)가 아웃바운드 연결을 맺는 것은 비정상
- DNS(53번 포트)로의 대량 연결은 DNS 터널링 가능성

**명령어 해설**:
- `linux.sockstat`: 메모리의 소켓 구조체를 파싱하여 네트워크 연결 정보 추출. 라이브 시스템의 `ss -tlnp`와 유사하지만, 이미 종료된 연결도 일부 포착 가능
- `grep -v -E "10\.|172\...."`: RFC 1918 사설 IP 대역을 제외하여 외부 연결만 필터링

**트러블슈팅**:
- sockstat 결과가 비어 있을 때: 심볼 테이블 불일치 가능성. 커널 버전 재확인
- IPv6 연결이 보이지 않을 때: `linux.sockstat`의 IPv6 지원 여부는 Volatility 버전에 따라 다름

### 실습 2.5: malfind -- 악성 코드 인젝션 탐지

**실습 목적**: 프로세스 메모리에서 코드 인젝션(injection)의 흔적을 탐지하고, 인젝션된 코드를 추출한다.

**배우는 것**: 프로세스 메모리 권한 분석, 셸코드/인젝션 패턴 식별, 악성코드 추출

```bash
# ─── 코드 인젝션 탐지 ───

# 1. malfind: 실행 가능(EXECUTE) + 쓰기 가능(WRITE) 메모리 영역에서
#    파일에 매핑되지 않은 코드를 탐지
vol -f "$EVIDENCE" linux.malfind > "$OUTPUT/malfind.txt"
cat "$OUTPUT/malfind.txt"
# PID    Process       Start              End                Protection
# 1234   suspicious    0x7f4a3c000000     0x7f4a3c001000     rwx
#   0x7f4a3c000000  48 31 c0 48 89 c7 48 89   H1.H..H.
#   0x7f4a3c000008  c6 0f 05 48 31 c0 48 c7   ...H1.H.
#   → 이것은 셸코드! (syscall 패턴)

# 2. 의심 프로세스의 메모리 맵 확인
vol -f "$EVIDENCE" linux.proc.maps --pid 1234 > "$OUTPUT/proc_maps_1234.txt"
cat "$OUTPUT/proc_maps_1234.txt"
# Start          End            Perms  Path
# 0x400000       0x401000       r-x    /usr/bin/suspicious
# 0x7f4a3c000000 0x7f4a3c001000 rwx    [anonymous]  ← 파일 없이 rwx = 인젝션!

# 3. malfind 결과에서 셸코드 패턴 분석
# 일반적인 x86_64 셸코드 시작 패턴
grep -c "48 31" "$OUTPUT/malfind.txt"  # xor rax, rax
grep -c "0f 05" "$OUTPUT/malfind.txt"  # syscall
grep -c "ff d0" "$OUTPUT/malfind.txt"  # call rax

# 4. 인젝션된 코드 덤프 (추가 분석용)
vol -f "$EVIDENCE" linux.malfind --pid 1234 --dump \
  --output-dir "$OUTPUT/malfind_dumps/"
ls -la "$OUTPUT/malfind_dumps/"

# 5. 덤프된 코드의 문자열 분석
strings "$OUTPUT/malfind_dumps/"*.dmp | \
  grep -iE "(http|socket|connect|bind|exec|/bin/sh|cmd)" | head -20

# 6. YARA 규칙으로 알려진 악성코드 패턴 매칭 (선택)
# vol -f "$EVIDENCE" linux.malfind --yara-rules /opt/yara/rules/malware.yar
```

**결과 해석**:
- `rwx`(읽기+쓰기+실행) 권한의 익명 메모리 영역은 코드 인젝션의 전형적 지표
- 정상 프로세스는 대부분 `r-x`(읽기+실행, 코드 영역) 또는 `rw-`(읽기+쓰기, 데이터 영역)
- `0x48 0x31 0xc0` (xor rax, rax)로 시작하는 패턴은 x86_64 셸코드의 일반적 시작
- `syscall` 명령어(0x0f 0x05)가 포함된 메모리 영역은 시스템 호출 사용 셸코드

**실전 활용**: malfind는 파일리스(Fileless) 악성코드를 탐지하는 핵심 도구이다. 디스크에는 아무 흔적이 없지만 메모리에만 존재하는 악성코드를 찾아낼 수 있다.

### 실습 2.6: dlllist (lsof) -- 로드된 라이브러리 분석

**실습 목적**: 프로세스가 로드한 공유 라이브러리(SO 파일)를 분석하여 악성 라이브러리 인젝션을 탐지한다.

**배우는 것**: LD_PRELOAD 인젝션 탐지, 비정상 라이브러리 경로 식별

```bash
# ─── 로드된 라이브러리 분석 ───

# 1. 특정 프로세스의 로드된 라이브러리 (Linux에서는 lsof/maps 활용)
vol -f "$EVIDENCE" linux.lsof --pid 1234 > "$OUTPUT/lsof_1234.txt"
cat "$OUTPUT/lsof_1234.txt"
# PID   FD    Path
# 1234  mem   /usr/lib/x86_64-linux-gnu/libc.so.6
# 1234  mem   /lib/x86_64-linux-gnu/libpthread.so.0
# 1234  mem   /tmp/.hidden/libevil.so        ← 비정상 경로!
# 1234  3     /dev/null
# 1234  4     socket:[12345]                 ← 네트워크 소켓

# 2. 전체 프로세스의 열린 파일 목록에서 비정상 탐지
vol -f "$EVIDENCE" linux.lsof > "$OUTPUT/lsof_all.txt"

# /tmp, /dev/shm, /var/tmp에서 로드된 라이브러리 (의심)
grep -E "/tmp/|/dev/shm/|/var/tmp/" "$OUTPUT/lsof_all.txt" | \
  grep -E "\.so|mem" > "$OUTPUT/suspicious_libs.txt"
echo "=== 의심스러운 라이브러리 ==="
cat "$OUTPUT/suspicious_libs.txt"

# 3. 숨겨진 파일 열기 (.으로 시작하는 파일)
grep "/\." "$OUTPUT/lsof_all.txt" > "$OUTPUT/hidden_files.txt"
echo "=== 숨김 파일에 접근 중인 프로세스 ==="
cat "$OUTPUT/hidden_files.txt"

# 4. 삭제된 파일을 여전히 열고 있는 프로세스
# (공격자가 파일 삭제 후에도 프로세스가 핸들을 유지)
grep "deleted" "$OUTPUT/lsof_all.txt" > "$OUTPUT/deleted_open.txt"
echo "=== 삭제된 파일 핸들 보유 프로세스 ==="
cat "$OUTPUT/deleted_open.txt"

# 5. 환경변수 확인 (LD_PRELOAD 인젝션 탐지)
vol -f "$EVIDENCE" linux.envars --pid 1234 > "$OUTPUT/envars_1234.txt"
grep -i "LD_PRELOAD" "$OUTPUT/envars_1234.txt"
# LD_PRELOAD=/tmp/.hidden/libevil.so  ← LD_PRELOAD 인젝션!
```

**결과 해석**:
- `/tmp`, `/dev/shm`, `/var/tmp`에서 로드된 `.so` 파일은 악성 라이브러리 인젝션 의심
- 숨김 파일(`.`으로 시작)에 접근하는 프로세스는 악성 활동 가능성
- LD_PRELOAD 환경변수에 비정상 경로가 설정되면 함수 후킹(hooking) 시도
- 삭제된 파일의 핸들을 유지하는 것은 안티포렌식 기법 (디스크에서 증거 삭제 + 메모리에서 계속 사용)

**명령어 해설**:
- `linux.lsof`: List Open Files. 각 프로세스가 열고 있는 파일, 소켓, 디바이스 목록
- `linux.envars`: 프로세스 환경변수 추출. LD_PRELOAD, PATH 조작 등 탐지에 활용
- `FD` 필드: `mem`=메모리 매핑 파일, 숫자=파일 디스크립터, `socket`=네트워크 소켓

**트러블슈팅**:
- `linux.lsof`가 느린 경우: `--pid` 옵션으로 특정 프로세스만 분석
- 환경변수가 비어 있을 때: 프로세스가 환경변수를 지운 경우 (안티포렌식)

## 2.4 악성 프로세스 식별 종합 분석 기법

### 악성 프로세스 식별 체크리스트

```
프로세스 분석 판단 기준
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 이름 위장 (Name Masquerading)
   □ 커널 스레드 이름인데 UID가 0이 아닌 경우
   □ 정상 서비스 이름의 오타 (예: systemd → systemdd, sshd → ssshd)
   □ 공백이나 특수문자가 포함된 프로세스 이름

2. 부모-자식 관계 이상
   □ 웹 서버(apache2, nginx)의 자식으로 셸(sh, bash)
   □ 데이터베이스 프로세스의 자식으로 네트워크 도구
   □ PPID=1인 알 수 없는 프로세스 (orphan + 재시작 시 자동실행)

3. 네트워크 활동 이상
   □ 일반적으로 네트워크를 사용하지 않는 프로세스의 외부 연결
   □ 고포트(4444, 5555, 8888)로의 아웃바운드 연결
   □ DNS(53), HTTPS(443)를 사용하는 비 브라우저/비 서버 프로세스

4. 메모리 권한 이상
   □ rwx (읽기+쓰기+실행) 권한의 익명 메모리 영역
   □ 파일에 매핑되지 않은 실행 가능 메모리
   □ 정상보다 과도하게 큰 메모리 사용

5. 파일 접근 이상
   □ /tmp, /dev/shm의 실행 파일 또는 라이브러리
   □ 숨김 파일(.으로 시작)에 대한 접근
   □ 삭제된 파일에 대한 핸들 유지
```

---

# Part 3: 디스크 분석 (50분)

## 3.1 디스크 이미지 생성

### 실습 3.1: dd를 이용한 포렌식 이미지 생성

**실습 목적**: 침해 시스템의 디스크를 비트 단위로 복제하여 포렌식 분석용 이미지를 생성하고 무결성을 검증한다.

**배우는 것**: dd 비트 복제, 해시 무결성 검증, 포렌식 이미지 관리

```bash
# ─── 디스크 이미지 생성 (web 서버, root 권한 필요) ───

# 1. 대상 디스크/파티션 확인
lsblk
# NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
# sda      8:0    0   50G  0 disk
# ├─sda1   8:1    0   48G  0 part /
# └─sda2   8:2    0    2G  0 part [SWAP]

# 2. 디스크 이미지 생성 (dd)
# conv=noerror: 읽기 오류 발생 시 건너뜀
# conv=sync: 오류 발생 시 해당 블록을 0으로 채움
# bs=4M: 블록 크기 4MB (성능 최적화)
# status=progress: 진행 상황 표시
sudo dd if=/dev/sda1 of=/tmp/disk_sda1.img \
  bs=4M conv=noerror,sync status=progress

# 3. dcfldd 사용 (dd의 포렌식 버전, 해시 동시 계산)
sudo dcfldd if=/dev/sda1 of=/tmp/disk_sda1.img \
  bs=4M conv=noerror,sync \
  hash=sha256 hashwindow=1G \
  hashlog=/tmp/disk_sda1.hashlog

# 4. 원본과 이미지의 해시 비교
sudo sha256sum /dev/sda1 > /tmp/original.sha256
sha256sum /tmp/disk_sda1.img > /tmp/image.sha256

echo "=== 원본 해시 ==="
cat /tmp/original.sha256
echo "=== 이미지 해시 ==="
cat /tmp/image.sha256

# 두 해시가 동일해야 한다!

# 5. 분석 워크스테이션으로 전송
scp /tmp/disk_sda1.img opsclaw@10.20.30.201:/home/opsclaw/forensics/evidence/
scp /tmp/original.sha256 opsclaw@10.20.30.201:/home/opsclaw/forensics/evidence/
scp /tmp/image.sha256 opsclaw@10.20.30.201:/home/opsclaw/forensics/evidence/

# ─── 워크스테이션에서 검증 ───

# 6. 전송 후 해시 재검증
cd /home/opsclaw/forensics/evidence
sha256sum disk_sda1.img
# 전송 전 해시와 비교

# 7. 이미지 정보 확인
file disk_sda1.img
# disk_sda1.img: Linux rev 1.0 ext4 filesystem data, ...

fdisk -l disk_sda1.img
# Disk disk_sda1.img: 48 GiB, ...
```

**결과 해석**:
- 원본과 이미지의 SHA-256 해시가 완전히 일치해야 한다
- `dcfldd`의 `hashwindow` 옵션은 대용량 디스크에서 부분 손상을 탐지할 수 있다
- `file` 명령으로 파일시스템 유형(ext4, xfs 등)을 확인

**실전 활용**: 프로덕션 서버에서는 디스크 이미징에 수 시간이 소요될 수 있다. 가능하면 LVM 스냅샷을 먼저 생성한 후 스냅샷에서 이미징하면 시스템 가용성에 미치는 영향을 줄일 수 있다.

**명령어 해설**:
- `dd if=INPUT of=OUTPUT`: input file에서 output file로 비트 단위 복사
- `bs=4M`: 블록 크기. 너무 작으면 느리고, 너무 크면 오류 시 데이터 손실 영역이 커짐
- `conv=noerror,sync`: 불량 섹터가 있어도 중단하지 않고, 해당 블록을 0으로 채워 이미지 크기 유지
- `dcfldd`: dd의 포렌식 확장. 해시 동시 계산, 분할 이미지, 상태 표시 등

**트러블슈팅**:
- "No space left on device": 이미지 저장 공간 부족. 외부 USB/NAS 사용 또는 `split -b 4G` 분할
- dd가 너무 느림: `bs` 값을 64M까지 늘려보기. 단, 오류 블록 크기도 커짐
- 해시 불일치: 활성 디스크에서 이미징 중 파일 변경 가능. 가능하면 시스템 종료 후 이미징

## 3.2 strings와 grep을 이용한 분석

### 실습 3.2: 디스크 이미지에서 문자열 분석

**실습 목적**: 디스크 이미지에서 의미 있는 문자열을 추출하여 공격 흔적, 악성 스크립트, 유출 데이터를 식별한다.

**배우는 것**: strings 필터링 기법, 정규표현식 패턴 매칭, 포렌식 키워드 검색

```bash
# ─── 문자열 분석 (opsclaw 워크스테이션) ───

DISK_IMG="/home/opsclaw/forensics/evidence/disk_sda1.img"
OUTPUT="/home/opsclaw/forensics/output"

# 1. 디스크 이미지 읽기 전용 마운트
sudo mkdir -p /mnt/forensic
sudo mount -o ro,loop,noexec,nosuid,nodev "$DISK_IMG" /mnt/forensic

# 마운트 옵션 설명:
# ro: 읽기 전용 (증거 보전)
# loop: 이미지 파일을 블록 디바이스로 사용
# noexec: 실행 금지 (악성코드 실수 실행 방지)
# nosuid: setuid 비활성화
# nodev: 디바이스 파일 무시

# 2. 전체 이미지에서 ASCII 문자열 추출 (최소 8자)
strings -n 8 "$DISK_IMG" > "$OUTPUT/all_strings.txt"
wc -l "$OUTPUT/all_strings.txt"
# 수백만 줄이 나올 수 있다

# 3. URL 패턴 검색 (C2 서버, 악성 다운로드)
grep -oE "https?://[a-zA-Z0-9._/-]+" "$OUTPUT/all_strings.txt" | \
  sort -u > "$OUTPUT/urls.txt"
echo "=== 발견된 URL (상위 20개) ==="
head -20 "$OUTPUT/urls.txt"

# 4. IP 주소 패턴 검색
grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" "$OUTPUT/all_strings.txt" | \
  sort -u | \
  grep -v -E "^(10\.|172\.(1[6-9]|2|3[01])\.|192\.168\.|127\.|0\.0\.)" \
  > "$OUTPUT/external_ips.txt"
echo "=== 외부 IP 주소 ==="
cat "$OUTPUT/external_ips.txt"

# 5. 악성 명령어 패턴 검색
grep -iE "(reverse.?shell|bind.?shell|meterpreter|payload|exploit|backdoor)" \
  "$OUTPUT/all_strings.txt" > "$OUTPUT/malicious_keywords.txt"
echo "=== 악성 키워드 ==="
cat "$OUTPUT/malicious_keywords.txt"

# 6. Base64 인코딩된 데이터 검색 (40자 이상)
grep -oE "[A-Za-z0-9+/]{40,}={0,2}" "$OUTPUT/all_strings.txt" | \
  head -20 | while read -r line; do
    echo "--- Encoded ---"
    echo "$line" | head -c 80
    echo ""
    echo "--- Decoded ---"
    echo "$line" | base64 -d 2>/dev/null | strings -n 4 | head -5
    echo ""
done > "$OUTPUT/base64_decoded.txt"
cat "$OUTPUT/base64_decoded.txt"

# 7. 비밀번호/크리덴셜 패턴 검색
grep -iE "(password|passwd|credential|secret|token|api.?key)" \
  "$OUTPUT/all_strings.txt" | \
  grep -v "^#" | head -30 > "$OUTPUT/credentials.txt"
echo "=== 크리덴셜 관련 문자열 ==="
cat "$OUTPUT/credentials.txt"

# 8. SSH 키 패턴 검색
grep -E "BEGIN (RSA |DSA |EC |OPENSSH )PRIVATE KEY" "$OUTPUT/all_strings.txt" \
  > "$OUTPUT/ssh_keys.txt"
echo "=== SSH 개인키 발견 여부 ==="
cat "$OUTPUT/ssh_keys.txt"

# 9. 마운트 해제
sudo umount /mnt/forensic
```

**결과 해석**:
- 외부 IP 목록에서 알려지지 않은 IP는 C2 서버 후보. VirusTotal에서 확인
- Base64 디코딩 결과에서 셸 명령어나 스크립트가 나오면 인코딩된 페이로드
- 크리덴셜 문자열은 공격자가 수집한 자격증명일 수 있음
- SSH 개인키가 비정상 경로에 있으면 공격자가 생성한 백도어 키

**명령어 해설**:
- `strings -n 8`: 최소 8바이트 이상의 연속된 출력 가능 문자 추출. 짧으면 노이즈 증가, 길면 놓치는 것 증가
- `grep -oE "정규표현식"`: `-o`는 매칭 부분만 출력, `-E`는 확장 정규표현식
- `sort -u`: 중복 제거 후 정렬

**트러블슈팅**:
- strings 결과가 너무 클 때: 특정 영역만 추출 (`dd skip=N count=M`)
- mount 실패 시: 파일시스템 손상 가능. `fsck`는 증거 변조이므로 사용 금지. `mount -o ro,loop,errors=continue` 시도

## 3.3 삭제 파일 복구

### 실습 3.3: 삭제된 파일 복구

**실습 목적**: 공격자가 삭제한 파일(악성코드, 도구, 로그)을 복구하여 추가 증거를 확보한다.

**배우는 것**: inode 기반 복구, 파일 카빙(carving) 기법, 삭제 파일 타임스탬프 분석

```bash
# ─── 삭제 파일 복구 (opsclaw 워크스테이션) ───

DISK_IMG="/home/opsclaw/forensics/evidence/disk_sda1.img"
OUTPUT="/home/opsclaw/forensics/output"
RECOVER_DIR="/home/opsclaw/forensics/output/recovered"
mkdir -p "$RECOVER_DIR"

# 1. Sleuth Kit의 fls로 삭제된 파일 목록 확인
# -r: 재귀, -d: 삭제된 파일만, -p: 전체 경로
fls -r -d -p "$DISK_IMG" > "$OUTPUT/deleted_files.txt"
echo "=== 삭제된 파일 목록 (상위 30개) ==="
head -30 "$OUTPUT/deleted_files.txt"
# d/d * 12345:  tmp/.hidden/reverse_shell.py    ← 삭제된 악성 스크립트!
# r/r * 12346:  var/log/auth.log.1              ← 삭제된 로그!
# r/r * 12347:  tmp/mimikatz                    ← 삭제된 공격 도구!

# 2. 특정 삭제 파일 복구 (inode 번호 기반)
# fls 출력에서 inode 번호를 확인하고 icat으로 복구
INODE=12345
icat "$DISK_IMG" "$INODE" > "$RECOVER_DIR/reverse_shell.py"
echo "=== 복구된 파일 내용 ==="
cat "$RECOVER_DIR/reverse_shell.py"

# 3. 특정 시간대에 삭제된 파일만 필터링
# 공격 시간대: 2026-04-01 14:00 ~ 16:00
ATTACK_START=$(date -d "2026-04-01 14:00" +%s)
ATTACK_END=$(date -d "2026-04-01 16:00" +%s)

fls -r -d -m "/" "$DISK_IMG" | \
  awk -F'|' -v start="$ATTACK_START" -v end="$ATTACK_END" \
  '$9 >= start && $9 <= end' > "$OUTPUT/deleted_attack_window.txt"
echo "=== 공격 시간대 삭제 파일 ==="
cat "$OUTPUT/deleted_attack_window.txt"

# 4. extundelete로 대량 복구 (ext3/ext4 전용)
extundelete "$DISK_IMG" --restore-all \
  --after "$ATTACK_START" \
  --before "$ATTACK_END" \
  --output-dir "$RECOVER_DIR/extundelete_output"
ls -la "$RECOVER_DIR/extundelete_output/RECOVERED_FILES/"

# 5. photorec으로 파일 카빙 (파일시스템 독립적)
# 파일 시그니처 기반으로 복구 — 파일명은 복구 불가
# photorec /d "$RECOVER_DIR/carving" "$DISK_IMG"
# (대화형이므로 실습 환경에서는 testdisk 패키지의 photorec 사용)

# 6. 특정 파일 유형만 수동 카빙 (예: ELF 바이너리)
# ELF 매직 넘버: 7f 45 4c 46
grep -aboP '\x7fELF' "$DISK_IMG" | head -10
# 오프셋 목록이 출력된다

# 7. 복구된 파일 분석
echo "=== 복구된 파일 해시 ==="
sha256sum "$RECOVER_DIR"/* 2>/dev/null
# 이 해시를 VirusTotal 등에서 검색

echo "=== 복구된 파일 유형 ==="
file "$RECOVER_DIR"/* 2>/dev/null
# ELF 64-bit, Python script, etc.

echo "=== 복구된 파일 문자열 분석 ==="
for f in "$RECOVER_DIR"/*; do
  echo "--- $f ---"
  strings -n 6 "$f" | grep -iE "(connect|socket|exec|shell|http)" | head -5
done
```

**결과 해석**:
- 삭제된 `/tmp` 하위 파일 중 스크립트나 바이너리는 공격 도구 가능성이 높다
- 삭제된 로그 파일은 공격자가 흔적을 지우려 한 것 — 복구하면 핵심 타임라인 증거
- `extundelete`는 inode가 아직 덮어쓰여지지 않은 경우에만 복구 가능
- `photorec`(파일 카빙)는 파일시스템이 손상되어도 동작하지만 파일명/경로 정보는 없음

**명령어 해설**:
- `fls -r -d -p`: `-r` 재귀 탐색, `-d` 삭제된 항목만, `-p` 전체 경로 표시
- `icat IMAGE INODE`: inode 번호에 해당하는 파일 내용을 표준출력으로 추출
- `extundelete --restore-all`: ext 파일시스템의 저널(journal)을 활용한 대량 복구
- `--after/--before`: Unix timestamp 기반 시간 필터

**트러블슈팅**:
- extundelete 복구 실패: inode가 이미 재사용됨. photorec(카빙)으로 시도
- fls에서 파일이 안 보임: 파일시스템 유형 확인. XFS는 xfs_undelete, NTFS는 ntfsundelete 사용
- 대용량 이미지에서 strings가 느림: `parallel`로 병렬 처리하거나 `dd`로 영역 분할

## 3.4 파일시스템 타임라인

### 실습 3.4: MACtime 타임라인 생성

**실습 목적**: 파일시스템의 타임스탬프(Modified, Accessed, Changed, Birth)를 기반으로 시간순 타임라인을 생성하여 공격 경로를 재구성한다.

**배우는 것**: bodyfile 포맷, MACtime 분석, 타임라인 시각화

```bash
# ─── 파일시스템 타임라인 (opsclaw 워크스테이션) ───

DISK_IMG="/home/opsclaw/forensics/evidence/disk_sda1.img"
OUTPUT="/home/opsclaw/forensics/output"

# 1. bodyfile 생성 (fls)
# bodyfile은 TSK의 표준 타임라인 입력 포맷
fls -r -m "/" "$DISK_IMG" > "$OUTPUT/bodyfile.txt"
wc -l "$OUTPUT/bodyfile.txt"
echo "=== bodyfile 샘플 (상위 5줄) ==="
head -5 "$OUTPUT/bodyfile.txt"
# MD5|name|inode|mode_as_string|UID|GID|size|atime|mtime|ctime|crtime

# 2. mactime으로 타임라인 변환
# -b: bodyfile 입력
# -d: CSV 출력 (날짜가 읽기 쉬움)
# 시간대: KST (UTC+9)
mactime -b "$OUTPUT/bodyfile.txt" -d -z Asia/Seoul \
  > "$OUTPUT/full_timeline.csv"
wc -l "$OUTPUT/full_timeline.csv"

# 3. 공격 시간대 필터링
# 공격 추정 시간: 2026-04-01 14:00 ~ 16:00
grep "2026-04-01 1[4-5]:" "$OUTPUT/full_timeline.csv" \
  > "$OUTPUT/attack_timeline.csv"
echo "=== 공격 시간대 타임라인 (상위 50줄) ==="
head -50 "$OUTPUT/attack_timeline.csv"

# 4. 타임스탬프 유형별 분석
# Date,Size,Type,Mode,UID,GID,Meta,File Name
# Type: m=Modified, a=Accessed, c=Changed, b=Born

# 수정(m)된 파일만 — 실제 내용 변경
grep ",m," "$OUTPUT/attack_timeline.csv" > "$OUTPUT/modified_files.csv"
echo "=== 공격 시간대 수정된 파일 ==="
cat "$OUTPUT/modified_files.csv"

# 생성(b)된 파일만 — 새로 만들어진 파일
grep ",b," "$OUTPUT/attack_timeline.csv" > "$OUTPUT/born_files.csv"
echo "=== 공격 시간대 생성된 파일 ==="
cat "$OUTPUT/born_files.csv"

# 5. Persistence 아티팩트 집중 분석
echo "=== Persistence 관련 변경 ==="
grep -E "(cron|systemd|\.bashrc|\.profile|init\.d|rc\.local)" \
  "$OUTPUT/attack_timeline.csv"

# 6. 웹 관련 파일 변경 (웹쉘 탐지)
echo "=== 웹 디렉토리 변경 ==="
grep -E "(var/www|html|public_html|\.php|\.jsp|\.asp)" \
  "$OUTPUT/attack_timeline.csv"

# 7. /tmp 디렉토리 활동 (공격 도구 스테이징)
echo "=== /tmp 디렉토리 활동 ==="
grep "/tmp/" "$OUTPUT/attack_timeline.csv"

# 8. 타임스탬프 조작(timestomping) 탐지
# crtime(생성)이 mtime(수정)보다 나중인 경우 → 비정상
awk -F',' 'NR>1 {
  if ($3 == "b" && $1 > prev_m && prev_name == $8) {
    print "TIMESTOMP SUSPECT:", $8, "born:", $1, "modified:", prev_m
  }
  if ($3 == "m") { prev_m = $1; prev_name = $8 }
}' "$OUTPUT/full_timeline.csv" > "$OUTPUT/timestomp_suspects.txt"
echo "=== 타임스탬프 조작 의심 ==="
cat "$OUTPUT/timestomp_suspects.txt"
```

**결과 해석**:
- 공격 시간대에 `/tmp`에 새 파일이 생성되었다면 공격 도구 업로드
- cron, systemd 관련 파일이 변경되었다면 Persistence 설정
- 웹 디렉토리에 새 PHP/JSP 파일이 생성되었다면 웹쉘 설치
- crtime > mtime인 파일은 timestomping(타임스탬프 조작) 시도

**MACtime 타임스탬프 의미**:

| 타임스탬프 | 의미 | 변경되는 경우 |
|-----------|------|-------------|
| **M** (Modified) | 파일 내용 수정 시간 | write(), truncate() |
| **A** (Accessed) | 파일 접근(읽기) 시간 | read(), exec() (noatime 마운트 시 미기록) |
| **C** (Changed) | inode 메타데이터 변경 시간 | chmod, chown, rename, link |
| **B** (Birth/Created) | 파일 최초 생성 시간 | 파일 생성 시 (ext4, btrfs만 지원) |

**트러블슈팅**:
- mactime 출력이 비어 있음: bodyfile 경로 확인, `-z` 시간대 옵션 확인
- 타임스탬프가 1970년으로 표시: 파일시스템 손상 또는 의도적 조작
- 대용량 타임라인에서 검색 느림: `csvgrep`(csvkit) 또는 `sqlite3`에 임포트하여 SQL 쿼리

---

# Part 4: 타임라인 구성 + 보고서 (50분)

## 4.1 log2timeline/plaso를 이용한 다중 소스 타임라인

### 실습 4.1: plaso 설치 및 다중 소스 타임라인 생성

**실습 목적**: log2timeline(plaso)을 사용하여 파일시스템, 시스템 로그, 웹 로그, 인증 로그 등 다양한 소스를 하나의 통합 타임라인으로 구성한다.

**배우는 것**: plaso 파이프라인(log2timeline -> psort -> psteal), 다중 아티팩트 파서, 타임라인 필터링

```bash
# ─── plaso 설치 및 설정 ───

# 1. plaso 설치 (Ubuntu/Debian)
# pip 설치
pip install plaso
# 또는 PPA (안정 버전)
# sudo add-apt-repository ppa:gift/stable
# sudo apt-get update && sudo apt-get install plaso-tools

# 2. 설치 확인
log2timeline.py --version
# plaso - log2timeline version 20xx.xx.xx

psort.py --version
# plaso - psort version 20xx.xx.xx

# 3. 지원하는 파서 목록 확인
log2timeline.py --parsers list 2>&1 | head -30
# apache_access, bash_history, cron, docker_json,
# filestat, gdrive_synclog, googlelog, linux_syslog,
# olecf, pls_recall, syslog, systemd_journal,
# utmp, wevtx, winevt, xchatlog, ...
```

### 실습 4.2: 통합 타임라인 생성

**실습 목적**: 디스크 이미지에서 모든 아티팩트를 파싱하여 단일 통합 타임라인(Super Timeline)을 생성한다.

**배우는 것**: plaso 스토리지 파일 생성, 파서 선택, 대규모 타임라인 처리

```bash
# ─── 통합 타임라인 생성 ───

DISK_IMG="/home/opsclaw/forensics/evidence/disk_sda1.img"
OUTPUT="/home/opsclaw/forensics/output"
PLASO_DIR="$OUTPUT/plaso"
mkdir -p "$PLASO_DIR"

# 1. log2timeline으로 plaso 스토리지 파일 생성
# 모든 Linux 관련 파서를 활성화하여 디스크 이미지 분석
# --storage-file: 결과를 저장할 plaso DB
# --parsers: 사용할 파서 (linux는 Linux 관련 파서 프리셋)
log2timeline.py --storage-file "$PLASO_DIR/timeline.plaso" \
  --parsers "linux,filestat,syslog,utmp,bash_history,cron,docker_json" \
  "$DISK_IMG"

# 처리 시간: 디스크 크기에 따라 수분~수시간 소요
# 진행 상황이 표시된다:
# Processing started.
# ...
# Processing completed.

# 2. 생성된 plaso 스토리지 파일 정보 확인
pinfo.py "$PLASO_DIR/timeline.plaso"
# Storage file:     timeline.plaso
# Serializer:       json
# Events:           123456
# Event sources:    7890
# ...

# 3. psort로 타임라인 CSV 출력
# --output-time-zone: 출력 시간대
# -o l2tcsv: log2timeline CSV 포맷
psort.py -o l2tcsv \
  --output-time-zone "Asia/Seoul" \
  -w "$PLASO_DIR/full_timeline.csv" \
  "$PLASO_DIR/timeline.plaso"

wc -l "$PLASO_DIR/full_timeline.csv"
echo "=== 타임라인 샘플 ==="
head -5 "$PLASO_DIR/full_timeline.csv"

# 4. 공격 시간대 필터링
psort.py -o l2tcsv \
  --output-time-zone "Asia/Seoul" \
  -w "$PLASO_DIR/attack_window.csv" \
  "$PLASO_DIR/timeline.plaso" \
  "date > '2026-04-01 14:00:00' AND date < '2026-04-01 16:00:00'"

echo "=== 공격 시간대 이벤트 수 ==="
wc -l "$PLASO_DIR/attack_window.csv"

# 5. 특정 유형의 이벤트만 필터링
# SSH 관련 이벤트
psort.py -o l2tcsv \
  -w "$PLASO_DIR/ssh_events.csv" \
  "$PLASO_DIR/timeline.plaso" \
  "source_short == 'LOG' AND message contains 'ssh'"

echo "=== SSH 관련 이벤트 ==="
head -20 "$PLASO_DIR/ssh_events.csv"

# 6. 파일 생성/수정 이벤트만
psort.py -o l2tcsv \
  -w "$PLASO_DIR/file_changes.csv" \
  "$PLASO_DIR/timeline.plaso" \
  "timestamp_desc contains 'Modification' OR timestamp_desc contains 'Creation'"

echo "=== 파일 변경 이벤트 (상위 30줄) ==="
head -30 "$PLASO_DIR/file_changes.csv"
```

**결과 해석**:
- plaso는 수십 종류의 아티팩트를 자동으로 파싱하여 하나의 타임라인으로 통합
- SSH 로그인, 파일 생성, cron 실행, bash 명령어가 모두 시간순으로 나열
- 공격 시간대 필터를 적용하면 수만 건의 이벤트에서 핵심 이벤트만 추출 가능
- `source_short` 필드로 이벤트 소스(LOG, FILE, REG 등)를 구분할 수 있다

**명령어 해설**:
- `log2timeline.py`: 입력 소스(디스크 이미지, 파일, 디렉토리)를 분석하여 plaso 스토리지에 이벤트 저장
- `psort.py`: plaso 스토리지에서 이벤트를 정렬/필터링/출력. `-o l2tcsv`는 CSV 포맷
- `pinfo.py`: plaso 스토리지의 메타데이터(이벤트 수, 파서 정보 등) 조회
- 필터 구문: `date > 'YYYY-MM-DD HH:MM:SS'`, `message contains 'keyword'`

### 실습 4.3: 다중 소스 상관 분석

**실습 목적**: 파일시스템 타임라인, 시스템 로그, 네트워크 로그를 상관 분석하여 공격의 전체 그림을 재구성한다.

**배우는 것**: 다중 소스 이벤트 상관 기법, 공격 단계 매핑, 킬 체인 재구성

```bash
# ─── 다중 소스 상관 분석 ───

PLASO_DIR="/home/opsclaw/forensics/output/plaso"
REPORT_DIR="/home/opsclaw/forensics/reports"
mkdir -p "$REPORT_DIR"

# 1. SIEM(Wazuh) 로그 수집 (siem 서버에서)
ssh siem@10.20.30.100 \
  'grep "10.20.30.80" /var/ossec/logs/alerts/alerts.json | \
   jq -c "select(.timestamp >= \"2026-04-01T14:00:00\")" | head -100' \
  > "$PLASO_DIR/wazuh_alerts.json"

# 2. 웹 서버 액세스 로그 (마운트된 이미지에서)
sudo mount -o ro,loop /home/opsclaw/forensics/evidence/disk_sda1.img /mnt/forensic
grep "01/Apr/2026:1[4-5]:" /mnt/forensic/var/log/apache2/access.log \
  > "$PLASO_DIR/web_access_attack.log"
sudo umount /mnt/forensic

# 3. 인증 로그
sudo mount -o ro,loop /home/opsclaw/forensics/evidence/disk_sda1.img /mnt/forensic
grep "Apr  1 1[4-5]:" /mnt/forensic/var/log/auth.log \
  > "$PLASO_DIR/auth_attack.log"
sudo umount /mnt/forensic

# 4. 타임라인 통합 (수동 상관 분석)
echo "=== 공격 타임라인 재구성 ===" > "$REPORT_DIR/attack_timeline.txt"
echo "" >> "$REPORT_DIR/attack_timeline.txt"

echo "--- 14:00~14:15: 초기 침투 ---" >> "$REPORT_DIR/attack_timeline.txt"
# 웹 로그에서 공격 시도
grep -E "(sqlmap|nikto|union.*select|<script)" "$PLASO_DIR/web_access_attack.log" | \
  head -10 >> "$REPORT_DIR/attack_timeline.txt"

echo "" >> "$REPORT_DIR/attack_timeline.txt"
echo "--- 14:15~14:30: 웹쉘 업로드 ---" >> "$REPORT_DIR/attack_timeline.txt"
# POST 요청 + 새 파일 생성
grep "POST.*upload" "$PLASO_DIR/web_access_attack.log" \
  >> "$REPORT_DIR/attack_timeline.txt"
grep -E "Creation.*var/www" "$PLASO_DIR/attack_window.csv" \
  >> "$REPORT_DIR/attack_timeline.txt"

echo "" >> "$REPORT_DIR/attack_timeline.txt"
echo "--- 14:30~15:00: 권한 상승 ---" >> "$REPORT_DIR/attack_timeline.txt"
# sudo 시도, su 명령
grep -E "(sudo|su |privilege|CVE)" "$PLASO_DIR/auth_attack.log" \
  >> "$REPORT_DIR/attack_timeline.txt"

echo "" >> "$REPORT_DIR/attack_timeline.txt"
echo "--- 15:00~15:30: 내부 이동 + 데이터 수집 ---" >> "$REPORT_DIR/attack_timeline.txt"
grep -E "(ssh|scp|rsync|tar|zip)" "$PLASO_DIR/auth_attack.log" \
  >> "$REPORT_DIR/attack_timeline.txt"

echo "" >> "$REPORT_DIR/attack_timeline.txt"
echo "--- 15:30~16:00: 흔적 삭제 ---" >> "$REPORT_DIR/attack_timeline.txt"
grep -E "Deletion" "$PLASO_DIR/attack_window.csv" | \
  grep -E "(log|history|tmp)" >> "$REPORT_DIR/attack_timeline.txt"

cat "$REPORT_DIR/attack_timeline.txt"

# 5. Cyber Kill Chain 매핑
echo "
=== Cyber Kill Chain 매핑 ===

1. Reconnaissance  : 웹 스캐닝 (sqlmap, nikto)
2. Weaponization   : SQL Injection 페이로드 준비
3. Delivery        : HTTP POST로 웹쉘 업로드
4. Exploitation    : 웹 취약점(파일 업로드) 악용
5. Installation    : 웹쉘 설치 + cron 백도어
6. C2              : 리버스 셸(203.0.113.50:4444)
7. Actions         : 데이터 수집 + 유출 시도
" >> "$REPORT_DIR/attack_timeline.txt"
```

**결과 해석**:
- 웹 로그의 공격 시도 -> 파일시스템의 웹쉘 생성 -> 인증 로그의 권한 상승을 시간순으로 연결하면 공격 전체 경로가 드러남
- Wazuh 알림과 파일시스템 변경을 대조하면 탐지된 것과 놓친 것을 확인할 수 있음
- Kill Chain 단계별 매핑으로 어느 단계에서 차단했어야 하는지 파악 가능

## 4.2 포렌식 보고서 작성

### 실습 4.4: 포렌식 보고서 작성

**실습 목적**: 분석 결과를 체계적인 포렌식 보고서로 정리하여 경영진, 법률팀, 규제 기관에 제출할 수 있는 형태로 문서화한다.

**배우는 것**: 포렌식 보고서 구조, 기술적 발견 사항 정리, 대상별 커뮤니케이션

```bash
# ─── 포렌식 보고서 생성 ───

REPORT_DIR="/home/opsclaw/forensics/reports"

cat << 'REPORT_TEMPLATE' > "$REPORT_DIR/forensic_report_template.txt"
================================================================
        디지털 포렌식 조사 보고서
================================================================

1. 보고서 개요
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  사건 번호    : INC-2026-0401-001
  보고서 작성일 : 2026-04-02
  조사관       : [이름, 자격증, 소속]
  요청자       : [요청 부서/담당자]
  보고서 버전   : 1.0

2. 조사 범위
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - 대상 시스템: web 서버 (10.20.30.80)
  - 조사 기간: 2026-04-01 00:00 ~ 2026-04-02 00:00 KST
  - 증거 목록:
    EVD-001: 메모리 덤프 (8GB, SHA-256: a3f2e1...)
    EVD-002: 디스크 이미지 (48GB, SHA-256: b5c4d3...)
    EVD-003: Wazuh 알림 로그 (JSON, 312건)

3. 경영 요약 (Executive Summary)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  2026-04-01 14:00경 외부 공격자가 웹 서버의 파일 업로드
  취약점을 악용하여 웹쉘을 설치하고, 로컬 권한 상승 후
  내부 네트워크 탐색을 시도하였다. C2 서버(203.0.113.50)와의
  통신이 확인되었으며, 데이터 유출 시도가 포착되었다.
  
  영향 범위: web 서버 1대 완전 침해
  데이터 유출: [확인 중 / 미확인 / N건 유출]
  현재 상태: 격리 완료, 복구 진행 중

4. 기술적 발견 사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  4.1 초기 침투 (14:00-14:15)
  - 공격 기법: SQL Injection + 파일 업로드
  - 증거: 웹 액세스 로그, 웹쉘 파일 (복구됨)
  - ATT&CK: T1190 (Exploit Public-Facing Application)

  4.2 실행 (14:15-14:30)
  - 공격 기법: 웹쉘을 통한 명령 실행
  - 증거: 메모리(pstree), bash_history
  - ATT&CK: T1059.004 (Unix Shell)

  4.3 권한 상승 (14:30-15:00)
  - 공격 기법: CVE-XXXX-XXXXX 커널 취약점 악용
  - 증거: auth.log, 메모리 내 exploit 코드
  - ATT&CK: T1068 (Exploitation for Privilege Escalation)

  4.4 지속성 확보 (15:00-15:15)
  - 공격 기법: crontab 등록, SSH 키 추가
  - 증거: 파일시스템 타임라인, cron 파일
  - ATT&CK: T1053.003 (Cron), T1098.004 (SSH Authorized Keys)

  4.5 C2 통신 (14:30-16:00)
  - C2 서버: 203.0.113.50:4444 (TCP)
  - 증거: 메모리(sockstat), 네트워크 로그
  - ATT&CK: T1071.001 (Application Layer Protocol)

  4.6 흔적 삭제 (15:30-16:00)
  - 삭제된 파일: auth.log, bash_history, 공격 도구
  - 증거: 삭제 파일 복구(extundelete), 타임라인
  - ATT&CK: T1070.004 (File Deletion)

5. 침해 지표 (IoC)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  IP:    203.0.113.50 (C2 서버)
  IP:    198.51.100.10 (스캐닝 소스)
  File:  /var/www/html/uploads/shell.php (SHA-256: ...)
  File:  /tmp/.hidden/reverse_shell.py (SHA-256: ...)
  File:  /tmp/.hidden/libevil.so (SHA-256: ...)
  Cron:  */5 * * * * curl http://203.0.113.50/beacon

6. 권고 사항
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [즉시 조치]
  - 침해 서버 네트워크 격리 (완료)
  - C2 IP(203.0.113.50) 방화벽 차단
  - 모든 계정 비밀번호 변경
  - SSH 키 전수 검사 및 재발급

  [단기 조치 (1주 이내)]
  - 웹 서버 파일 업로드 기능 보안 강화
  - 커널 보안 패치 적용
  - WAF 규칙 강화 (SQL Injection, 파일 업로드)
  - IDS/IPS 시그니처 추가 (IoC 기반)

  [중장기 조치 (1개월 이내)]
  - 웹 애플리케이션 전체 보안 감사
  - 네트워크 세그멘테이션 강화
  - EDR 솔루션 도입 검토
  - 포렌식 자동 수집 체계 구축

7. 증거 목록 및 Chain of Custody
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [별첨 A 참조]

8. 분석 도구 및 방법론
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - Volatility 3.x.x: 메모리 분석
  - Sleuth Kit 4.x.x: 파일시스템 분석
  - plaso 20xx.xx.xx: 타임라인 생성
  - extundelete 0.x.x: 파일 복구

================================================================
REPORT_TEMPLATE

echo "=== 보고서 템플릿 생성 완료 ==="
echo "위치: $REPORT_DIR/forensic_report_template.txt"

# IoC 자동 추출 스크립트
cat << 'IOC_SCRIPT' > "$REPORT_DIR/extract_ioc.sh"
#!/bin/bash
# IoC 자동 추출 스크립트
OUTPUT_DIR="/home/opsclaw/forensics/output"
IOC_FILE="/home/opsclaw/forensics/reports/ioc_list.txt"

echo "=== Indicators of Compromise ===" > "$IOC_FILE"
echo "Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$IOC_FILE"
echo "" >> "$IOC_FILE"

echo "[IP Addresses]" >> "$IOC_FILE"
cat "$OUTPUT_DIR/external_ips.txt" >> "$IOC_FILE" 2>/dev/null
cat "$OUTPUT_DIR/suspicious_ips.txt" >> "$IOC_FILE" 2>/dev/null
echo "" >> "$IOC_FILE"

echo "[URLs]" >> "$IOC_FILE"
cat "$OUTPUT_DIR/urls.txt" >> "$IOC_FILE" 2>/dev/null
echo "" >> "$IOC_FILE"

echo "[File Hashes (SHA-256)]" >> "$IOC_FILE"
sha256sum "$OUTPUT_DIR/recovered/"* 2>/dev/null >> "$IOC_FILE"
echo "" >> "$IOC_FILE"

echo "[Malicious Files]" >> "$IOC_FILE"
cat "$OUTPUT_DIR/suspicious_libs.txt" >> "$IOC_FILE" 2>/dev/null
echo "" >> "$IOC_FILE"

echo "IoC list saved to: $IOC_FILE"
IOC_SCRIPT

chmod +x "$REPORT_DIR/extract_ioc.sh"
echo "=== IoC 추출 스크립트 생성 완료 ==="
```

**결과 해석**:
- 포렌식 보고서는 대상 독자에 따라 수준을 조절: 경영진에게는 Executive Summary, 기술팀에게는 기술적 발견 사항, 법률팀에게는 증거 목록과 Chain of Custody
- IoC(침해 지표) 목록은 방화벽, IDS, SIEM에 즉시 적용하여 동일 공격 재발을 차단
- 권고 사항은 즉시/단기/중장기로 우선순위를 구분하여 실행 가능성을 높임

**실전 활용**: 실제 사고에서는 보고서를 여러 버전으로 작성한다. 속보 보고서(1시간 이내), 중간 보고서(24시간), 최종 보고서(1-2주). 각 단계에서 확인된 사실만 기록하고, 추측은 명확히 "추정"으로 표기한다.

## 4.3 OpsClaw를 활용한 포렌식 자동화

### 실습 4.5: OpsClaw 포렌식 수집 자동화

**실습 목적**: OpsClaw의 execute-plan을 활용하여 다수 서버에서 포렌식 아티팩트를 자동으로 수집한다.

**배우는 것**: API 기반 포렌식 수집 자동화, 다중 서버 동시 수집, 증거 중앙 집중

```bash
# ─── OpsClaw 포렌식 수집 자동화 ───

export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 1. 포렌식 수집 프로젝트 생성
PROJECT_RESP=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "forensic-collection-20260401",
    "request_text": "침해 의심 서버(web)에서 포렌식 아티팩트 자동 수집",
    "master_mode": "external"
  }')
PROJECT_ID=$(echo "$PROJECT_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Project ID: $PROJECT_ID"

# 2. Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/plan" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 3. 포렌식 수집 태스크 실행
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "ps auxf && echo === && ss -tlnp && echo === && last -20 && echo === && cat /etc/crontab && crontab -l 2>/dev/null && echo === && ls -la /etc/cron.d/",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 2,
        "instruction_prompt": "find /etc/systemd/system -name \"*.service\" -newer /etc/os-release -exec stat {} \\; -exec cat {} \\; 2>/dev/null && echo === && find /tmp /var/tmp /dev/shm -type f -executable 2>/dev/null | head -20",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 3,
        "instruction_prompt": "tail -200 /var/log/auth.log | grep -E \"Accepted|Failed|sudo|su\" && echo === && tail -200 /var/log/syslog | grep -iE \"error|warning|critical|segfault\"",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 4,
        "instruction_prompt": "find / -name \"*.php\" -newer /etc/os-release -not -path \"/proc/*\" -not -path \"/sys/*\" 2>/dev/null | head -20 && echo === && find /home -name \".bashrc\" -exec grep -l \"alias\\|export\\|curl\\|wget\" {} \\; 2>/dev/null",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      },
      {
        "order": 5,
        "instruction_prompt": "cat /home/*/.bash_history 2>/dev/null | tail -100 && echo === && cat /root/.bash_history 2>/dev/null | tail -100",
        "risk_level": "low",
        "subagent_url": "http://10.20.30.80:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'

# 4. 결과 확인
sleep 5
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/projects/$PROJECT_ID/evidence/summary" | \
  python3 -m json.tool

# 5. 완료 보고서
curl -s -X POST "http://localhost:8000/projects/$PROJECT_ID/completion-report" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "web 서버 포렌식 아티팩트 자동 수집 완료",
    "outcome": "success",
    "work_details": [
      "프로세스/네트워크/로그인 이력 수집",
      "Persistence 아티팩트(systemd, cron) 점검",
      "인증/시스템 로그 수집",
      "웹쉘 후보 파일 탐지",
      "bash_history 수집"
    ]
  }'
```

**결과 해석**:
- execute-plan의 각 태스크가 성공적으로 실행되면 evidence에 결과가 저장된다
- task별로 서로 다른 subagent_url을 지정하면 여러 서버에서 동시 수집 가능
- risk_level을 "low"로 설정하여 읽기 전용 명령만 실행 (증거 보전 원칙 준수)

**실전 활용**: 대규모 환경(수십~수백 대 서버)에서 동일한 포렌식 수집 태스크를 반복 실행할 때, OpsClaw의 자동화가 수동 작업 대비 10배 이상의 시간 절약을 가능하게 한다.

**트러블슈팅**:
- 태스크 실행 타임아웃: 명령이 오래 걸리면 timeout 설정 조정
- SubAgent 연결 실패: 대상 서버의 SubAgent(8002) 기동 상태 확인
- 권한 부족: 일부 명령은 root 권한 필요. risk_level 조정 또는 sudo 설정 확인

---

## 검증 체크리스트

학습이 완료된 항목에 체크 표시를 한다.

### Part 1: 디지털 포렌식 이론
- [ ] 디지털 포렌식의 5대 기본 원칙(증거 보전, 무결성, CoC, 재현성, 최소 침습)을 설명할 수 있다
- [ ] 휘발성 순서(Order of Volatility)에 따른 증거 수집 우선순위를 설명할 수 있다
- [ ] 라이브 포렌식과 데드 포렌식의 차이점과 각각의 장단점을 설명할 수 있다
- [ ] Chain of Custody 기록서의 필수 항목을 나열할 수 있다
- [ ] 한국 법률 체계에서 디지털 증거의 요건(형사소송법, 정보통신망법)을 설명할 수 있다
- [ ] 포렌식 도구를 목적별(수집/분석/타임라인)로 분류할 수 있다

### Part 2: 메모리 분석
- [ ] Volatility 3를 설치하고 Linux 심볼 테이블을 구성할 수 있다
- [ ] LiME으로 메모리 덤프를 수집하고 SHA-256으로 무결성을 검증할 수 있다
- [ ] pslist/pstree로 프로세스를 분석하고 비정상 프로세스를 식별할 수 있다
- [ ] sockstat으로 네트워크 연결을 분석하고 C2 통신을 탐지할 수 있다
- [ ] malfind로 코드 인젝션(rwx 메모리 영역)을 탐지할 수 있다
- [ ] lsof/envars로 악성 라이브러리 로딩과 LD_PRELOAD 인젝션을 탐지할 수 있다

### Part 3: 디스크 분석
- [ ] dd/dcfldd로 포렌식 디스크 이미지를 생성하고 해시로 검증할 수 있다
- [ ] strings와 grep으로 디스크 이미지에서 의미 있는 문자열(URL, IP, 키워드)을 추출할 수 있다
- [ ] fls/icat/extundelete로 삭제된 파일을 복구할 수 있다
- [ ] MACtime 타임라인을 생성하고 공격 시간대의 파일 변경을 분석할 수 있다
- [ ] 읽기 전용 마운트(ro, noexec)로 증거를 보전하며 분석할 수 있다

### Part 4: 타임라인 구성 + 보고서
- [ ] log2timeline/plaso로 다중 소스 통합 타임라인을 생성할 수 있다
- [ ] psort로 시간대/키워드 필터링을 적용할 수 있다
- [ ] 다중 소스(파일시스템, 로그, 네트워크) 이벤트를 상관 분석할 수 있다
- [ ] Cyber Kill Chain에 매핑하여 공격 경로를 재구성할 수 있다
- [ ] 포렌식 보고서(Executive Summary, 기술적 발견 사항, IoC, 권고 사항)를 작성할 수 있다
- [ ] OpsClaw execute-plan으로 다중 서버 포렌식 수집을 자동화할 수 있다

---

## 자가 점검 퀴즈

### 퀴즈 1: 라이브 포렌식 vs 데드 포렌식

**문제**: 침해 사고 대응 시 라이브 포렌식을 데드 포렌식보다 먼저 수행해야 하는 이유를 3가지 이상 제시하고, 라이브 포렌식 수행 시 증거 변조를 최소화하기 위한 방법을 설명하시오.

**정답 가이드**:
- 이유 1: 메모리는 전원 차단 시 즉시 소실되므로 살아있는 상태에서만 수집 가능
- 이유 2: 활성 네트워크 연결(C2 통신 등)은 시스템 종료 시 끊어져 증거 소멸
- 이유 3: 실행 중인 프로세스의 환경변수, 열린 파일 핸들, 암호화 키는 메모리에만 존재
- 이유 4: 암호화된 디스크의 복호화 키가 메모리에 있어, 종료 후에는 디스크 분석 불가
- 변조 최소화: 수집 도구는 USB/네트워크 공유에서 실행, 로컬 디스크에 쓰지 않음, 수집 행위 자체를 문서화

### 퀴즈 2: Volatility 플러그인

**문제**: Volatility 3에서 pslist와 psscan(메모리 스캔 방식)의 차이점을 설명하고, pslist에서는 보이지 않지만 psscan에서만 보이는 프로세스가 있다면 어떤 공격 기법이 사용되었는지 설명하시오.

**정답 가이드**:
- pslist: 커널의 task_struct 이중 연결 리스트를 순회하여 프로세스 열거
- psscan: 메모리 전체를 스캔하여 task_struct 시그니처/패턴을 검색
- pslist에 없고 psscan에만 있는 프로세스: DKOM(Direct Kernel Object Manipulation) 기법으로 task_struct 연결 리스트에서 자신을 제거하여 은닉
- 이는 루트킷(rootkit)의 전형적인 프로세스 은닉 기법

### 퀴즈 3: MACtime 타임스탬프

**문제**: Linux ext4 파일시스템에서 M(Modified), A(Accessed), C(Changed), B(Birth) 타임스탬프가 각각 변경되는 조건을 구체적으로 설명하시오. `cp`, `mv`, `chmod` 명령 실행 시 각 타임스탬프는 어떻게 변하는가?

**정답 가이드**:
- M (mtime): 파일 내용이 변경될 때 (write, truncate). `echo "data" >> file`
- A (atime): 파일이 읽혀질 때 (read, exec). `cat file`. 단, noatime/relatime 마운트 옵션에 따라 동작이 달라짐
- C (ctime): inode 메타데이터가 변경될 때 (chmod, chown, rename, hard link 생성/삭제, mtime 변경 시에도 ctime 갱신)
- B (crtime): 파일이 최초 생성될 때 한 번만 설정. ext4, btrfs에서 지원
- `cp src dst`: dst의 MACB 모두 현재 시간 (새 파일 생성). `cp -p`는 mtime/atime 보존
- `mv src dst`: 같은 파일시스템이면 ctime만 변경 (rename). 다른 파일시스템이면 cp+delete와 동일
- `chmod 755 file`: ctime만 변경 (inode 메타데이터 변경)

### 퀴즈 4: 안티 포렌식 대응

**문제**: 공격자가 사용할 수 있는 안티 포렌식(Anti-Forensics) 기법 5가지를 나열하고, 각각에 대한 대응(탐지 또는 무력화) 방법을 제시하시오.

**정답 가이드**:
1. Timestomping (타임스탬프 조작): crtime > mtime 불일치 검사, 저널 로그 분석으로 원래 시간 확인
2. 로그 삭제: 원격 syslog/SIEM으로 로그 이중화, 삭제된 로그 파일 복구(extundelete)
3. 디스크 와이핑 (shred, wipe): SSD TRIM 이전 이미지 생성, NAND 플래시 레벨 복구 (비용 높음)
4. 파일리스 악성코드: 메모리 포렌식(Volatility malfind)으로 탐지, 정기적 메모리 덤프
5. 프로세스 은닉 (DKOM): pslist vs psscan 교차 비교, 커널 무결성 검사

### 퀴즈 5: Chain of Custody

**문제**: Chain of Custody(증거 관리 연쇄)가 법적 증거에서 중요한 이유를 설명하고, Chain of Custody가 단절될 수 있는 실무 시나리오 3가지와 예방 방법을 제시하시오.

**정답 가이드**:
- 중요 이유: 증거가 수집 후 법정 제출까지 변조되지 않았음을 입증. 단절 시 상대측이 증거 변조 가능성을 주장하여 증거 능력 상실
- 시나리오 1: 증거 USB를 택배로 발송 시 운송 기록 누락 -> 봉인 테이프 + 서명 + 추적 번호
- 시나리오 2: 야간에 분석실에 접근 통제 없이 방치 -> 물리적 잠금 + 접근 로그 시스템
- 시나리오 3: 이메일로 증거 파일 전송 시 중간자 공격 가능성 -> 암호화 전송 + 수신 확인 + 해시 별도 전달

### 퀴즈 6: malfind 분석

**문제**: Volatility의 malfind 플러그인이 탐지하는 "의심스러운 메모리 영역"의 조건을 설명하시오. 정상적인 프로그램에서도 rwx 메모리 영역이 존재할 수 있는 경우는 어떤 것이 있는가?

**정답 가이드**:
- malfind 탐지 조건: (1) 실행 가능(EXECUTE) 권한이 있고, (2) 쓰기 가능(WRITE) 권한이 있으며, (3) 파일에 매핑되지 않은(anonymous) 메모리 영역
- 정상적인 rwx 존재 사례: JIT 컴파일러(JVM, V8 JavaScript 엔진, .NET CLR), 동적 코드 생성 라이브러리(libffi), 자체 수정 코드(self-modifying code)를 사용하는 프로그램
- 따라서 malfind 결과를 무조건 악성으로 판단하면 안 되며, 프로세스 이름, 메모리 내용, 실행 컨텍스트를 종합 판단해야 함

### 퀴즈 7: 디스크 이미징

**문제**: `dd if=/dev/sda of=disk.img bs=4M conv=noerror,sync`에서 각 옵션의 의미를 설명하시오. `conv=noerror,sync`를 사용하지 않으면 어떤 문제가 발생할 수 있는가?

**정답 가이드**:
- `if=/dev/sda`: 입력 파일 (소스 디스크)
- `of=disk.img`: 출력 파일 (이미지)
- `bs=4M`: 블록 크기 4MB (한 번에 읽고 쓰는 단위)
- `conv=noerror`: 읽기 오류(배드 섹터 등) 발생 시 중단하지 않고 계속 진행
- `conv=sync`: 오류 블록을 0(null)으로 채워 이미지 크기를 원본과 동일하게 유지
- noerror,sync 없이: 배드 섹터를 만나면 dd가 즉시 중단되어 불완전 이미지 생성. 또는 오류 블록을 건너뛰면 이미지의 오프셋이 틀어져 파일시스템 구조가 깨짐

### 퀴즈 8: plaso 타임라인

**문제**: log2timeline/plaso가 단순한 MACtime(fls+mactime) 타임라인보다 우수한 점 3가지를 설명하시오. plaso의 3단계 파이프라인(log2timeline -> psort -> 출력)에서 각 단계의 역할은 무엇인가?

**정답 가이드**:
- 우수한 점 1: 파일시스템뿐 아니라 시스템 로그, 웹 로그, bash 히스토리, 레지스트리 등 수십 종 아티팩트를 자동 파싱하여 "Super Timeline" 생성
- 우수한 점 2: 다양한 필터링(시간대, 소스, 키워드) 및 출력 포맷(CSV, JSON, Elasticsearch) 지원
- 우수한 점 3: 플러그인 아키텍처로 커스텀 파서 추가 가능, 지속적으로 새로운 아티팩트 파서 추가
- log2timeline: 입력 소스를 파싱하여 이벤트를 추출하고 plaso 스토리지 파일에 저장
- psort: 스토리지 파일의 이벤트를 정렬, 필터링, 중복 제거
- 출력 (psteal 또는 psort -o): 최종 포맷(CSV, JSON 등)으로 변환하여 파일 출력

### 퀴즈 9: 포렌식 보고서

**문제**: 포렌식 보고서의 "경영 요약(Executive Summary)"과 "기술적 발견 사항" 섹션의 차이점을 설명하시오. 각 섹션의 독자는 누구이며, 어떤 수준의 기술적 세부사항을 포함해야 하는가?

**정답 가이드**:
- Executive Summary: 독자는 경영진/의사결정자. 기술 용어 최소화. "무엇이 일어났고, 영향은 무엇이며, 어떻게 해야 하는가"에 집중. 1-2 페이지 이내
- 기술적 발견 사항: 독자는 보안팀/IT팀/포렌식 전문가. ATT&CK 매핑, 구체적 명령어, 로그 증거, 해시값 등 상세 기술 정보 포함. 재현 가능한 수준의 세부사항
- 공통: 둘 다 사실만 기술하고, 추측은 "추정"으로 명시. 시간순 서술

### 퀴즈 10: 종합 시나리오

**문제**: 웹 서버에서 다음과 같은 포렌식 증거가 발견되었다. 공격 타임라인을 재구성하고, 사용된 ATT&CK 기법을 매핑하시오.

```
[증거 1] 웹 로그: POST /upload.php?cmd=ls HTTP/1.1 (14:12)
[증거 2] 파일시스템: /var/www/html/uploads/shell.php (생성: 14:15, 수정: 14:15)
[증거 3] 메모리 pstree: apache2 → sh → python3 (14:20)
[증거 4] 메모리 sockstat: python3 → 203.0.113.50:4444 ESTABLISHED (14:22)
[증거 5] auth.log: sudo su - root (성공, 14:30)
[증거 6] 파일시스템: /etc/cron.d/update-check (생성: 14:35)
[증거 7] 파일시스템: /var/log/auth.log (삭제: 14:40)
```

**정답 가이드**:
- 14:12 - 초기 정찰: 기존 웹쉘 또는 명령 인젝션 테스트 (T1190)
- 14:15 - 웹쉘 업로드: 파일 업로드 취약점 악용 (T1505.003 Web Shell)
- 14:20 - 명령 실행: 웹쉘을 통해 셸 획득 후 Python 리버스 쉘 실행 (T1059.004, T1059.006)
- 14:22 - C2 수립: 외부 C2 서버와 리버스 쉘 연결 (T1071.001)
- 14:30 - 권한 상승: sudo를 이용한 root 권한 획득 (T1548.003)
- 14:35 - Persistence: cron 작업 등록으로 재부팅 후에도 접근 유지 (T1053.003)
- 14:40 - 흔적 삭제: 인증 로그 삭제로 증거 인멸 시도 (T1070.004)

---

## 과제

### 과제 1: 종합 포렌식 분석 실습 (개인, 제출 기한: 다음 주)

다음 시나리오에 대한 포렌식 분석을 수행하고 보고서를 제출하시오.

**시나리오**: web 서버(10.20.30.80)에서 비정상적인 외부 통신이 탐지되었다. Wazuh에서 "Possible SQL injection attempt" 알림이 다수 발생하였고, 이후 서버의 CPU 사용률이 급증하였다. 침해 여부를 판단하고 전체 공격 경로를 재구성하시오.

**제출 항목**:
1. **메모리 분석 결과** (40점)
   - pslist/pstree 분석 결과 및 의심 프로세스 목록
   - sockstat 분석 결과 및 외부 연결 목록
   - malfind 분석 결과 (코드 인젝션 여부)
   - lsof/envars 분석 결과 (비정상 파일/환경변수)

2. **디스크 분석 결과** (30점)
   - strings/grep 분석으로 발견한 IoC (URL, IP, 키워드)
   - 삭제 파일 복구 결과 및 복구된 파일 분석
   - MACtime 타임라인 (공격 시간대 필터링)

3. **통합 타임라인 및 보고서** (30점)
   - plaso 또는 수동 통합 타임라인 (파일시스템 + 로그 + 메모리)
   - Cyber Kill Chain 매핑
   - 포렌식 보고서 (Executive Summary, 기술적 발견 사항, IoC, 권고 사항)
   - Chain of Custody 기록서

**평가 기준**:
- 증거 수집 절차의 정확성 (해시 검증, 읽기 전용 마운트)
- 분석 도구 활용의 적절성 (올바른 플러그인/명령어 선택)
- 타임라인 재구성의 논리적 일관성
- 보고서의 완성도 (사실 기반 기술, 대상별 수준 조절)
- IoC의 구체성과 활용 가능성

### 과제 2: 포렌식 자동화 스크립트 개발 (선택, 보너스)

OpsClaw의 execute-plan API를 활용하여 다음 기능을 자동화하는 Bash 스크립트를 작성하시오.

1. 지정된 서버에서 포렌식 아티팩트 자동 수집 (프로세스, 네트워크, 로그, cron, systemd)
2. 수집 결과에서 IoC 자동 추출 (외부 IP, 의심 URL, 비정상 프로세스)
3. 추출된 IoC를 nftables 차단 규칙으로 변환
4. 결과 보고서 자동 생성

---

## 참고 자료

### 필수 읽기
- NIST SP 800-86: Guide to Integrating Forensic Techniques into Incident Response
- RFC 3227: Guidelines for Evidence Collection and Archiving
- SANS SIFT Workstation Documentation: https://www.sans.org/tools/sift-workstation/

### 도구 문서
- Volatility 3 Documentation: https://volatility3.readthedocs.io/
- Sleuth Kit (TSK) Wiki: https://wiki.sleuthkit.org/
- plaso Documentation: https://plaso.readthedocs.io/

### ATT&CK 참조
- MITRE ATT&CK Linux Matrix: https://attack.mitre.org/matrices/enterprise/linux/
- ATT&CK Navigator: https://mitre-attack.github.io/attack-navigator/

### 법률 참조
- 형사소송법 제313조 (디지털 증거)
- 정보통신망 이용촉진 및 정보보호 등에 관한 법률 제48조
- 개인정보보호법 제34조 (개인정보 유출 등의 통지)
