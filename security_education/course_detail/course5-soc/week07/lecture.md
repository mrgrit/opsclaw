# Week 07: SIGMA 룰 작성 (상세 버전)

## 학습 목표
- SIGMA 룰의 구조와 문법을 이해한다
- 커스텀 탐지 규칙을 SIGMA 형식으로 작성할 수 있다
- SIGMA 룰을 Wazuh/SIEM 형식으로 변환하는 방법을 이해한다
- 실습 환경의 위협에 맞는 탐지 규칙을 개발한다
- 각 개념의 보안 관점에서의 위험과 대응 방안을 분석할 수 있다
- OpsClaw를 활용하여 실습 작업을 자동화하고 증적을 관리할 수 있다
- 실제 보안 사고 사례와 연결하여 학습 내용을 적용할 수 있다


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

# Week 07: SIGMA 룰 작성

## 학습 목표

- SIGMA 룰의 구조와 문법을 이해한다
- 커스텀 탐지 규칙을 SIGMA 형식으로 작성할 수 있다
- SIGMA 룰을 Wazuh/SIEM 형식으로 변환하는 방법을 이해한다
- 실습 환경의 위협에 맞는 탐지 규칙을 개발한다

---

## 1. SIGMA란?

### 1.1 개요

SIGMA는 **SIEM 제품에 독립적인** 탐지 규칙 표현 형식이다.

- YARA가 파일/악성코드용이라면, SIGMA는 **로그/이벤트용**
- YAML 형식으로 작성
- 다양한 SIEM으로 변환 가능 (Splunk, ELK, QRadar, Wazuh 등)
- 커뮤니티에서 수천 개의 규칙을 공유

### 1.2 왜 SIGMA인가?

| 문제 | SIGMA의 해결 |
|------|------------|
| SIEM마다 쿼리 문법이 다름 | 하나의 규칙으로 여러 SIEM에 적용 |
| 탐지 규칙 공유가 어려움 | 표준화된 형식으로 쉽게 공유 |
| 제품 교체 시 규칙 재작성 필요 | 변환기로 자동 변환 |

---

## 2. SIGMA 룰 구조

### 2.1 기본 구조

```yaml
title: SSH Brute Force Attempt
id: a8b1c2d3-e4f5-6789-abcd-ef0123456789
status: experimental
description: Detects multiple SSH authentication failures
author: Student
date: 2026/03/27
references:
    - https://attack.mitre.org/techniques/T1110/
tags:
    - attack.credential_access
    - attack.t1110
logsource:
    category: authentication
    product: linux
detection:
    selection:
        EventType: 'authentication_failure'
        Service: 'sshd'
    condition: selection | count() > 5
    timeframe: 5m
falsepositives:
    - Legitimate admin with wrong password
    - Automated monitoring tools
level: medium
```

### 2.2 각 필드 설명

| 필드 | 필수 | 설명 |
|------|------|------|
| title | 필수 | 규칙 이름 |
| id | 권장 | UUID (고유 식별자) |
| status | 권장 | stable / experimental / test |
| description | 필수 | 규칙 설명 |
| logsource | 필수 | 로그 소스 정의 |
| detection | 필수 | 탐지 조건 |
| level | 필수 | 심각도 (low/medium/high/critical) |
| tags | 권장 | ATT&CK 매핑 등 |
| falsepositives | 권장 | 오탐 가능 상황 |

---

## 3. detection 문법 상세

### 3.1 기본 매칭

```yaml
detection:
    selection:
        FieldName: 'value'            # 정확한 값
        FieldName|contains: 'value'   # 포함
        FieldName|startswith: 'value'  # 시작
        FieldName|endswith: 'value'    # 끝
        FieldName|re: 'regex'          # 정규식
    condition: selection
```

### 3.2 리스트 매칭 (OR)

```yaml
detection:
    selection:
        FieldName:
            - 'value1'
            - 'value2'
            - 'value3'
    condition: selection  # value1 OR value2 OR value3
```

### 3.3 다중 조건 (AND)

```yaml
detection:
    selection:
        FieldA: 'value1'
        FieldB: 'value2'   # FieldA=value1 AND FieldB=value2
    condition: selection
```

### 3.4 조건 결합

```yaml
detection:
    selection1:
        FieldA: 'value1'
    selection2:
        FieldB: 'value2'
    filter:
        FieldC: 'whitelist_value'
    condition: (selection1 or selection2) and not filter
```

### 3.5 집계 (Aggregation)

```yaml
detection:
    selection:
        EventType: 'login_failure'
    condition: selection | count(SourceIP) > 10
    timeframe: 5m
```

---

## 4. SIGMA 룰 작성 실습

### 4.1 규칙 1: SSH 무차별 대입 탐지

```yaml
title: SSH Brute Force Detection
id: d1234567-89ab-cdef-0123-456789abcdef
status: experimental
description: |
    Detects SSH brute force attempts by monitoring
    multiple authentication failures from the same source IP
author: Security Course Student
date: 2026/03/27
tags:
    - attack.credential_access
    - attack.t1110.001
logsource:
    category: authentication
    product: linux
    service: sshd
detection:
    selection:
        action: 'failure'
        service: 'sshd'
    condition: selection | count(src_ip) > 5
    timeframe: 5m
falsepositives:
    - Administrator testing access
    - Automated deployment tools
level: medium
```

검증:
```bash
# 실제 환경에서 이 패턴이 발생하는지 확인
sshpass -p1 ssh user@192.168.208.142 "grep 'Failed password' /var/log/auth.log 2>/dev/null | \
  awk '{print \$(NF-3)}' | sort | uniq -c | sort -rn | awk '\$1>5 {print \$1, \$2}' | head -5"
```

### 4.2 규칙 2: 의심스러운 sudo 사용

```yaml
title: Suspicious Sudo Command Execution
id: e2345678-9abc-def0-1234-567890abcdef
status: experimental
description: Detects sudo execution of potentially dangerous commands
author: Security Course Student
date: 2026/03/27
tags:
    - attack.privilege_escalation
    - attack.t1548.003
logsource:
    product: linux
    service: auth
detection:
    selection:
        program: 'sudo'
    keywords:
        - 'COMMAND=/bin/bash'
        - 'COMMAND=/bin/sh'
        - 'COMMAND=/usr/bin/passwd'
        - 'COMMAND=/usr/sbin/useradd'
        - 'COMMAND=/usr/sbin/userdel'
        - 'COMMAND=/usr/bin/chmod 777'
    condition: selection and keywords
falsepositives:
    - Legitimate system administration
level: high
```

검증:
```bash
sshpass -p1 ssh user@192.168.208.142 "grep 'COMMAND=' /var/log/auth.log 2>/dev/null | \
  grep -E 'bash|sh |passwd|useradd|userdel|chmod' | tail -5"
```

### 4.3 규칙 3: 웹 SQL Injection 탐지

```yaml
title: Web SQL Injection Attempt
id: f3456789-abcd-ef01-2345-67890abcdef0
status: experimental
description: Detects SQL injection attempts in web access logs
author: Security Course Student
date: 2026/03/27
tags:
    - attack.initial_access
    - attack.t1190
logsource:
    category: webserver
    product: nginx
detection:
    selection:
        cs-uri-query|contains:
            - 'UNION SELECT'
            - 'OR 1=1'
            - "' OR '"
            - 'DROP TABLE'
            - 'INSERT INTO'
            - '--'
            - 'SLEEP('
            - 'BENCHMARK('
    condition: selection
falsepositives:
    - Web application using SQL keywords in URLs
level: high
```

검증:
```bash
sshpass -p1 ssh user@192.168.208.151 "grep -iE 'union.select|or.1=1|drop.table|sleep\(' /var/log/nginx/access.log 2>/dev/null | tail -5"
```

### 4.4 규칙 4: 파일 무결성 위반

```yaml
title: Critical System File Modification
id: a4567890-bcde-f012-3456-7890abcdef01
status: stable
description: Detects modification of critical system files
author: Security Course Student
date: 2026/03/27
tags:
    - attack.persistence
    - attack.t1543
logsource:
    product: linux
    service: syscheck
detection:
    selection:
        file_path|startswith:
            - '/etc/passwd'
            - '/etc/shadow'
            - '/etc/sudoers'
            - '/etc/ssh/sshd_config'
            - '/etc/crontab'
        event_type: 'modified'
    condition: selection
falsepositives:
    - Legitimate system administration
    - Automated configuration management
level: critical
```

---

## 5. SIGMA를 Wazuh 규칙으로 변환

### 5.1 수동 변환

SIGMA 규칙을 Wazuh의 XML 규칙으로 변환한다:

```xml
<!-- SSH Brute Force Detection (SIGMA → Wazuh) -->
<group name="custom_sigma,">
  <rule id="100100" level="10" frequency="5" timeframe="300">
    <if_matched_sid>5503</if_matched_sid>
    <same_source_ip/>
    <description>SIGMA: SSH Brute Force - 5+ failures from same IP in 5min</description>
    <mitre>
      <id>T1110.001</id>
    </mitre>
    <group>authentication_failures,sigma,</group>
  </rule>
</group>
```

### 5.2 자동 변환 도구

```bash
# sigma-cli 또는 pySigma 사용 (설치 필요)
# pip install sigma-cli

# Wazuh 백엔드로 변환
# sigma convert -t wazuh -p wazuh ssh_bruteforce.yml

# 현재 Wazuh의 사용자 정의 규칙 확인
sshpass -p1 ssh user@192.168.208.152 "cat /var/ossec/etc/rules/local_rules.xml 2>/dev/null"
```

### 5.3 Wazuh에 규칙 추가 후 테스트

```bash
# 규칙 문법 검증
sshpass -p1 ssh user@192.168.208.152 "/var/ossec/bin/wazuh-logtest 2>/dev/null <<< 'Mar 27 10:00:00 opsclaw sshd[1234]: Failed password for root from 10.0.0.1 port 22 ssh2'"
```

---

## 6. SIGMA 룰 공유 및 커뮤니티

### 6.1 SigmaHQ

공식 규칙 저장소: https://github.com/SigmaHQ/sigma

```
sigma/rules/
├── cloud/          # 클라우드 탐지 규칙
├── linux/          # Linux 탐지 규칙
├── network/        # 네트워크 탐지 규칙
├── web/            # 웹 탐지 규칙
└── windows/        # Windows 탐지 규칙
```

### 6.2 규칙 품질 수준

| 상태 | 의미 |
|------|------|
| stable | 검증 완료, 운영 사용 가능 |
| test | 테스트 단계 |
| experimental | 실험적, 오탐 가능 |

---

## 7. 종합 실습: 커스텀 탐지 규칙 개발

### 7.1 과정

```
1. 위협 시나리오 정의
2. 필요한 로그 소스 식별
3. 탐지 로직 설계
4. SIGMA 룰 작성
5. 실제 로그로 검증
6. Wazuh 규칙으로 변환
7. 배포 및 모니터링
```

### 7.2 실습: 내부자 위협 탐지

```yaml
title: After-Hours SSH Login
id: b5678901-cdef-0123-4567-890abcdef012
status: experimental
description: Detects SSH login outside business hours (22:00-06:00)
author: Security Course Student
date: 2026/03/27
tags:
    - attack.initial_access
    - attack.t1078
logsource:
    product: linux
    service: auth
detection:
    selection:
        action: 'success'
        service: 'sshd'
    timeframe_filter:
        - '|22:'
        - '|23:'
        - '|00:'
        - '|01:'
        - '|02:'
        - '|03:'
        - '|04:'
        - '|05:'
    condition: selection
falsepositives:
    - Night shift administrators
    - Emergency maintenance
level: medium
```

검증:
```bash
# 새벽 시간대 로그인 확인
sshpass -p1 ssh user@192.168.208.142 "grep 'Accepted' /var/log/auth.log 2>/dev/null | \
  awk '{print \$3}' | awk -F: '{h=\$1; if(h>=22||h<=5) print}' | head -10"
```

---

## 8. 핵심 정리

1. **SIGMA** = SIEM 독립적인 탐지 규칙 표준 (YAML 형식)
2. **구조** = logsource(어디서) + detection(무엇을) + level(심각도)
3. **detection** = selection + condition + filter 조합
4. **변환** = sigma-cli 또는 수동으로 Wazuh XML로 변환
5. **개발 프로세스** = 위협 정의 → 규칙 작성 → 검증 → 배포

---

## 과제

1. 실습 환경의 위협 3가지를 선택하여 SIGMA 규칙을 각각 작성하시오
2. 작성한 규칙을 실제 로그로 검증하시오 (탐지 건수 포함)
3. 1개 규칙을 Wazuh XML 형식으로 변환하시오

---

## 참고 자료

- SigmaHQ (https://github.com/SigmaHQ/sigma)
- SIGMA Specification (https://sigmahq.io/docs/)
- pySigma Documentation
- Wazuh Custom Rules Guide


---


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 07: SIGMA 룰 작성"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **보안관제 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 로그 분석의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **인시던트 대응 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

**Q4.** OpsClaw를 통해 실습을 실행하는 가장 큰 이점은?
- (a) 속도  (b) **모든 실행의 자동 증적(evidence) 기록**  (c) 무료  (d) 간편함

**Q5.** 이 주제의 보안 위험이 높은 이유는?
- (a) 비용이 많이 들어서  (b) 복잡해서  (c) **악용 시 시스템/데이터에 직접적 피해**  (d) 법적 문제

**Q6.** 방어/대응의 핵심 원칙은?
- (a) 모든 트래픽 차단  (b) **최소 권한 + 탐지 + 대응의 조합**  (c) 서버 재시작  (d) 비밀번호 변경

**Q7.** 실습 결과를 분석할 때 가장 먼저 확인해야 하는 것은?
- (a) 서버 이름  (b) **exit_code (성공/실패 여부)**  (c) 파일 크기  (d) 날짜

**Q8.** 이 주제와 관련된 MITRE ATT&CK 전술은?
- (a) Impact만  (b) Reconnaissance만  (c) **주제에 해당하는 전술(들)**  (d) 해당 없음

**Q9.** 실무에서 이 기법/도구를 사용할 때 가장 주의할 점은?
- (a) 속도  (b) **법적 허가와 범위 준수**  (c) 비용  (d) 보고서 양식

**Q10.** 다음 주차와의 연결 포인트는?
- (a) 관련 없음  (b) **이번 주 결과를 다음 주에서 활용/심화**  (c) 완전히 다른 주제  (d) 복습만

**정답:** Q1:b, Q2:c, Q3:b, Q4:b, Q5:c, Q6:b, Q7:b, Q8:c, Q9:b, Q10:b

---

## 과제 (다음 주까지)


## 검증 체크리스트

이번 주차의 학습을 완료하려면 다음 항목을 모두 확인하라:


