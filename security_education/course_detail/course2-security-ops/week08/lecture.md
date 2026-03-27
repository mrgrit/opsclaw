# Week 08: 중간고사 — 방화벽 + IPS 구성 실기 (상세 버전)

## 학습 목표

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

# Week 08: 중간고사 — 방화벽 + IPS 구성 실기

## 시험 개요

- **유형**: 실기 시험 (hands-on practical exam)
- **시간**: 90분
- **범위**: Week 02~07 (nftables, Suricata IPS, BunkerWeb WAF)
- **환경**: secu(10.20.30.1), web(10.20.30.80)
- **배점**: 총 100점

---

## 시험 환경 접속 정보

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| secu | 10.20.30.1 | 방화벽 + IPS | `sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1` |
| web | 10.20.30.80 | WAF + 웹 앱 | `sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80` |

---

## Part 1: nftables 방화벽 구성 (40점)

### 문제 1-1: 기본 방화벽 구성 (20점)

secu 서버에 다음 조건의 방화벽을 구성하라.

**테이블 이름**: `inet exam_filter`

**요구사항:**

1. (4점) 기본 정책: INPUT=drop, FORWARD=drop, OUTPUT=accept
2. (4점) 수립된 연결(established, related) 허용, invalid 패킷 차단
3. (2점) 루프백 인터페이스(lo) 허용
4. (4점) 허용 서비스:
   - SSH (22/tcp)
   - HTTP (80/tcp)
   - HTTPS (443/tcp)
   - ICMP ping
5. (3점) 내부 네트워크(10.20.30.0/24)에서만 8000/tcp 허용
6. (3점) 차단되는 패킷에 `[EXAM-DROP]` prefix로 로깅

**정답 예시:**

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1

# 테이블 및 체인 생성
echo 1 | sudo -S nft add table inet exam_filter

echo 1 | sudo -S nft add chain inet exam_filter input \
  '{ type filter hook input priority 0; policy drop; }'
echo 1 | sudo -S nft add chain inet exam_filter forward \
  '{ type filter hook forward priority 0; policy drop; }'
echo 1 | sudo -S nft add chain inet exam_filter output \
  '{ type filter hook output priority 0; policy accept; }'

# conntrack
echo 1 | sudo -S nft add rule inet exam_filter input ct state established,related accept
echo 1 | sudo -S nft add rule inet exam_filter input ct state invalid drop

# 루프백
echo 1 | sudo -S nft add rule inet exam_filter input iif lo accept

# 허용 서비스
echo 1 | sudo -S nft add rule inet exam_filter input tcp dport 22 accept
echo 1 | sudo -S nft add rule inet exam_filter input tcp dport { 80, 443 } accept
echo 1 | sudo -S nft add rule inet exam_filter input icmp type echo-request accept

# 내부 네트워크에서만 8000
echo 1 | sudo -S nft add rule inet exam_filter input \
  ip saddr 10.20.30.0/24 tcp dport 8000 accept

# 차단 로깅
echo 1 | sudo -S nft add rule inet exam_filter input \
  log prefix "[EXAM-DROP] " level warn
```

**검증:**

```bash
# 룰셋 확인
echo 1 | sudo -S nft list table inet exam_filter

# SSH 연결 유지 확인
echo "SSH OK"

# ping 테스트
ping -c 1 10.20.30.1
```

---

### 문제 1-2: NAT 및 포트 포워딩 (20점)

secu 서버에 다음 NAT 설정을 구성하라.

**테이블 이름**: `inet exam_nat`

**요구사항:**

1. (6점) 내부 네트워크(10.20.30.0/24) → 외부: masquerade
2. (8점) 외부에서 secu:8080 → web(10.20.30.80):80 포트 포워딩
3. (6점) forward 체인에서 포워딩 트래픽 허용:
   - 10.20.30.0/24에서 나가는 트래픽 허용
   - 수립된 연결의 응답 허용

**정답 예시:**

```bash
# NAT 테이블
echo 1 | sudo -S nft add table inet exam_nat

# prerouting (DNAT)
echo 1 | sudo -S nft add chain inet exam_nat prerouting \
  '{ type nat hook prerouting priority -100; policy accept; }'

# postrouting (SNAT)
echo 1 | sudo -S nft add chain inet exam_nat postrouting \
  '{ type nat hook postrouting priority 100; policy accept; }'

# masquerade
echo 1 | sudo -S nft add rule inet exam_nat postrouting \
  ip saddr 10.20.30.0/24 masquerade

# 포트 포워딩
echo 1 | sudo -S nft add rule inet exam_nat prerouting \
  tcp dport 8080 dnat to 10.20.30.80:80

# forward 허용 (exam_filter 테이블에 추가)
echo 1 | sudo -S nft add rule inet exam_filter forward \
  ct state established,related accept
echo 1 | sudo -S nft add rule inet exam_filter forward \
  ip saddr 10.20.30.0/24 accept

# IP 포워딩 활성화
echo 1 | sudo -S sysctl -w net.ipv4.ip_forward=1
```

---

## Part 2: Suricata IPS 룰 (35점)

### 문제 2-1: 탐지 룰 작성 (20점)

`/etc/suricata/rules/local.rules`에 다음 공격을 탐지하는 룰을 작성하라.

1. (5점) HTTP URI에서 `../` 패턴 탐지 (디렉터리 트래버설)
2. (5점) HTTP URI에서 `<script` 패턴 탐지 (XSS)
3. (5점) HTTP User-Agent에 `nikto` 또는 `sqlmap` 포함 시 탐지
4. (5점) SSH(22번 포트)에 60초 내 10회 이상 연결 시도 탐지

**정답 예시:**

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1

echo 1 | sudo -S tee /etc/suricata/rules/local.rules << 'EOF'
# 1. 디렉터리 트래버설
alert http $HOME_NET any -> any any (msg:"EXAM - Directory Traversal"; flow:to_server,established; http.uri; content:"../"; classtype:web-application-attack; sid:9100001; rev:1;)

# 2. XSS
alert http $HOME_NET any -> any any (msg:"EXAM - XSS script tag"; flow:to_server,established; http.uri; content:"<script"; nocase; classtype:web-application-attack; sid:9100002; rev:1;)

# 3. 스캐너 탐지
alert http any any -> $HOME_NET any (msg:"EXAM - Scanner detected (nikto)"; flow:to_server,established; http.user_agent; content:"nikto"; nocase; classtype:web-application-attack; sid:9100003; rev:1;)
alert http any any -> $HOME_NET any (msg:"EXAM - Scanner detected (sqlmap)"; flow:to_server,established; http.user_agent; content:"sqlmap"; nocase; classtype:web-application-attack; sid:9100004; rev:1;)

# 4. SSH 브루트포스
alert tcp any any -> $HOME_NET 22 (msg:"EXAM - SSH brute force"; flow:to_server; flags:S; threshold:type threshold, track by_src, count 10, seconds 60; classtype:attempted-admin; sid:9100005; rev:1;)
EOF
```

### 문제 2-2: 룰 검증 및 테스트 (15점)

1. (3점) `suricata -T`로 설정 검증 통과
2. (4점) 룰 리로드 실행
3. (8점) 각 룰별 테스트 트래픽을 생성하고 탐지 결과를 확인

**정답 예시:**

```bash
# 검증
echo 1 | sudo -S suricata -T -c /etc/suricata/suricata.yaml

# 리로드
echo 1 | sudo -S kill -USR2 $(pidof suricata)
sleep 3

# 테스트
curl -s "http://10.20.30.80/../../etc/passwd" > /dev/null
curl -s "http://10.20.30.80/?q=%3Cscript%3Ealert(1)%3C/script%3E" > /dev/null
curl -s -A "nikto/2.1.6" "http://10.20.30.80/" > /dev/null
curl -s -A "sqlmap/1.0" "http://10.20.30.80/" > /dev/null

# 결과 확인
echo 1 | sudo -S tail -10 /var/log/suricata/fast.log
```

---

## Part 3: 종합 문제 (25점)

### 문제 3-1: 보안 아키텍처 서술 (10점)

다음 질문에 답하라 (텍스트 파일 작성):

1. (3점) nftables, Suricata IPS, BunkerWeb WAF 각각의 역할과 보호 범위를 설명하라
2. (3점) 패킷이 외부에서 web 서버에 도달하기까지 거치는 보안 장비의 순서를 설명하라
3. (4점) SQL Injection 공격이 각 보안 장비에서 어떻게 처리되는지 설명하라

**정답 예시:**

```bash
cat << 'EOF' > /tmp/exam_answer.txt
1. 역할과 보호 범위
- nftables: L3/L4 방화벽. IP, 포트 기반으로 접근 제어.
  허용된 IP/포트만 통과시키고 나머지 차단.
- Suricata IPS: L3~L7 침입방지. 패킷 내용(페이로드)을 검사하여
  알려진 공격 패턴을 탐지/차단. NFQUEUE 모드로 인라인 동작.
- BunkerWeb WAF: L7 웹 방화벽. HTTP 요청/응답을 파싱하여
  SQL Injection, XSS 등 웹 공격을 차단.

2. 트래픽 경로
  외부 → nftables(L3/L4 필터링) → Suricata IPS(페이로드 검사)
  → BunkerWeb WAF(HTTP 검사) → 백엔드 웹 앱(JuiceShop)

3. SQL Injection 처리
- nftables: 80/tcp 포트만 허용하므로, HTTP를 통한 접근은 통과됨.
  nftables는 페이로드를 검사하지 않으므로 SQL Injection 자체는 탐지 불가.
- Suricata IPS: HTTP URI에서 "union select", "OR 1=1" 등
  SQL Injection 패턴을 content 매칭으로 탐지. alert 또는 drop.
- BunkerWeb WAF: ModSecurity CRS 942xxx 룰이 HTTP 파라미터를
  파싱하여 SQL 구문을 탐지. Anomaly Score 5점 이상이면 403 차단.
EOF
```

### 문제 3-2: 트러블슈팅 (15점)

다음 상황을 해결하라:

**상황**: web 서버(10.20.30.80)의 HTTP 서비스에 접근이 안 된다.

**진단 절차 (각 5점):**

1. nftables에서 80번 포트가 허용되어 있는지 확인
2. Suricata가 정상 동작 중인지 확인 (패킷 드롭 없는지)
3. BunkerWeb이 정상 동작 중인지 확인

**정답 예시:**

```bash
# 1. nftables 확인
echo 1 | sudo -S nft list ruleset | grep "dport 80"
# 출력이 없으면 → 80 포트 허용 룰 추가 필요

# 2. Suricata 확인
echo 1 | sudo -S systemctl is-active suricata
echo 1 | sudo -S grep "kernel_drops" /var/log/suricata/stats.log | tail -1
# drops이 급증하면 → Suricata 성능 문제
# fail-open이 아니면 → Suricata 정지 시 트래픽 차단

# 3. BunkerWeb 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.80
echo 1 | sudo -S docker ps | grep bunkerweb
echo 1 | sudo -S docker logs bunkerweb --tail 20
# 컨테이너가 멈춰있으면 → docker restart bunkerweb
```

---

## 채점 기준 요약

| 영역 | 배점 | 핵심 체크포인트 |
|------|------|-----------------|
| 기본 방화벽 | 20점 | policy drop, conntrack, 서비스별 허용, 로깅 |
| NAT/포워딩 | 20점 | masquerade, DNAT, forward 허용, ip_forward |
| Suricata 룰 | 20점 | 올바른 문법, content/flow/threshold, sid 고유 |
| 룰 테스트 | 15점 | 검증 통과, 리로드, 테스트 결과 |
| 서술형 | 10점 | 정확한 역할 구분, 트래픽 흐름 이해 |
| 트러블슈팅 | 15점 | 체계적 진단, 해결 방안 |

---

## 시험 종료 후 정리

```bash
# 시험 설정 제거
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1
echo 1 | sudo -S nft delete table inet exam_filter 2>/dev/null
echo 1 | sudo -S nft delete table inet exam_nat 2>/dev/null
echo 1 | sudo -S sed -i '/EXAM/d' /etc/suricata/rules/local.rules 2>/dev/null
echo 1 | sudo -S kill -USR2 $(pidof suricata) 2>/dev/null
```

---

## 참고: 자주 하는 실수

| 실수 | 결과 | 해결 |
|------|------|------|
| SSH 허용 전 policy drop | SSH 연결 끊김 | 콘솔 접속하여 복구 |
| conntrack 미설정 | 기존 연결 끊김 | 첫 번째 룰로 conntrack 추가 |
| Suricata sid 중복 | 룰 로드 실패 | 고유한 sid 부여 |
| ip_forward 미활성화 | NAT 미동작 | sysctl 설정 |
| 룰 리로드 안 함 | 새 룰 미적용 | kill -USR2 실행 |


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

**Q1.** 이번 주차 "Week 08: 중간고사 — 방화벽 + IPS 구성 실기"의 핵심 목적은 무엇인가?
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

