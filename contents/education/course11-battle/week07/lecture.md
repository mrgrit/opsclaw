# Week 07: IDS/IPS 구축 — Suricata 설치, 룰 작성

## 학습 목표
- IDS와 IPS의 차이점과 동작 원리를 이해한다
- Suricata를 설치하고 기본 설정을 구성할 수 있다
- 커스텀 탐지 룰을 작성하여 특정 공격을 탐지할 수 있다
- 공방전에서 IDS/IPS를 활용한 실시간 모니터링 체계를 구축할 수 있다

## 선수 지식
- nftables 방화벽 기초 (Week 06 수강 완료)
- TCP/IP 패킷 구조 이해
- 정규표현식 기본 문법

## 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | IDS/IPS 이론 및 Suricata 아키텍처 | 강의 |
| 0:30-0:50 | Suricata 룰 문법 | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:40 | Suricata 설치 및 기본 설정 실습 | 실습 |
| 1:40-2:20 | 커스텀 룰 작성 실습 | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | IPS 모드 전환 + 실시간 탐지 실습 | 실습 |
| 3:10-3:40 | 탐지 회피 토론 + 퀴즈 | 토론/퀴즈 |

---

# Part 1: IDS/IPS 이론 (30분)

## 1.1 IDS vs IPS

| 항목 | IDS (탐지 시스템) | IPS (방지 시스템) |
|------|-----------------|-----------------|
| 동작 | 탐지 + 알림 | 탐지 + 차단 |
| 배치 | 미러/TAP (패시브) | 인라인 (액티브) |
| 영향 | 트래픽에 영향 없음 | 악성 트래픽 차단 |
| 위험 | 미탐지 | 오탐으로 정상 차단 |

### 탐지 방식

| 방식 | 원리 | 장점 | 단점 |
|------|------|------|------|
| **시그니처 기반** | 알려진 패턴 매칭 | 정확, 빠름 | 제로데이 탐지 불가 |
| **이상 탐지** | 정상 행위 기준선 이탈 | 제로데이 가능 | 오탐률 높음 |
| **프로토콜 분석** | 프로토콜 규격 위반 탐지 | 프로토콜 악용 탐지 | 규격 정의 필요 |

## 1.2 Suricata 아키텍처

Suricata는 오픈소스 고성능 IDS/IPS 엔진이다. 멀티스레드 아키텍처로 높은 처리량을 제공한다.

```
패킷 흐름 (IPS 모드)
┌─────────┐     ┌──────────┐     ┌─────────┐
│ 네트워크 │ ──→ │ Suricata │ ──→ │ 서버    │
│ (외부)   │     │ (검사)   │     │ (내부)  │
└─────────┘     └──────────┘     └─────────┘
                     │
                 ┌───┴───┐
                 │ alert │ → fast.log, eve.json
                 │ drop  │ → 패킷 차단
                 └───────┘
```

## 1.3 Suricata 룰 문법

```
action protocol src_ip src_port -> dst_ip dst_port (옵션;)

예시:
alert tcp any any -> any 80 (msg:"HTTP GET 탐지"; content:"GET"; sid:100001; rev:1;)
```

### 주요 룰 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `msg` | 알림 메시지 | `msg:"SQLi 탐지"` |
| `content` | 페이로드 내 문자열 매칭 | `content:"' OR 1=1"` |
| `pcre` | 정규표현식 매칭 | `pcre:"/union.+select/i"` |
| `flow` | 세션 방향 지정 | `flow:to_server,established` |
| `sid` | 룰 고유 ID | `sid:100001` |
| `threshold` | 빈도 기반 탐지 | `threshold:type both,track by_src,count 5,seconds 60` |

---

# Part 2: 실습 가이드

## 실습 2.1: Suricata 설치 및 기본 설정

> **목적**: Suricata를 설치하고 IDS 모드로 동작시킨다
> **배우는 것**: 설치, 설정 파일 구조, 룰 업데이트

```bash
# Suricata 설치 (secu 서버)
sudo apt install -y suricata

# 버전 확인
suricata --build-info | head -5

# 설정 파일 위치
ls -la /etc/suricata/suricata.yaml

# 네트워크 인터페이스 확인
ip link show

# 기본 설정에서 HOME_NET 수정
sudo vi /etc/suricata/suricata.yaml
# HOME_NET: "[10.20.30.0/24]"

# 룰 업데이트 (Emerging Threats)
sudo suricata-update

# IDS 모드로 실행
sudo suricata -c /etc/suricata/suricata.yaml -i eth0

# 로그 확인
tail -f /var/log/suricata/fast.log
tail -f /var/log/suricata/eve.json | jq .
```

> **결과 해석**: `fast.log`에 탐지 알림이 기록되며, `eve.json`은 JSON 형태의 상세 로그이다. `eve.json`은 Wazuh/ELK 등 SIEM과 연동에 적합하다.
> **실전 활용**: 공방전에서 secu 서버에 Suricata를 IDS 모드로 배치하여 Red Team 활동을 탐지한다.

## 실습 2.2: 커스텀 탐지 룰 작성

> **목적**: 공방전에서 필요한 커스텀 탐지 룰을 작성한다
> **배우는 것**: 룰 작성 문법, 테스트, 튜닝

```bash
# 커스텀 룰 파일 생성
sudo tee /etc/suricata/rules/local.rules << 'EOF'
# 포트 스캔 탐지 (SYN 패킷 다수)
alert tcp any any -> $HOME_NET any (msg:"PORT SCAN detected"; \
  flags:S; threshold:type both, track by_src, count 20, seconds 10; \
  sid:200001; rev:1;)

# SQL Injection 탐지
alert http any any -> $HOME_NET any (msg:"SQL Injection attempt"; \
  content:"' OR "; nocase; \
  flow:to_server,established; sid:200002; rev:1;)

# XSS 탐지
alert http any any -> $HOME_NET any (msg:"XSS attempt"; \
  content:"<script>"; nocase; \
  flow:to_server,established; sid:200003; rev:1;)

# SSH brute force 탐지
alert tcp any any -> $HOME_NET 22 (msg:"SSH brute force"; \
  flow:to_server; threshold:type both, track by_src, count 5, seconds 60; \
  sid:200004; rev:1;)

# nmap 탐지 (User-Agent)
alert http any any -> $HOME_NET any (msg:"Nmap scan detected"; \
  content:"Nmap"; http_user_agent; sid:200005; rev:1;)
EOF

# 룰 문법 검증
sudo suricata -T -c /etc/suricata/suricata.yaml

# suricata.yaml에 local.rules 추가
# rule-files:
#   - local.rules

# Suricata 재시작
sudo systemctl restart suricata
```

> **결과 해석**: `-T` 옵션으로 설정과 룰의 문법을 검증한다. 에러 없이 통과하면 룰이 정상적으로 로드된다.

## 실습 2.3: IPS 모드 전환 및 차단 테스트

> **목적**: Suricata를 IPS 모드로 전환하여 실제 트래픽을 차단한다
> **배우는 것**: IPS 모드 설정, drop 액션, nftables 연동

```bash
# nftables와 연동하여 IPS 모드 설정
sudo nft add table inet filter
sudo nft add chain inet filter forward { type filter hook forward priority 0 \; }
sudo nft add rule inet filter forward queue num 0

# IPS 모드 drop 룰 추가
sudo tee -a /etc/suricata/rules/local.rules << 'EOF'
# SQLi 차단 (alert → drop)
drop http any any -> $HOME_NET any (msg:"BLOCKED: SQL Injection"; \
  content:"' OR "; nocase; \
  flow:to_server,established; sid:200010; rev:1;)
EOF

# 공격 시뮬레이션으로 차단 테스트
curl "http://10.20.30.80/search?q=' OR 1=1--"

# 차단 로그 확인
grep "BLOCKED" /var/log/suricata/fast.log
```

> **결과 해석**: `drop` 액션이 적용된 룰에 매칭되면 패킷이 폐기되고 로그에 기록된다.

---

# Part 3: 심화 학습

## 3.1 IDS 회피 기법 (Red Team 관점)

- **패킷 분할**: 시그니처를 여러 패킷으로 나눠 전송
- **인코딩**: URL 인코딩, 유니코드로 패턴 변환
- **암호화 통신**: HTTPS/SSH 터널 사용
- **느린 스캔**: 탐지 임계값 이하로 속도 조절

## 3.2 룰 튜닝

오탐을 줄이기 위한 룰 튜닝이 중요하다.

- `suppress` 지시어로 특정 조건의 알림 억제
- `threshold`로 빈도 기반 탐지 설정
- `flowbits`로 다단계 탐지 구현

---

## 검증 체크리스트
- [ ] Suricata를 설치하고 IDS 모드로 동작시켰는가
- [ ] 최소 3개의 커스텀 룰을 작성하고 검증했는가
- [ ] 공격 시뮬레이션으로 탐지 로그를 확인했는가
- [ ] IPS 모드에서 악성 트래픽이 차단되는 것을 확인했는가

## 자가 점검 퀴즈
1. IDS와 IPS의 배치 방식 차이를 네트워크 다이어그램으로 설명하라.
2. Suricata 룰에서 `flow:to_server,established`의 의미는?
3. `threshold:type both, track by_src, count 5, seconds 60`은 어떤 동작을 하는가?
4. IPS 모드에서 오탐이 발생하면 어떤 문제가 생기는가?
5. 암호화된 트래픽(HTTPS)에서 Suricata가 탐지할 수 있는 방법은?
