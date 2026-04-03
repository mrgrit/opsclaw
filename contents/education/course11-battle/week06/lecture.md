# Week 06: 방화벽 구축 — nftables 규칙, 로깅

## 학습 목표
- nftables의 아키텍처와 기본 개념을 이해한다
- 방화벽 규칙을 작성하여 트래픽을 필터링할 수 있다
- 로깅 규칙을 설정하여 의심 트래픽을 기록할 수 있다
- 공방전에서 효과적인 방화벽 정책을 설계할 수 있다

## 선수 지식
- TCP/IP 네트워크 기초 (IP, 포트, 프로토콜)
- 리눅스 네트워크 명령어 (ip, ss, netstat)
- 패킷 흐름 기본 개념

## 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | nftables 아키텍처 이론 | 강의 |
| 0:30-0:50 | 규칙 문법 및 체인 구조 | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:40 | 기본 방화벽 규칙 구축 실습 | 실습 |
| 1:40-2:20 | 로깅 및 고급 규칙 실습 | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | 공방전용 방화벽 정책 설계 | 실습 |
| 3:10-3:40 | 방화벽 우회 토론 + 퀴즈 | 토론/퀴즈 |

---

# Part 1: nftables 아키텍처 이론 (30분)

## 1.1 nftables 개요

nftables는 리눅스 커널의 넷필터(Netfilter) 프레임워크 위에서 동작하는 패킷 필터링 도구이다. iptables의 후속으로, 더 간결한 문법과 향상된 성능을 제공한다.

### iptables vs nftables

| 항목 | iptables | nftables |
|------|----------|---------|
| 문법 | 복잡한 플래그 | 간결한 구문 |
| 테이블 | 미리 정의됨 | 사용자 정의 |
| 성능 | 선형 탐색 | set/map 지원 |
| IPv4/IPv6 | 별도 명령 | 통합 처리 |

### nftables 구조

```
nftables 계층 구조
├── Table (테이블) ─── 규칙의 최상위 컨테이너
│   ├── Chain (체인) ─── 규칙의 순서 목록
│   │   ├── Rule (규칙) ─── 매칭 조건 + 액션
│   │   ├── Rule
│   │   └── Rule
│   └── Chain
└── Table
```

## 1.2 체인 유형과 훅(Hook)

| Hook | 설명 | 용도 |
|------|------|------|
| `input` | 로컬 시스템으로 들어오는 패킷 | 서비스 접근 제어 |
| `output` | 로컬 시스템에서 나가는 패킷 | 아웃바운드 제어 |
| `forward` | 시스템을 통과하는 패킷 | 라우터/게이트웨이 |
| `prerouting` | 라우팅 전 패킷 | DNAT |
| `postrouting` | 라우팅 후 패킷 | SNAT/Masquerade |

## 1.3 규칙 문법

```bash
# 기본 구문
nft add rule [family] [table] [chain] [매칭조건] [액션]

# 예시
nft add rule inet filter input tcp dport 22 accept
nft add rule inet filter input tcp dport 80 accept
nft add rule inet filter input drop
```

---

# Part 2: 실습 가이드

## 실습 2.1: 기본 방화벽 규칙 구축

> **목적**: nftables로 기본 방화벽을 구축하여 서비스 접근을 제어한다
> **배우는 것**: 테이블/체인 생성, 규칙 추가, 기본 정책 설정

```bash
# 기존 규칙 확인
sudo nft list ruleset

# 테이블 생성
sudo nft add table inet filter

# input 체인 생성 (기본 정책: drop)
sudo nft add chain inet filter input { type filter hook input priority 0 \; policy drop \; }

# 기본 허용 규칙
# 루프백 허용
sudo nft add rule inet filter input iifname "lo" accept

# 이미 수립된 연결 허용
sudo nft add rule inet filter input ct state established,related accept

# SSH 허용 (관리용)
sudo nft add rule inet filter input tcp dport 22 accept

# HTTP/HTTPS 허용
sudo nft add rule inet filter input tcp dport { 80, 443 } accept

# ICMP 허용 (ping)
sudo nft add rule inet filter input icmp type echo-request accept

# 규칙 확인
sudo nft list ruleset
```

> **결과 해석**: `policy drop`이 설정되면 명시적으로 허용되지 않은 모든 트래픽이 차단된다. 규칙은 위에서 아래로 순서대로 평가된다.
> **실전 활용**: 공방전 시작 직후 Blue Team이 가장 먼저 수행해야 할 작업이다.

## 실습 2.2: 로깅 규칙 설정

> **목적**: 의심 트래픽을 로그에 기록하여 모니터링한다
> **배우는 것**: nftables 로그 규칙, 로그 분석

```bash
# 차단된 패킷 로깅 (drop 전에 log 추가)
sudo nft add rule inet filter input log prefix "NFT-DROP: " level warn
sudo nft add rule inet filter input drop

# 특정 포트 접근 시도 로깅
sudo nft add rule inet filter input tcp dport 3389 log prefix "RDP-ATTEMPT: " drop

# 포트 스캔 의심 트래픽 로깅
sudo nft add rule inet filter input tcp flags syn ct state new \
  log prefix "NEW-SYN: " level info

# 로그 확인
sudo journalctl -k | grep "NFT-DROP"
sudo dmesg | grep "NFT-DROP"

# 실시간 모니터링
sudo journalctl -kf | grep "NFT-"
```

> **결과 해석**: 로그에서 소스 IP, 포트, 프로토콜 정보를 확인하여 공격 패턴을 식별한다. 짧은 시간에 다수의 SYN 로그는 포트 스캔을 의미한다.

## 실습 2.3: 공방전용 방화벽 정책 설계

> **목적**: 공방전 시나리오에 최적화된 방화벽 정책을 설계한다
> **배우는 것**: 서비스별 규칙, Rate limiting, IP 기반 제어

```bash
# Rate limiting (SSH brute force 방어)
sudo nft add rule inet filter input tcp dport 22 \
  ct state new limit rate 3/minute accept

# 특정 IP 대역만 SSH 허용
sudo nft add rule inet filter input ip saddr 10.20.30.0/24 tcp dport 22 accept

# 특정 IP 차단 (공격자 IP)
sudo nft add rule inet filter input ip saddr 10.20.30.99 drop

# Named Set을 이용한 IP 관리
sudo nft add set inet filter blocked_ips { type ipv4_addr \; }
sudo nft add rule inet filter input ip saddr @blocked_ips drop
sudo nft add element inet filter blocked_ips { 10.20.30.99, 10.20.30.98 }

# 규칙 영구 저장
sudo nft list ruleset > /etc/nftables.conf
```

> **결과 해석**: Named Set을 사용하면 차단 IP를 동적으로 관리할 수 있다. Rate limiting은 brute force 공격을 효과적으로 완화한다.

---

# Part 3: 심화 학습

## 3.1 방화벽 우회 기법 (Red Team 관점)

공격자가 시도하는 방화벽 우회 기법을 이해해야 방어도 강화할 수 있다.

- **허용 포트 터널링**: SSH 터널(443 포트), HTTP 터널
- **프로토콜 우회**: DNS 터널링, ICMP 터널
- **패킷 분할**: Fragmentation으로 룰 우회 시도

## 3.2 nftables 스크립트 파일

복잡한 규칙은 스크립트 파일로 관리한다.

```
#!/usr/sbin/nft -f
flush ruleset
table inet filter {
    set blocked_ips { type ipv4_addr; }
    chain input {
        type filter hook input priority 0; policy drop;
        iifname "lo" accept
        ct state established,related accept
        tcp dport 22 ct state new limit rate 3/minute accept
        tcp dport { 80, 443 } accept
        ip saddr @blocked_ips drop
        log prefix "NFT-DROP: " drop
    }
}
```

---

## 검증 체크리스트
- [ ] nftables로 기본 방화벽을 구축하고 서비스 접근을 제어했는가
- [ ] 로깅 규칙을 설정하고 차단 로그를 확인했는가
- [ ] Rate limiting으로 brute force 공격을 완화했는가
- [ ] 방화벽 규칙을 파일로 저장하고 재적용했는가

## 자가 점검 퀴즈
1. nftables에서 `policy drop`과 `policy accept`의 차이를 설명하라.
2. `ct state established,related`를 허용하는 이유는 무엇인가?
3. Named Set의 장점과 활용 사례를 설명하라.
4. Rate limiting 규칙이 SSH brute force를 방어하는 원리는?
5. 공방전에서 Blue Team이 방화벽을 구축할 때 가장 먼저 해야 할 3가지는?
