# Week 05: 경보 분석 (1) - 기초

## 학습 목표

- 보안 경보(Alert)의 분류 체계를 이해한다
- True Positive / False Positive를 구분할 수 있다
- 경보 레벨과 우선순위 결정 기준을 이해한다
- Wazuh 경보를 체계적으로 분석하는 방법을 익힌다

---

## 1. 경보(Alert) 기초

### 1.1 용어 정리

| 용어 | 정의 |
|------|------|
| 이벤트 (Event) | 시스템에서 발생한 기록 (로그인, 파일 접근 등) |
| 경보 (Alert) | 이벤트 중 보안 규칙에 매칭된 것 |
| 인시던트 (Incident) | 분석 결과 실제 보안 사고로 확인된 것 |

```
이벤트 (수만~수백만 건/일)
  → 경보 (수십~수백 건/일)
    → 인시던트 (0~수 건/일)
```

### 1.2 SOC 분석원의 역할

SOC 분석원은 경보를 분석하여 **실제 위협인지 판별**한다.

```
경보 수신 → 초기 분류 → 상세 분석 → 판정 → 에스컬레이션/종료
```

---

## 2. True/False Positive/Negative

### 2.1 4가지 분류

| 분류 | 실제 공격 여부 | 탐지 여부 | 설명 |
|------|--------------|----------|------|
| True Positive (TP) | 공격 O | 탐지 O | 정확한 탐지 |
| False Positive (FP) | 공격 X | 탐지 O | 오탐 (거짓 경보) |
| True Negative (TN) | 공격 X | 탐지 X | 정상적 미탐지 |
| False Negative (FN) | 공격 O | 탐지 X | 미탐 (위험!) |

### 2.2 SOC에서의 중요성

- **FP (오탐)가 많으면**: 분석원 피로 → "경보 피로(Alert Fatigue)"
- **FN (미탐)이 많으면**: 실제 공격을 놓침 → 사고 발생
- SOC의 목표: **FP를 줄이면서 FN도 줄이기** (균형이 핵심)

### 2.3 실습: TP/FP 판별 연습

```bash
# 경보 샘플 추출
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
alerts = []
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 5:
            alerts.append({
                'time': a.get('timestamp',''),
                'level': r.get('level',0),
                'rule_id': r.get('id',''),
                'desc': r.get('description',''),
                'agent': a.get('agent',{}).get('name',''),
                'srcip': a.get('data',{}).get('srcip',''),
                'full_log': a.get('full_log','')[:100]
            })
    except: pass
for i, a in enumerate(alerts[-10:], 1):
    print(f'--- 경보 #{i} ---')
    print(f'  시간: {a[\"time\"]}')
    print(f'  레벨: {a[\"level\"]}')
    print(f'  규칙: {a[\"rule_id\"]} - {a[\"desc\"]}')
    print(f'  에이전트: {a[\"agent\"]}')
    print(f'  출발지: {a[\"srcip\"]}')
    print(f'  로그: {a[\"full_log\"]}')
    print()
\" 2>/dev/null"
```

각 경보에 대해 다음을 판단해보자:
1. 이것은 **실제 공격**인가, **정상 활동**인가?
2. **TP**인가 **FP**인가?
3. 판단 근거는 무엇인가?

---

## 3. 경보 분류 체계

### 3.1 심각도 분류

| 등급 | Wazuh 레벨 | 대응 |
|------|-----------|------|
| Critical | 12~15 | 즉시 대응, 에스컬레이션 |
| High | 8~11 | 1시간 내 분석 |
| Medium | 4~7 | 업무 시간 내 분석 |
| Low | 0~3 | 로그 기록만 |

### 3.2 경보 분류 프로세스

```
경보 수신
  ↓
[1단계] 초기 분류 (Triage)
  - 레벨/심각도 확인
  - 출발지 IP 확인
  - 규칙 설명 확인
  ↓
[2단계] 상세 분석
  - 전체 로그 확인
  - 이전 이력 조회
  - 관련 경보 상관 분석
  ↓
[3단계] 판정
  - TP → 인시던트 생성, 대응
  - FP → 규칙 튜닝 검토
  - 추가 조사 필요 → 에스컬레이션
```

---

## 4. 실습: 경보 분석 워크플로우

### 4.1 단계 1: 전체 현황 파악

```bash
# 오늘의 경보 현황
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
levels = Counter()
rules = Counter()
agents = Counter()
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        levels[r.get('level',0)] += 1
        rules[r.get('description','unknown')] += 1
        agents[a.get('agent',{}).get('name','unknown')] += 1
    except: pass

print('=== 레벨별 통계 ===')
for l in sorted(levels.keys(), reverse=True):
    print(f'  Level {l:2d}: {levels[l]:5d}건')

print()
print('=== Top 10 경보 유형 ===')
for desc, cnt in rules.most_common(10):
    print(f'  {cnt:5d}건: {desc}')

print()
print('=== 에이전트별 통계 ===')
for agent, cnt in agents.most_common():
    print(f'  {cnt:5d}건: {agent}')
\" 2>/dev/null"
```

### 4.2 단계 2: 고위험 경보 상세 분석

```bash
# Level 8 이상 경보 상세 분석
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        if r.get('level',0) >= 8:
            print('='*60)
            print(f'시간: {a.get(\"timestamp\",\"\")}')
            print(f'레벨: {r.get(\"level\",\"\")}')
            print(f'규칙 ID: {r.get(\"id\",\"\")}')
            print(f'설명: {r.get(\"description\",\"\")}')
            print(f'그룹: {r.get(\"groups\",[])}')
            print(f'에이전트: {a.get(\"agent\",{}).get(\"name\",\"\")} ({a.get(\"agent\",{}).get(\"ip\",\"\")})')
            data = a.get('data',{})
            if data.get('srcip'): print(f'출발지 IP: {data[\"srcip\"]}')
            if data.get('dstuser'): print(f'대상 사용자: {data[\"dstuser\"]}')
            log = a.get('full_log','')
            if log: print(f'원본 로그: {log[:200]}')
            print()
    except: pass
\" 2>/dev/null | tail -60"
```

### 4.3 단계 3: 특정 경보 심층 분석

```bash
# 특정 규칙 ID에 대한 모든 경보
RULE_ID="5710"  # SSH authentication failed (예시)

sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
sources = Counter()
targets = Counter()
count = 0
for line in sys.stdin:
    try:
        a = json.loads(line)
        if a.get('rule',{}).get('id','') == '$RULE_ID':
            count += 1
            data = a.get('data',{})
            if data.get('srcip'): sources[data['srcip']] += 1
            if data.get('dstuser'): targets[data['dstuser']] += 1
    except: pass
print(f'규칙 {\"$RULE_ID\"} 총 {count}건')
print()
print('출발지 IP:')
for ip, cnt in sources.most_common(5):
    print(f'  {cnt}건: {ip}')
print()
print('대상 사용자:')
for user, cnt in targets.most_common(5):
    print(f'  {cnt}건: {user}')
\" 2>/dev/null"
```

---

## 5. 경보 판별 기준

### 5.1 TP 판별 지표

| 지표 | TP 가능성 높음 |
|------|---------------|
| 출발지 IP | 외부 IP, 알려진 악성 IP |
| 시간대 | 업무 외 시간 |
| 빈도 | 단시간 대량 발생 |
| 대상 | 중요 서버, 관리자 계정 |
| 패턴 | 알려진 공격 패턴 일치 |
| 연관 경보 | 여러 유형의 경보가 동시 발생 |

### 5.2 FP 판별 지표

| 지표 | FP 가능성 높음 |
|------|---------------|
| 출발지 IP | 내부 관리 IP, 모니터링 서버 |
| 시간대 | 정기 점검 시간 |
| 빈도 | 항상 동일 패턴 |
| 대상 | 테스트 서버 |
| 패턴 | 정상 운영 활동과 일치 |

### 5.3 실습: TP/FP 판별

```bash
# SSH 실패 경보 중 TP/FP 판별
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{
    # IP 추출
    for(i=1;i<=NF;i++) if($i==\"from\") ip=$(i+1)
    # 사용자 추출
    for(i=1;i<=NF;i++) if($i==\"for\" && $(i+1)!=\"invalid\") user=$(i+1)
    print ip, user
  }' | sort | uniq -c | sort -rn | head -10"

# 내부 IP 대역 확인 (FP 가능성)
# 192.168.x.x, 10.x.x.x = 내부 → FP 가능성
# 그 외 = 외부 → TP 가능성
```

---

## 6. 경보 튜닝

### 6.1 FP 줄이기

자주 발생하는 FP는 규칙을 튜닝하여 줄인다:

```bash
# 반복되는 FP 경보 확인
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
rules = Counter()
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        rules[f'{r.get(\"id\",\"\")}:{r.get(\"description\",\"\")}'] += 1
    except: pass
print('=== 가장 많이 발생하는 경보 (FP 후보) ===')
for desc, cnt in rules.most_common(10):
    print(f'  {cnt:5d}건: {desc}')
\" 2>/dev/null"
```

### 6.2 화이트리스트 설정

```xml
<!-- 예시: 모니터링 서버의 SSH 접근은 제외 -->
<rule id="100001" level="0">
  <if_sid>5710</if_sid>
  <srcip>192.168.208.142</srcip>
  <description>SSH failure from monitoring server - whitelisted</description>
</rule>
```

---

## 7. 경보 분석 보고서 양식

```
=== 경보 분석 보고서 ===
날짜: 2026-03-27
분석원: (이름)

[경보 요약]
- 총 경보: XXX건
- Critical(12+): X건
- High(8-11): X건
- Medium(4-7): X건
- Low(0-3): X건

[분석 결과]
| No | 규칙ID | 설명 | 건수 | 판정(TP/FP) | 근거 |
|----|--------|------|------|------------|------|
| 1 | 5710 | SSH auth failed | 150 | TP(30)/FP(120) | 외부IP=TP, 내부IP=FP |
| 2 | ... | ... | ... | ... | ... |

[조치 사항]
- TP: (대응 조치)
- FP: (튜닝 권고)
```

---

## 8. 핵심 정리

1. **TP/FP 판별** = SOC 분석원의 핵심 역량
2. **초기 분류(Triage)** = 레벨, IP, 시간, 빈도로 빠르게 판단
3. **상관 분석** = 단일 경보가 아닌 연관 경보를 함께 분석
4. **경보 피로** = FP가 많으면 실제 위협을 놓칠 위험
5. **튜닝** = 반복되는 FP를 줄여 분석 효율 향상

---

## 과제

1. Wazuh 알림 중 Level 8 이상을 모두 추출하여 TP/FP로 분류하시오 (근거 포함)
2. 가장 많이 발생하는 경보 Top 5를 분석하고 FP 여부를 판정하시오
3. 경보 분석 보고서를 작성하시오

---

## 참고 자료

- SANS SOC Analyst Handbook
- Wazuh Alert Levels Documentation
- SOC Metrics: MTTD, MTTR
