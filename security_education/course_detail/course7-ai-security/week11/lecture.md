# Week 11: 자율 미션 (상세 버전)

## 학습 목표
- 자율 미션(Autonomous Mission)의 개념을 이해한다
- Red Team / Blue Team 자율 에이전트의 동작 원리를 익힌다
- /a2a/mission API를 통한 자율 미션 실행을 실습한다
- Purple Team 자동화의 보안적 가치를 설명할 수 있다


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

# Week 11: 자율 미션

## 학습 목표
- 자율 미션(Autonomous Mission)의 개념을 이해한다
- Red Team / Blue Team 자율 에이전트의 동작 원리를 익힌다
- /a2a/mission API를 통한 자율 미션 실행을 실습한다
- Purple Team 자동화의 보안적 가치를 설명할 수 있다

---

## 1. 자율 미션이란?

자율 미션은 SubAgent가 **LLM의 추론 능력**을 활용하여 사람의 개입 없이 보안 작업을 수행하는 기능이다.

### 수동 실행 vs 자율 미션

| 항목 | 수동 (dispatch) | 자율 (mission) |
|------|---------------|---------------|
| 명령 | 사람이 직접 지정 | LLM이 스스로 결정 |
| 판단 | 사람이 결과 해석 | LLM이 결과 분석 후 다음 행동 결정 |
| 범위 | 단일 명령 | 목표 기반 다중 단계 |
| 자율성 | 없음 | 높음 |

---

## 2. Red Team vs Blue Team

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


### 2.1 역할 정의

| 팀 | 목표 | LLM 모델 | 성격 |
|----|------|---------|------|
| **Red Team** | 취약점 탐색, 공격 시뮬레이션 | gemma3:12b | 공격적, 탐색적 |
| **Blue Team** | 방어, 탐지, 대응 | llama3.1:8b | 방어적, 분석적 |

### 2.2 Purple Team

Red와 Blue를 동시에 운영하여 서로 상호작용하게 한다.

```
Red Team: 취약점 발견 → 공격 시도
    ↕ (정보 공유)
Blue Team: 공격 탐지 → 방어 강화
    ↕ (결과 피드백)
보안 수준 지속 향상
```

---

## 3. /a2a/mission API

### 3.1 미션 실행

```bash
# Red Team 미션: web 서버 취약점 탐색
curl -s -X POST "http://localhost:8000/projects/$PID/dispatch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "command": "RED_MISSION: web 서버(10.20.30.80)의 열린 포트와 서비스를 탐색하고 보안 취약점을 식별하라",
    "subagent_url": "http://10.20.30.1:8002"
  }' | python3 -m json.tool
```

### 3.2 미션 구조

SubAgent가 /a2a/mission 요청을 받으면:

```
1. 미션 목표 파악 (LLM 추론)
2. 실행 계획 수립 (어떤 명령을 실행할지)
3. 명령 실행 (run_command 도구 호출)
4. 결과 분석 (LLM이 결과 해석)
5. 다음 행동 결정 (추가 탐색 또는 완료)
6. 보고서 생성
```

### 3.3 Red Team 미션 예시

```bash
# 포트 스캔 → 서비스 식별 → 취약점 탐색
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Red Team 보안 전문가입니다. 주어진 대상의 보안 취약점을 체계적으로 탐색합니다. 교육/테스트 환경에서만 수행합니다."},
      {"role": "user", "content": "대상: web 서버 (10.20.30.80)\n\n다음 순서로 탐색 계획을 수립하세요:\n1. 포트 스캔 명령어\n2. 서비스 버전 확인 명령어\n3. 발견된 서비스별 취약점 확인 방법\n\n각 단계의 실행 명령어를 제시하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 3.4 Blue Team 미션 예시

```bash
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "system", "content": "Blue Team 방어 전문가입니다. 시스템의 보안 상태를 점검하고 강화 방안을 제시합니다."},
      {"role": "user", "content": "web 서버(10.20.30.80)에서 다음 Red Team 발견사항에 대한 방어 조치를 제시하세요:\n- SSH 포트(22) 외부 노출\n- 웹 서버 버전 헤더 노출\n- Docker 소켓 접근 가능\n\n각 취약점에 대한 구체적인 방어 명령어를 제시하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 4. Purple Team 자동화

### 4.1 Red → Blue 루프

```bash
# Step 1: Red Team이 취약점 발견
RED_FINDING="SSH 포트(22)가 0.0.0.0에 바인딩되어 외부에서 접근 가능"

# Step 2: Blue Team이 방어 조치 생성
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"llama3.1:8b\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"Blue Team입니다. Red Team 발견사항에 대한 방어 조치를 생성합니다.\"},
      {\"role\": \"user\", \"content\": \"Red Team 발견: $RED_FINDING\\n\\n즉시 실행 가능한 방어 조치 명령어를 제시하세요.\"}
    ],
    \"temperature\": 0.3
  }" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"

# Step 3: OpsClaw로 방어 조치 실행 (승인 후)
```

### 4.2 자동화 스크립트

```python
#!/usr/bin/env python3
"""purple_team_auto.py - 자율 Purple Team 시뮬레이션"""
import requests

OLLAMA = "http://192.168.0.105:11434/v1/chat/completions"
OPSCLAW = "http://localhost:8000"
API_KEY = "opsclaw-api-key-2026"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def red_team_scan(target):
    """Red Team: 취약점 탐색"""
    resp = requests.post(OLLAMA, json={
        "model": "gemma3:12b",
        "messages": [
            {"role": "system", "content": "Red Team 전문가. 취약점을 JSON 리스트로 보고."},
            {"role": "user", "content": f"대상 {target}의 일반적인 Linux 서버 취약점 3가지를 식별하세요."}
        ],
        "temperature": 0.3
    })
    return resp.json()["choices"][0]["message"]["content"]

def blue_team_defend(findings):
    """Blue Team: 방어 조치 생성"""
    resp = requests.post(OLLAMA, json={
        "model": "llama3.1:8b",
        "messages": [
            {"role": "system", "content": "Blue Team 전문가. 각 취약점에 대한 방어 명령어를 제시."},
            {"role": "user", "content": f"다음 취약점에 대한 방어 조치:\n{findings}"}
        ],
        "temperature": 0.3
    })
    return resp.json()["choices"][0]["message"]["content"]

# 실행
findings = red_team_scan("10.20.30.80")
print("=== Red Team 발견 ===")
print(findings)
print("\n=== Blue Team 방어 ===")
print(blue_team_defend(findings))
```

---

## 5. 실습

### 실습 1: Red Team 미션 실행

```bash
# 프로젝트 생성 및 준비
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{"name":"purple-team-lab","request_text":"Purple Team 실습","master_mode":"external"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")

curl -s -X POST "http://localhost:8000/projects/$PID/plan" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null
curl -s -X POST "http://localhost:8000/projects/$PID/execute" -H "X-API-Key: opsclaw-api-key-2026" > /dev/null

# Red Team: 정보 수집
curl -s -X POST "http://localhost:8000/projects/$PID/execute-plan" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: opsclaw-api-key-2026" \
  -d '{
    "tasks": [
      {"order":1, "instruction_prompt":"ss -tlnp", "risk_level":"low"},
      {"order":2, "instruction_prompt":"curl -sI http://10.20.30.80 | head -10", "risk_level":"low"},
      {"order":3, "instruction_prompt":"cat /etc/passwd | grep -v nologin | grep -v false", "risk_level":"low"}
    ],
    "subagent_url": "http://localhost:8002"
  }' | python3 -m json.tool
```

### 실습 2: Red 결과를 LLM으로 분석

```bash
# 수집된 정보를 LLM에 전달하여 취약점 식별
curl -s http://192.168.0.105:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma3:12b",
    "messages": [
      {"role": "system", "content": "Red Team 분석가입니다. 수집된 정보에서 보안 취약점을 식별합니다."},
      {"role": "user", "content": "다음은 대상 서버에서 수집한 정보입니다:\n\n1. 열린 포트: 22(SSH), 80(HTTP), 8000(API), 8002(SubAgent)\n2. HTTP 헤더: Server: nginx/1.24.0\n3. 셸 접근 가능 사용자: root, opsclaw, student\n\n보안 취약점과 공격 가능 경로를 분석하세요."}
    ],
    "temperature": 0.3
  }' | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 6. 안전 고려사항

자율 미션은 강력하지만 위험할 수 있다.

| 위험 | 방어 |
|------|------|
| 과도한 스캔 | rate limiting, 대상 화이트리스트 |
| 파괴적 명령 실행 | risk_level + dry_run |
| 정보 유출 | 미션 결과 접근 제어 |
| 무한 루프 | 최대 단계 수 제한 |

### 안전 규칙

1. 자율 미션은 **테스트 환경에서만** 실행한다
2. critical risk 명령은 **사용자 확인 필수**이다
3. 모든 미션 결과는 **PoW 체인에 기록**된다
4. **프로덕션 환경**에서는 읽기 전용 미션만 허용한다

---

## 핵심 정리

1. 자율 미션은 LLM이 스스로 판단하고 행동하는 보안 작업이다
2. Red Team은 공격 시뮬레이션, Blue Team은 방어 강화를 수행한다
3. Purple Team은 Red/Blue를 결합하여 보안 수준을 지속 향상시킨다
4. 안전 장치(risk_level, dry_run, PoW)로 자율 미션의 위험을 관리한다
5. 자율 미션은 보조 도구이며, 최종 판단은 사람이 내린다

---

## 다음 주 예고
- Week 12: Agent Daemon - explore + daemon + stimulate


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

**Q1.** "Week 11: 자율 미션"에서 가장 핵심적인 학습 목표는?
- (a) 데이터베이스 최적화  (b) **AI/LLM 보안 활용의 원리와 실습**  (c) UI 개발  (d) 네트워크 속도

**Q2.** "1. 자율 미션이란?"의 보안 관점에서의 의의는?
- (a) 성능 향상  (b) **보안 위협 이해 또는 방어 역량 강화**  (c) 비용 절감  (d) 사용성 개선

**Q3.** "2. Red Team vs Blue Team"에서 사용하는 주요 도구/기법은?
- (a) 워드프로세서  (b) **AI/LLM 보안 활용 전용 도구/명령**  (c) 게임 엔진  (d) 그래픽 도구

**Q4.** 이번 실습에서 OpsClaw evidence가 제공하는 가치는?
- (a) 속도  (b) **작업 증적의 자동 기록과 감사 추적**  (c) 화면 출력  (d) 파일 압축

**Q5.** "3. /a2a/mission API"의 실무 활용 방안은?
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
