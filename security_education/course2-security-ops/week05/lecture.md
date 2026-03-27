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
sshpass -p1 ssh -o StrictHostKeyChecking=no user@10.20.30.1
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
