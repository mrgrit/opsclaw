# Week 08: 로그 분석 — auth.log, 타임라인, IOC

## 학습 목표
- 리눅스 시스템 로그의 종류와 위치를 파악할 수 있다
- auth.log를 분석하여 침입 시도를 식별할 수 있다
- 로그 기반 타임라인을 구성하여 공격 흐름을 재구성할 수 있다
- IOC(Indicators of Compromise)를 추출하고 활용할 수 있다

## 선수 지식
- 리눅스 텍스트 처리 도구 (grep, awk, sort, uniq)
- 시스템 로그 기본 개념
- IDS/IPS 기초 (Week 07 수강 완료)

## 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:30 | 로그 분석 이론 및 로그 소스 | 강의 |
| 0:30-0:50 | IOC 개념 및 타임라인 분석 방법론 | 강의 |
| 0:50-1:00 | 휴식 | - |
| 1:00-1:40 | auth.log 분석 실습 | 실습 |
| 1:40-2:20 | 다중 로그 소스 타임라인 구성 | 실습 |
| 2:20-2:30 | 휴식 | - |
| 2:30-3:10 | IOC 추출 및 위협 인텔리전스 연동 | 실습 |
| 3:10-3:40 | 분석 결과 공유 + 퀴즈 | 토론/퀴즈 |

---

# Part 1: 로그 분석 이론 (30분)

## 1.1 리눅스 주요 로그 파일

| 로그 파일 | 내용 | 보안 관련성 |
|----------|------|-----------|
| `/var/log/auth.log` | 인증 이벤트 (로그인, sudo) | 높음 — 침입 시도 탐지 |
| `/var/log/syslog` | 시스템 전반 이벤트 | 중간 — 서비스 이상 |
| `/var/log/kern.log` | 커널 메시지 | 중간 — 커널 익스플로잇 |
| `/var/log/apache2/access.log` | 웹 접근 로그 | 높음 — 웹 공격 탐지 |
| `/var/log/suricata/eve.json` | IDS 이벤트 | 높음 — 네트워크 공격 |
| `/var/log/cron.log` | cron 실행 기록 | 중간 — 백도어 탐지 |
| `~/.bash_history` | 명령어 이력 | 높음 — 행위 분석 |

## 1.2 IOC(Indicators of Compromise)

IOC는 시스템이 침해당했음을 나타내는 증거이다.

### IOC 유형

| 유형 | 예시 | 수집 소스 |
|------|------|----------|
| **네트워크** | 악성 IP, 도메인, URL | 방화벽, IDS 로그 |
| **호스트** | 악성 파일 해시, 프로세스 | 시스템 로그, 파일 시스템 |
| **행위** | 비정상 로그인 패턴 | auth.log, audit 로그 |
| **시간** | 비업무 시간 활동 | 모든 로그의 타임스탬프 |

### 타임라인 분석

```
시간순 이벤트 재구성 예시
──────────────────────────────────────────────
14:00  정찰 — nmap 스캔 (suricata: PORT SCAN)
14:05  취약점 — nikto 스캔 (access.log: 다수 404)
14:15  침투 — SQLi 시도 (access.log: ' OR 1=1)
14:20  접근 — SSH 로그인 성공 (auth.log: Accepted)
14:25  상승 — sudo su (auth.log: session opened for root)
14:30  유지 — crontab 수정 (cron.log: EDIT)
14:35  유출 — 외부 전송 (nftables log: 외부 IP 접속)
──────────────────────────────────────────────
```

---

# Part 2: 실습 가이드

## 실습 2.1: auth.log 분석

> **목적**: auth.log에서 침입 시도와 성공 여부를 분석한다
> **배우는 것**: 로그인 실패/성공 패턴 식별, 공격 IP 추출

```bash
# 최근 로그인 실패 확인
grep "Failed password" /var/log/auth.log | tail -20

# 실패한 IP별 통계
grep "Failed password" /var/log/auth.log | \
  awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -10

# 실패한 사용자명 통계
grep "Failed password" /var/log/auth.log | \
  awk '{for(i=1;i<=NF;i++) if($i=="for") print $(i+1)}' | \
  sort | uniq -c | sort -rn | head -10

# 로그인 성공 확인
grep "Accepted" /var/log/auth.log | tail -20

# sudo 사용 이력
grep "sudo" /var/log/auth.log | tail -20

# 비정상 시간대 로그인 (00:00-06:00)
grep "Accepted" /var/log/auth.log | \
  awk '{print $3}' | awk -F: '$1>=0 && $1<6'
```

> **결과 해석**: 같은 IP에서 짧은 시간 동안 다수의 로그인 실패가 발생하면 brute force 공격이다. 실패 후 성공이 이어지면 계정이 탈취된 것이다.
> **실전 활용**: 공방전 중 실시간으로 auth.log를 모니터링하여 Red Team의 침입 시도를 탐지한다.

## 실습 2.2: 다중 로그 소스 타임라인 구성

> **목적**: 여러 로그를 시간순으로 통합하여 공격 흐름을 재구성한다
> **배우는 것**: 로그 통합, 타임라인 생성, 상관 분석

```bash
# 여러 로그에서 특정 IP의 활동 추출
TARGET_IP="10.20.30.99"

echo "=== IDS 알림 ===" > /tmp/timeline.txt
grep "$TARGET_IP" /var/log/suricata/fast.log >> /tmp/timeline.txt

echo "=== 인증 이벤트 ===" >> /tmp/timeline.txt
grep "$TARGET_IP" /var/log/auth.log >> /tmp/timeline.txt

echo "=== 웹 접근 ===" >> /tmp/timeline.txt
grep "$TARGET_IP" /var/log/apache2/access.log 2>/dev/null >> /tmp/timeline.txt

echo "=== 방화벽 로그 ===" >> /tmp/timeline.txt
grep "$TARGET_IP" /var/log/syslog | grep "NFT-" >> /tmp/timeline.txt

# 결과 확인
cat /tmp/timeline.txt

# Suricata eve.json에서 상세 정보 추출
cat /var/log/suricata/eve.json | \
  jq -r "select(.src_ip==\"$TARGET_IP\") | [.timestamp, .event_type, .alert.signature // .http.url // \"N/A\"] | @tsv"
```

> **결과 해석**: 시간순으로 정렬된 이벤트를 통해 공격자의 전체 행동 패턴을 파악할 수 있다. 정찰 → 침투 → 권한 상승 순서를 확인한다.

## 실습 2.3: IOC 추출 및 활용

> **목적**: 로그에서 IOC를 추출하여 위협 대응에 활용한다
> **배우는 것**: IP/도메인/해시 추출, 차단 목록 생성

```bash
# 공격 IP 목록 추출 (IDS 알림 기반)
grep "\[Classification:" /var/log/suricata/fast.log | \
  awk '{print $NF}' | sort -u > /tmp/ioc_ips.txt

# 웹 공격 URL 패턴 추출
grep -E "(\' OR |<script>|UNION SELECT)" /var/log/apache2/access.log 2>/dev/null | \
  awk '{print $1, $7}' > /tmp/ioc_urls.txt

# 의심 파일 해시 수집
find /tmp /var/tmp /dev/shm -newer /var/log/auth.log -type f 2>/dev/null | \
  xargs md5sum 2>/dev/null > /tmp/ioc_hashes.txt

# IOC IP를 nftables 차단 목록에 추가
while read ip; do
  sudo nft add element inet filter blocked_ips { "$ip" }
done < /tmp/ioc_ips.txt
```

> **결과 해석**: 추출된 IOC는 방화벽 차단, IDS 룰 업데이트, 팀 내 공유에 활용한다.

---

# Part 3: 심화 학습

## 3.1 로그 무결성 보호

공격자가 로그를 삭제하거나 변조할 수 있으므로 보호 조치가 필요하다.

- 원격 syslog 서버로 로그 전송
- 로그 파일 불변 속성 설정: `chattr +a /var/log/auth.log`
- Wazuh/OSSEC로 파일 무결성 모니터링(FIM)

## 3.2 자동화 스크립트

반복적인 로그 분석을 스크립트로 자동화하면 공방전에서 대응 속도를 높일 수 있다.

---

## 검증 체크리스트
- [ ] auth.log에서 로그인 실패 통계를 추출했는가
- [ ] 다중 로그 소스에서 타임라인을 구성했는가
- [ ] IOC(IP, URL, 해시)를 추출했는가
- [ ] 추출된 IOC를 방화벽 차단에 활용했는가

## 자가 점검 퀴즈
1. auth.log에서 SSH brute force 공격을 식별하는 방법은?
2. 타임라인 분석에서 여러 로그 소스의 시간 동기화가 중요한 이유는?
3. IOC의 3가지 유형(네트워크/호스트/행위)을 각각 예시와 함께 설명하라.
4. 공격자가 로그를 삭제했을 때 이를 탐지할 수 있는 방법은?
5. eve.json과 fast.log의 차이와 각각의 활용 사례를 설명하라.
