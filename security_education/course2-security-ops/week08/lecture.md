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
