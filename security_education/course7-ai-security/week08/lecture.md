# Week 08: 중간고사 - LLM 보안 도구 구축

## 시험 개요

| 항목 | 내용 |
|------|------|
| 유형 | 실기 시험 (도구 구축 + 분석 보고서) |
| 시간 | 90분 |
| 배점 | 100점 |
| 환경 | Ollama (192.168.0.105:11434), OpsClaw (localhost:8000) |
| 제출 | 스크립트 + 실행 결과 + 분석 보고서 |

---

## 시험 범위

- Week 02: LLM 기초, Ollama API
- Week 03: 프롬프트 엔지니어링
- Week 04: LLM 기반 로그 분석
- Week 05: 탐지 룰 자동 생성
- Week 06: 취약점 분석
- Week 07: AI 에이전트 아키텍처

---

## 문제 1: 보안 로그 분석 도구 (40점)

### 요구사항

Wazuh 스타일의 보안 알림을 입력받아 LLM으로 분석하는 셸 스크립트를 작성하라.

### 입력 데이터

```json
[
  {"id":1,"rule_id":"5710","level":10,"desc":"SSH login failed","src":"203.0.113.50","dst":"web","time":"10:00"},
  {"id":2,"rule_id":"5710","level":10,"desc":"SSH login failed","src":"203.0.113.50","dst":"web","time":"10:01"},
  {"id":3,"rule_id":"5710","level":10,"desc":"SSH login failed","src":"203.0.113.50","dst":"web","time":"10:02"},
  {"id":4,"rule_id":"5501","level":5,"desc":"SSH login success","src":"203.0.113.50","dst":"web","time":"10:05"},
  {"id":5,"rule_id":"550","level":8,"desc":"User added: backdoor","src":"web","dst":"web","time":"10:06"},
  {"id":6,"rule_id":"510","level":12,"desc":"File integrity changed: /etc/passwd","src":"web","dst":"web","time":"10:07"}
]
```

### 기능 요구사항

1. **알림 분류** (10점): 각 알림의 위협 수준 분류 (CRITICAL/HIGH/MEDIUM/LOW)
2. **상관 분석** (15점): 알림들을 연결하여 공격 시나리오 추론
3. **대응 방안** (10점): 즉시 수행할 조치 목록 생성
4. **JSON 출력** (5점): 결과를 구조화된 JSON으로 출력

### 스크립트 구조

```bash
#!/bin/bash
# midterm_analyzer.sh

OLLAMA_URL="http://192.168.0.105:11434/v1/chat/completions"
MODEL="gemma3:12b"
ALERTS='[위 JSON 데이터]'

# 1. 알림 분류
echo "=== 알림 분류 ==="
curl -s $OLLAMA_URL \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"...\"},
      {\"role\": \"user\", \"content\": \"...\"}
    ],
    \"temperature\": 0
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

# 2. 상관 분석
# ...

# 3. 대응 방안
# ...
```

---

## 문제 2: 탐지 룰 생성 (30점)

### 2-1. SIGMA 룰 생성 (15점)

다음 3가지 공격에 대한 SIGMA 룰을 LLM으로 생성하라:

1. **SSH 브루트포스**: 5분 내 동일 IP에서 10회 이상 SSH 인증 실패
2. **웹 디렉토리 스캔**: 1분 내 동일 IP에서 20개 이상 404 응답
3. **권한 상승**: 일반 사용자가 /etc/shadow 접근 시도

```bash
# 각 공격에 대해 LLM으로 SIGMA 룰 생성
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "SIGMA 룰 전문가입니다. 유효한 SIGMA YAML을 생성하세요."},
      {"role": "user", "content": "[공격 설명]"}
    ],
    "temperature": 0.2
  }'
```

### 2-2. 룰 품질 검증 (15점)

생성된 3개의 룰을 LLM으로 상호 검증하라.
각 룰에 대해 오탐 가능성, 우회 방법, 개선 사항을 분석하라.

---

## 문제 3: OpsClaw 오케스트레이션 (30점)

### 3-1. 프로젝트 생성 및 실행 (15점)

OpsClaw API를 사용하여 보안 점검 프로젝트를 생성하고 실행하라.

```bash
# 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "name": "midterm-security-check",
    "request_text": "서버 보안 상태 점검",
    "master_mode": "external"
  }'

# Stage 전환 → 실행 → 결과 확인
# (전체 플로우를 수행하라)
```

### 3-2. 결과 분석 보고서 (15점)

실행 결과를 LLM으로 분석하여 보안 상태 보고서를 작성하라.

보고서에 포함할 내용:
1. 점검 개요
2. 발견 사항
3. 위험도 평가
4. 대응 권고

---

## 채점 기준

| 항목 | 배점 | 기준 |
|------|------|------|
| 알림 분류 정확성 | 10 | 각 알림의 위협 수준 적절성 |
| 상관 분석 | 15 | 공격 킬체인 추론 논리성 |
| 대응 방안 | 10 | 조치의 구체성, 실행 가능성 |
| JSON 출력 | 5 | 유효한 JSON, 필수 필드 포함 |
| SIGMA 룰 | 15 | 문법 정확성, 탐지 효과 |
| 룰 검증 | 15 | 분석 깊이, 개선 제안 |
| OpsClaw 실행 | 15 | API 호출 정확성, 플로우 완성 |
| 분석 보고서 | 15 | 분석 깊이, 보고서 품질 |

---

## 핵심 팁

1. **프롬프트 품질**: system 메시지에 역할과 출력 형식을 명확히 지정
2. **temperature**: 분석 업무는 0~0.3, 창의적 업무는 0.5~0.7
3. **Few-shot**: 예시를 포함하면 더 정확한 출력을 얻음
4. **검증**: LLM 출력은 반드시 직접 확인
5. **API 키**: OpsClaw API 호출 시 X-API-Key 헤더 필수

---

## 다음 주 예고
- Week 09: OpsClaw 기본 - project, dispatch, execute-plan 실전 활용
