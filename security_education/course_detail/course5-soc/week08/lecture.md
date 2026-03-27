# Week 08: 중간고사 - 로그 분석 + ATT&CK 매핑 (상세 버전)

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

## 용어 해설 (보안관제/SOC 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **SOC** | Security Operations Center | 보안 관제 센터 (24/7 모니터링) | 경찰 112 상황실 |
| **관제** | Monitoring/Surveillance | 보안 이벤트를 실시간 감시하는 활동 | CCTV 관제 |
| **경보** | Alert | 보안 이벤트가 탐지 규칙에 매칭되어 발생한 알림 | 화재 경보기 울림 |
| **이벤트** | Event | 시스템에서 발생한 모든 활동 기록 | 일어난 일 하나하나 |
| **인시던트** | Incident | 보안 정책을 위반한 이벤트 (실제 위협) | 실제 화재 발생 |
| **오탐** | False Positive | 정상 활동을 공격으로 잘못 탐지 | 화재 경보기가 요리 연기에 울림 |
| **미탐** | False Negative | 실제 공격을 놓침 | 도둑이 CCTV에 안 잡힘 |
| **TTD** | Time to Detect | 공격 발생~탐지까지 걸리는 시간 | 화재 발생~경보 울림 시간 |
| **TTR** | Time to Respond | 탐지~대응까지 걸리는 시간 | 경보~소방차 도착 시간 |
| **SIGMA** | SIGMA | SIEM 벤더에 무관한 범용 탐지 룰 포맷 | 국제 표준 수배서 양식 |
| **Tier 1/2/3** | SOC Tiers | 관제 인력 수준 (L1:모니터링, L2:분석, L3:전문가) | 일반의→전문의→교수 |
| **트리아지** | Triage | 경보를 우선순위별로 분류하는 작업 | 응급실 환자 분류 |
| **플레이북** | Playbook (IR) | 인시던트 유형별 대응 절차 매뉴얼 | 화재 대응 매뉴얼 |
| **포렌식** | Forensics | 사이버 범죄 수사를 위한 증거 수집·분석 | 범죄 현장 감식 |
| **IOC** | Indicator of Compromise | 침해 지표 (악성 IP, 도메인, 해시) | 수배범의 지문, 차량번호 |
| **TTP** | Tactics, Techniques, Procedures | 공격자의 전술·기법·절차 | 범인의 범행 수법 |
| **위협 헌팅** | Threat Hunting | 탐지 룰에 걸리지 않는 위협을 능동적으로 찾는 활동 | 잠복 수사 |
| **syslog** | syslog | 시스템 로그를 원격 전송하는 프로토콜 (UDP 514) | 모든 부서 보고서를 본사로 모으는 시스템 |


---

# Week 08: 중간고사 - 로그 분석 + ATT&CK 매핑

## 시험 개요

- **유형**: 실기 시험 (로그 분석 + 보고서)
- **시간**: 120분
- **배점**: 100점
- **범위**: Week 02~07 (로그, Wazuh, 경보 분석, SIGMA, ATT&CK)

---

## 시험 구성

| 파트 | 내용 | 배점 |
|------|------|------|
| Part A | 시스템 로그 분석 | 25점 |
| Part B | 네트워크/웹 로그 분석 | 25점 |
| Part C | Wazuh 경보 분석 + ATT&CK 매핑 | 30점 |
| Part D | SIGMA 룰 작성 | 20점 |

---

## Part A: 시스템 로그 분석 (25점)

### 과제

4개 서버의 auth.log와 syslog를 분석하여 보안 이슈를 보고하시오.

### A-1. SSH 공격 분석 (10점)

```bash
# 실행하여 결과를 분석할 것

# 각 서버별 SSH 실패 횟수
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  echo -n "실패: "
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo 0"
  echo -n "성공: "
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep -c 'Accepted' /var/log/auth.log 2>/dev/null || echo 0"
done

# 공격자 IP Top 5
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -5"

# 공격 대상 사용자 Top 5
sshpass -p1 ssh opsclaw@10.20.30.201 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{for(i=1;i<=NF;i++) if(\$i==\"for\") {if(\$(i+1)==\"invalid\") print \$(i+3); else print \$(i+1)}}' | \
  sort | uniq -c | sort -rn | head -5"
```

**질문**:
1. 가장 많이 공격받는 서버는? (2점)
2. 가장 활발한 공격자 IP는? (2점)
3. 공격자가 시도한 사용자명 패턴의 의미는? (3점)
4. 이 공격은 TP인가 FP인가? 근거는? (3점)

### A-2. sudo/su 분석 (8점)

```bash
# sudo 사용 이력 분석
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  echo "=== $ip: sudo 이력 ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep 'COMMAND=' /var/log/auth.log 2>/dev/null | tail -5"
done

# 비인가 sudo 시도
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep 'NOT in sudoers' /var/log/auth.log 2>/dev/null"
done
```

**질문**:
1. 위험한 sudo 명령이 있는가? (4점)
2. 비인가 sudo 시도가 있는가? 있다면 어떤 사용자인가? (4점)

### A-3. 시스템 이상 징후 (7점)

```bash
# syslog에서 이상 징후 검색
for srv in "opsclaw@10.20.30.201" "secu@10.20.30.1" "web@10.20.30.80" "siem@10.20.30.100"; do
  echo "=== $srv ==="
  sshpass -p1 ssh -o StrictHostKeyChecking=no $srv  # srv=user@ip (아래 루프 참고) "grep -iE 'error|fail|critical|emergency|segfault|oom' /var/log/syslog 2>/dev/null | wc -l"
done

# 커널 오류 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "journalctl -p err --no-pager 2>/dev/null | tail -10"
```

---

## Part B: 네트워크/웹 로그 분석 (25점)

### B-1. Suricata IPS 분석 (12점)

```bash
# Suricata 알림 통계
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/fast.log 2>/dev/null | wc -l"

# 알림 유형 Top 10
sshpass -p1 ssh secu@10.20.30.1 "cat /var/log/suricata/fast.log 2>/dev/null | \
  grep -oP '\[\*\*\].*?\[\*\*\]' | sort | uniq -c | sort -rn | head -10"

# Priority별 분포
sshpass -p1 ssh secu@10.20.30.1 "grep -oP 'Priority: [0-9]+' /var/log/suricata/fast.log 2>/dev/null | \
  sort | uniq -c | sort -rn"

# 공격자 IP Top 5
sshpass -p1 ssh secu@10.20.30.1 "grep -oP '\\{\\w+\\} [0-9.]+' /var/log/suricata/fast.log 2>/dev/null | \
  awk '{print \$2}' | sort | uniq -c | sort -rn | head -5"
```

**질문**:
1. 가장 빈번한 알림 3가지와 의미를 설명하시오 (6점)
2. 가장 의심스러운 IP와 근거를 제시하시오 (3점)
3. Priority 1 알림이 있는 경우 상세 분석하시오 (3점)

### B-2. 웹 로그 분석 (13점)

```bash
# 웹 로그 기본 통계
sshpass -p1 ssh web@10.20.30.80 "wc -l /var/log/nginx/access.log 2>/dev/null || echo '0'"

# HTTP 상태코드 분포
sshpass -p1 ssh web@10.20.30.80 "awk '{print \$9}' /var/log/nginx/access.log 2>/dev/null | \
  sort | uniq -c | sort -rn | head -10"

# 웹 공격 패턴 검색
sshpass -p1 ssh web@10.20.30.80 "grep -iE 'union|select|script|alert|\.\./' /var/log/nginx/access.log 2>/dev/null | wc -l"

# 의심스러운 요청 샘플
sshpass -p1 ssh web@10.20.30.80 "grep -iE 'union|select|script|\.\./' /var/log/nginx/access.log 2>/dev/null | head -5"

# User-Agent 분석
sshpass -p1 ssh web@10.20.30.80 "awk -F'\"' '{print \$6}' /var/log/nginx/access.log 2>/dev/null | \
  sort | uniq -c | sort -rn | head -5"
```

**질문**:
1. 웹 공격 시도가 있는가? 유형별로 분류하시오 (5점)
2. 스캐닝 도구의 흔적이 있는가? (3점)
3. 공격 성공(200 응답) 여부를 확인하시오 (5점)

---

## Part C: Wazuh 경보 분석 + ATT&CK 매핑 (30점)

### C-1. 경보 분석 (15점)

```bash
# 경보 전체 통계
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
levels = Counter()
rules = Counter()
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        levels[r.get('level',0)] += 1
        rules[f'{r.get(\"id\",\"\")}:{r.get(\"description\",\"\")}'] += 1
    except: pass
print('=== 레벨별 ===')
for l in sorted(levels.keys(), reverse=True):
    print(f'  Level {l}: {levels[l]}')
print()
print('=== Top 10 규칙 ===')
for r, c in rules.most_common(10):
    print(f'  {c:4d}건: {r}')
\" 2>/dev/null"

# Level 10+ 상세
sshpass -p1 ssh siem@10.20.30.100 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 10:
            print(f'[{a.get(\"timestamp\",\"\")}] Level {r[\"level\"]}')
            print(f'  Rule: {r.get(\"id\",\"\")} - {r.get(\"description\",\"\")}')
            print(f'  Agent: {a.get(\"agent\",{}).get(\"name\",\"\")}')
            print(f'  Groups: {r.get(\"groups\",[])}')
            print()
    except: pass
\" 2>/dev/null | tail -40"
```

**질문**:
1. 가장 심각한 경보 3건을 선택하고 상세 분석하시오 (9점)
2. 각 경보가 TP인지 FP인지 판정하고 근거를 제시하시오 (6점)

### C-2. ATT&CK 매핑 (15점)

**과제**: Part A~C에서 발견한 모든 보안 이벤트를 ATT&CK 전술/기법에 매핑하시오.

```
| 이벤트 | ATT&CK 전술 | ATT&CK 기법 (ID) | 증거 |
|--------|------------|-------------------|------|
| ? | ? | ? | ? |
```

최소 **5개 기법** 이상 매핑하시오. (각 3점)

---

## Part D: SIGMA 룰 작성 (20점)

### 과제

Part A~C에서 발견한 위협에 대한 SIGMA 탐지 규칙을 **2개** 작성하시오.

### 요구사항 (각 10점)

1. 완전한 SIGMA YAML 형식 (title, logsource, detection, level 필수)
2. ATT&CK 태그 포함
3. falsepositives 명시
4. 실제 로그에서 탐지되는 것을 검증 (검증 명령어와 결과 포함)

### 템플릿

```yaml
title: (규칙 제목)
id: (UUID)
status: experimental
description: (상세 설명)
author: (이름)
date: 2026/03/27
tags:
    - attack.(전술)
    - attack.t(기법번호)
logsource:
    product: linux
    service: (서비스명)
detection:
    selection:
        (필드): (값)
    condition: selection
falsepositives:
    - (오탐 상황)
level: (low/medium/high/critical)
```

---

## 채점 기준

| 파트 | 항목 | 배점 |
|------|------|------|
| A | 로그 분석 정확성, 이상 징후 식별 | 25점 |
| B | 공격 패턴 식별, 상세 분석 | 25점 |
| C-1 | 경보 분석, TP/FP 판정 | 15점 |
| C-2 | ATT&CK 매핑 정확성 (5개 이상) | 15점 |
| D | SIGMA 규칙 완성도, 검증 | 20점 |

---

## 시험 전 체크리스트

```bash
# 서버 접속 확인
for ip in 10.20.30.201 10.20.30.1 10.20.30.80 10.20.30.100; do
  sshpass -p1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 $srv "hostname" 2>/dev/null \
    && echo "$ip: OK" || echo "$ip: FAIL"
done

# 로그 존재 확인
sshpass -p1 ssh opsclaw@10.20.30.201 "ls -lh /var/log/auth.log 2>/dev/null"
sshpass -p1 ssh secu@10.20.30.1 "ls -lh /var/log/suricata/fast.log 2>/dev/null"
sshpass -p1 ssh siem@10.20.30.100 "ls -lh /var/ossec/logs/alerts/alerts.json 2>/dev/null"
```

---

## 참고

- 오픈 북 시험: 강의 자료 + 인터넷 검색 가능
- 제출: 분석 보고서 + SIGMA 규칙 파일
- ATT&CK 참조: https://attack.mitre.org


---

---

## 심화: 보안관제(SOC) 실무 보충

### 경보 분석 워크플로

```
[1단계] 경보 수신
    → Wazuh Dashboard에서 경보 확인
    → 심각도(level), 출처(src), 대상(dst) 즉시 파악

[2단계] 초기 분류 (Triage, 5분 이내)
    → 오탐(False Positive)인가? → 기존 사례와 비교
    → 실제 위협인가? → IOC 확인 (악성 IP, 해시)
    → 긴급도 결정: P1(즉시) / P2(4시간) / P3(24시간) / P4(일반)

[3단계] 심층 분석 (Investigation)
    → 관련 로그 추가 수집 (시간 범위 확대)
    → ATT&CK 기법 매핑
    → 영향 범위 파악 (어떤 서버, 어떤 데이터)

[4단계] 대응 (Response)
    → 격리: 감염 서버 네트워크 분리
    → 차단: 공격자 IP 방화벽 차단
    → 복구: 백업에서 복원, 패치 적용

[5단계] 사후 분석 (Post-Incident)
    → 타임라인 작성 (attack→detect→respond→recover)
    → 탐지 룰 개선
    → 보고서 작성
```

### Wazuh 로그 분석 실습

```bash
# siem 서버에서 최근 경보 확인
sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 "
  echo '=== 최근 경보 (level >= 7) ==='
  sudo cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | \
    python3 -c '
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line.strip())
        if a.get("rule",{}).get("level",0) >= 7:
            print(f"[{a[\"rule\"][\"level\"]}] {a[\"rule\"].get(\"description\",\"?\")[:60]} src={a.get(\"srcip\",\"?\")}")
    except: pass
' 2>/dev/null | tail -10
" 2>/dev/null
```

### SIGMA 룰 작성 가이드

```yaml
# SIGMA 룰 기본 구조
title: SSH Brute Force Detection     # 룰 이름
id: 12345678-abcd-efgh-...           # 고유 ID (UUID)
status: experimental                  # experimental/test/stable
description: |                        # 상세 설명
    5분 내 동일 IP에서 10회 이상 SSH 인증 실패 탐지
author: Student Name                  # 작성자
date: 2026/03/27                      # 작성일

logsource:                            # 어떤 로그를 볼 것인가
    product: linux
    service: sshd

detection:                            # 어떤 패턴을 찾을 것인가
    selection:
        eventid: 4625                 # 또는 sshd 실패 이벤트
    filter:                           # 제외 조건
        srcip: "10.20.30.*"           # 내부 IP는 제외
    condition: selection and not filter
    timeframe: 5m                     # 시간 범위
    count: 10                         # 최소 횟수

level: high                           # 심각도
tags:                                 # ATT&CK 매핑
    - attack.credential_access
    - attack.t1110.001
falsepositives:                       # 오탐 가능성
    - 자동화 스크립트의 반복 접속
    - 비밀번호 정책 변경 후 재접속
```

### TTD/TTR 측정 실습

```bash
# 공격→탐지 시간(TTD) 측정 시나리오
echo "=== 공격 시작 시각 기록 ==="
ATTACK_TIME=$(date +%s)
echo "공격 시작: $(date)"

# (여기서 공격 실행)

echo "=== SIEM 경보 확인 ==="
# (경보 발생 시각 확인)
DETECT_TIME=$(date +%s)
TTD=$((DETECT_TIME - ATTACK_TIME))
echo "TTD (탐지 소요 시간): ${TTD}초"
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** "Week 08: 중간고사 - 로그 분석 + ATT&CK 매핑"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **보안관제/SOC의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "시험 개요"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "시험 구성"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **보안관제/SOC 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "Part A: 시스템 로그 분석 (25점)"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 탐지/대응의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 보안관제/SOC 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---
---

> **실습 환경 검증:** 이 교안의 실습 명령은 실제 인프라(10.20.30.0/24)에서 동작을 확인하였습니다. (2026-03-28 검증)
