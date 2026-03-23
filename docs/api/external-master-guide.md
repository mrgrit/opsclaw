# OpsClaw External Master 가이드

**대상:** Claude Code, Codex 등 외부 AI가 OpsClaw Manager API를 직접 오케스트레이션할 때 사용하는 참조 문서

---

## 개요: Mode B (AI-Driven)

OpsClaw는 두 가지 실행 모드를 지원한다.

| 모드 | `master_mode` | Master 역할 | 사용 케이스 |
|------|---------------|------------|------------|
| **Mode A: Native** | `native` | OpsClaw 내장 LLM (master-service:8001) | 웹 UI/API에서 직접 요청 |
| **Mode B: AI-Driven** | `external` | 외부 AI (Claude Code 등) | AI가 API 직접 호출로 오케스트레이션 |

**Mode B에서 외부 AI의 역할:**
- 사용자 자연어 → 작업 계획 수립 (외부 AI 담당)
- `POST /projects` → `POST /projects/{id}/execute-plan` 등 API 순서대로 직접 호출
- OpsClaw는 실행 control-plane 역할: 인증, evidence 기록, 상태 전이, SubAgent dispatch

---

## 핵심 API 흐름 (Mode B)

### 1단계: 프로젝트 생성

```http
POST /projects
{
  "name": "작업 이름",
  "request_text": "자연어 요구사항",
  "master_mode": "external"
}
```

응답에서 `project.id` 저장.

---

### 2단계: (선택) Playbook 연결

특정 Playbook을 사용할 경우:

```http
POST /playbooks
{ "name": "my-playbook", "version": "1.0" }

POST /playbooks/{playbook_id}/steps
{ "step_order": 1, "step_type": "tool", "name": "run_command", "ref_id": "run_command",
  "params": { "command": "apt-get install -y nginx" } }

POST /projects/{project_id}/playbooks/{playbook_id}
```

---

### 3단계: Stage 전환

```http
POST /projects/{project_id}/plan    → current_stage: plan
POST /projects/{project_id}/execute → current_stage: execute
```

---

### 4단계: 작업 실행

#### 방법 A — execute-plan (Master 계획 결과 tasks 배열 직접 실행)

```http
POST /projects/{project_id}/execute-plan
{
  "tasks": [
    { "order": 1, "title": "패키지 업데이트", "instruction_prompt": "apt-get update -y", "risk_level": "low" },
    { "order": 2, "title": "Nginx 설치", "instruction_prompt": "apt-get install -y nginx", "risk_level": "low" }
  ],
  "subagent_url": "http://<subagent-host>:8002",
  "dry_run": false
}
```

응답: `{ tasks_total, tasks_ok, tasks_failed, overall, task_results[] }`

#### 방법 B — dispatch (단일 명령 즉시 실행)

```http
POST /projects/{project_id}/dispatch
{ "command": "systemctl status nginx", "subagent_url": "http://...:8002" }
```

#### 방법 C — Playbook 실행 (사전 등록된 Playbook 기반)

```http
POST /projects/{project_id}/playbook/run
{ "dry_run": false, "subagent_url": "http://...:8002" }
```

---

### 5단계: 결과 확인

```http
GET /projects/{project_id}/evidence        # 실행 증거 목록
GET /projects/{project_id}/evidence/summary # 요약
GET /projects/{project_id}/report          # 프로젝트 보고서
```

---

### 6단계: 완료보고서 생성

```http
POST /projects/{project_id}/completion-report
{
  "summary": "작업 완료 요약",
  "outcome": "success",
  "work_details": ["완료 항목 1", "완료 항목 2"],
  "issues": [],
  "next_steps": ["후속 권장사항"]
}
```

---

### 7단계: 프로젝트 종료

```http
POST /projects/{project_id}/close
```

---

## 서비스 포트

| 서비스 | 포트 | 역할 |
|--------|------|------|
| manager-api | 8000 | 주 API (Mode B 진입점) |
| master-service | 8001 | Mode A 전용 (LLM 계획 수립) |
| subagent-runtime | 8002 | 명령 실행 |

---

## 등록된 Tool/Skill 목록

### Tools (실행 가능한 shell 명령 단위)

| name | 설명 | 주요 params |
|------|------|------------|
| `run_command` | 임의 shell 명령 실행 | `command` |
| `fetch_log` | 로그 파일 조회 | `log_path`, `lines` |
| `query_metric` | CPU/메모리/디스크/네트워크 현황 | (없음) |
| `read_file` | 파일 읽기 | `path` |
| `write_file` | 파일 쓰기 | `path`, `content` |
| `restart_service` | systemctl 서비스 재시작 | `service` |

### Skills (Tool 조합 절차 단위)

| name | 설명 |
|------|------|
| `probe_linux_host` | hostname/uptime/커널/디스크/메모리/프로세스/포트 수집 |
| `check_tls_cert` | TLS 인증서 유효기간/발급자 확인 |
| `collect_web_latency_facts` | HTTP 응답 시간 3회 측정 |
| `monitor_disk_growth` | 디렉토리 디스크 사용량 분석 |
| `summarize_incident_timeline` | 시스템 오류 로그 타임라인 요약 |
| `analyze_wazuh_alert_burst` | Wazuh 알림 급증 분석 |

---

## 예시 시나리오

### 시나리오 1: 신규 서버 온보딩

```
1. POST /projects {name:"server-onboard", master_mode:"external"}
2. POST /projects/{id}/plan
3. POST /projects/{id}/execute
4. POST /projects/{id}/execute-plan {tasks:[
     {order:1, instruction_prompt:"hostname && uptime && df -h"},
     {order:2, instruction_prompt:"apt-get update -y && apt-get upgrade -y"}
   ], subagent_url:"http://target:8002"}
5. GET /projects/{id}/evidence
6. POST /projects/{id}/completion-report
```

### 시나리오 2: 패키지 설치

```
1. POST /projects {master_mode:"external"}
2. Playbook 생성 (steps: run_command "apt-get install -y <pkg>")
3. /plan → /execute → /playbook/run
4. /evidence/summary로 성공 확인
```

### 시나리오 3: 보안 점검

```
1. POST /projects {master_mode:"external"}
2. Playbook 생성 (steps: skill "probe_linux_host", skill "check_tls_cert")
3. /plan → /execute → /playbook/run
4. evidence에서 stdout 확인 → 이슈 분석
```

---

## PoW & Reward API

`execute-plan`으로 Task를 실행하면 **자동으로 PoW 블록이 생성되고 보상이 지급**된다.
별도의 채굴 API 호출은 필요 없다.

### 채굴 흐름

```
execute-plan → Task 실행 → generate_proof() 자동 호출
  ├─ evidence_hash = sha256(stdout + stderr + exit_code)
  ├─ nonce 채굴 (sha256 반복하여 leading zero 해시 탐색)
  ├─ proof_of_work INSERT (블록 기록)
  ├─ task_reward INSERT (보상 기록)
  └─ reward_ledger UPSERT (잔액 갱신)
```

### 엔드포인트

#### PoW 블록 조회

```http
GET /pow/blocks?agent_id=http://localhost:8002&limit=50
```

응답:
```json
{
  "status": "ok",
  "total": 5,
  "blocks": [
    {
      "id": "pow_88210bdf570b",
      "agent_id": "http://localhost:8002",
      "project_id": "prj_...",
      "task_order": 1,
      "task_title": "task-1",
      "evidence_hash": "c530...",
      "prev_hash": "0000...",
      "block_hash": "000052f7...",
      "nonce": 36166,
      "difficulty": 4,
      "ts": "2026-03-23T05:47:13Z"
    }
  ]
}
```

#### 단건 블록 조회

```http
GET /pow/blocks/{pow_id}
```

#### 체인 무결성 검증

```http
GET /pow/verify?agent_id=http://localhost:8002
```

응답:
```json
{
  "status": "ok",
  "result": {
    "agent_id": "http://localhost:8002",
    "valid": true,
    "blocks": 11,
    "tampered": []
  }
}
```

위변조 감지 시 `tampered` 배열에 `block_hash_mismatch`, `difficulty_not_met`, `chain_broken` 중 하나의 reason 포함.

#### 보상 랭킹

```http
GET /pow/leaderboard?limit=10
```

#### 에이전트 잔액 + 보상 이력

```http
GET /rewards/agents?agent_id=http://localhost:8002
```

#### 프로젝트별 PoW 블록

```http
GET /projects/{id}/pow
```

#### 프로젝트 Replay (작업 타임라인)

```http
GET /projects/{id}/replay
```

응답:
```json
{
  "project_id": "prj_...",
  "steps_total": 3,
  "steps_success": 3,
  "total_reward": 3.9,
  "timeline": [
    {
      "task_order": 1,
      "task_title": "현황 수집",
      "exit_code": 0,
      "duration_s": 1.2,
      "total_reward": 1.3,
      "block_hash": "0000..."
    }
  ]
}
```

### 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OPSCLAW_POW_DIFFICULTY` | 4 | leading zero hex 개수 (4 ≈ 65K회 시행) |
| `OPSCLAW_POW_MAX_NONCE` | 10,000,000 | 무한루프 방지 |
