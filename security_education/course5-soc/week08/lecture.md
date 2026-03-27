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
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  echo -n "실패: "
  sshpass -p1 ssh user@$ip "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo 0"
  echo -n "성공: "
  sshpass -p1 ssh user@$ip "grep -c 'Accepted' /var/log/auth.log 2>/dev/null || echo 0"
done

# 공격자 IP Top 5
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -5"

# 공격 대상 사용자 Top 5
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
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
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip: sudo 이력 ==="
  sshpass -p1 ssh user@$ip "grep 'COMMAND=' /var/log/auth.log 2>/dev/null | tail -5"
done

# 비인가 sudo 시도
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "grep 'NOT in sudoers' /var/log/auth.log 2>/dev/null"
done
```

**질문**:
1. 위험한 sudo 명령이 있는가? (4점)
2. 비인가 sudo 시도가 있는가? 있다면 어떤 사용자인가? (4점)

### A-3. 시스템 이상 징후 (7점)

```bash
# syslog에서 이상 징후 검색
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo "=== $ip ==="
  sshpass -p1 ssh user@$ip "grep -iE 'error|fail|critical|emergency|segfault|oom' /var/log/syslog 2>/dev/null | wc -l"
done

# 커널 오류 확인
sshpass -p1 ssh user@192.168.208.142 "journalctl -p err --no-pager 2>/dev/null | tail -10"
```

---

## Part B: 네트워크/웹 로그 분석 (25점)

### B-1. Suricata IPS 분석 (12점)

```bash
# Suricata 알림 통계
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/fast.log 2>/dev/null | wc -l"

# 알림 유형 Top 10
sshpass -p1 ssh user@192.168.208.150 "cat /var/log/suricata/fast.log 2>/dev/null | \
  grep -oP '\[\*\*\].*?\[\*\*\]' | sort | uniq -c | sort -rn | head -10"

# Priority별 분포
sshpass -p1 ssh user@192.168.208.150 "grep -oP 'Priority: [0-9]+' /var/log/suricata/fast.log 2>/dev/null | \
  sort | uniq -c | sort -rn"

# 공격자 IP Top 5
sshpass -p1 ssh user@192.168.208.150 "grep -oP '\\{\\w+\\} [0-9.]+' /var/log/suricata/fast.log 2>/dev/null | \
  awk '{print \$2}' | sort | uniq -c | sort -rn | head -5"
```

**질문**:
1. 가장 빈번한 알림 3가지와 의미를 설명하시오 (6점)
2. 가장 의심스러운 IP와 근거를 제시하시오 (3점)
3. Priority 1 알림이 있는 경우 상세 분석하시오 (3점)

### B-2. 웹 로그 분석 (13점)

```bash
# 웹 로그 기본 통계
sshpass -p1 ssh user@192.168.208.151 "wc -l /var/log/nginx/access.log 2>/dev/null || echo '0'"

# HTTP 상태코드 분포
sshpass -p1 ssh user@192.168.208.151 "awk '{print \$9}' /var/log/nginx/access.log 2>/dev/null | \
  sort | uniq -c | sort -rn | head -10"

# 웹 공격 패턴 검색
sshpass -p1 ssh user@192.168.208.151 "grep -iE 'union|select|script|alert|\.\./' /var/log/nginx/access.log 2>/dev/null | wc -l"

# 의심스러운 요청 샘플
sshpass -p1 ssh user@192.168.208.151 "grep -iE 'union|select|script|\.\./' /var/log/nginx/access.log 2>/dev/null | head -5"

# User-Agent 분석
sshpass -p1 ssh user@192.168.208.151 "awk -F'\"' '{print \$6}' /var/log/nginx/access.log 2>/dev/null | \
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
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
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
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
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
for ip in 192.168.208.142 192.168.208.150 192.168.208.151 192.168.208.152; do
  sshpass -p1 ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 user@$ip "hostname" 2>/dev/null \
    && echo "$ip: OK" || echo "$ip: FAIL"
done

# 로그 존재 확인
sshpass -p1 ssh user@192.168.208.142 "ls -lh /var/log/auth.log 2>/dev/null"
sshpass -p1 ssh user@192.168.208.150 "ls -lh /var/log/suricata/fast.log 2>/dev/null"
sshpass -p1 ssh user@192.168.208.152 "ls -lh /var/ossec/logs/alerts/alerts.json 2>/dev/null"
```

---

## 참고

- 오픈 북 시험: 강의 자료 + 인터넷 검색 가능
- 제출: 분석 보고서 + SIGMA 규칙 파일
- ATT&CK 참조: https://attack.mitre.org
