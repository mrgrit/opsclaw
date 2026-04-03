# Week 09: 인시던트 대응 — 격리, 증거 보존, 초동 조치

## 학습 목표
- 인시던트 대응의 6단계 프로세스를 이해한다
- 침해 시스템을 안전하게 격리하는 방법을 실습한다
- 디지털 증거를 보존하고 포렌식 기초를 적용할 수 있다
- 초동 조치를 신속하게 수행하는 체크리스트를 활용할 수 있다

## 선수 지식
- 방화벽 규칙 설정 (Week 06)
- 로그 분석 기초 (Week 08)
- 리눅스 시스템 관리 명령어

## 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 인시던트 대응 프로세스 이론 | 강의 |
| 0:30-0:50 | 증거 보존 및 포렌식 원칙 | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:40 | 시스템 격리 실습 | 실습 |
| 1:40-2:20 | 증거 수집 및 보존 실습 | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | 초동 조치 시뮬레이션 | 실습 |
| 3:10-3:40 | 대응 절차 리뷰 + 퀴즈 | 토론/퀴즈 |

---

# Part 1: 인시던트 대응 이론 (30분)

## 1.1 인시던트 대응 프로세스 (NIST SP 800-61)

인시던트 대응은 보안 사고에 체계적으로 대응하기 위한 프로세스이다.

### 6단계 프로세스

```
1. 준비 (Preparation)
   └── 도구 준비, 팀 구성, 절차 수립
2. 탐지 및 분석 (Detection & Analysis)
   └── IDS 알림, 로그 분석, 트리아지
3. 격리 (Containment)
   └── 네트워크 차단, 서비스 중지
4. 근절 (Eradication)
   └── 악성코드 제거, 취약점 패치
5. 복구 (Recovery)
   └── 서비스 재개, 모니터링 강화
6. 사후 분석 (Lessons Learned)
   └── 보고서 작성, 절차 개선
```

## 1.2 증거 보존 원칙

디지털 포렌식에서 증거의 무결성 유지는 핵심이다.

### 휘발성 순서 (Order of Volatility)

증거는 휘발성이 높은 것부터 수집해야 한다.

| 우선순위 | 데이터 | 휘발성 | 수집 명령 |
|---------|--------|--------|----------|
| 1 | 메모리 (RAM) | 매우 높음 | `dd`, LiME |
| 2 | 네트워크 연결 | 높음 | `ss`, `netstat` |
| 3 | 프로세스 목록 | 높음 | `ps aux` |
| 4 | 로그 파일 | 중간 | `cp`, `tar` |
| 5 | 디스크 이미지 | 낮음 | `dd`, `dcfldd` |
| 6 | 물리 매체 | 매우 낮음 | 물리 보존 |

### 증거 보관 체인 (Chain of Custody)

- 누가, 언제, 어떤 증거를, 어떻게 수집했는지 기록
- 해시값으로 무결성 검증 (MD5 + SHA256)
- 원본은 보존하고 사본으로 분석

---

# Part 2: 실습 가이드

## 실습 2.1: 침해 시스템 격리

> **목적**: 침해가 확인된 시스템을 네트워크에서 안전하게 격리한다
> **배우는 것**: 방화벽 기반 격리, 서비스 중지, 관리 접근 유지

```bash
# 방법 1: nftables로 네트워크 격리 (관리 IP만 허용)
sudo nft flush ruleset
sudo nft add table inet emergency
sudo nft add chain inet emergency input { type filter hook input priority 0 \; policy drop \; }
sudo nft add chain inet emergency output { type filter hook output priority 0 \; policy drop \; }

# 관리자 IP만 SSH 허용
sudo nft add rule inet emergency input ip saddr 10.20.30.201 tcp dport 22 accept
sudo nft add rule inet emergency output ip daddr 10.20.30.201 tcp sport 22 accept

# 루프백 허용
sudo nft add rule inet emergency input iifname "lo" accept
sudo nft add rule inet emergency output oifname "lo" accept

# 이미 수립된 연결 허용
sudo nft add rule inet emergency input ct state established,related accept
sudo nft add rule inet emergency output ct state established,related accept

# 방법 2: 의심 서비스 중지
sudo systemctl stop apache2
sudo systemctl stop nginx

# 격리 상태 확인
sudo nft list ruleset
ss -tlnp
```

> **결과 해석**: 격리 후에는 관리자만 SSH로 접근할 수 있고, 외부 통신은 모두 차단된다. 이를 통해 추가 피해 확산을 방지한다.
> **실전 활용**: 공방전에서 침해가 확인되면 즉시 격리하여 Red Team의 추가 활동을 차단한다.

## 실습 2.2: 증거 수집 및 보존

> **목적**: 휘발성 순서에 따라 체계적으로 증거를 수집한다
> **배우는 것**: 시스템 상태 스냅샷, 로그 백업, 해시 검증

```bash
# 증거 저장 디렉토리 생성
EVIDENCE_DIR="/tmp/evidence_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EVIDENCE_DIR"

# 1. 네트워크 연결 상태 수집
ss -tlnpa > "$EVIDENCE_DIR/network_connections.txt"
ip addr > "$EVIDENCE_DIR/ip_addresses.txt"
ip route > "$EVIDENCE_DIR/routing_table.txt"

# 2. 프로세스 목록 수집
ps auxf > "$EVIDENCE_DIR/processes.txt"
ls -la /proc/*/exe 2>/dev/null > "$EVIDENCE_DIR/process_executables.txt"

# 3. 로그 파일 백업
cp /var/log/auth.log "$EVIDENCE_DIR/"
cp /var/log/syslog "$EVIDENCE_DIR/"
cp -r /var/log/suricata/ "$EVIDENCE_DIR/suricata_logs/" 2>/dev/null

# 4. 시스템 정보 수집
uname -a > "$EVIDENCE_DIR/system_info.txt"
last -a > "$EVIDENCE_DIR/login_history.txt"
crontab -l > "$EVIDENCE_DIR/crontab.txt" 2>/dev/null
cat /etc/passwd > "$EVIDENCE_DIR/passwd.txt"

# 5. 최근 변경된 파일 탐색
find / -mmin -60 -type f 2>/dev/null > "$EVIDENCE_DIR/recent_modified.txt"

# 6. 해시값 생성 (무결성 검증용)
sha256sum "$EVIDENCE_DIR"/* > "$EVIDENCE_DIR/checksums.sha256"

# 증거 확인
ls -la "$EVIDENCE_DIR/"
```

> **결과 해석**: 수집된 증거의 SHA256 해시를 기록하여 이후 변조 여부를 확인할 수 있다. 타임스탬프가 포함된 디렉토리명으로 수집 시점을 명확히 한다.

## 실습 2.3: 초동 조치 시뮬레이션

> **목적**: 침해 시나리오에서 초동 조치를 시간 제한 내에 수행한다
> **배우는 것**: 우선순위 판단, 신속한 대응, 팀 협업

```bash
# 시나리오: auth.log에서 비인가 root 로그인이 감지됨
# 초동 조치 체크리스트

# 1단계: 확인 (1분)
grep "Accepted.*root" /var/log/auth.log | tail -5
last root | head -5

# 2단계: 격리 (2분)
# 공격자 세션 강제 종료
who | grep -v "$(whoami)"
# sudo pkill -u suspicious_user

# 3단계: 비밀번호 변경 (1분)
sudo passwd root
sudo passwd $(whoami)

# 4단계: 백도어 점검 (3분)
crontab -l
cat /etc/crontab
ls -la /etc/cron.d/
grep -r "authorized_keys" /root/.ssh/ /home/*/.ssh/ 2>/dev/null

# 5단계: 증거 보존 (위 실습 참조)
# 6단계: 보고 (팀 내 공유)
```

> **결과 해석**: 초동 조치는 속도가 중요하다. 체크리스트를 미리 준비하고 순서대로 실행하면 대응 시간을 크게 단축할 수 있다.

---

# Part 3: 심화 학습

## 3.1 악성코드 분석 기초

의심 파일이 발견된 경우 기본적인 분석을 수행한다.

```bash
# 파일 유형 확인
file suspicious_file

# 문자열 추출
strings suspicious_file | head -50

# 해시 계산 후 VirusTotal 조회
sha256sum suspicious_file
```

## 3.2 사후 분석 보고서 구성

- 인시던트 개요 (언제, 무엇이, 어떻게)
- 영향 범위 (시스템, 데이터, 서비스)
- 대응 타임라인
- 근본 원인 분석
- 재발 방지 권고사항

---

## 검증 체크리스트
- [ ] 침해 시스템을 nftables로 격리하고 관리 접근만 유지했는가
- [ ] 휘발성 순서에 따라 증거를 수집하고 해시를 기록했는가
- [ ] 초동 조치 체크리스트를 5분 이내에 수행했는가
- [ ] 백도어(cron, SSH 키, 사용자 추가) 여부를 점검했는가

## 자가 점검 퀴즈
1. 휘발성 순서에서 RAM을 가장 먼저 수집해야 하는 이유는?
2. 증거 보관 체인(Chain of Custody)이 중요한 이유를 설명하라.
3. 시스템 격리 시 관리자 접근을 유지해야 하는 이유는?
4. 백도어를 탐지하기 위해 점검해야 할 5가지 항목을 나열하라.
5. 인시던트 대응 6단계 중 '준비' 단계에서 해야 할 일 3가지는?
