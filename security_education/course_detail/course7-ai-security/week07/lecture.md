# Week 07: AI 에이전트 아키텍처 (상세 버전)

## 학습 목표
- AI 에이전트의 개념과 구성요소를 이해한다
- Master-Manager-SubAgent 계층 구조를 설명할 수 있다
- 에이전트 간 통신 프로토콜(A2A)을 이해한다
- OpsClaw의 아키텍처를 분석할 수 있다


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

## 용어 해설 (AI/LLM 보안 활용 과목)

| 용어 | 영문 | 설명 | 비유 |
|------|------|------|------|
| **LLM** | Large Language Model | 대규모 언어 모델 (GPT, Claude, Llama 등) | 방대한 텍스트로 훈련된 AI 두뇌 |
| **Ollama** | Ollama | 로컬에서 LLM을 실행하는 도구 | 내 PC에서 돌리는 AI |
| **프롬프트** | Prompt | LLM에게 보내는 입력 텍스트 | AI에게 하는 질문/지시 |
| **토큰** | Token (LLM) | LLM이 처리하는 텍스트의 최소 단위 (~4글자) | 단어의 조각 |
| **컨텍스트 윈도우** | Context Window | LLM이 한 번에 처리할 수 있는 최대 토큰 수 | AI의 단기 기억 용량 |
| **파인튜닝** | Fine-tuning | 사전 학습된 모델을 특정 목적에 맞게 추가 학습 | 일반의가 전공 수련 |
| **RAG** | Retrieval-Augmented Generation | 외부 데이터를 검색하여 LLM 응답에 반영 | AI가 자료를 찾아보고 답변 |
| **에이전트** | Agent (AI) | 도구를 사용하여 자율적으로 작업하는 AI 시스템 | AI 비서 (스스로 판단하고 실행) |
| **도구 호출** | Tool Calling | LLM이 외부 도구/API를 호출하는 기능 | AI가 계산기를 꺼내서 계산 |
| **하네스** | Harness | 에이전트를 관리·제어하는 프레임워크 | AI 비서의 업무 규칙·관리 시스템 |
| **Playbook** | Playbook | 자동화된 작업 절차 (도구/스킬의 순서화된 묶음) | 표준 작업 지침서 (SOP) |
| **PoW** | Proof of Work | 작업 증명 (해시 체인 기반 실행 기록) | 작업 일지 + 영수증 |
| **보상** | Reward (RL) | 태스크 실행 결과에 따른 점수 (+성공, -실패) | 성과급 |
| **Q-learning** | Q-learning | 보상을 기반으로 최적 행동을 학습하는 RL 알고리즘 | 시행착오로 최적 경로를 찾는 학습 |
| **UCB1** | Upper Confidence Bound | 탐험(exploration)과 활용(exploitation)을 균형 잡는 전략 | "가본 길 vs 안 가본 길" 선택 전략 |
| **SubAgent** | SubAgent | 대상 서버에서 명령을 실행하는 경량 런타임 | 현장 파견 직원 |


---

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
    "subagent_url": "http://10.20.30.1:8002"
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


---

---

## 심화: AI/LLM 보안 활용 보충

### Ollama API 상세 가이드

#### 기본 호출 구조

```bash
# Ollama는 OpenAI 호환 API를 제공한다
# URL: http://192.168.0.105:11434/v1/chat/completions

curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",        ← 사용할 모델
    "messages": [
      {"role": "system", "content": "역할 부여"},  ← 시스템 프롬프트
      {"role": "user", "content": "실제 질문"}      ← 사용자 입력
    ],
    "temperature": 0.1,            ← 출력 다양성 (0=결정론, 1=창의적)
    "max_tokens": 1000             ← 최대 출력 길이
  }'
```

> **각 파라미터의 의미:**
> - `model`: 어떤 AI 모델을 사용할지. 큰 모델일수록 정확하지만 느림
> - `messages`: 대화 내역. system(역할)→user(질문)→assistant(답변) 순서
> - `temperature`: 0에 가까우면 같은 질문에 항상 같은 답. 1에 가까우면 매번 다른 답
> - `max_tokens`: 출력 길이 제한. 토큰 ≈ 글자 수 × 0.5 (한국어)

#### 모델별 특성

| 모델 | 크기 | 응답 시간 | 정확도 | 권장 용도 |
|------|------|---------|--------|---------|
| gemma3:12b | 12B | ~5초 | 양호 | 분석, 룰 생성, 보고서 |
| llama3.1:8b | 8B | ~3초 | 보통 | 빠른 분류, 검증 |
| qwen3:8b | 8B | ~5초 | 보통 | 교차 검증 (다른 벤더) |
| gpt-oss:120b | 120B | ~25초 | 높음 | 복잡한 분석 (시간 여유 시) |

#### 프롬프트 엔지니어링 패턴

**패턴 1: 역할 부여 (Role Assignment)**
```json
{"role":"system","content":"당신은 10년 경력의 SOC 분석가입니다. MITRE ATT&CK에 정통합니다."}
```

**패턴 2: 출력 형식 강제 (Format Control)**
```json
{"role":"system","content":"반드시 JSON으로만 응답하세요. 마크다운, 설명, 주석을 포함하지 마세요."}
```

**패턴 3: Few-shot (예시 제공)**
```json
{"role":"user","content":"예시:\n입력: SSH 실패 5회\n출력: {\"severity\":\"HIGH\",\"attack\":\"brute_force\"}\n\n이제 분석하세요: SSH 실패 20회 후 성공"}
```

**패턴 4: Chain of Thought (단계별 사고)**
```json
{"role":"system","content":"단계별로 분석하세요: 1)현상 파악 2)원인 추론 3)ATT&CK 매핑 4)대응 방안"}
```

### OpsClaw API 핵심 흐름 요약

```
[1] POST /projects                     → 프로젝트 생성
    Body: {"name":"...", "master_mode":"external"}
    Response: {"project":{"id":"prj_xxx"}}

[2] POST /projects/{id}/plan           → plan 단계로 전환
[3] POST /projects/{id}/execute        → execute 단계로 전환

[4] POST /projects/{id}/execute-plan   → 태스크 실행
    Body: {"tasks":[...], "parallel":true, "subagent_url":"..."}
    Response: {"overall":"success", "tasks_ok":N}

[5] GET /projects/{id}/evidence/summary → 증적 확인
[6] GET /projects/{id}/replay           → 타임라인 재구성
[7] POST /projects/{id}/completion-report → 완료 보고

모든 API에 필수: -H "X-API-Key: opsclaw-api-key-2026"
```


---

## 자가 점검 퀴즈 (10문항)

이번 주차의 핵심 내용을 점검한다. 8/10 이상 정답을 목표로 한다.

**Q1.** 이번 주차 "Week 07: AI 에이전트 아키텍처"의 핵심 목적은 무엇인가?
- (a) 네트워크 속도 향상  (b) **LLM 기법/개념의 이해와 실습**  (c) 데이터베이스 관리  (d) UI 디자인

**Q2.** 이 주제에서 AI 보안의 역할은?
- (a) 성능 최적화  (b) 비용 절감  (c) **체계적 분류와 대응 기준 제공**  (d) 사용자 편의

**Q3.** 실습에서 사용한 주요 도구/명령어의 1차 목적은?
- (a) 파일 복사  (b) **OpsClaw 수행 및 결과 확인**  (c) 메모리 관리  (d) 화면 출력

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


