# Week 10: OpsClaw (2) - Playbook + RL (상세 버전)

## 학습 목표
- OpsClaw Playbook의 개념과 구조를 이해한다
- Playbook을 생성하고 실행할 수 있다
- 강화학습(RL) 보상 시스템의 원리를 이해한다
- RL 학습과 정책 추천 기능을 활용할 수 있다


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

# Week 10: OpsClaw (2) - Playbook + RL

## 학습 목표
- OpsClaw Playbook의 개념과 구조를 이해한다
- Playbook을 생성하고 실행할 수 있다
- 강화학습(RL) 보상 시스템의 원리를 이해한다
- RL 학습과 정책 추천 기능을 활용할 수 있다

---

## 1. Playbook이란?

Playbook은 반복적인 보안 작업을 재사용 가능한 절차로 정의한 것이다.
Ansible Playbook과 유사한 개념이다.

### Playbook vs 수동 실행

| 항목 | 수동 dispatch | Playbook |
|------|-------------|----------|
| 재사용 | 매번 작성 | 한 번 정의, 반복 사용 |
| 일관성 | 사람마다 다름 | 항상 동일 |
| 감사 | 명령어 추적 어려움 | 실행 이력 자동 기록 |
| 공유 | 개인 지식 | 팀 공유 가능 |

---

## 2. Playbook 구조

> **이 실습을 왜 하는가?**
> AI/LLM 보안 활용 과목에서 이 주차의 실습은 핵심 개념을 **직접 체험**하여 이론을 실무로 연결하는 과정이다.
> AI 보안 자동화에서 이 기법은 로그 분석, 룰 생성, 대응 실행을 LLM이 수행하는 기반이다.
>
> **이걸 하면 무엇을 알 수 있는가?**
> - 이론에서 배운 개념이 실제 시스템에서 어떻게 동작하는지 확인
> - 실제 명령어와 도구 사용법을 체득
> - 결과를 분석하고 보안 관점에서 판단하는 능력 배양
>
> **주의:** 모든 실습은 허가된 실습 환경(10.20.30.0/24)에서만 수행한다.


```json
{
  "name": "ssh-security-audit",
  "description": "SSH 보안 설정 점검 Playbook",
  "steps": [
    {
      "order": 1,
      "tool": "run_command",
      "params": {"command": "sshd -T | grep -E 'permitrootlogin|passwordauthentication|maxauthtries'"},
      "risk_level": "low",
      "description": "SSH 설정 확인"
    },
    {
      "order": 2,
      "tool": "run_command",
      "params": {"command": "last -20"},
      "risk_level": "low",
      "description": "최근 로그인 이력 확인"
    },
    {
      "order": 3,
      "tool": "run_command",
      "params": {"command": "grep 'Failed password' /var/log/auth.log | tail -20"},
      "risk_level": "low",
      "description": "인증 실패 로그 확인"
    }
  ]
}
```

---

## 3. Playbook 실행

### 3.1 Playbook을 execute-plan으로 실행

```bash
PID="프로젝트_ID"

# Playbook의 steps를 tasks로 변환하여 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "instruction_prompt": "sshd -T 2>/dev/null | grep -E \"permitrootlogin|passwordauthentication|maxauthtries\" || echo SSH_NOT_RUNNING",
        "risk_level": "low"
      },
      {
        "order": 2,
        "instruction_prompt": "last -10",
        "risk_level": "low"
      },
      {
        "order": 3,
        "instruction_prompt": "grep \"Failed password\" /var/log/auth.log 2>/dev/null | tail -10 || echo NO_AUTH_LOG",
        "risk_level": "low"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

---

## 4. 강화학습 (RL) 보상 시스템

### 4.1 PoW와 보상의 관계

```
태스크 실행 → PoW 블록 생성 → 보상(reward) 자동 계산
```

execute-plan으로 태스크를 실행하면 자동으로:
1. PoW 블록이 생성된다
2. 태스크 결과에 따라 보상이 기록된다
3. 보상 데이터가 RL 학습에 사용된다

### 4.2 보상 요소

| 요소 | 설명 | 보상 영향 |
|------|------|----------|
| 성공/실패 | 명령 실행 결과 | 성공 +1, 실패 -1 |
| risk_level | 태스크 위험도 | 높을수록 보상 큼 |
| 실행 시간 | 태스크 소요 시간 | 빠를수록 보상 큼 |
| 에이전트 | 실행한 SubAgent | 에이전트별 통계 |

### 4.3 Q-learning 기초

OpsClaw는 Q-learning 알고리즘으로 최적 행동을 학습한다.

```
Q(상태, 행동) = 현재 보상 + 감가율 * 미래 최대 보상
```

- **상태(State)**: 에이전트 ID + risk_level
- **행동(Action)**: 태스크 실행 여부
- **보상(Reward)**: 성공/실패 + 위험도 가중치

---

## 5. RL API 사용

### 5.1 학습 실행

```bash
# 축적된 보상 데이터로 Q-learning 학습
curl -s -X POST http://localhost:8000/rl/train \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### 5.2 정책 추천

```bash
# 특정 에이전트+위험수준에 대한 최적 행동 추천
curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=low" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool

curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=high" \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### 5.3 정책 상태 확인

```bash
# 현재 학습된 Q-table 상태
curl -s http://localhost:8000/rl/policy \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

### 5.4 보상 랭킹

```bash
# SubAgent별 누적 보상 순위
curl -s http://localhost:8000/pow/leaderboard \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
```

---

## 6. 실습

### 실습 1: 보안 점검 Playbook 실행

```bash
# 프로젝트 생성
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"playbook-lab","request_text":"Playbook 실습","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

# Stage 전환
curl -s -X POST "http://localhost:8000/projects/$PID/plan" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" \
  -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# 시스템 보안 점검 Playbook 실행
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"uname -a", "risk_level":"low"},
      {"order":2, "instruction_prompt":"ss -tlnp | head -20", "risk_level":"low"},
      {"order":3, "instruction_prompt":"df -h", "risk_level":"low"},
      {"order":4, "instruction_prompt":"free -h", "risk_level":"low"},
      {"order":5, "instruction_prompt":"who", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 2: RL 학습 체험

```bash
# 현재 정책 확인
curl -s http://localhost:8000/rl/policy \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool

# 학습 실행
curl -s -X POST http://localhost:8000/rl/train \
  -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool

# 학습 후 추천 확인
for level in low medium high critical; do
  echo "=== $level ==="
  curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=$level" \
    -H "X-API-Key: opsclaw-api-key-2026" | python3 -m json.tool
done
```

### 실습 3: LLM으로 Playbook 설계

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "OpsClaw 보안 자동화 전문가입니다. 보안 점검 Playbook을 JSON 형식으로 설계합니다."},
      {"role": "user", "content": "Linux 서버의 보안 하드닝 상태를 점검하는 Playbook을 설계하세요.\n점검 항목: SSH 설정, 패스워드 정책, 방화벽 상태, 불필요 서비스, 파일 권한\n\nJSON 형식: {\"name\": \"\", \"steps\": [{\"order\": N, \"tool\": \"run_command\", \"params\": {\"command\": \"\"}, \"risk_level\": \"\", \"description\": \"\"}]}"}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 7. RL이 보안 자동화에 주는 가치

```
                 ┌──────────────┐
                 │  위험 판단    │
                 │  (Q-table)   │
                 └──────┬───────┘
                        │
    태스크 요청 ─────────▶ RL 추천 ─────▶ 실행/거부
                        │
                  과거 데이터 기반
                  자동 의사결정
```

- **반복적 작업**: 과거 성공/실패 데이터로 최적 전략 학습
- **위험 관리**: risk_level별 행동 정책 자동 조정
- **에이전트 평가**: SubAgent별 신뢰도 축적

---

## 핵심 정리

1. Playbook은 반복 가능한 보안 작업을 표준화한 절차이다
2. execute-plan의 tasks가 Playbook의 steps에 대응한다
3. PoW 블록과 보상이 자동 생성되어 RL 학습 데이터가 된다
4. Q-learning으로 에이전트별, 위험수준별 최적 행동을 추천한다
5. LLM으로 Playbook을 설계하고, RL로 실행 정책을 최적화한다

---

## 다음 주 예고
- Week 11: 자율 미션 - /a2a/mission Red/Blue Team


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

**Q1.** "Week 10: OpsClaw (2) - Playbook + RL"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **AI/LLM 보안 활용의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. Playbook이란?"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. Playbook 구조"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **AI/LLM 보안 활용 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. Playbook 실행"의 실무 활용 방안은?
- (a) 개인 블로그  (b) **보안 점검, 대응, 보고서 작성에 활용**  (c) 게임 개발  (d) 영상 편집

**Q6.** 이 주차에서 LLM/OpsClaw의 핵심 원칙은?
- (a) 모든 기능 비활성화  (b) **최소 권한 + 모니터링 + 대응의 조합**  (c) 무조건 차단  (d) 설정 변경 금지

**Q7.** 실습 결과를 평가할 때 가장 중요한 기준은?
- (a) 파일 크기  (b) **보안 효과성과 정확성**  (c) 실행 속도  (d) 줄 수

**Q8.** 이 주제가 전체 AI/LLM 보안 활용 커리큘럼에서 차지하는 위치는?
- (a) 독립적 주제  (b) **이전 주차의 심화/다음 주차의 기반**  (c) 선택 과목  (d) 부록

**Q9.** 실무에서 이 기법을 적용할 때 주의할 점은?
- (a) 속도  (b) **법적 허가, 범위 준수, 증적 관리**  (c) 디자인  (d) 비용

**Q10.** 이번 주차 학습의 성과를 어떻게 측정하는가?
- (a) 시간  (b) **실습 완료율 + 퀴즈 점수 + 과제 품질**  (c) 줄 수  (d) 파일 수

**정답:** Q1:b, Q2:b, Q3:b, Q4:b, Q5:b, Q6:b, Q7:b, Q8:b, Q9:b, Q10:b

---
---

> **실습 환경 검증:** 이 교안의 실습 명령은 실제 인프라(10.20.30.0/24)에서 동작을 확인하였습니다. (2026-03-28 검증)
