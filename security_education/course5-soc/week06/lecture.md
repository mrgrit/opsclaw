# Week 06: 경보 분석 (2) - 실전 + ATT&CK 매핑

## 학습 목표

- 실제 공격 로그를 분석하고 공격 유형을 식별할 수 있다
- MITRE ATT&CK 프레임워크의 구조를 이해한다
- 탐지된 경보를 ATT&CK 전술/기법에 매핑할 수 있다
- 킬 체인 관점에서 공격 흐름을 재구성할 수 있다

---

## 1. MITRE ATT&CK 프레임워크

### 1.1 ATT&CK이란?

**ATT&CK** = Adversarial Tactics, Techniques, and Common Knowledge

- 실제 사이버 공격에서 관찰된 전술/기법을 체계적으로 정리한 지식 기반
- https://attack.mitre.org
- SOC, Red/Blue Team에서 사실상의 표준으로 사용

### 1.2 구조

```
전술 (Tactic)     = "공격자의 목표" (WHY)
  └ 기법 (Technique)  = "목표 달성 방법" (HOW)
      └ 하위 기법 (Sub-technique) = "구체적 구현"
```

### 1.3 Enterprise ATT&CK 14개 전술

| ID | 전술 | 설명 | 예시 |
|----|------|------|------|
| TA0001 | 초기 접근 (Initial Access) | 시스템 침입 | 피싱, 취약점 악용 |
| TA0002 | 실행 (Execution) | 코드 실행 | 명령줄, 스크립트 |
| TA0003 | 지속성 (Persistence) | 재접근 확보 | 백도어, cron 등록 |
| TA0004 | 권한 상승 (Privilege Escalation) | 높은 권한 획득 | sudo 악용, 커널 취약점 |
| TA0005 | 방어 회피 (Defense Evasion) | 탐지 회피 | 로그 삭제, 난독화 |
| TA0006 | 자격 증명 접근 (Credential Access) | 인증 정보 탈취 | 비밀번호 크래킹 |
| TA0007 | 탐색 (Discovery) | 환경 파악 | 포트 스캔, 계정 조회 |
| TA0008 | 측면 이동 (Lateral Movement) | 다른 시스템 침투 | SSH, RDP |
| TA0009 | 수집 (Collection) | 데이터 수집 | 파일 수집 |
| TA0010 | 유출 (Exfiltration) | 데이터 유출 | HTTP, DNS 터널링 |
| TA0011 | 명령 및 제어 (C2) | 원격 조종 | 리버스 셸 |
| TA0040 | 영향 (Impact) | 시스템 파괴 | 랜섬웨어, 데이터 삭제 |
| TA0042 | 정찰 (Reconnaissance) | 사전 정보 수집 | OSINT |
| TA0043 | 자원 개발 (Resource Dev.) | 공격 인프라 준비 | 도메인 등록, 악성코드 제작 |

---

## 2. 실제 공격 로그 분석

### 2.1 시나리오: SSH 무차별 대입 → 권한 상승

```bash
# 1단계: 정찰 (Reconnaissance) - TA0043
# 포트 스캔 흔적
sshpass -p1 ssh user@192.168.208.150 "grep -i 'scan' /var/log/suricata/fast.log 2>/dev/null | tail -5"

# 2단계: 초기 접근 (Initial Access) - TA0001
# SSH 무차별 대입 공격
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | head -5"

# 무차별 대입 후 성공 여부
sshpass -p1 ssh user@192.168.208.142 "grep 'Accepted password' /var/log/auth.log 2>/dev/null | tail -5"

# 3단계: 실행 (Execution) - TA0002
# 로그인 후 실행된 명령 (auth.log에서 sudo 사용 확인)
sshpass -p1 ssh user@192.168.208.142 "grep 'sudo:' /var/log/auth.log 2>/dev/null | tail -10"

# 4단계: 권한 상승 (Privilege Escalation) - TA0004
# sudo를 통한 root 권한 획득
sshpass -p1 ssh user@192.168.208.142 "grep 'COMMAND=' /var/log/auth.log 2>/dev/null | tail -10"
```

### 2.2 시나리오: 웹 공격 체인

```bash
# 1단계: 정찰 - 디렉토리 스캐닝
sshpass -p1 ssh user@192.168.208.151 "grep ' 404 ' /var/log/nginx/access.log 2>/dev/null | \
  awk '{print \$1}' | sort | uniq -c | sort -rn | head -5"

# 2단계: 초기 접근 - SQL Injection 시도
sshpass -p1 ssh user@192.168.208.151 "grep -iE 'union|select.*from|or.1=1' /var/log/nginx/access.log 2>/dev/null | tail -5"

# 3단계: Suricata에서 웹 공격 탐지
sshpass -p1 ssh user@192.168.208.150 "grep -i 'SQL\|XSS\|injection\|web' /var/log/suricata/fast.log 2>/dev/null | tail -10"

# 4단계: Wazuh에서 웹 공격 경보
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        groups = r.get('groups',[])
        if 'web' in str(groups) or 'attack' in str(groups):
            print(f'  [{r.get(\"level\",0)}] {r.get(\"description\",\"\")}')
    except: pass
\" 2>/dev/null | tail -10"
```

---

## 3. ATT&CK 매핑 실습

### 3.1 Wazuh의 ATT&CK 매핑

Wazuh는 일부 규칙에 MITRE ATT&CK ID를 포함하고 있다.

```bash
# ATT&CK 매핑이 있는 경보 확인
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/logs/alerts/alerts.json 2>/dev/null | python3 -c \"
import sys, json
from collections import Counter
techniques = Counter()
for line in sys.stdin:
    try:
        a = json.loads(line)
        r = a.get('rule',{})
        mitre = r.get('mitre',{})
        for tech in mitre.get('technique',[]):
            techniques[tech] += 1
        for tid in mitre.get('id',[]):
            techniques[tid] += 1
    except: pass
if techniques:
    print('=== ATT&CK 기법별 통계 ===')
    for tech, cnt in techniques.most_common(15):
        print(f'  {cnt:4d}건: {tech}')
else:
    print('ATT&CK 매핑된 경보가 없거나 mitre 필드 미포함')
\" 2>/dev/null"
```

### 3.2 수동 ATT&CK 매핑

경보에 ATT&CK 매핑이 없어도, 분석원이 직접 매핑할 수 있다:

| 경보 유형 | ATT&CK 전술 | ATT&CK 기법 |
|-----------|------------|------------|
| SSH 인증 실패 다수 | 자격증명 접근 (TA0006) | Brute Force (T1110) |
| SSH 로그인 성공 (외부IP) | 초기 접근 (TA0001) | Valid Accounts (T1078) |
| sudo 실행 | 권한 상승 (TA0004) | Abuse Elevation Control (T1548) |
| 파일 변경 탐지 | 지속성 (TA0003) | Modify System Process (T1543) |
| 포트 스캔 | 탐색 (TA0007) | Network Service Discovery (T1046) |
| SQL Injection | 초기 접근 (TA0001) | Exploit Public-Facing App (T1190) |
| 로그 파일 삭제 | 방어 회피 (TA0005) | Indicator Removal (T1070) |
| 대량 데이터 전송 | 유출 (TA0010) | Exfiltration Over C2 (T1041) |

---

## 4. 킬 체인 분석

### 4.1 Cyber Kill Chain (Lockheed Martin)

```
1. 정찰 (Reconnaissance)     → 포트 스캔, 정보 수집
2. 무기화 (Weaponization)     → 악성코드 제작
3. 배달 (Delivery)            → 피싱, 웹 취약점 악용
4. 악용 (Exploitation)        → 취약점 실행
5. 설치 (Installation)        → 백도어 설치
6. 명령/제어 (C2)              → 원격 조종
7. 목표 달성 (Actions)         → 데이터 유출, 파괴
```

### 4.2 실습: 킬 체인 재구성

```bash
# 실습 환경에서 관찰 가능한 킬 체인 단계를 추적

echo "=== 1. 정찰 단계 ==="
echo "포트 스캔 흔적:"
sshpass -p1 ssh user@192.168.208.150 "grep -i 'scan' /var/log/suricata/fast.log 2>/dev/null | wc -l"

echo ""
echo "=== 2. 초기 접근 시도 ==="
echo "SSH 무차별 대입:"
sshpass -p1 ssh user@192.168.208.142 "grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo '0'"
echo "웹 공격 시도:"
sshpass -p1 ssh user@192.168.208.151 "grep -cE 'union|select|script' /var/log/nginx/access.log 2>/dev/null || echo '0'"

echo ""
echo "=== 3. 초기 접근 성공 ==="
echo "외부IP SSH 로그인 성공:"
sshpass -p1 ssh user@192.168.208.142 "grep 'Accepted' /var/log/auth.log 2>/dev/null | grep -v '192.168.208' | head -5"

echo ""
echo "=== 4. 권한 상승 ==="
echo "sudo 사용:"
sshpass -p1 ssh user@192.168.208.142 "grep 'COMMAND=' /var/log/auth.log 2>/dev/null | tail -5"

echo ""
echo "=== 5. 지속성 확보 (의심) ==="
echo "cron 변경:"
sshpass -p1 ssh user@192.168.208.142 "ls -la /var/spool/cron/crontabs/ 2>/dev/null"
echo "SSH authorized_keys:"
sshpass -p1 ssh user@192.168.208.142 "ls -la ~/.ssh/authorized_keys 2>/dev/null || echo '없음'"
```

---

## 5. ATT&CK Navigator 활용

### 5.1 ATT&CK Navigator란?

ATT&CK 매트릭스를 시각화하는 도구이다.
https://mitre-attack.github.io/attack-navigator/

### 5.2 실습: 관찰된 기법 매핑

지금까지 실습 환경에서 탐지한 기법을 정리한다:

```
관찰된 ATT&CK 기법:
- T1110 Brute Force (SSH 무차별 대입)
- T1078 Valid Accounts (로그인 성공)
- T1046 Network Service Discovery (포트 스캔)
- T1190 Exploit Public-Facing App (웹 공격)
- T1548 Abuse Elevation Control (sudo)
```

ATT&CK Navigator에서 해당 기법에 색상을 표시하여 "우리 환경의 위협 맵"을 만든다.

---

## 6. 종합 분석 보고서

### 6.1 양식

```
=== 공격 분석 보고서 ===
분석일: 2026-03-27
분석원: (이름)

[공격 개요]
- 공격 유형: (SSH 무차별 대입 / 웹 공격 등)
- 공격 기간: YYYY-MM-DD HH:MM ~ YYYY-MM-DD HH:MM
- 출발지: X.X.X.X
- 대상: (서버명/IP)

[킬 체인 분석]
1. 정찰: (관찰 내용)
2. 무기화: (해당 없음 / 정보 없음)
3. 배달: (공격 방법)
4. 악용: (취약점 이용 내용)
5. 설치: (관찰 내용)
6. C2: (관찰 내용)
7. 목표: (성공/실패)

[ATT&CK 매핑]
| 전술 | 기법 ID | 기법명 | 증거 |
|------|---------|--------|------|
| TA0006 | T1110 | Brute Force | auth.log 실패 150건 |
| ... | ... | ... | ... |

[판정]
- TP / FP 판정 및 근거
- 공격 성공 여부
- 피해 범위

[권고사항]
- 즉시 조치
- 단기 개선
- 중장기 개선
```

---

## 7. 핵심 정리

1. **ATT&CK** = 전술(WHY) → 기법(HOW) → 하위기법 체계
2. **14개 전술** = 정찰부터 영향까지 공격의 전 단계
3. **킬 체인** = 공격의 시간순 흐름을 재구성
4. **매핑** = 경보를 ATT&CK 기법에 연결하여 공격 맥락 파악
5. **상관 분석** = 여러 경보를 연결하여 전체 공격 그림 파악

---

## 과제

1. 실습 환경의 Wazuh/Suricata 경보를 분석하여 ATT&CK 매핑 표를 작성하시오
2. 관찰된 공격 시나리오를 킬 체인으로 재구성하시오
3. 공격 분석 보고서를 작성하시오

---

## 참고 자료

- MITRE ATT&CK (https://attack.mitre.org)
- ATT&CK Navigator (https://mitre-attack.github.io/attack-navigator/)
- Lockheed Martin Cyber Kill Chain
