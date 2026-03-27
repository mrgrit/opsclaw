# Week 03: nftables 방화벽 (2) — 실전 (상세 버전)

## 학습 목표
- NAT(SNAT/DNAT)와 포트 포워딩을 구성할 수 있다
- 화이트리스트(기본 차단) 정책을 설계할 수 있다
- nftables 로깅 기능을 활용할 수 있다
- 룰셋을 파일로 저장하고 복원할 수 있다
- 각 개념의 보안 관점에서의 위험과 대응 방안을 분석할 수 있다
- OpsClaw를 활용하여 실습 작업을 자동화하고 증적을 관리할 수 있다
- 실제 보안 사고 사례와 연결하여 학습 내용을 적용할 수 있다


## 실습 환경 (공통)

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| opsclaw | 10.20.30.201 | Control Plane (OpsClaw) | `ssh opsclaw@10.20.30.201` (pw: 1) |
| secu | 10.20.30.1 | 방화벽/IPS (nftables, Suricata) | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 웹서버 (JuiceShop:3000, Apache:80) | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM (Wazuh:443, OpenCTI:9400) | `sshpass -p1 ssh siem@10.20.30.100` |
| dgx-spark | 192.168.0.105 | AI/GPU (Ollama:11434) | 원격 API만 |

**OpsClaw API:** `http://localhost:8000` / Key: `opsclaw-api-key-2026`


## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:40 | 이론 강의 (Part 1) | 강의 |
| 0:40-1:10 | 이론 심화 + 사례 분석 (Part 2) | 강의/토론 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | 실습 (Part 3) | 실습 |
| 2:00-2:40 | 심화 실습 + 도구 활용 (Part 4) | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:20 | 응용 실습 + OpsClaw 연동 (Part 5) | 실습 |
| 3:20-3:40 | 복습 퀴즈 + 과제 안내 (Part 6) | 퀴즈 |

---


---

## 용어 해설 (보안 솔루션 운영 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **방화벽** | Firewall | 네트워크 트래픽을 규칙에 따라 허용/차단하는 시스템 | 건물 출입 통제 시스템 |
| **체인** | Chain (nftables) | 패킷 처리 규칙의 묶음 (input, forward, output) | 심사 단계 |
| **룰/규칙** | Rule | 특정 조건의 트래픽을 어떻게 처리할지 정의 | "택배 기사만 출입 허용" |
| **시그니처** | Signature | 알려진 공격 패턴을 식별하는 규칙 (IPS/AV) | 수배범 얼굴 사진 |
| **NFQUEUE** | Netfilter Queue | 커널에서 사용자 영역으로 패킷을 넘기는 큐 | 의심 택배를 별도 검사대로 보내는 것 |
| **FIM** | File Integrity Monitoring | 파일 변조 감시 (해시 비교) | CCTV로 금고 감시 |
| **SCA** | Security Configuration Assessment | 보안 설정 점검 (CIS 벤치마크 기반) | 건물 안전 점검표 |
| **Active Response** | Active Response | 탐지 시 자동 대응 (IP 차단 등) | 침입 감지 시 자동 잠금 |
| **디코더** | Decoder (Wazuh) | 로그를 파싱하여 구조화하는 규칙 | 외국어 통역사 |
| **CRS** | Core Rule Set (ModSecurity) | 범용 웹 공격 탐지 규칙 모음 | 표준 보안 검사 매뉴얼 |
| **CTI** | Cyber Threat Intelligence | 사이버 위협 정보 (IOC, TTPs) | 범죄 정보 공유 시스템 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 해시, 도메인 등) | 수배범의 지문, 차량번호 |
| **STIX** | Structured Threat Information eXpression | 위협 정보 표준 포맷 | 범죄 보고서 표준 양식 |
| **TAXII** | Trusted Automated eXchange of Intelligence Information | CTI 자동 교환 프로토콜 | 경찰서 간 수배 정보 공유 시스템 |
| **NAT** | Network Address Translation | 내부 IP를 외부 IP로 변환 | 회사 대표번호 (내선→외선) |
| **masquerade** | masquerade (nftables) | 나가는 패킷의 소스 IP를 게이트웨이 IP로 변환 | 회사 이름으로 편지 보내기 |


---

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


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 03: nftables 방화벽 (2) — 실전"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **보안 솔루션 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 방화벽/IPS의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **SIEM 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

**Q4.** OpsClaw를 통해 실습을 실행하는 가장 큰 이점은?
- (a) 속도  (b) **모든 실행의 자동 증적(evidence) 기록**  (c) 무료  (d) 간편함

**Q5.** 이 주제의 보안 위험이 높은 이유는?
- (a) 비용이 많이 들어서  (b) 복잡해서  (c) **악용 시 시스템/데이터에 직접적 피해**  (d) 법적 문제

**Q6.** 방어/대응의 핵심 원칙은?
- (a) 모든 트래픽 차단  (b) **최소 권한 + 탐지 + 대응의 조합**  (c) 서버 재시작  (d) 비밀번호 변경

**Q7.** 실습 결과를 분석할 때 가장 먼저 확인해야 하는 것은?
- (a) 서버 이름  (b) **exit_code (성공/실패 여부)**  (c) 파일 크기  (d) 날짜

**Q8.** 이 주제와 관련된 MITRE ATT&CK 전술은?
- (a) Impact만  (b) Reconnaissance만  (c) **주제에 해당하는 전술(들)**  (d) 해당 없음

**Q9.** 실무에서 이 기법/도구를 사용할 때 가장 주의할 점은?
- (a) 속도  (b) **법적 허가와 범위 준수**  (c) 비용  (d) 보고서 양식

**Q10.** 다음 주차와의 연결 포인트는?
- (a) 관련 없음  (b) **이번 주 결과를 다음 주에서 활용/심화**  (c) 완전히 다른 주제  (d) 복습만

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:c, Q6:b, Q7:b, Q8:c, Q9:b, Q10:b

---

## 과제 (다음 주까지)


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


