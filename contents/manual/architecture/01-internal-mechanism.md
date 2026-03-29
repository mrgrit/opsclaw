# OpsClaw 내부 메커니즘 상세 가이드

## 1. 3계층 아키텍처 개요

OpsClaw는 **Master - Manager - SubAgent** 3계층 구조로 설계되어 있다.
각 계층은 독립적인 FastAPI 서비스로 실행되며, REST API를 통해 통신한다.

```
┌──────────────────────────────────────────────────────────┐
│                     사용자 / Claude Code                   │
│               (CLI, Web UI, External Master)               │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP REST
                         ▼
┌──────────────────────────────────────────────────────────┐
│              Master Service (:8001)                        │
│   LLM 기반 계획 수립, 리뷰, Escalation, RAG 참조           │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP REST
                         ▼
┌──────────────────────────────────────────────────────────┐
│              Manager API (:8000)                           │
│   프로젝트 수명주기, 상태 머신, Evidence, Policy Engine     │
│   PoW 채굴, RL 학습, Notification, RBAC, Audit             │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP REST (A2A 프로토콜)
                         ▼
┌──────────────────────────────────────────────────────────┐
│            SubAgent Runtime (:8002)                        │
│   실제 명령 실행, LLM 분석, 도구 설치, 자율 미션            │
│   (각 서버에 1개씩 배포)                                    │
└──────────────────────────────────────────────────────────┘
```

### 1.1 Master Service (:8001)

Master는 LLM(Ollama)을 활용하여 **지적 판단**을 담당한다.

**핵심 기능:**
- `/projects/{id}/master-plan`: 요구사항 분석 후 Task 배열 생성
- `/projects/{id}/master-review`: 실행 결과 검수 (approved/rejected/needs_replan)
- `/projects/{id}/replan`: 재계획 지시
- `/runtime/invoke`: LLM 직접 호출

**작업 계획 생성 과정:**

1. 프로젝트의 `request_text`를 읽는다
2. `retrieval_documents` 테이블에서 FTS로 유사 Playbook/완료보고서를 검색한다 (RAG)
3. LLM에 요구사항 + 유사 사례를 전달하여 JSON 형식 Task 배열을 생성한다
4. 각 Task에 `order`, `title`, `playbook_hint`, `instruction_prompt`, `risk_level`을 부여한다

```bash
# Master Plan 생성 (Native 모드)
curl -X POST http://localhost:8001/projects/{project_id}/master-plan \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 응답 예시
{
  "summary": "v-secu 서버 방화벽 점검 및 불필요 포트 차단",
  "tasks": [
    {"order": 1, "title": "현재 nftables 규칙 확인", "instruction_prompt": "nft list ruleset", "risk_level": "low"},
    {"order": 2, "title": "열린 포트 스캔", "instruction_prompt": "ss -tlnp", "risk_level": "low"},
    {"order": 3, "title": "불필요 포트 차단", "instruction_prompt": "nft add rule ...", "risk_level": "high"}
  ],
  "similar_playbooks": [{"name": "firewall_audit", "relevance": "keyword"}]
}
```

**Master Review 과정:**

```bash
# 리뷰 생성
curl -X POST http://localhost:8001/projects/{project_id}/master-review \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "reviewer_id": "master-llm",
    "review_status": "approved",
    "summary": "방화벽 설정 정상 완료, 변경사항 적절",
    "auto_replan": false
  }'
```

### 1.2 Manager API (:8000)

Manager는 OpsClaw의 **핵심 control-plane**으로, 모든 상태 관리와 데이터 저장을 담당한다.

**핵심 기능 영역:**

| 영역 | 설명 | 주요 엔드포인트 |
|------|------|-----------------|
| 프로젝트 수명주기 | 생성~종료까지 상태 전이 | `/projects`, `/projects/{id}/plan` 등 |
| Evidence 관리 | 실행 증적 기록/조회 | `/projects/{id}/evidence` |
| PoW 채굴 | 작업증명 블록체인 | `/pow/blocks`, `/pow/verify` |
| RL 학습 | Q-learning + UCB1 | `/rl/train`, `/rl/recommend` |
| 4계층 메모리 | Evidence → Experience | `/experience`, `/projects/{id}/memory/build` |
| Playbook 엔진 | 결정적 실행 | `/playbooks`, `/projects/{id}/playbook/run` |
| Schedule/Watcher | 반복/감시 실행 | `/schedules`, `/watchers` |
| Notification | 알림 라우팅 | `/notifications/channels`, `/notifications/rules` |
| RBAC/Audit | 접근 제어/감사 | `/admin/roles`, `/admin/audit` |

### 1.3 SubAgent Runtime (:8002)

SubAgent는 각 서버에 배포되어 **실제 명령을 실행**한다.

**A2A (Agent-to-Agent) 프로토콜 엔드포인트:**

| 엔드포인트 | 기능 |
|-----------|------|
| `POST /a2a/run_script` | bash 스크립트 실행 |
| `POST /a2a/invoke_llm` | SubAgent 로컬 LLM 호출 |
| `POST /a2a/install_tool` | 도구 설치 (apt/pip/npm) |
| `POST /a2a/analyze` | 명령 출력 LLM 분석 |
| `POST /a2a/mission` | 자율 Red/Blue 미션 실행 |
| `GET /capabilities` | SubAgent 능력 목록 |
| `GET /health` | 상태 확인 |

```bash
# SubAgent는 Manager를 통해서만 호출한다 (직접 호출 금지)
# Manager의 dispatch가 내부적으로 A2A를 호출함
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command": "hostname", "subagent_url": "http://192.168.0.108:8002"}'
```

---

## 2. 상태 머신 (LangGraph)

프로젝트는 LangGraph 기반 상태 머신으로 관리된다.
각 Stage 전환은 API 호출로 이루어진다.

```
                     ┌──────────┐
                     │  intake   │  POST /projects (자동)
                     └────┬─────┘
                          │
                     ┌────▼─────┐
                     │   plan   │  POST /projects/{id}/plan
                     └────┬─────┘
                          │
                     ┌────▼─────┐
                     │ execute  │  POST /projects/{id}/execute
                     └────┬─────┘
                          │
                     ┌────▼─────┐
              ┌──────┤ validate │  POST /projects/{id}/validate
              │      └────┬─────┘
              │           │
        needs_replan      │ passed
              │      ┌────▼─────┐
              │      │  report  │  POST /projects/{id}/report/finalize
              │      └────┬─────┘
              │           │
              │      ┌────▼─────┐
              └─────►│  close   │  POST /projects/{id}/close
                     └──────────┘
```

**Stage 전환 규칙:**

- `intake → plan`: 무조건 전환 가능
- `plan → execute`: 무조건 전환 가능
- `execute → validate`: 실행 후 자동 또는 수동 전환
- `validate → report`: 검증 통과 시
- `validate → plan` (replan): 검증 실패 시 재계획
- `report → close`: 보고서 확정 후 종료

```bash
# 프로젝트 생성 (intake 자동)
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name": "fw-audit", "request_text": "방화벽 규칙 점검", "master_mode": "external"}'

# Stage 순차 전환
curl -X POST http://localhost:8000/projects/{id}/plan -H "X-API-Key: $OPSCLAW_API_KEY"
curl -X POST http://localhost:8000/projects/{id}/execute -H "X-API-Key: $OPSCLAW_API_KEY"

# execute-plan으로 실제 Task 실행
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"tasks": [{"order": 1, "instruction_prompt": "nft list ruleset", "risk_level": "low"}],
       "subagent_url": "http://192.168.0.108:8002"}'

# 종료
curl -X POST http://localhost:8000/projects/{id}/close -H "X-API-Key: $OPSCLAW_API_KEY"
```

**LangGraph 자동 실행:**

`POST /projects/{id}/run`을 호출하면 LangGraph가 intake부터 close까지 자동으로 전환한다.
approval이 필요한 단계에서는 멈추고 사용자 확인을 대기한다.

---

## 3. Evidence 흐름

모든 명령 실행은 Evidence로 기록된다. 이것이 OpsClaw의 핵심 가치다.

```
명령 실행          Evidence 기록         PoW 블록           보상 계산
 command    →   stdout/stderr/    →   SHA-256 채굴   →   base_score
                exit_code                                 + speed_bonus
                                                          - risk_penalty
```

### 3.1 Evidence 생성 과정

1. Manager가 SubAgent에 `run_script` A2A 요청을 보낸다
2. SubAgent가 bash 스크립트를 실행한다
3. SubAgent가 `stdout`, `stderr`, `exit_code`를 반환한다
4. Manager가 `evidence` 테이블에 기록한다
5. Evidence ID가 프로젝트에 연결된다

```bash
# Evidence 조회
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/{id}/evidence

# Evidence 요약
curl -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/{id}/evidence/summary
```

**Evidence 테이블 주요 필드:**

| 필드 | 설명 |
|------|------|
| `id` | Evidence 고유 ID |
| `project_id` | 소속 프로젝트 |
| `agent_role` | 실행 주체 (manager/subagent/master) |
| `tool_name` | 사용된 도구 |
| `command_text` | 실행 명령어 |
| `stdout_ref` | 표준 출력 (inline:// 형식) |
| `stderr_ref` | 표준 에러 |
| `exit_code` | 종료 코드 |
| `evidence_type` | command/file_diff/api_call/probe/report_fragment |

### 3.2 Minimal Evidence (수동 기록)

외부에서 실행한 결과도 Evidence로 기록할 수 있다.

```bash
curl -X POST http://localhost:8000/projects/{id}/evidence/minimal \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "직접 실행한 명령",
    "stdout": "실행 결과",
    "stderr": "",
    "exit_code": 0
  }'
```

---

## 4. PoW (Proof of Work) 채굴

`execute-plan`이 Task를 실행할 때마다 자동으로 PoW 블록이 생성된다.

### 4.1 블록 구조

```
┌──────────────────────────────────────────────────┐
│  PoW Block                                        │
│  ─────────────────────────────────                │
│  id:            pow_xxxx                          │
│  agent_id:      http://192.168.0.108:8002         │
│  project_id:    proj_xxxx                         │
│  task_order:    1                                 │
│  task_title:    "nftables 규칙 확인"               │
│  evidence_hash: sha256(stdout+stderr+exit_code)   │
│  prev_hash:     이전 블록의 block_hash              │
│  block_hash:    sha256(prev_hash+evidence_hash+ts)│
│  ts:            2026-03-30T10:15:30.123456+00:00  │
│  ts_raw:        원본 timestamp 문자열               │
└──────────────────────────────────────────────────┘
```

### 4.2 체인 연결 원리

각 에이전트별로 독립된 블록체인이 형성된다.

```
Agent: http://192.168.0.108:8002

Block 1              Block 2              Block 3
┌──────────┐        ┌──────────┐        ┌──────────┐
│prev: 000..│───────►│prev: abc..│───────►│prev: def..│
│hash: abc..│        │hash: def..│        │hash: ghi..│
│evidence:..│        │evidence:..│        │evidence:..│
└──────────┘        └──────────┘        └──────────┘
(첫 블록 prev = "0"*64)
```

### 4.3 채굴 과정 (SHA-256)

```python
# 내부 동작 (packages/pow_service.py)
evidence_hash = sha256(stdout + stderr + str(exit_code))
block_data = prev_hash + evidence_hash + ts_raw
block_hash = sha256(block_data)
```

현재 OpsClaw는 difficulty=0 (즉시 채굴)이다. 향후 difficulty를 높여 nonce 탐색 방식으로 전환 가능하다.

### 4.4 체인 무결성 검증

```bash
# 에이전트 체인 검증
curl "http://localhost:8000/pow/verify?agent_id=http://192.168.0.108:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 정상 응답
{
  "valid": true,
  "blocks": 15,
  "orphans": 0,
  "tampered": []
}

# 변조 감지 시
{
  "valid": false,
  "blocks": 15,
  "orphans": 0,
  "tampered": ["pow_xxx", "pow_yyy"]
}
```

---

## 5. RL (강화학습) 시스템

### 5.1 보상 신호 (Reward Signal)

Task 실행마다 `task_reward` 테이블에 보상이 기록된다.

```
total_reward = base_score + speed_bonus - risk_penalty

base_score:   성공(exit_code=0) → +1.0 / 실패 → -1.0
speed_bonus:  실행 시간에 비례 +0.0 ~ +0.3 (빠를수록 높음)
risk_penalty: 실패 + 고위험(high/critical) 시 -0.1 ~ -0.2
```

### 5.2 Q-learning 학습

```bash
# 학습 실행 (task_reward 데이터 기반)
curl -X POST "http://localhost:8000/rl/train?alpha=0.1&gamma=0.95&epsilon=0.15" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 응답
{
  "episodes": 150,
  "states": 12,
  "policy_size": 48,
  "avg_reward": 0.85
}
```

**Q-table 상태 공간:**

- State = `(agent_id, risk_level, task_order_bucket)`
- Action = `{low, medium, high, critical}` (risk_level 선택)
- Reward = `total_reward` from `task_reward`

### 5.3 UCB1 탐색 전략 (M24)

Epsilon-greedy 외에 UCB1(Upper Confidence Bound) 탐색을 지원한다.

```bash
# Greedy 추천 (exploitation 위주)
curl "http://localhost:8000/rl/recommend?agent_id=http://192.168.0.108:8002&risk_level=medium&exploration=greedy" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# UCB1 추천 (exploration + exploitation 균형)
curl "http://localhost:8000/rl/recommend?agent_id=http://192.168.0.108:8002&risk_level=medium&exploration=ucb1&ucb_c=1.5" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 응답
{
  "recommended_action": "medium",
  "q_value": 0.92,
  "exploration": "ucb1",
  "ucb_score": 1.15,
  "visit_count": 23
}
```

### 5.4 정책 상태 확인

```bash
curl http://localhost:8000/rl/policy -H "X-API-Key: $OPSCLAW_API_KEY"
```

---

## 6. 4계층 메모리 아키텍처

OpsClaw는 실행 데이터를 점진적으로 추상화하여 장기 지식으로 변환한다.

```
Layer 1: Evidence (Raw)
  │  명령 실행 결과 그대로 (stdout, stderr, exit_code)
  │  테이블: evidence
  ▼
Layer 2: Task Memory (Summary)
  │  프로젝트 단위 실행 요약 (LLM이 생성)
  │  테이블: task_memories
  ▼
Layer 3: Experience (Knowledge)
  │  도메인별 경험 지식 (카테고리, 결론, 교훈)
  │  테이블: experiences
  ▼
Layer 4: Retrieval (FTS Index)
     전문 검색 인덱스 — RAG로 유사 경험 참조
     테이블: retrieval_documents
```

### 6.1 Task Memory 생성

```bash
# 프로젝트 Evidence를 Task Memory로 집약
curl -X POST http://localhost:8000/projects/{id}/memory/build \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# Experience까지 자동 승격
curl -X POST "http://localhost:8000/projects/{id}/memory/build?promote=true" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### 6.2 Experience 관리

```bash
# 경험 목록 조회
curl http://localhost:8000/experience -H "X-API-Key: $OPSCLAW_API_KEY"

# 카테고리별 조회
curl "http://localhost:8000/experience?category=firewall" -H "X-API-Key: $OPSCLAW_API_KEY"

# 경험 검색 (RAG)
curl "http://localhost:8000/experience/search?q=nftables+설정" -H "X-API-Key: $OPSCLAW_API_KEY"
```

### 6.3 고보상 에피소드 자동 승격

`execute-plan` 완료 시 `total_reward`가 높은 에피소드는 자동으로 Experience로 승격된다.
이 메커니즘은 `auto_promote_high_reward()` 함수가 담당한다.

---

## 7. Playbook 엔진

Playbook은 **결정적으로 실행 가능한** 자동화 작업 정의다.

### 7.1 Playbook 구조

```
Playbook
├── name: "firewall_audit"
├── version: "1.2"
├── category: "security"
├── execution_mode: "one_shot" | "batch" | "continuous"
├── default_risk_level: "medium"
├── dry_run_supported: true
├── failure_policy: {"max_retries": 2, "on_failure": "stop"}
└── Steps[]
    ├── Step 1: {step_type: "tool", ref_id: "run_command", params: {...}}
    ├── Step 2: {step_type: "tool", ref_id: "fetch_log", params: {...}}
    └── Step 3: {step_type: "skill", ref_id: "analyze_wazuh_alert_burst"}
```

### 7.2 실행 방법

```bash
# 프로젝트에 Playbook 연결 후 실행
curl -X POST http://localhost:8000/projects/{id}/playbooks/{playbook_id} \
  -H "X-API-Key: $OPSCLAW_API_KEY"

curl -X POST http://localhost:8000/projects/{id}/playbook/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"subagent_url": "http://192.168.0.108:8002", "dry_run": false}'
```

### 7.3 버전 관리

```bash
# 현재 상태를 스냅샷으로 저장
curl -X POST http://localhost:8000/playbooks/{id}/snapshot \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"note": "v1.2 안정화 버전"}'

# 버전 목록 조회
curl http://localhost:8000/playbooks/{id}/versions -H "X-API-Key: $OPSCLAW_API_KEY"

# 특정 버전으로 롤백
curl -X POST http://localhost:8000/playbooks/{id}/rollback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"version_number": 1}'
```

---

## 8. Notification 시스템

### 8.1 채널/규칙 기반 라우팅

```
이벤트 발생 → 규칙 매칭 → 채널 전송

이벤트 유형:
  incident.created, schedule.failed, project.completed, *, ...

채널 유형:
  webhook:  HTTP POST로 payload 전송
  email:    SMTP로 이메일 전송
  slack:    Slack Bot Token으로 메시지 전송
  log:      시스템 로그 기록
```

### 8.2 설정 예시

```bash
# Slack 채널 생성
curl -X POST http://localhost:8000/notifications/channels \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "slack-alerts",
    "channel_type": "slack",
    "config": {"channel": "#bot-cc"},
    "enabled": true
  }'

# 규칙 생성: incident 발생 시 Slack 알림
curl -X POST http://localhost:8000/notifications/rules \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "incident-to-slack",
    "event_type": "incident.created",
    "channel_id": "<channel_id>",
    "enabled": true
  }'

# 테스트 전송
curl -X POST http://localhost:8000/notifications/test \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"event_type": "incident.created", "payload": {"summary": "테스트 알림"}}'
```

---

## 9. 인증 (M28)

모든 Manager API 호출에 API Key 인증이 필요하다.

```bash
# 환경변수 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026

# 헤더로 전달 (방법 1: X-API-Key)
curl -H "X-API-Key: $OPSCLAW_API_KEY" http://localhost:8000/projects

# 헤더로 전달 (방법 2: Authorization Bearer)
curl -H "Authorization: Bearer $OPSCLAW_API_KEY" http://localhost:8000/projects
```

**인증 면제 경로:** `/health`, `/`, `/ui`, `/app/*`, WebSocket, CORS preflight

---

## 10. 비동기 실행 (M23)

### 10.1 async_mode

대규모 Task 배열은 백그라운드로 실행하고 폴링으로 결과를 확인한다.

```bash
# 비동기 실행
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"tasks": [...], "async_mode": true, "subagent_url": "http://192.168.0.108:8002"}'

# 응답: job_id 반환
{"status": "accepted", "job_id": "job_xxx", "project_id": "proj_xxx"}

# 폴링
curl http://localhost:8000/projects/{id}/async-jobs/job_xxx -H "X-API-Key: $OPSCLAW_API_KEY"
```

### 10.2 parallel 모드

여러 Task를 동시에 실행한다 (ThreadPoolExecutor, max_workers=5).

```bash
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {"order": 1, "instruction_prompt": "hostname", "subagent_url": "http://192.168.0.108:8002"},
      {"order": 2, "instruction_prompt": "hostname", "subagent_url": "http://192.168.0.110:8002"},
      {"order": 3, "instruction_prompt": "hostname", "subagent_url": "http://192.168.0.109:8002"}
    ],
    "parallel": true
  }'
```

---

## 11. 안전 메커니즘

### 11.1 risk_level 기반 보호

- `low/medium`: 즉시 실행
- `high`: 실행하되 RL penalty 적용
- `critical`: **dry_run 자동 강제** (confirmed=true 없으면 실제 실행 불가)
- `sudo` 포함 명령: 자동으로 risk_level을 `high`로 상향

### 11.2 시크릿 마스킹

모든 API 응답에서 GitHub PAT, Token, Password 패턴을 자동 마스킹한다.

```
ghp_AbCdEfGh1234... → ghp_****
github_pat_xxxx...   → github_pat_****
https://user@github.com → https://****@github.com
```

### 11.3 dispatch 모드

| 모드 | 동작 |
|------|------|
| `shell` | 명령을 그대로 bash로 실행 |
| `adhoc` | 항상 LLM으로 자연어→shell 변환 후 실행 |
| `auto` | 한글 포함 또는 긴 문장이면 LLM 변환, 아니면 그대로 실행 |
