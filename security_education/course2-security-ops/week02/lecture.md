# Week 02: nftables 방화벽 (1) — 기초

## 학습 목표

- nftables의 기본 구조(Table, Chain, Rule)를 이해한다
- inet filter 테이블과 INPUT/FORWARD/OUTPUT 체인의 역할을 구분한다
- 실습 서버에서 방화벽 룰을 조회, 추가, 삭제할 수 있다

---

## 1. 방화벽이란?

방화벽(Firewall)은 네트워크 트래픽을 필터링하는 보안 장비(또는 소프트웨어)이다.
허용된 트래픽만 통과시키고, 나머지는 차단한다.

**리눅스 방화벽의 역사:**

| 도구 | 커널 버전 | 상태 |
|------|-----------|------|
| ipchains | 2.2 | 폐기 |
| iptables | 2.4~5.x | 레거시 (아직 많이 사용) |
| **nftables** | 3.13+ | **현재 표준** |

nftables는 iptables를 대체하는 리눅스 공식 패킷 필터링 프레임워크이다.

---

## 2. nftables 기본 구조

nftables는 3단계 계층 구조를 가진다:

```
Table (테이블)
 └── Chain (체인)
      └── Rule (룰)
```

### 2.1 Table (테이블)

테이블은 체인을 담는 컨테이너이다. **address family**를 지정한다:

| Family | 설명 |
|--------|------|
| `ip` | IPv4만 |
| `ip6` | IPv6만 |
| `inet` | IPv4 + IPv6 동시 처리 (**권장**) |
| `arp` | ARP |
| `bridge` | 브리지 |
| `netdev` | 네트워크 디바이스 레벨 |

### 2.2 Chain (체인)

체인은 룰을 담는 컨테이너이다. **base chain**은 hook point를 가진다:

| Hook | 설명 | 용도 |
|------|------|------|
| `input` | 이 서버로 들어오는 패킷 | 서비스 접근 제어 |
| `forward` | 이 서버를 경유하는 패킷 | 라우터/게이트웨이 |
| `output` | 이 서버에서 나가는 패킷 | 아웃바운드 제어 |

### 2.3 Rule (룰)

룰은 조건(match)과 동작(verdict)으로 구성된다:

| Verdict | 설명 |
|---------|------|
| `accept` | 허용 |
| `drop` | 조용히 차단 |
| `reject` | 거부 메시지와 함께 차단 |
| `log` | 로그 기록 |
| `counter` | 카운터 증가 |

---

## 3. 실습 환경 접속

실습 서버 `secu` (방화벽/IPS 서버)에 접속한다:

```bash
# 실습 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1
```

접속 후 nftables 버전을 확인한다:

```bash
echo 1 | sudo -S nft --version
```

**예상 출력:**
```
nftables v1.0.6 (Lester Gooch)
```

---

## 4. 현재 룰셋 조회

### 4.1 전체 룰셋 보기

```bash
echo 1 | sudo -S nft list ruleset
```

**예상 출력 (예시):**
```
table inet filter {
    chain input {
        type filter hook input priority 0; policy accept;
        ct state established,related accept
        iif "lo" accept
        tcp dport 22 accept
    }
    chain forward {
        type filter hook forward priority 0; policy accept;
    }
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

### 4.2 특정 테이블만 보기

```bash
echo 1 | sudo -S nft list table inet filter
```

### 4.3 특정 체인만 보기

```bash
echo 1 | sudo -S nft list chain inet filter input
```

---

## 5. 테이블 생성과 삭제

### 5.1 테이블 생성

```bash
# inet family 테이블 생성 (실습용)
echo 1 | sudo -S nft add table inet lab_filter
```

### 5.2 테이블 확인

```bash
echo 1 | sudo -S nft list tables
```

**예상 출력:**
```
table inet filter
table inet lab_filter
```

### 5.3 테이블 삭제

```bash
echo 1 | sudo -S nft delete table inet lab_filter
```

---

## 6. 체인 생성

base chain을 만들 때는 `type`, `hook`, `priority`, `policy`를 지정한다:

```bash
# 먼저 테이블 생성
echo 1 | sudo -S nft add table inet lab_filter

# input 체인 생성 (기본 정책: accept)
echo 1 | sudo -S nft add chain inet lab_filter input \
  '{ type filter hook input priority 0; policy accept; }'

# output 체인 생성
echo 1 | sudo -S nft add chain inet lab_filter output \
  '{ type filter hook output priority 0; policy accept; }'

# forward 체인 생성
echo 1 | sudo -S nft add chain inet lab_filter forward \
  '{ type filter hook forward priority 0; policy accept; }'
```

**확인:**
```bash
echo 1 | sudo -S nft list table inet lab_filter
```

**예상 출력:**
```
table inet lab_filter {
    chain input {
        type filter hook input priority filter; policy accept;
    }
    chain output {
        type filter hook output priority filter; policy accept;
    }
    chain forward {
        type filter hook forward priority filter; policy accept;
    }
}
```

---

## 7. 룰 추가

### 7.1 기본 문법

```
nft add rule <family> <table> <chain> <match> <verdict>
```

### 7.2 SSH 허용 룰

```bash
echo 1 | sudo -S nft add rule inet lab_filter input tcp dport 22 accept
```

### 7.3 ICMP(ping) 허용 룰

```bash
echo 1 | sudo -S nft add rule inet lab_filter input icmp type echo-request accept
```

### 7.4 특정 IP에서 오는 트래픽 차단

```bash
# 10.20.30.80(web 서버)에서 오는 트래픽 차단
echo 1 | sudo -S nft add rule inet lab_filter input ip saddr 10.20.30.80 drop
```

### 7.5 포트 범위 허용

```bash
# 8000~8100 포트 범위 허용
echo 1 | sudo -S nft add rule inet lab_filter input tcp dport 8000-8100 accept
```

### 7.6 룰 확인 (핸들 번호 포함)

```bash
echo 1 | sudo -S nft -a list chain inet lab_filter input
```

**예상 출력:**
```
table inet lab_filter {
    chain input {
        type filter hook input priority filter; policy accept;
        tcp dport 22 accept # handle 4
        icmp type echo-request accept # handle 5
        ip saddr 10.20.30.80 drop # handle 6
        tcp dport 8000-8100 accept # handle 7
    }
}
```

> **핵심**: `-a` 옵션으로 handle 번호를 확인한다. 삭제 시 필요하다.

---

## 8. 룰 삭제

handle 번호를 사용하여 특정 룰을 삭제한다:

```bash
# handle 6번 룰 삭제 (10.20.30.80 차단 룰)
echo 1 | sudo -S nft delete rule inet lab_filter input handle 6
```

**삭제 확인:**
```bash
echo 1 | sudo -S nft -a list chain inet lab_filter input
```

---

## 9. Connection Tracking (conntrack)

conntrack은 이미 수립된 연결의 패킷을 자동으로 허용하는 기능이다.
방화벽 룰 작성 시 가장 먼저 추가해야 한다:

```bash
# 이미 수립된/관련된 연결 허용
echo 1 | sudo -S nft add rule inet lab_filter input ct state established,related accept

# 잘못된(invalid) 패킷 차단
echo 1 | sudo -S nft add rule inet lab_filter input ct state invalid drop
```

**ct state 종류:**

| State | 설명 |
|-------|------|
| `new` | 새 연결의 첫 패킷 |
| `established` | 수립된 연결의 패킷 |
| `related` | 기존 연결과 관련된 새 연결 (예: FTP data) |
| `invalid` | 추적 불가능한 패킷 |

---

## 10. 실습 과제

### 과제 1: 기본 방화벽 구성

아래 조건을 만족하는 방화벽을 `inet lab_filter` 테이블에 구성하라:

1. 이미 수립된 연결은 허용 (`ct state established,related`)
2. 루프백 인터페이스(lo) 허용
3. SSH(22번 포트) 허용
4. ICMP ping 허용
5. HTTP(80번), HTTPS(443번) 허용
6. 나머지 전부 차단(drop)하려면 → policy를 drop으로 변경하지 말고, 마지막에 drop 룰 추가

```bash
# 1. conntrack
echo 1 | sudo -S nft add rule inet lab_filter input ct state established,related accept
echo 1 | sudo -S nft add rule inet lab_filter input ct state invalid drop

# 2. 루프백
echo 1 | sudo -S nft add rule inet lab_filter input iif lo accept

# 3. SSH
echo 1 | sudo -S nft add rule inet lab_filter input tcp dport 22 accept

# 4. ICMP
echo 1 | sudo -S nft add rule inet lab_filter input icmp type echo-request accept

# 5. HTTP/HTTPS
echo 1 | sudo -S nft add rule inet lab_filter input tcp dport { 80, 443 } accept

# 6. 나머지 차단
echo 1 | sudo -S nft add rule inet lab_filter input drop
```

### 과제 2: 테스트

web 서버에서 secu 서버로 접근 테스트:

```bash
# web 서버에 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80

# ping 테스트 (허용되어야 함)
ping -c 2 10.20.30.1

# SSH 테스트 (허용되어야 함)
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 hostname

# 차단된 포트 테스트 (연결 안 됨)
nc -zv 10.20.30.1 8888
```

### 과제 3: 정리

실습이 끝나면 테이블을 삭제한다:

```bash
echo 1 | sudo -S nft delete table inet lab_filter
```

---

## 11. 핵심 정리

| 개념 | 설명 |
|------|------|
| Table | 체인을 담는 컨테이너 (inet family 권장) |
| Chain | 룰을 담는 컨테이너 (hook point: input/forward/output) |
| Rule | 조건 + 동작 (accept/drop/reject) |
| conntrack | 수립된 연결 자동 허용 |
| handle | 룰의 고유 번호 (삭제 시 필요) |
| `nft list ruleset` | 전체 룰 조회 |
| `nft -a list` | handle 번호 포함 조회 |
| `nft add rule` | 룰 추가 (체인 끝에) |
| `nft delete rule` | handle로 룰 삭제 |

---

## 다음 주 예고

Week 03에서는 nftables의 실전 기능을 다룬다:
- NAT (Network Address Translation)
- 포트 포워딩
- 화이트리스트 정책
- 로깅
- 룰셋 저장/복원
