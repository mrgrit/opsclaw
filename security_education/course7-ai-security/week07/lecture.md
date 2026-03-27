# Week 07: AI 에이전트 아키텍처

## 학습 목표
- AI 에이전트의 개념과 구성요소를 이해한다
- Master-Manager-SubAgent 계층 구조를 설명할 수 있다
- 에이전트 간 통신 프로토콜(A2A)을 이해한다
- OpsClaw의 아키텍처를 분석할 수 있다

---

## 1. AI 에이전트란?

AI 에이전트는 **자율적으로 목표를 달성**하기 위해 환경을 관찰하고, 판단하고, 행동하는 시스템이다.

### 에이전트 vs 챗봇

| 항목 | 챗봇 | 에이전트 |
|------|------|---------|
| 상호작용 | 질문-답변 | 목표 기반 자율 행동 |
| 도구 사용 | 없음 | 다양한 도구 호출 |
| 계획 수립 | 없음 | 목표 → 계획 → 실행 |
| 상태 관리 | 대화 이력만 | 작업 상태, 환경 상태 |
| 자율성 | 낮음 | 높음 |

### 에이전트 구성요소

```
에이전트 = LLM(두뇌) + 도구(손) + 메모리(기억) + 계획(전략)
```

| 구성요소 | 역할 | 예시 |
|---------|------|------|
| **LLM** | 추론, 판단 | Gemma3, Llama3.1 |
| **도구(Tools)** | 실제 작업 수행 | 명령 실행, 파일 읽기, API 호출 |
| **메모리** | 과거 경험 저장 | 작업 이력, 학습된 지식 |
| **계획** | 작업 분해, 순서 결정 | Task 목록, 우선순위 |

---

## 2. 계층적 에이전트 아키텍처

### 2.1 왜 계층 구조인가?

단일 에이전트는 복잡한 작업에서 한계가 있다.
계층 구조로 역할을 분리하면:
- **전문화**: 각 에이전트가 특정 역할에 집중
- **격리**: 실행 환경 격리로 안전성 확보
- **확장성**: 새 서버/역할 추가 용이

### 2.2 Master-Manager-SubAgent

```
[Master]  ← 계획 수립 (LLM 기반 추론)
    ↓
[Manager] ← 실행 관리 (상태 추적, 증거 기록)
    ↓
[SubAgent] ← 실제 명령 실행 (각 서버에 배포)
```

| 계층 | 포트 | 역할 | 위치 |
|------|------|------|------|
| Master | :8001 | LLM 기반 계획 수립 | control plane |
| Manager | :8000 | 프로젝트/태스크 관리, API 진입점 | control plane |
| SubAgent | :8002 | 명령 실행, 결과 반환 | 각 서버 |

---

## 3. OpsClaw 아키텍처

### 3.1 전체 구조

```
                    ┌─────────────────┐
                    │  Claude Code /  │
                    │  External Master│
                    └────────┬────────┘
                             │ HTTP API
                    ┌────────▼────────┐
                    │  Manager API    │
                    │  :8000          │
                    │  - 프로젝트 관리  │
                    │  - 증거 기록     │
                    │  - PoW 체인     │
                    └────────┬────────┘
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ SubAgent     │ │ SubAgent     │ │ SubAgent     │
    │ secu:8002    │ │ web:8002     │ │ siem:8002    │
    │ nftables/IPS │ │ Docker/WAF   │ │ Wazuh SIEM   │
    └──────────────┘ └──────────────┘ └──────────────┘
```

### 3.2 통신 흐름

```bash
# 1. External Master(Claude Code)가 Manager에 프로젝트 생성
curl -X POST http://localhost:8000/projects \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"name":"test","request_text":"테스트","master_mode":"external"}'

# 2. Manager가 SubAgent에 명령 전달 (dispatch)
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"command":"hostname","subagent_url":"http://localhost:8002"}'

# 3. SubAgent가 명령 실행 후 결과 반환 → Manager가 증거 기록
```

### 3.3 안전 장치

| 안전 장치 | 설명 |
|----------|------|
| **API 인증** | X-API-Key 헤더 필수 |
| **Risk Level** | low/medium/high/critical 분류 |
| **Dry Run** | critical 태스크는 자동 시뮬레이션 |
| **PoW 체인** | 모든 작업을 블록체인으로 기록 |
| **증거 기록** | 명령어, 결과, 타임스탬프 영구 저장 |

---

## 4. A2A (Agent-to-Agent) 프로토콜

에이전트 간 통신을 위한 표준화된 인터페이스이다.

### 4.1 SubAgent API 엔드포인트

```
POST /a2a/invoke_tool    → 도구(명령어) 실행
POST /a2a/invoke_llm     → 로컬 LLM 호출
POST /a2a/analyze         → LLM 기반 분석
POST /a2a/mission         → 자율 미션 실행
GET  /health              → 상태 확인
```

### 4.2 도구 호출 예시

```bash
# Manager를 통해 SubAgent의 도구 호출
# (직접 SubAgent 호출은 금지)
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "uname -a",
    "subagent_url": "http://192.168.208.150:8002"
  }'
```

---

## 5. 실습

### 실습 1: OpsClaw API 탐색

```bash
# Manager API 상태 확인
curl -s http://localhost:8000/health | python3 -m json.tool

# 프로젝트 목록 조회
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  http://localhost:8000/projects | python3 -m json.tool

# SubAgent 상태 확인
curl -s http://localhost:8002/health | python3 -m json.tool
```

### 실습 2: LLM으로 에이전트 아키텍처 분석

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "AI 시스템 아키텍트입니다."},
      {"role": "user", "content": "Master-Manager-SubAgent 3계층 AI 에이전트 아키텍처의 장단점을 분석하세요.\n\n고려사항:\n1. 보안 (권한 격리)\n2. 확장성 (서버 추가)\n3. 장애 허용 (단일 실패점)\n4. 성능 (레이턴시)\n5. 감사 (작업 추적)"}
    ],
    "temperature": 0.4
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 실습 3: 간단한 오케스트레이션 체험

```bash
# 프로젝트 생성 → 계획 → 실행 → 결과 확인 플로우
PROJECT=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"arch-lab","request_text":"아키텍처 실습","master_mode":"external"}')
echo $PROJECT | python3 -m json.tool

# 프로젝트 ID 추출
PID=$(echo $PROJECT | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Project ID: $PID"

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool

curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool

# 명령 실행
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"command":"hostname && date","subagent_url":"http://localhost:8002"}'

# 증거 확인
curl -s -H "X-API-Key: opsclaw-api-key-2026" \
  "http://localhost:8000/projects/$PID/evidence/summary" | python3 -m json.tool
```

---

## 6. 다른 에이전트 프레임워크 비교

| 프레임워크 | 특징 | 용도 |
|-----------|------|------|
| **OpsClaw** | 보안 특화, PoW, 계층적 | IT 운영/보안 자동화 |
| **LangChain** | 범용, 도구 체인 | 다양한 LLM 앱 |
| **AutoGPT** | 자율 에이전트 | 범용 자동화 |
| **CrewAI** | 다중 에이전트 협업 | 팀 기반 작업 |

---

## 핵심 정리

1. AI 에이전트는 LLM + 도구 + 메모리 + 계획으로 구성된 자율 시스템이다
2. Master-Manager-SubAgent 계층 구조로 역할을 분리하고 안전성을 확보한다
3. A2A 프로토콜로 에이전트 간 표준화된 통신을 수행한다
4. OpsClaw는 API 인증, Risk Level, PoW 체인 등 다중 안전 장치를 제공한다
5. 모든 명령은 Manager를 통해서만 SubAgent에 전달한다 (직접 호출 금지)

---

## 다음 주 예고
- Week 08: 중간고사 - LLM 보안 도구 구축
