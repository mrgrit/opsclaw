# Week 03: nftables 방화벽 (2) — 실전

## 학습 목표

- NAT(SNAT/DNAT)와 포트 포워딩을 구성할 수 있다
- 화이트리스트(기본 차단) 정책을 설계할 수 있다
- nftables 로깅 기능을 활용할 수 있다
- 룰셋을 파일로 저장하고 복원할 수 있다

---

## 1. NAT 개요

NAT(Network Address Translation)는 패킷의 IP 주소를 변환하는 기술이다.

| 종류 | 설명 | 사용 예 |
|------|------|---------|
| **SNAT** | 출발지 IP 변환 | 내부 → 외부 통신 시 공인 IP로 변환 |
| **DNAT** | 목적지 IP 변환 | 외부 → 내부 포트 포워딩 |
| **Masquerade** | 동적 SNAT | 유동 IP 환경에서의 NAT |

---

## 2. 실습 환경 접속

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1
```

secu 서버는 게이트웨이 역할을 한다:
- `eth1`: 10.20.30.1 (내부 네트워크)
- 내부 서버: web(10.20.30.80), siem(10.20.30.100)

---

## 3. NAT 테이블 구성

### 3.1 NAT 테이블과 체인 생성

```bash
# NAT 전용 테이블 생성
echo 1 | sudo -S nft add table inet lab_nat

# prerouting 체인 (DNAT용)
echo 1 | sudo -S nft add chain inet lab_nat prerouting \
  '{ type nat hook prerouting priority -100; policy accept; }'

# postrouting 체인 (SNAT용)
echo 1 | sudo -S nft add chain inet lab_nat postrouting \
  '{ type nat hook postrouting priority 100; policy accept; }'
```

### 3.2 SNAT (Masquerade)

내부 네트워크(10.20.30.0/24)의 트래픽을 외부로 내보낼 때 IP 변환:

```bash
# masquerade: 나가는 인터페이스의 IP로 자동 변환
echo 1 | sudo -S nft add rule inet lab_nat postrouting \
  ip saddr 10.20.30.0/24 masquerade
```

### 3.3 DNAT (포트 포워딩)

외부에서 secu 서버의 8080 포트로 접근하면 web 서버(10.20.30.80)의 80 포트로 전달:

```bash
echo 1 | sudo -S nft add rule inet lab_nat prerouting \
  tcp dport 8080 dnat to 10.20.30.80:80
```

**확인:**
```bash
echo 1 | sudo -S nft list table inet lab_nat
```

**예상 출력:**
```
table inet lab_nat {
    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;
        tcp dport 8080 dnat to 10.20.30.80:80
    }
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        ip saddr 10.20.30.0/24 masquerade
    }
}
```

### 3.4 IP 포워딩 활성화

NAT가 동작하려면 커널의 IP 포워딩이 활성화되어야 한다:

```bash
# 현재 상태 확인
cat /proc/sys/net/ipv4/ip_forward

# 활성화 (즉시)
echo 1 | sudo -S sysctl -w net.ipv4.ip_forward=1
```

**예상 출력:**
```
net.ipv4.ip_forward = 1
```

---

## 4. 포트 포워딩 테스트

### 4.1 web 서버 HTTP 접근 테스트

secu 서버 자체에서 포트 포워딩 테스트:

```bash
# 직접 접근 (정상 동작)
curl -s -o /dev/null -w "%{http_code}" http://10.20.30.80:80
```

**예상 출력:**
```
200
```

---

## 5. 화이트리스트 정책 (기본 차단)

보안에서 가장 중요한 원칙: **기본 차단, 명시적 허용**

### 5.1 정책 설계

```
[기본 정책: DROP]
  ↓ 허용 목록:
  1. 수립된 연결 (conntrack)
  2. 루프백 인터페이스
  3. SSH (22/tcp)
  4. ICMP (ping)
  5. 특정 관리 IP에서만 접근
```

### 5.2 구현

```bash
# 실습용 테이블 생성
echo 1 | sudo -S nft add table inet whitelist
echo 1 | sudo -S nft add chain inet whitelist input \
  '{ type filter hook input priority 0; policy drop; }'
echo 1 | sudo -S nft add chain inet whitelist forward \
  '{ type filter hook forward priority 0; policy drop; }'
echo 1 | sudo -S nft add chain inet whitelist output \
  '{ type filter hook output priority 0; policy accept; }'
```

> **주의**: policy drop 설정 시 SSH 연결이 끊길 수 있다. 반드시 SSH 허용 룰을 먼저 추가하라.

```bash
# 1. conntrack
echo 1 | sudo -S nft add rule inet whitelist input ct state established,related accept
echo 1 | sudo -S nft add rule inet whitelist input ct state invalid drop

# 2. 루프백
echo 1 | sudo -S nft add rule inet whitelist input iif lo accept

# 3. SSH — 전체 허용 (실습 환경)
echo 1 | sudo -S nft add rule inet whitelist input tcp dport 22 accept

# 4. ICMP
echo 1 | sudo -S nft add rule inet whitelist input icmp type echo-request accept
echo 1 | sudo -S nft add rule inet whitelist input icmpv6 type { echo-request, nd-neighbor-solicit, nd-router-advert, nd-neighbor-advert } accept

# 5. 내부 네트워크에서만 8000번(Manager API) 접근 허용
echo 1 | sudo -S nft add rule inet whitelist input ip saddr 10.20.30.0/24 tcp dport 8000 accept
```

### 5.3 테스트

```bash
# 허용: SSH (이미 접속 중이므로 유지됨)
# 허용: ping
ping -c 1 10.20.30.1

# 차단 확인: 허용되지 않은 포트
nc -zv -w 2 10.20.30.1 9999
```

**예상 출력 (nc):**
```
10.20.30.1: inverse host lookup failed: Unknown host
(UNKNOWN) [10.20.30.1] 9999 (?) : Connection timed out
```

---

## 6. nftables 로깅

### 6.1 기본 로깅

```bash
# 차단되는 패킷 로깅 (policy drop 전에)
echo 1 | sudo -S nft add rule inet whitelist input log prefix \"[NFT-DROP] \" level warn
```

> **주의**: 위 룰은 마지막 drop 정책 전에 모든 패킷을 로깅한다. 많은 트래픽 환경에서는 조건부 로깅이 필요하다.

### 6.2 조건부 로깅

```bash
# SSH 브루트포스 시도 로깅 (새 연결만)
echo 1 | sudo -S nft insert rule inet whitelist input \
  tcp dport 22 ct state new log prefix \"[NFT-SSH-NEW] \" level info
```

### 6.3 로그 확인

```bash
# 실시간 로그 확인
echo 1 | sudo -S journalctl -k -f --grep="NFT-"
```

**예상 출력 (다른 터미널에서 차단되는 접근 시도 시):**
```
Mar 27 10:15:32 secu kernel: [NFT-DROP] IN=eth1 OUT= MAC=... SRC=10.20.30.80 DST=10.20.30.1 ...
```

### 6.4 Rate Limiting 로그

로그 폭주를 방지하기 위해 속도 제한을 건다:

```bash
# 초당 최대 5개까지만 로깅
echo 1 | sudo -S nft add rule inet whitelist input \
  limit rate 5/second log prefix \"[NFT-RATE] \" level warn
```

---

## 7. 룰셋 저장과 복원

### 7.1 현재 룰셋 파일로 저장

```bash
echo 1 | sudo -S nft list ruleset > /tmp/nftables-backup.conf
cat /tmp/nftables-backup.conf
```

### 7.2 룰셋 파일에서 복원

```bash
# 기존 룰 전부 삭제 후 복원
echo 1 | sudo -S nft flush ruleset
echo 1 | sudo -S nft -f /tmp/nftables-backup.conf
```

### 7.3 영구 저장 (부팅 시 자동 로드)

```bash
# 시스템 설정 파일로 저장
echo 1 | sudo -S nft list ruleset | sudo tee /etc/nftables.conf > /dev/null

# nftables 서비스 활성화
echo 1 | sudo -S systemctl enable nftables
echo 1 | sudo -S systemctl status nftables
```

**예상 출력:**
```
● nftables.service - nftables
     Loaded: loaded (/lib/systemd/system/nftables.service; enabled; ...)
     Active: active (exited) ...
```

### 7.4 룰셋 파일 문법

nftables 설정 파일은 스크립트 형식으로 작성할 수도 있다:

```bash
cat << 'NFTEOF' > /tmp/lab-firewall.conf
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        ct state established,related accept
        ct state invalid drop
        iif lo accept
        tcp dport 22 accept
        icmp type echo-request accept
        ip saddr 10.20.30.0/24 tcp dport { 80, 443, 8000 } accept

        log prefix "[NFT-DROP] " level warn
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
        ct state established,related accept
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
NFTEOF

# 문법 검사 (적용하지 않고 확인만)
echo 1 | sudo -S nft -c -f /tmp/lab-firewall.conf
```

**예상 출력 (문법 정상 시):**
```
(출력 없음 = 정상)
```

---

## 8. 유용한 nftables 기능

### 8.1 Named Set (이름 있는 집합)

자주 사용하는 IP나 포트를 집합으로 관리:

```bash
echo 1 | sudo -S nft add table inet lab_set
echo 1 | sudo -S nft add chain inet lab_set input \
  '{ type filter hook input priority 10; policy accept; }'

# 관리자 IP 집합 생성
echo 1 | sudo -S nft add set inet lab_set admin_ips '{ type ipv4_addr; }'
echo 1 | sudo -S nft add element inet lab_set admin_ips '{ 10.20.30.80, 10.20.30.100 }'

# 집합을 사용하는 룰
echo 1 | sudo -S nft add rule inet lab_set input ip saddr @admin_ips tcp dport 22 accept
```

### 8.2 Counter (카운터)

룰 매칭 횟수와 바이트 수를 추적:

```bash
echo 1 | sudo -S nft add rule inet lab_set input tcp dport 22 counter accept
```

**확인:**
```bash
echo 1 | sudo -S nft list chain inet lab_set input
```

**예상 출력:**
```
tcp dport 22 counter packets 15 bytes 1240 accept
```

---

## 9. 실습 과제

### 과제 1: 완전한 게이트웨이 방화벽 구성

secu 서버를 게이트웨이로 구성하라:

1. 기본 정책: input=drop, forward=drop, output=accept
2. SSH(22), ICMP 허용
3. 내부(10.20.30.0/24)에서 외부로의 forward 허용
4. NAT(masquerade) 구성
5. 외부에서 8080 포트 → web 서버(10.20.30.80:80) 포트 포워딩

### 과제 2: 룰셋 파일 작성

위 과제의 설정을 `/tmp/gateway-firewall.conf` 파일로 작성하고, 문법 검사를 통과시켜라.

### 과제 3: 정리

```bash
echo 1 | sudo -S nft delete table inet lab_nat 2>/dev/null
echo 1 | sudo -S nft delete table inet whitelist 2>/dev/null
echo 1 | sudo -S nft delete table inet lab_set 2>/dev/null
```

---

## 10. 핵심 정리

| 개념 | 설명 |
|------|------|
| SNAT/Masquerade | 출발지 IP 변환 (내부 → 외부) |
| DNAT | 목적지 IP 변환 (포트 포워딩) |
| policy drop | 화이트리스트 정책의 핵심 |
| log prefix | 패킷 로깅 (prefix로 구분) |
| limit rate | 로그 폭주 방지 |
| `nft list ruleset` | 전체 룰 백업 |
| `nft -f` | 파일에서 룰 복원 |
| `nft -c -f` | 문법 검사 (적용 없이) |
| Named Set | IP/포트 집합 관리 |
| counter | 매칭 통계 추적 |

---

## 다음 주 예고

Week 04에서는 Suricata IPS의 설치와 구성을 다룬다:
- IDS vs IPS 개념
- NFQUEUE 모드
- YAML 설정
- 룰 소스 관리
