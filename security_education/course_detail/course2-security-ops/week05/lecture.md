# Week 05: Suricata IPS (2) — 룰 작성 (상세 버전)

## 학습 목표
- Suricata 룰의 전체 문법 구조를 이해한다
- alert/drop/reject 액션의 차이를 구분한다
- content, flow, pcre 등 핵심 키워드를 사용할 수 있다
- 커스텀 룰을 작성하고 테스트할 수 있다


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

# Week 05: Suricata IPS (2) — 룰 작성

## 학습 목표

- Suricata 룰의 전체 문법 구조를 이해한다
- alert/drop/reject 액션의 차이를 구분한다
- content, flow, pcre 등 핵심 키워드를 사용할 수 있다
- 커스텀 룰을 작성하고 테스트할 수 있다

---

## 1. 룰 문법 개요

Suricata 룰은 한 줄로 구성되며, **Header**와 **Options**로 나뉜다:

```
action protocol src_ip src_port -> dst_ip dst_port (options;)
```

**예시:**
```
alert http $HOME_NET any -> $EXTERNAL_NET any (msg:"Malware download"; content:"malware.exe"; sid:1000001; rev:1;)
```

| 부분 | 예시 값 | 설명 |
|------|---------|------|
| action | `alert` | 동작 (alert/drop/reject/pass) |
| protocol | `http` | 프로토콜 |
| src_ip | `$HOME_NET` | 출발지 IP |
| src_port | `any` | 출발지 포트 |
| direction | `->` | 방향 (-> 또는 <>) |
| dst_ip | `$EXTERNAL_NET` | 목적지 IP |
| dst_port | `any` | 목적지 포트 |
| options | `(msg:...; sid:...; )` | 탐지 조건과 메타데이터 |

---

## 2. Action (동작)

> **이 실습을 왜 하는가?**
> 보안 솔루션 운영 과목에서 이 주차의 실습은 핵심 개념을 **직접 체험**하여 이론을 실무로 연결하는 과정이다.
> 보안 엔지니어가 인프라를 구축/운영할 때 이 솔루션의 설정과 관리가 핵심 업무이다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이론에서 배운 개념이 실제 시스템에서 어떻게 동작하는지 확인
> - 실제 명령어와 도구 사용법을 체득
> - 결과를 분석하고 보안 관점에서 판단하는 능력 배양
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.


| Action | 설명 | IDS | IPS |
|--------|------|-----|-----|
| `alert` | 로그 기록 (경고) | O | O |
| `drop` | 패킷 차단 + 로그 | X | O |
| `reject` | RST/ICMP unreachable + 로그 | X | O |
| `pass` | 허용 (이후 룰 무시) | O | O |

> **IDS 모드**에서는 drop/reject가 alert처럼 동작한다 (차단 불가).

---

## 3. Protocol (프로토콜)

Suricata가 지원하는 프로토콜:

| 프로토콜 | 설명 |
|----------|------|
| `tcp` | TCP |
| `udp` | UDP |
| `icmp` | ICMP |
| `ip` | 모든 IP |
| `http` | HTTP (L7 파싱) |
| `tls` | TLS/SSL |
| `dns` | DNS |
| `ssh` | SSH |
| `ftp` | FTP |
| `smtp` | SMTP |

> `http`를 사용하면 Suricata가 HTTP를 파싱하여 URI, header 등을 개별 검사할 수 있다.

---

## 4. 실습 환경 접속

```bash
sshpass -p1 ssh -o StrictHostKeyChecking=no secu@10.20.30.1
```

룰 파일 위치 확인:

```bash
echo 1 | sudo -S cat /etc/suricata/rules/local.rules 2>/dev/null
```

---

## 5. 핵심 옵션 키워드

### 5.1 msg (메시지)

알림에 표시되는 설명:

```
msg:"SQL Injection attempt detected";
```

### 5.2 sid / rev (고유 ID / 리비전)

모든 룰에 필수. sid는 고유해야 한다:

```
sid:9000001; rev:1;
```

| sid 범위 | 용도 |
|----------|------|
| 1~999999 | Snort/ET 공식 룰 |
| 1000000~1999999 | ET Open |
| **9000000~** | **커스텀 룰 (실습용)** |

### 5.3 content (내용 매칭)

패킷 페이로드에서 문자열을 검색:

```
content:"admin"; nocase;          # 대소문자 무시
content:"|0d 0a|";                # 16진수 매칭
content:"GET"; offset:0; depth:3; # 처음 3바이트에서만 검색
```

**content 수정자:**

| 수정자 | 설명 |
|--------|------|
| `nocase` | 대소문자 무시 |
| `offset` | 검색 시작 위치 |
| `depth` | 검색 깊이 (offset부터) |
| `distance` | 이전 content 매칭 이후 거리 |
| `within` | distance 이후 검색 범위 |

### 5.4 flow (흐름)

연결 방향과 상태를 지정:

```
flow:to_server,established;   # 클라이언트 → 서버, 연결 수립됨
flow:to_client,established;   # 서버 → 클라이언트
flow:established;              # 양방향 수립된 연결
```

### 5.5 http 키워드

HTTP 프로토콜 파싱 활용:

```
http.method;          # GET, POST 등
http.uri;             # 요청 URI
http.host;            # Host 헤더
http.user_agent;      # User-Agent 헤더
http.request_body;    # POST 본문
http.stat_code;       # 응답 상태 코드
http.response_body;   # 응답 본문
```

### 5.6 pcre (정규표현식)

```
pcre:"/admin.*password/i";    # 정규식 매칭 (i: 대소문자 무시)
```

### 5.7 threshold (임계값)

```
threshold:type threshold, track by_src, count 10, seconds 60;
# 같은 출발지에서 60초 내 10회 이상 매칭 시 알림
```

### 5.8 classtype / priority

```
classtype:web-application-attack;
priority:1;    # 1(높음) ~ 4(낮음)
```

---

## 6. 커스텀 룰 작성 실습

### 6.1 룰 1: SQL Injection 탐지

```bash
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
alert http $HOME_NET any -> any any (msg:"CUSTOM - SQL Injection in URI (union select)"; flow:to_server,established; http.uri; content:"union"; nocase; content:"select"; nocase; distance:0; classtype:web-application-attack; sid:9000010; rev:1;)
EOF
```

### 6.2 룰 2: XSS 탐지

```bash
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
alert http $HOME_NET any -> any any (msg:"CUSTOM - XSS attempt (script tag)"; flow:to_server,established; http.uri; content:"<script"; nocase; classtype:web-application-attack; sid:9000011; rev:1;)
EOF
```

### 6.3 룰 3: 디렉터리 트래버설 탐지

```bash
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
alert http $HOME_NET any -> any any (msg:"CUSTOM - Directory Traversal attempt"; flow:to_server,established; http.uri; content:"../"; classtype:web-application-attack; sid:9000012; rev:1;)
EOF
```

### 6.4 룰 4: SSH 브루트포스 탐지

```bash
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
alert tcp any any -> $HOME_NET 22 (msg:"CUSTOM - SSH brute force attempt"; flow:to_server; flags:S; threshold:type threshold, track by_src, count 5, seconds 60; classtype:attempted-admin; sid:9000013; rev:1;)
EOF
```

### 6.5 룰 5: 차단 룰 (IPS용, drop)

```bash
echo 1 | sudo -S tee -a /etc/suricata/rules/local.rules << 'EOF'
drop http any any -> $HOME_NET any (msg:"CUSTOM - Block /etc/passwd access"; flow:to_server,established; http.uri; content:"/etc/passwd"; classtype:web-application-attack; sid:9000014; rev:1;)
EOF
```

### 6.6 작성한 룰 확인

```bash
echo 1 | sudo -S cat /etc/suricata/rules/local.rules
```

---

## 7. 룰 검증과 리로드

### 7.1 설정 검증

```bash
echo 1 | sudo -S suricata -T -c /etc/suricata/suricata.yaml
```

오류가 있으면 해당 룰의 문법을 수정한다.

### 7.2 룰 리로드 (재시작 없이)

```bash
echo 1 | sudo -S kill -USR2 $(pidof suricata)
```

### 7.3 리로드 확인

```bash
echo 1 | sudo -S tail -5 /var/log/suricata/suricata.log
```

**예상 출력:**
```
<Notice> - rule reload starting
<Notice> - rule reload complete
```

---

## 8. 룰 테스트

### 8.1 SQL Injection 테스트

```bash
# web 서버(JuiceShop)에 SQL Injection 패턴 요청
curl -s "http://10.20.30.80/?q=1%20union%20select%201,2,3" > /dev/null

# 알림 확인
echo 1 | sudo -S tail -3 /var/log/suricata/fast.log
```

**예상 출력:**
```
03/27/2026-11:00:01.123  [**] [1:9000010:1] CUSTOM - SQL Injection in URI (union select) [**] ...
```

### 8.2 XSS 테스트

```bash
curl -s "http://10.20.30.80/?q=%3Cscript%3Ealert(1)%3C/script%3E" > /dev/null

echo 1 | sudo -S tail -3 /var/log/suricata/fast.log
```

### 8.3 디렉터리 트래버설 테스트

```bash
curl -s "http://10.20.30.80/../../etc/passwd" > /dev/null

echo 1 | sudo -S tail -3 /var/log/suricata/fast.log
```

### 8.4 eve.json으로 상세 확인

```bash
# 마지막 alert 이벤트 상세 보기
echo 1 | sudo -S tail -20 /var/log/suricata/eve.json | \
  python3 -m json.tool | grep -A 5 '"alert"'
```

---

## 9. 룰 작성 팁

### 9.1 방향 연산자

```
->    출발지에서 목적지 방향만
<>    양방향 (요청과 응답 모두)
```

### 9.2 변수 활용

```
$HOME_NET        내부 네트워크
$EXTERNAL_NET    외부 네트워크
$HTTP_SERVERS    웹 서버
$HTTP_PORTS      웹 포트
```

### 9.3 여러 content 조합

AND 조건으로 동작한다 (모든 content가 매칭되어야 알림 발생):

```
alert http any any -> any any (
  msg:"Multi content match";
  content:"admin"; nocase;
  content:"password"; nocase; distance:0;
  sid:9000020; rev:1;
)
```

### 9.4 부정(NOT) 매칭

```
content:!"safe_string";    # "safe_string"이 없을 때 매칭
```

### 9.5 flowbits (상태 추적)

```
# 첫 번째 룰: 로그인 페이지 접근 감지
alert http any any -> any any (msg:"Login page"; content:"/login"; http.uri; flowbits:set,login_attempt; sid:9000030; rev:1;)

# 두 번째 룰: 로그인 후 admin 접근
alert http any any -> any any (msg:"Admin after login"; content:"/admin"; http.uri; flowbits:isset,login_attempt; sid:9000031; rev:1;)
```

---

## 10. 실습 과제

### 과제 1: 탐지 룰 작성

다음 공격을 탐지하는 룰을 `/etc/suricata/rules/local.rules`에 추가하라:

1. HTTP 요청에서 `cmd=` 파라미터 탐지 (명령 주입)
2. User-Agent에 `nikto`가 포함된 요청 탐지 (스캐너)
3. HTTP 응답에서 `root:x:0:0` 탐지 (passwd 유출)

**힌트:**
```
# 1번
alert http ... (msg:"Command Injection"; http.uri; content:"cmd="; sid:9000040; rev:1;)

# 2번
alert http ... (msg:"Nikto Scanner"; http.user_agent; content:"nikto"; nocase; sid:9000041; rev:1;)

# 3번
alert http ... (msg:"Passwd Leak"; flow:to_client,established; http.response_body; content:"root:x:0:0"; sid:9000042; rev:1;)
```

### 과제 2: 차단 룰 작성

다음을 **차단(drop)**하는 룰을 작성하라:

1. URI에 `wp-admin`이 포함된 요청 (WordPress 관리자 페이지 차단)
2. `.php.bak` 파일 요청 차단

### 과제 3: 테스트

작성한 룰을 검증(`suricata -T`)하고, curl로 테스트 트래픽을 발생시켜 동작을 확인하라.

### 정리

```bash
# 실습 룰 정리 (원하는 룰만 남기기)
echo 1 | sudo -S cp /etc/suricata/rules/local.rules /tmp/local.rules.bak
```

---

## 11. 핵심 정리

| 개념 | 설명 |
|------|------|
| alert/drop/reject/pass | 룰 동작 (IPS에서 drop 가능) |
| content | 페이로드 문자열 매칭 |
| nocase | 대소문자 무시 |
| flow | 연결 방향/상태 지정 |
| http.uri | HTTP URI 전용 매칭 |
| pcre | 정규표현식 매칭 |
| threshold | 임계값 기반 알림 |
| flowbits | 상태 추적 (다단계 탐지) |
| sid | 룰 고유 ID (커스텀은 9000000+) |
| `kill -USR2` | 재시작 없이 룰 리로드 |

---

## 다음 주 예고

Week 06에서는 Suricata 운영을 다룬다:
- eve.json/fast.log 분석
- 성능 튜닝
- 오탐(False Positive) 관리


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 05: Suricata IPS (2) — 룰 작성"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안 솔루션 운영의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. 룰 문법 개요"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. Action (동작)"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안 솔루션 운영 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. Protocol (프로토콜)"의 실무 활용 방안은?
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
