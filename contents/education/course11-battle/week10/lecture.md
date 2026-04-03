# Week 10: 공방전 준비 — 인프라 강화, 패치, 불필요 서비스 제거

## 학습 목표
- 공방전 시작 전 인프라 보안 강화(Hardening) 절차를 수행할 수 있다
- 시스템 패치 관리 프로세스를 이해하고 적용할 수 있다
- 불필요한 서비스를 식별하고 제거하여 공격 표면을 줄일 수 있다
- 팀 역할 분담과 방어 전략을 수립할 수 있다

## 선수 지식
- 방화벽 구축 (Week 06)
- IDS/IPS 구축 (Week 07)
- 인시던트 대응 (Week 09)

## 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 시스템 강화(Hardening) 이론 | 강의 |
| 0:30-0:50 | 공방전 전략 수립 방법론 | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:40 | 서비스 점검 및 제거 실습 | 실습 |
| 1:40-2:20 | 패치 관리 및 설정 강화 실습 | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | 종합 강화 체크리스트 실행 | 실습 |
| 3:10-3:40 | 팀 전략 토론 + 퀴즈 | 토론/퀴즈 |

---

# Part 1: 시스템 강화 이론 (30분)

## 1.1 Hardening이란?

시스템 강화(Hardening)는 불필요한 기능을 제거하고 보안 설정을 강화하여 공격 표면(Attack Surface)을 최소화하는 과정이다.

### CIS Benchmark 기반 강화 영역

| 영역 | 내용 | 우선순위 |
|------|------|---------|
| **서비스 관리** | 불필요 서비스 중지/제거 | 높음 |
| **패치 관리** | OS/애플리케이션 업데이트 | 높음 |
| **계정 관리** | 불필요 계정 제거, 패스워드 강화 | 높음 |
| **네트워크** | 방화벽, 불필요 포트 차단 | 높음 |
| **파일 권한** | SUID/SGID 정리, 권한 최소화 | 중간 |
| **감사/로깅** | 로그 설정, 모니터링 활성화 | 중간 |

## 1.2 공방전 방어 전략

### 시간 관리 (Blue Team 15분 준비 시간 기준)

```
공방전 준비 타임라인
0분  ─── 인프라 현황 파악 (서비스, 포트, 계정)
3분  ─── 방화벽 기본 정책 적용
5분  ─── 불필요 서비스 중지
7분  ─── 패스워드 변경 (기본/약한 패스워드)
9분  ─── IDS 활성화
11분 ─── 로그 모니터링 시작
13분 ─── 백업 생성
15분 ─── 공방전 시작
```

### 팀 역할 분담

| 역할 | 담당 업무 |
|------|----------|
| **방화벽 담당** | nftables 규칙, 실시간 IP 차단 |
| **IDS 담당** | Suricata 모니터링, 알림 전달 |
| **로그 분석** | auth.log, 웹 로그 실시간 감시 |
| **시스템 관리** | 패치, 서비스 관리, 백업 |

---

# Part 2: 실습 가이드

## 실습 2.1: 불필요 서비스 점검 및 제거

> **목적**: 공격 표면을 줄이기 위해 불필요한 서비스를 식별하고 중지한다
> **배우는 것**: 서비스 열거, 위험 평가, 중지/비활성화

```bash
# 열려있는 포트와 서비스 확인
ss -tlnp

# 실행 중인 서비스 목록
systemctl list-units --type=service --state=running

# 부팅 시 자동 시작 서비스
systemctl list-unit-files --state=enabled

# 불필요 서비스 식별 기준
# - 공방전에서 사용하지 않는 서비스
# - 알려진 취약점이 있는 서비스
# - 외부 접근이 필요 없는 내부 서비스

# 불필요 서비스 중지 및 비활성화
sudo systemctl stop cups          # 프린터 서비스
sudo systemctl disable cups
sudo systemctl stop avahi-daemon   # 서비스 검색
sudo systemctl disable avahi-daemon
sudo systemctl stop rpcbind        # NFS/NIS
sudo systemctl disable rpcbind

# 중지 후 확인
ss -tlnp
```

> **결과 해석**: 중지 전후로 `ss -tlnp` 결과를 비교하여 열린 포트가 줄어든 것을 확인한다.
> **실전 활용**: 공방전 준비 시간에 가장 먼저 수행해야 할 작업 중 하나이다.

## 실습 2.2: 패치 관리 및 설정 강화

> **목적**: 시스템과 애플리케이션을 최신 상태로 업데이트하고 보안 설정을 강화한다
> **배우는 것**: 패키지 업데이트, SSH 강화, 커널 파라미터 튜닝

```bash
# 패키지 업데이트 확인
sudo apt update
apt list --upgradable 2>/dev/null

# 보안 업데이트만 적용
sudo apt upgrade -y

# SSH 설정 강화 (/etc/ssh/sshd_config)
sudo tee -a /etc/ssh/sshd_config.d/hardening.conf << 'EOF'
PermitRootLogin no
PasswordAuthentication no
MaxAuthTries 3
LoginGraceTime 20
AllowUsers opsclaw
Protocol 2
X11Forwarding no
EOF
sudo systemctl restart sshd

# 커널 보안 파라미터 설정
sudo tee -a /etc/sysctl.d/99-hardening.conf << 'EOF'
# SYN flood 방어
net.ipv4.tcp_syncookies = 1
# ICMP redirect 비활성화
net.ipv4.conf.all.accept_redirects = 0
# IP spoofing 방어
net.ipv4.conf.all.rp_filter = 1
# 소스 라우팅 비활성화
net.ipv4.conf.all.accept_source_route = 0
EOF
sudo sysctl --system
```

> **결과 해석**: SSH 강화 후 root 직접 로그인이 차단되고 최대 인증 시도가 3회로 제한된다. 커널 파라미터 변경으로 네트워크 공격에 대한 저항성이 향상된다.

## 실습 2.3: 종합 강화 체크리스트 실행

> **목적**: 미리 준비된 체크리스트를 순서대로 실행하여 전체 시스템을 강화한다
> **배우는 것**: 체계적 강화 절차, 자동화 스크립트 활용

```bash
# 종합 강화 스크립트 예시
echo "=== 1. 불필요 계정 점검 ==="
awk -F: '$3 >= 1000 && $1 != "nobody" {print $1}' /etc/passwd

echo "=== 2. SUID 바이너리 점검 ==="
find / -perm -4000 -type f 2>/dev/null

echo "=== 3. World-writable 파일 점검 ==="
find / -perm -0002 -type f ! -path "/proc/*" ! -path "/sys/*" 2>/dev/null | head -20

echo "=== 4. crontab 점검 ==="
for user in $(cut -d: -f1 /etc/passwd); do
  crontab -u "$user" -l 2>/dev/null && echo "--- $user ---"
done

echo "=== 5. SSH 키 점검 ==="
find /home -name "authorized_keys" -exec ls -la {} \;

echo "=== 6. 열린 포트 최종 확인 ==="
ss -tlnp

echo "=== 7. 방화벽 상태 ==="
sudo nft list ruleset | head -30
```

> **결과 해석**: 각 항목의 결과를 검토하여 비정상적인 항목을 식별하고 조치한다. 이 스크립트를 미리 준비해두면 공방전 준비 시간을 효율적으로 활용할 수 있다.

---

# Part 3: 심화 학습

## 3.1 자동화 강화 도구

- **Lynis**: 리눅스 보안 감사 도구 (`lynis audit system`)
- **OpenSCAP**: CIS Benchmark 자동 점검
- **Ansible**: 강화 설정 자동 배포

## 3.2 백업 전략

공방전 시작 전 중요 설정 파일을 백업한다.

```bash
# 설정 파일 백업
tar czf /tmp/config_backup_$(date +%Y%m%d).tar.gz \
  /etc/ssh/ /etc/nftables.conf /etc/suricata/ \
  /etc/passwd /etc/shadow /etc/sudoers
```

---

## 검증 체크리스트
- [ ] 불필요한 서비스를 최소 3개 이상 중지했는가
- [ ] SSH 설정을 강화하고 root 로그인을 차단했는가
- [ ] 커널 보안 파라미터를 적용했는가
- [ ] 종합 강화 체크리스트를 실행하고 이상 항목을 조치했는가
- [ ] 설정 파일 백업을 생성했는가

## 자가 점검 퀴즈
1. 시스템 강화에서 '공격 표면 축소'의 의미를 구체적으로 설명하라.
2. 공방전 준비 시간(15분)에 가장 먼저 수행해야 할 3가지 작업은?
3. `net.ipv4.tcp_syncookies = 1`이 SYN flood를 방어하는 원리는?
4. SSH 설정에서 `MaxAuthTries 3`과 fail2ban의 역할 차이는?
5. Blue Team 역할 분담에서 각 역할의 핵심 업무를 설명하라.
