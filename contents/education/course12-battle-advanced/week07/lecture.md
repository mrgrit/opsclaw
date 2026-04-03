# Week 07: 포렌식 기반 방어 — 메모리 분석(Volatility), 디스크 분석

## 학습 목표
- 디지털 포렌식의 기본 원칙과 증거 보전 절차를 이해한다
- Volatility 3를 이용한 메모리 포렌식 분석 기법을 실습한다
- 디스크 이미지 분석으로 공격 흔적을 추적할 수 있다
- 타임라인 분석을 통해 공격 경로를 재구성할 수 있다
- 포렌식 결과를 기반으로 방어 규칙을 개선할 수 있다

## 선수 지식
- 공방전 기초 과정 이수
- 운영체제(프로세스, 메모리, 파일시스템) 기본 지식
- Week 02-05 공격 기법 이해

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | 포렌식 분석 워크스테이션 | `ssh opsclaw@10.20.30.201` |
| web | 10.20.30.80 | 침해 시스템 (분석 대상) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | 로그 상관 분석 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 디지털 포렌식 이론 | 강의 |
| 0:30-1:10 | 메모리 덤프 수집 및 분석 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | Volatility 3 심화 분석 | 실습 |
| 2:00-2:40 | 디스크 포렌식 실습 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | 타임라인 재구성 토론 + 퀴즈 | 토론 |

---

# Part 1: 디지털 포렌식 이론 (30분)

## 1.1 포렌식 기본 원칙

| 원칙 | 설명 |
|------|------|
| 증거 보전 | 원본 데이터를 변경하지 않는다 |
| 무결성 입증 | 해시값으로 증거 무결성을 보장한다 |
| 연속성 유지 | Chain of Custody (증거 관리 연쇄) |
| 재현 가능성 | 동일 분석 시 동일 결과 |
| 최소 침습 | 시스템에 최소한의 영향 |

## 1.2 포렌식 분석 유형

```
라이브 포렌식 (Live Forensics)
├── 메모리 덤프 → 프로세스, 네트워크, 암호화 키
├── 네트워크 캡처 → 활성 연결, C2 통신
└── 실행 중인 프로세스 → 악성코드 분석

데드 포렌식 (Dead Forensics)
├── 디스크 이미지 → 파일시스템, 삭제 파일
├── 로그 분석 → 타임라인 재구성
└── 레지스트리/설정 → Persistence 아티팩트
```

## 1.3 ATT&CK와 포렌식 아티팩트

| 공격 기법 | 포렌식 아티팩트 | 분석 도구 |
|----------|----------------|----------|
| T1053 (Cron) | crontab 파일 | strings, cat |
| T1543 (Systemd) | 유닛 파일 | find, stat |
| T1059 (Shell) | bash_history | cat, timeline |
| T1071 (C2) | 네트워크 소켓 | volatility, netstat |
| T1003 (Credential) | 메모리 내 해시 | volatility |

---

# Part 2: 메모리 포렌식 실습 (40분)

## 실습 2.1: 메모리 덤프 수집

> **목적**: 침해 시스템의 메모리를 안전하게 수집한다
> **배우는 것**: 메모리 덤프 방법, 무결성 검증

```bash
# 메모리 덤프 수집 (web)
# 방법 1: /proc/kcore (제한적)
dd if=/proc/kcore of=/tmp/memdump.raw bs=1M count=512

# 방법 2: LiME (Linux Memory Extractor)
insmod /opt/lime/lime.ko "path=/tmp/memdump.lime format=lime"

# 무결성 해시 생성
sha256sum /tmp/memdump.lime > /tmp/memdump.sha256

# 분석 워크스테이션으로 전송
scp /tmp/memdump.lime opsclaw@10.20.30.201:/tmp/forensics/
```

## 실습 2.2: Volatility 3 분석

> **목적**: 메모리 덤프에서 악성 활동의 흔적을 찾는다
> **배우는 것**: Volatility 플러그인 활용

```bash
# 프로세스 목록 (숨겨진 프로세스 탐지)
vol3 -f /tmp/forensics/memdump.lime linux.pslist
vol3 -f /tmp/forensics/memdump.lime linux.pstree

# 네트워크 연결 (C2 통신 탐지)
vol3 -f /tmp/forensics/memdump.lime linux.sockstat

# bash 히스토리 추출
vol3 -f /tmp/forensics/memdump.lime linux.bash

# 프로세스 메모리 덤프 (의심 프로세스)
vol3 -f /tmp/forensics/memdump.lime linux.proc.maps --pid 1234
```

---

# Part 3: 디스크 포렌식 실습 (40분)

## 실습 3.1: 파일시스템 분석

> **목적**: 디스크에서 공격 흔적과 삭제된 파일을 복구한다
> **배우는 것**: 타임스탬프 분석, 삭제 파일 복구

```bash
# 디스크 이미지 생성
dd if=/dev/sda1 of=/tmp/disk.img bs=4M conv=noerror,sync
sha256sum /tmp/disk.img > /tmp/disk.sha256

# 마운트 (읽기 전용)
mkdir -p /mnt/forensic
mount -o ro,loop /tmp/disk.img /mnt/forensic

# 최근 수정된 파일 찾기 (공격 시간대)
find /mnt/forensic -newermt "2026-04-01 00:00" -not -newermt "2026-04-02 00:00" \
  -type f -exec ls -la {} \;

# 삭제된 파일 복구
extundelete /tmp/disk.img --restore-all --after $(date -d "2026-04-01" +%s)

# Persistence 아티팩트 검색
cat /mnt/forensic/var/spool/cron/crontabs/*
ls -la /mnt/forensic/etc/systemd/system/*.service
cat /mnt/forensic/home/*/.bashrc | grep -v "^#"
```

## 실습 3.2: 타임라인 생성

> **목적**: 파일시스템 활동의 시간순 타임라인을 생성한다
> **배우는 것**: MACtime 분석, 공격 경로 재구성

```bash
# fls + mactime으로 타임라인 생성
fls -r -m "/" /tmp/disk.img > /tmp/bodyfile.txt
mactime -b /tmp/bodyfile.txt -d 2026-04-01..2026-04-02 > /tmp/timeline.csv

# 의심 시간대 필터링
grep "2026-04-01 14:" /tmp/timeline.csv | head -30
```

---

# Part 4: 포렌식 기반 방어 개선 (40분)

## 4.1 OpsClaw 포렌식 자동화

```bash
# 포렌식 수집 자동화 프로젝트
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order":1,"instruction_prompt":"ps auxf && netstat -tlnp && last -20","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":2,"instruction_prompt":"find /etc/systemd/system -name *.service -newer /etc/os-release -exec cat {} \\;","risk_level":"low","subagent_url":"http://10.20.30.80:8002"},
      {"order":3,"instruction_prompt":"cat /var/log/auth.log | grep -E \"Accepted|Failed\" | tail -50","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002"
  }'
```

---

## 검증 체크리스트
- [ ] 메모리 덤프를 수집하고 무결성을 검증할 수 있다
- [ ] Volatility 3로 프로세스/네트워크/히스토리를 분석할 수 있다
- [ ] 디스크 이미지에서 삭제된 파일을 복구할 수 있다
- [ ] 타임라인 분석으로 공격 경로를 재구성할 수 있다
- [ ] 포렌식 결과를 기반으로 탐지 규칙을 개선할 수 있다

## 자가 점검 퀴즈
1. 라이브 포렌식을 데드 포렌식보다 먼저 수행해야 하는 이유는?
2. Volatility에서 pslist와 psscan의 차이점과 각각이 탐지하는 것은?
3. MACtime(Modified, Accessed, Changed)에서 각 타임스탬프가 변경되는 조건은?
4. 안티 포렌식(timestomping, 로그 삭제)에 대한 대응 방법 3가지를 제시하시오.
5. Chain of Custody가 법적 증거에서 중요한 이유를 설명하시오.
