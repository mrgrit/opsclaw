# OpsClaw API 레퍼런스

## 1. 공통 사항

### 1.1 인증

모든 API 호출에 인증 헤더가 필요하다 (M28).

```
X-API-Key: opsclaw-api-key-2026
```

또는:

```
Authorization: Bearer opsclaw-api-key-2026
```

**인증 면제 경로:** `/health`, `/`, `/ui`, `/app/*`, WebSocket, CORS preflight OPTIONS

### 1.2 기본 URL

| 서비스 | URL | 역할 |
|--------|-----|------|
| Manager API | http://localhost:8000 | 주 진입점 |
| Master Service | http://localhost:8001 | LLM 계획/리뷰 |
| SubAgent Runtime | http://localhost:8002 | 명령 실행 |

### 1.3 공통 응답 형식

성공:
```json
{"status": "ok", ...}
```

에러:
```json
{"detail": {"message": "에러 메시지"}}
```

### 1.4 HTTP 상태 코드

| 코드 | 의미 |
|------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (stage 전환 오류 등) |
| 401 | 인증 실패 (API Key 누락/불일치) |
| 404 | 리소스 없음 |
| 409 | 충돌 (중복 생성) |
| 422 | 필수 필드 누락 |
| 500 | 서버 내부 오류 |
| 501 | 미구현 기능 |
| 502 | LLM/SubAgent 연결 실패 |

---

## 2. Manager API (:8000)

### 2.1 Health

```
GET /health
```

응답:
```json
{"status": "ok", "service": "manager-api"}
```

---

### 2.2 Projects

#### 프로젝트 목록 조회

```
GET /projects?limit=50
```

응답:
```json
{"projects": [...], "items": [...]}
```

#### 프로젝트 생성

```
POST /projects
Content-Type: application/json

{
  "name": "프로젝트명",
  "request_text": "작업 설명",
  "mode": "one_shot",         // one_shot | batch | continuous
  "master_mode": "external"   // native | external
}
```

응답:
```json
{
  "status": "ok",
  "project": {
    "id": "proj_xxx",
    "name": "...",
    "status": "created",
    "current_stage": "intake",
    "master_mode": "external"
  }
}
```

#### 프로젝트 조회

```
GET /projects/{project_id}
```

#### Stage 전환

```
POST /projects/{project_id}/plan        # intake → plan
POST /projects/{project_id}/execute     # plan → execute
POST /projects/{project_id}/validate    # execute → validate
POST /projects/{project_id}/report/finalize  # validate → report
POST /projects/{project_id}/close       # → closed
```

#### Replan (재계획)

```
POST /projects/{project_id}/replan
Content-Type: application/json

{"reason": "검증 실패로 재계획"}
```

#### 자동 실행 (LangGraph)

```
POST /projects/{project_id}/run
```

응답:
```json
{
  "status": "ok",
  "final_stage": "report",
  "stop_reason": null,
  "approval_required": false
}
```

---

### 2.3 Dispatch (단일 명령)

```
POST /projects/{project_id}/dispatch
Content-Type: application/json

{
  "command": "hostname",
  "subagent_url": "http://192.168.0.108:8002",
  "timeout_s": 30,
  "mode": "auto"   // auto | shell | adhoc
}
```

응답:
```json
{
  "status": "ok",
  "result": {
    "exit_code": 0,
    "stdout": "v-secu",
    "stderr": "",
    "evidence_id": "ev_xxx",
    "original_command": "hostname",
    "llm_converted": false
  }
}
```

**mode 설명:**
- `shell`: 명령을 그대로 bash로 실행
- `adhoc`: 자연어를 LLM으로 shell 변환 후 실행
- `auto`: 한글 포함이나 긴 문장이면 adhoc, 아니면 shell

---

### 2.4 Execute-Plan (다중 Task 실행)

```
POST /projects/{project_id}/execute-plan
Content-Type: application/json

{
  "tasks": [
    {
      "order": 1,
      "title": "작업 제목",
      "instruction_prompt": "실행할 명령",
      "risk_level": "low",           // low | medium | high | critical
      "subagent_url": "http://192.168.0.108:8002",  // 선택
      "playbook_hint": null           // 기존 Playbook 이름 (선택)
    }
  ],
  "subagent_url": "http://localhost:8002",  // 전역 기본값
  "dry_run": false,
  "confirmed": false,    // true면 critical도 실행
  "async_mode": false,   // true면 백그라운드 실행
  "parallel": false,     // true면 병렬 실행
  "playbook_id": null    // Playbook 직접 실행 (tasks 불필요)
}
```

응답 (동기):
```json
{
  "status": "ok",
  "project_id": "proj_xxx",
  "tasks_total": 3,
  "tasks_ok": 3,
  "tasks_failed": 0,
  "overall": "success",
  "task_results": [
    {
      "order": 1,
      "title": "작업 제목",
      "status": "ok",
      "risk_level": "low",
      "dry_run": false,
      "method": "adhoc",
      "duration_s": 1.234,
      "detail": {
        "exit_code": 0,
        "stdout": "...",
        "stderr": ""
      }
    }
  ]
}
```

응답 (async_mode=true):
```json
{"status": "accepted", "job_id": "job_xxx", "project_id": "proj_xxx"}
```

---

### 2.5 Async Jobs

```
GET /projects/{project_id}/async-jobs?limit=20
GET /projects/{project_id}/async-jobs/{job_id}
```

---

### 2.6 Evidence

```
GET /projects/{project_id}/evidence
GET /projects/{project_id}/evidence/summary

POST /projects/{project_id}/evidence/minimal
Content-Type: application/json

{
  "command": "수동 실행 명령",
  "stdout": "실행 결과",
  "stderr": "",
  "exit_code": 0
}
```

---

### 2.7 Validation

```
GET /projects/{project_id}/validations

POST /projects/{project_id}/validate/check
Content-Type: application/json

{
  "validator_name": "manual",
  "command": "systemctl is-active apache2",
  "expected_contains": "active",
  "expected_exit_code": 0,
  "subagent_url": "http://192.168.0.110:8002",
  "asset_id": null
}
```

---

### 2.8 Completion Reports

```
POST /projects/{project_id}/completion-report
Content-Type: application/json

{
  "summary": "작업 요약",
  "outcome": "success",       // success | partial | failed | unknown
  "work_details": ["항목1", "항목2"],
  "issues": ["이슈1"],
  "next_steps": ["다음 작업"],
  "reviewer_id": null,
  "auto": false               // true면 Evidence 자동 집계
}

GET /projects/{project_id}/completion-reports
GET /completion-reports?playbook_name=&outcome=&limit=20
GET /completion-reports/{report_id}
GET /completion-reports/search?q=검색어&limit=10
```

---

### 2.9 PoW (Proof of Work)

```
GET /pow/blocks?agent_id=http://...&limit=50
GET /pow/blocks/{pow_id}
GET /pow/verify?agent_id=http://...
GET /pow/leaderboard?limit=10

GET /projects/{project_id}/pow
GET /projects/{project_id}/replay
```

**verify 응답:**
```json
{
  "status": "ok",
  "result": {
    "valid": true,
    "blocks": 15,
    "orphans": 0,
    "tampered": []
  }
}
```

**leaderboard 응답:**
```json
{
  "status": "ok",
  "leaderboard": [
    {
      "agent_id": "http://192.168.0.108:8002",
      "balance": 45.2,
      "total_tasks": 50,
      "success_count": 47,
      "fail_count": 3
    }
  ]
}
```

---

### 2.10 Rewards

```
GET /rewards/agents?agent_id=http://...
```

응답:
```json
{
  "status": "ok",
  "ledger": {
    "agent_id": "http://...",
    "balance": 45.2,
    "total_tasks": 50,
    "success_count": 47,
    "fail_count": 3
  },
  "recent_rewards": [
    {
      "task_order": 3,
      "task_title": "nft list ruleset",
      "total_reward": 1.25,
      "exit_code": 0,
      "risk_level": "low"
    }
  ]
}
```

---

### 2.11 RL (강화학습)

```
POST /rl/train?alpha=0.1&gamma=0.95&epsilon=0.15&limit=500

GET /rl/recommend?agent_id=http://...&risk_level=medium&task_order=1&exploration=greedy&ucb_c=1.0

GET /rl/policy
```

**recommend 응답:**
```json
{
  "status": "ok",
  "recommended_action": "medium",
  "q_value": 0.92,
  "exploration": "greedy"
}
```

---

### 2.12 Assets

```
GET /assets?env=production&type=server
POST /assets
GET /assets/{asset_id}
PUT /assets/{asset_id}
DELETE /assets/{asset_id}
POST /assets/{asset_id}/resolve
GET /assets/{asset_id}/health
POST /assets/{asset_id}/bootstrap
POST /assets/onboard
```

**생성 요청:**
```json
{
  "name": "v-secu",
  "type": "server",
  "platform": "linux",
  "env": "production",
  "mgmt_ip": "192.168.0.108",
  "roles": ["firewall", "ids"],
  "expected_subagent_port": 8002
}
```

---

### 2.13 Targets

```
GET /targets
```

---

### 2.14 Registry (Tools / Skills / Playbooks)

#### Tools

```
GET /tools?enabled=true
GET /tools/{tool_id}
```

#### Skills

```
GET /skills?category=security
GET /skills/{skill_id}
```

#### Playbooks

```
GET /playbooks?category=security&enabled=true
POST /playbooks
PUT /playbooks/{playbook_id}
DELETE /playbooks/{playbook_id}
GET /playbooks/{playbook_id}
GET /playbooks/{playbook_id}/steps
POST /playbooks/{playbook_id}/steps
GET /playbooks/{playbook_id}/resolve
GET /playbooks/{playbook_id}/explain

POST /playbooks/{playbook_id}/snapshot
GET /playbooks/{playbook_id}/versions
POST /playbooks/{playbook_id}/rollback   {"version_number": 1}

POST /playbook/run   {"project_id": "...", "playbook_id": "...", "subagent_url": "..."}
```

**Playbook 생성 요청:**
```json
{
  "name": "firewall_audit",
  "version": "1.0",
  "category": "security",
  "description": "방화벽 규칙 감사",
  "execution_mode": "one_shot",
  "default_risk_level": "medium",
  "dry_run_supported": true,
  "explain_supported": true,
  "steps": [
    {
      "step_order": 1,
      "step_type": "tool",
      "ref_id": "run_command",
      "name": "nftables 규칙 확인",
      "params": {"command": "nft list ruleset"},
      "on_failure": "stop"
    }
  ]
}
```

---

### 2.15 Playbook Run

```
POST /projects/{project_id}/playbook/run
Content-Type: application/json

{
  "subagent_url": "http://192.168.0.108:8002",
  "dry_run": false,
  "params": {}
}
```

---

### 2.16 History / Memory / Experience

```
POST /projects/{project_id}/history/ingest
GET /projects/{project_id}/history?limit=50
GET /assets/{asset_id}/history?limit=50

POST /projects/{project_id}/task-memory/build
GET /projects/{project_id}/task-memory

POST /projects/{project_id}/reindex
GET /projects/{project_id}/context

POST /projects/{project_id}/memory/build?promote=true

GET /experience?category=firewall&limit=20
GET /experience/search?q=검색어&limit=10
POST /experience
GET /experience/{experience_id}
POST /experience/task-memories/{task_memory_id}/promote
```

---

### 2.17 Schedules

```
GET /schedules
POST /schedules
GET /schedules/{schedule_id}
PATCH /schedules/{schedule_id}   {"enabled": false, "cron_expr": "0 2 * * *"}
DELETE /schedules/{schedule_id}
POST /schedules/{schedule_id}/run
```

---

### 2.18 Watchers

```
GET /watchers
POST /watchers
GET /watchers/{watch_job_id}
PATCH /watchers/{watch_job_id}/status   {"status": "stopped"}
DELETE /watchers/{watch_job_id}
GET /watchers/{watch_job_id}/events
POST /watchers/{watch_job_id}/check
```

---

### 2.19 Incidents

```
GET /incidents?status=open
POST /incidents/{incident_id}/resolve
```

---

### 2.20 Notifications

#### Channels

```
GET /notifications/channels?enabled_only=false
POST /notifications/channels
GET /notifications/channels/{channel_id}
PATCH /notifications/channels/{channel_id}   {"enabled": false, "config": {...}}
DELETE /notifications/channels/{channel_id}
```

**채널 생성 요청:**
```json
{
  "name": "slack-alerts",
  "channel_type": "slack",       // webhook | email | slack | log
  "config": {"channel": "#bot-cc"},
  "enabled": true
}
```

#### Rules

```
GET /notifications/rules?event_type=incident.created&enabled_only=true
POST /notifications/rules
GET /notifications/rules/{rule_id}
PATCH /notifications/rules/{rule_id}   {"enabled": false}
DELETE /notifications/rules/{rule_id}
```

**규칙 생성 요청:**
```json
{
  "name": "incident-to-slack",
  "event_type": "incident.created",
  "channel_id": "<uuid>",
  "filter_conditions": {},
  "enabled": true
}
```

#### Test / Logs

```
POST /notifications/test   {"event_type": "incident.created", "payload": {...}}
GET /notifications/logs?event_type=&channel_id=&limit=50
```

---

### 2.21 Admin

#### Health / Metrics

```
GET /admin/health
GET /admin/metrics
```

#### Audit

```
GET /admin/audit?event_type=&actor_id=&project_id=&limit=100

POST /admin/audit/export
Content-Type: application/json

{
  "format": "json",    // json | csv
  "event_type": null,
  "project_id": null,
  "limit": 1000
}
```

#### RBAC

```
GET /admin/roles
POST /admin/roles   {"name": "custom", "permissions": ["project:read"], "description": "..."}
GET /admin/roles/{role_id}
POST /admin/roles/assign   {"actor_id": "user01", "role_id": "<uuid>", "actor_type": "user"}
GET /admin/roles/actor/{actor_id}/permissions
GET /admin/roles/actor/{actor_id}/check?permission=project:write
```

#### Backup

```
POST /admin/backup
GET /admin/backups
```

---

### 2.22 Reports

```
GET /reports/project/{project_id}
GET /reports/project/{project_id}/evidence-pack
GET /reports/project/{project_id}/evidence-pack/json
```

---

### 2.23 Chat (RAG 기반)

```
POST /chat
Content-Type: application/json

{
  "message": "이 프로젝트의 방화벽 설정이 적절한가?",
  "context_type": "project",     // project | agent | playbook
  "context_id": "proj_xxx",
  "history": [
    {"role": "user", "content": "이전 질문"},
    {"role": "assistant", "content": "이전 답변"}
  ]
}
```

응답:
```json
{
  "status": "ok",
  "reply": "LLM 답변 내용...",
  "context_type": "project",
  "context_id": "proj_xxx",
  "rag_sources": 3
}
```

---

### 2.24 Runtime (LLM 직접 호출)

```
POST /runtime/invoke
Content-Type: application/json

{
  "prompt": "nftables 규칙 작성법을 설명해줘",
  "role": "manager"
}
```

---

### 2.25 Project 하위 리소스

```
POST /projects/{id}/assets/{asset_id}       # Asset 연결
GET /projects/{id}/assets                   # 연결된 Assets
POST /projects/{id}/targets/{target_id}     # Target 연결
GET /projects/{id}/targets                  # 연결된 Targets
POST /projects/{id}/playbooks/{playbook_id} # Playbook 연결
GET /projects/{id}/playbooks                # 연결된 Playbooks
POST /projects/{id}/select_assets           # 자동 Asset 선택
POST /projects/{id}/resolve_targets         # 자동 Target 해석
GET /projects/{id}/approval                 # 승인 상태
GET /projects/{id}/report                   # 보고서
```

---

## 3. Master Service (:8001)

```
GET /health

POST /runtime/invoke   {"prompt": "...", "role": "master"}

POST /projects/{project_id}/master-plan
POST /projects/{project_id}/master-review
  {"reviewer_id": "master-llm", "review_status": "approved", "summary": "...", "auto_replan": false}

POST /projects/{project_id}/replan
  {"reason": "master-initiated replan"}

GET /projects/{project_id}/reviews
GET /projects/{project_id}/reviews/latest
```

---

## 4. SubAgent Runtime (:8002)

> SubAgent는 Manager를 통해서만 호출한다. 직접 호출은 금지.

```
GET /health
GET /capabilities

POST /runtime/invoke   {"prompt": "...", "role": "subagent"}

POST /a2a/run_script
  {"project_id": "...", "job_run_id": "...", "script": "hostname", "timeout_s": 120}

POST /a2a/invoke_llm
  {"project_id": "...", "job_run_id": "...", "task": "로그 분석", "timeout_s": 120}

POST /a2a/install_tool
  {"project_id": "...", "job_run_id": "...", "tool_name": "nmap", "method": "apt", "timeout_s": 120}

POST /a2a/analyze
  {"project_id": "...", "job_run_id": "...", "command_output": "...", "question": "이상 패턴이 있는가?", "timeout_s": 120}

POST /a2a/mission
  {
    "mission_id": "m001",
    "role": "red",               // red | blue
    "objective": "SSH 취약점 탐색",
    "target": "localhost",
    "model": "gemma3:12b",       // Ollama 모델
    "playbook_context": [],
    "experience_context": [],
    "max_steps": 10,
    "timeout_s": 180
  }
```

**capabilities 응답:**
```json
{
  "service": "subagent-runtime",
  "version": "0.4.0-m12",
  "capabilities": [
    "health", "capabilities", "run_script",
    "invoke_llm", "install_tool", "analyze",
    "evidence_return", "runtime_invoke"
  ],
  "llm_available": true
}
```

---

## 5. 등록된 Tools

| 도구 | 설명 |
|------|------|
| `run_command` | bash 명령 실행 |
| `fetch_log` | 로그 파일 읽기 |
| `query_metric` | 메트릭 조회 |
| `read_file` | 파일 읽기 |
| `write_file` | 파일 쓰기 |
| `restart_service` | 서비스 재시작 |

## 6. 등록된 Skills

| 스킬 | 설명 |
|------|------|
| `probe_linux_host` | Linux 서버 상태 종합 점검 |
| `check_tls_cert` | TLS 인증서 점검 |
| `collect_web_latency_facts` | 웹 서버 응답 시간 수집 |
| `monitor_disk_growth` | 디스크 사용량 증가 추이 모니터링 |
| `summarize_incident_timeline` | 인시던트 타임라인 요약 |
| `analyze_wazuh_alert_burst` | Wazuh 알림 폭증 분석 |
