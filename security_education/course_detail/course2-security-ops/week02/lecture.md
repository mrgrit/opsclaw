# Week 02: nftables 방화벽 (1) — 기초 (상세 버전)

## 학습 목표
- nftables의 기본 구조(Table, Chain, Rule)를 이해한다
- inet filter 테이블과 INPUT/FORWARD/OUTPUT 체인의 역할을 구분한다
- 실습 서버에서 방화벽 룰을 조회, 추가, 삭제할 수 있다


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
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1
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
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80

# ping 테스트 (허용되어야 함)
ping -c 2 10.20.30.1

# SSH 테스트 (허용되어야 함)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 hostname

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


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 02: nftables 방화벽 (1) — 기초"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안 솔루션 운영의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. 방화벽이란?"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. nftables 기본 구조"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안 솔루션 운영 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. 실습 환경 접속"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 올바른 설정의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 보안 솔루션 운영 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---

## 과제 (다음 주까지)


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


