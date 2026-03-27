# Week 03: 프롬프트 엔지니어링 for 보안

## 학습 목표
- 프롬프트 엔지니어링의 핵심 기법을 익힌다
- 보안 로그 분석용 프롬프트를 설계할 수 있다
- 취약점 설명 및 대응 방안 생성 프롬프트를 작성할 수 있다
- Few-shot, Chain-of-Thought 기법을 보안 업무에 적용할 수 있다

---

## 1. 프롬프트 엔지니어링이란?

LLM에 전달하는 입력(프롬프트)을 설계하여 원하는 출력을 이끌어내는 기술이다.
좋은 프롬프트 = 좋은 결과이다.

### 프롬프트의 구성요소

| 요소 | 설명 | 예시 |
|------|------|------|
| **역할** | AI의 전문 분야 설정 | "SOC 분석가로서" |
| **맥락** | 배경 정보 제공 | "Wazuh SIEM에서 수집된 로그" |
| **작업** | 구체적인 요청 | "위협 수준을 평가하라" |
| **형식** | 출력 형태 지정 | "JSON으로 응답하라" |
| **제약** | 제한 조건 | "200자 이내로" |

---

## 2. 핵심 프롬프트 기법

### 2.1 Zero-shot (예시 없이 요청)

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC 분석가로서 보안 이벤트를 분석합니다."},
      {"role": "user", "content": "다음 로그를 분석하세요:\nMar 27 10:15:33 web sshd[1234]: Failed password for root from 192.168.1.100 port 54321 ssh2"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 2.2 Few-shot (예시 포함)

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 로그를 분석하여 위협 수준을 평가하세요."},
      {"role": "user", "content": "로그: Failed password for admin from 10.0.0.5"},
      {"role": "assistant", "content": "위협수준: LOW\n분석: 단일 실패 시도. 내부 IP에서 발생. 사용자 실수 가능성 높음."},
      {"role": "user", "content": "로그: Failed password for root from 203.0.113.50 (5회 반복)"},
      {"role": "assistant", "content": "위협수준: HIGH\n분석: 외부 IP에서 root 계정 반복 시도. 브루트포스 공격 의심."},
      {"role": "user", "content": "로그: Accepted publickey for deploy from 10.20.30.80 port 22"}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 2.3 Chain-of-Thought (단계적 추론)

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 분석가입니다. 단계별로 추론하세요."},
      {"role": "user", "content": "다음 이벤트들을 시간순으로 분석하고, 단계별로 사고 경위를 추론하세요:\n\n1. 10:00 - web 서버에서 SQL 에러 로그 급증\n2. 10:05 - DB 서버에서 비정상 쿼리 실행\n3. 10:10 - DB 서버에서 외부로 대량 데이터 전송\n4. 10:15 - web 서버 접근 로그에 union select 패턴\n\n단계별로 추론하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 3. 보안 업무별 프롬프트 템플릿

### 3.1 로그 분석 프롬프트

```
[System]
당신은 SOC(Security Operations Center) Tier-2 분석가입니다.
아래 보안 로그를 분석하고 다음 형식으로 응답하세요:

- 이벤트 요약: (한 줄)
- 위협 수준: (CRITICAL/HIGH/MEDIUM/LOW/INFO)
- 공격 유형: (해당 시)
- 영향 범위: (영향받는 시스템)
- 대응 권고: (즉시 수행할 조치)

[User]
{로그 데이터 입력}
```

### 3.2 취약점 설명 프롬프트

```
[System]
보안 교육 전문가로서 취약점을 초보자도 이해할 수 있게 설명합니다.

[User]
다음 CVE를 분석해주세요:
- CVE ID: {CVE-YYYY-NNNNN}
- 영향 소프트웨어: {소프트웨어명}

다음 형식으로 응답:
1. 취약점 요약 (2줄)
2. 위험도와 이유
3. 공격 시나리오 (비유 사용)
4. 패치/대응 방법
```

### 3.3 보안 보고서 생성 프롬프트

```
[System]
CISO에게 보고할 보안 인시던트 보고서를 작성합니다.
비전문가도 이해할 수 있는 언어로 작성하되, 기술적 세부사항도 포함합니다.

[User]
다음 정보로 인시던트 보고서를 작성하세요:
- 발생 시각: {시각}
- 영향 시스템: {시스템}
- 공격 유형: {유형}
- 현재 상태: {상태}
- 수행 조치: {조치}
```

---

## 4. 구조화된 출력

### 4.1 JSON 형식 요청

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 이벤트를 분석하고 반드시 JSON 형식으로만 응답하세요."},
      {"role": "user", "content": "다음 로그를 분석하세요. JSON으로 응답: {\"severity\": \"\", \"type\": \"\", \"source_ip\": \"\", \"action\": \"\"}\n\nMar 27 14:22:01 secu suricata[5678]: [1:2001219:20] ET SCAN Potential SSH Scan from 45.33.32.156"}
    ],
    "temperature": 0
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 4.2 테이블 형식 요청

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "OWASP Top 10 (2021)을 마크다운 테이블로 정리해주세요. 컬럼: 순위, 취약점명, 설명(한 줄), 위험도"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 5. 실습

### 실습 1: 로그 분석 프롬프트 비교

```bash
# 나쁜 프롬프트
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "user", "content": "이 로그 분석해줘: Failed password for root from 203.0.113.50"}
    ]
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

echo "---"

# 좋은 프롬프트
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SOC Tier-2 분석가입니다. 위협수준(CRITICAL/HIGH/MEDIUM/LOW), 공격유형, 대응방안을 포함하여 분석하세요."},
      {"role": "user", "content": "환경: 웹 서버(Ubuntu 22.04), 인터넷 노출\n로그:\nMar 27 10:15:33 web sshd[1234]: Failed password for root from 203.0.113.50 port 54321 ssh2\nMar 27 10:15:35 web sshd[1234]: Failed password for root from 203.0.113.50 port 54322 ssh2\nMar 27 10:15:37 web sshd[1234]: Failed password for root from 203.0.113.50 port 54323 ssh2\n(총 50회 반복)"}
    ],
    "temperature": 0.2
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 2: CVE 분석 프롬프트

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "보안 교육 전문가입니다. 대학 1학년 학생도 이해할 수 있게 설명하세요."},
      {"role": "user", "content": "CVE-2021-44228 (Log4Shell)을 설명해주세요.\n\n형식:\n1. 한 줄 요약\n2. 비유로 설명 (일상 생활 비유)\n3. 공격 과정 (단계별)\n4. 대응 방법\n5. 교훈"}
    ],
    "temperature": 0.5
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 3: 대응 플레이북 자동 생성

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "인시던트 대응 전문가입니다. 구체적이고 실행 가능한 대응 절차를 작성합니다."},
      {"role": "user", "content": "SSH 브루트포스 공격이 탐지되었습니다.\n소스 IP: 203.0.113.50\n대상: web 서버 (10.20.30.80)\n시도 횟수: 500회/10분\n\n대응 플레이북을 단계별로 작성하세요. 각 단계에 실제 명령어를 포함하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. 프롬프트 엔지니어링 팁

### 좋은 프롬프트의 특징

1. **구체적**: "분석해줘" → "위협수준, 공격유형, 대응방안을 포함하여 분석"
2. **맥락 제공**: 환경, 시스템 정보, 배경을 포함
3. **형식 지정**: 출력 형식을 명확히 지정 (JSON, 테이블, 단계별)
4. **역할 부여**: 전문가 역할을 system 메시지로 설정
5. **예시 포함**: Few-shot으로 원하는 출력 패턴 제시

### 나쁜 프롬프트 vs 좋은 프롬프트

| 나쁜 프롬프트 | 좋은 프롬프트 |
|-------------|-------------|
| "이 로그 봐줘" | "SOC 분석가로서 이 Wazuh 알림의 위협수준을 평가하세요" |
| "보안 강화해" | "Ubuntu 22.04 SSH 서버의 보안 설정 5가지를 설명하세요" |
| "해킹 방법" | "SQL Injection의 원리와 방어 방법을 교육 목적으로 설명하세요" |

---

## 핵심 정리

1. 프롬프트 엔지니어링은 역할+맥락+작업+형식+제약으로 구성한다
2. Few-shot으로 예시를 제공하면 더 정확한 출력을 얻는다
3. Chain-of-Thought로 복잡한 보안 분석의 추론 과정을 이끌어낸다
4. JSON/테이블 형식 지정으로 자동화에 활용 가능한 구조화된 출력을 얻는다
5. temperature를 낮게 설정하면 보안 분석에 적합한 일관된 답변을 얻는다

---

## 다음 주 예고
- Week 04: LLM 기반 로그 분석 - Wazuh 알림을 LLM으로 분석
