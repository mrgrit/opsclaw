# Week 02: nftables 방화벽 (1) — 기초 (상세 버전)

## 학습 목표
- nftables의 기본 구조(Table, Chain, Rule)를 이해한다
- inet filter 테이블과 INPUT/FORWARD/OUTPUT 체인의 역할을 구분한다
- 실습 서버에서 방화벽 룰을 조회, 추가, 삭제할 수 있다
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


# 본 강의 내용

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


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 2)

이 주차에서 다루는 기술의 동작 방식을 단계별로 분해하여 이해한다.

```
[1단계] 입력/요청 → 시스템이 데이터를 수신
[2단계] 처리 → 내부 로직에 의한 데이터 처리
[3단계] 출력/응답 → 결과 반환 또는 상태 변경
[4단계] 기록 → 로그/증적 생성
```

> **왜 이 순서가 중요한가?**
> 각 단계에서 보안 검증이 누락되면 취약점이 발생한다.
> 1단계: 입력값 검증 미흡 → Injection
> 2단계: 인가 확인 누락 → Broken Access Control
> 3단계: 에러 정보 노출 → Information Disclosure
> 4단계: 로깅 실패 → Monitoring Failures

#### 개념 2: 보안 관점에서의 위험 분석

| 위험 요소 | 발생 조건 | 영향도 | 대응 방안 |
|----------|---------|--------|---------|
| 설정 미흡 | 기본 설정 사용 | 높음 | 보안 하드닝 가이드 적용 |
| 패치 누락 | 업데이트 미적용 | 높음 | 정기 패치 관리 프로세스 |
| 접근 제어 부재 | 인증/인가 미구현 | 매우 높음 | RBAC, MFA 적용 |
| 로깅 미흡 | 감사 로그 미수집 | 중간 | SIEM 연동, 로그 정책 |

#### 개념 3: 실제 사례 분석

**사례 1: 유사 취약점이 실제 피해로 이어진 경우**

실제 보안 사고에서 이 주차의 주제가 어떻게 악용되었는지 살펴본다.
공격자는 동일한 기법을 사용하여 대규모 데이터 유출, 서비스 장애, 금전적 피해를 초래하였다.

**교훈:**
- 기본적인 보안 조치의 중요성
- 탐지 체계의 필수성
- 사고 대응 절차의 사전 수립 필요성

### 도구 비교표

| 도구 | 용도 | 장점 | 단점 | 라이선스 |
|------|------|------|------|---------|
| 도구 A | 기본 점검 | 간편, 빠름 | 기능 제한 | 오픈소스 |
| 도구 B | 심층 분석 | 상세 결과 | 학습 곡선 | 상용/무료 |
| 도구 C | 자동화 | CI/CD 연동 | 오탐 가능 | 오픈소스 |


---

## 보충 실습

### 보충 실습 1: 기본 동작 확인

이론에서 배운 내용을 직접 확인하는 기초 실습이다.

```bash
# Step 1: 현재 상태 확인
echo "=== 현재 상태 ==="
# (해당 주차에 맞는 확인 명령)

# Step 2: 설정/변경 적용
echo "=== 변경 적용 ==="
# (해당 주차에 맞는 실습 명령)

# Step 3: 결과 검증
echo "=== 결과 확인 ==="
# (변경 결과 확인 명령)
```

> **트러블슈팅:**
> - 명령이 실패하면: 권한(sudo), 경로, 서비스 상태를 먼저 확인
> - 예상과 다른 결과: 이전 실습의 설정이 남아있을 수 있으므로 초기화 후 재시도
> - 타임아웃: 네트워크 연결 또는 서비스 가동 상태 확인

### 보충 실습 2: 탐지/모니터링 관점

공격자가 아닌 **방어자 관점**에서 동일한 활동을 모니터링하는 실습이다.

```bash
# siem 서버에서 관련 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 \
  "sudo cat /var/ossec/logs/alerts/alerts.json | tail -5" 2>/dev/null

# Suricata 알림 확인 (해당 시)
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1 \
  "sudo tail -20 /var/log/suricata/fast.log" 2>/dev/null
```

> **왜 방어자 관점도 배우는가?**
> 공격 기법만 알면 "스크립트 키디"에 불과하다.
> 공격이 어떻게 탐지되는지 이해해야 진정한 보안 전문가이다.
> 이 과목의 모든 공격 실습에는 대응하는 탐지/방어 관점이 포함된다.

### 보충 실습 3: OpsClaw 자동화

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화한다.

```bash
# 프로젝트 생성 (이번 주차용)
RESULT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"weekXX-lab","request_text":"이번 주차 실습 자동화","master_mode":"external"}')
PID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 실습 태스크 실행 (해당 주차에 맞게 수정)
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1,"title":"실습 태스크 1","instruction_prompt":"echo 실습1","risk_level":"low","subagent_url":"http://localhost:8002"},
      {"order":2,"title":"실습 태스크 2","instruction_prompt":"echo 실습2","risk_level":"low","subagent_url":"http://10.20.30.80:8002"}
    ],
    "subagent_url":"http://localhost:8002",
    "parallel":true
  }'

# Evidence 확인
curl -s "http://localhost:8000/projects/$PID/evidence/summary" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 02: nftables 방화벽 (1) — 기초"의 핵심 목적은 무엇인가?
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

### 과제 1: 이론 정리 보고서 (30점)

이번 주차의 핵심 개념을 자신의 말로 정리하라.

| 항목 | 배점 |
|------|------|
| 핵심 개념 정의 및 설명 | 10점 |
| 실습 결과 캡처 및 해석 | 10점 |
| 보안 관점 분석 (공격↔방어) | 10점 |

### 과제 2: 실습 수행 보고서 (40점)

이번 주차의 모든 실습을 수행하고 결과를 보고서로 작성하라.

| 항목 | 배점 |
|------|------|
| 실습 명령어 및 실행 결과 캡처 | 15점 |
| 결과 해석 및 보안 의미 분석 | 15점 |
| 트러블슈팅 경험 (있는 경우) | 10점 |

### 과제 3: OpsClaw 자동화 (30점)

이번 주차의 핵심 실습을 OpsClaw execute-plan으로 자동화하라.

| 항목 | 배점 |
|------|------|
| 프로젝트 생성 + stage 전환 | 5점 |
| execute-plan 태스크 설계 (3개 이상) | 10점 |
| evidence/summary 결과 | 5점 |
| replay 타임라인 결과 | 5점 |
| 자동화의 이점 분석 (직접 실행 대비) | 5점 |

**제출:** 보고서(PDF 또는 MD) + OpsClaw project_id


---

## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:

- [ ] 이론 강의 내용 이해 (핵심 용어 설명 가능)
- [ ] 기본 실습 모두 수행 완료
- [ ] 보충 실습 1 (기본 동작 확인) 완료
- [ ] 보충 실습 2 (탐지/모니터링 관점) 수행
- [ ] 보충 실습 3 (OpsClaw 자동화) 수행
- [ ] 자가 점검 퀴즈 8/10 이상 정답
- [ ] 과제 1 (이론 정리) 작성
- [ ] 과제 2 (실습 보고서) 작성
- [ ] 과제 3 (OpsClaw 자동화) 완료

