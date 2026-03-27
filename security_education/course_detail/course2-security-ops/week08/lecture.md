# Week 08: 중간고사 — 방화벽 + IPS 구성 실기 (상세 버전)

## 학습 목표


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

# Week 08: 중간고사 — 방화벽 + IPS 구성 실기

## 시험 개요

- **유형**: 실기 시험 (hands-on practical exam)
- **시간**: 90분
- **범위**: Week 02~07 (nftables, Suricata IPS, Apache+ModSecurity WAF)
- **환경**: secu(10.20.30.1), web(10.20.30.80)
- **배점**: 총 100점

---

## 시험 환경 접속 정보

| 서버 | IP | 역할 | 접속 |
|------|-----|------|------|
| secu | 10.20.30.1 | 방화벽 + IPS | `sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1` |
| web | 10.20.30.80 | WAF + 웹 앱 | `sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80` |

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
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1

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
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1

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

1. (3점) nftables, Suricata IPS, Apache+ModSecurity WAF 각각의 역할과 보호 범위를 설명하라
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
- Apache+ModSecurity WAF: L7 웹 방화벽. HTTP 요청/응답을 파싱하여
  SQL Injection, XSS 등 웹 공격을 차단.

2. 트래픽 경로
  외부 → nftables(L3/L4 필터링) → Suricata IPS(페이로드 검사)
  → Apache+ModSecurity WAF(HTTP 검사) → 백엔드 웹 앱(JuiceShop)

3. SQL Injection 처리
- nftables: 80/tcp 포트만 허용하므로, HTTP를 통한 접근은 통과됨.
  nftables는 페이로드를 검사하지 않으므로 SQL Injection 자체는 탐지 불가.
- Suricata IPS: HTTP URI에서 "union select", "OR 1=1" 등
  SQL Injection 패턴을 content 매칭으로 탐지. alert 또는 drop.
- Apache+ModSecurity WAF: ModSecurity CRS 942xxx 룰이 HTTP 파라미터를
  파싱하여 SQL 구문을 탐지. Anomaly Score 5점 이상이면 403 차단.
EOF
```

### 문제 3-2: 트러블슈팅 (15점)

다음 상황을 해결하라:

**상황**: web 서버(10.20.30.80)의 HTTP 서비스에 접근이 안 된다.

**진단 절차 (각 5점):**

1. nftables에서 80번 포트가 허용되어 있는지 확인
2. Suricata가 정상 동작 중인지 확인 (패킷 드롭 없는지)
3. Apache+ModSecurity이 정상 동작 중인지 확인

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

# 3. Apache+ModSecurity 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no web@10.20.30.80
systemctl is-active apache2
echo 1 | sudo -S apache2ctl -M 2>/dev/null | grep security
# security2_module이 로드되어 있으면 ModSecurity 정상
# WAF 테스트: curl -s -o /dev/null -w "%{http_code}" "http://10.20.30.80:8082/?id=1'+OR+1=1--"
# 403이면 WAF 정상 동작
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
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1
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


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 08: 중간고사 — 방화벽 + IPS 구성 실기"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안 솔루션 운영의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "시험 개요"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "시험 환경 접속 정보"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안 솔루션 운영 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "Part 1: nftables 방화벽 구성 (40점)"의 실무 활용 방안은?
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
---

> **실습 환경 검증:** 이 교안의 실습 명령은 실제 인프라(10.20.30.0/24)에서 동작을 확인하였습니다. (2026-03-28 검증)
