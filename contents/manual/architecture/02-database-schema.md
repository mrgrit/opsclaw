# OpsClaw 데이터베이스 스키마 가이드

## 1. 데이터베이스 개요

OpsClaw는 **PostgreSQL 15**를 사용하며, Docker 컨테이너로 실행된다.

```bash
# PostgreSQL 기동
echo "1" | sudo -S docker compose -f docker/postgres-compose.yaml up -d

# 접속 정보
Host:     127.0.0.1
Port:     5432
Database: opsclaw
User:     opsclaw
Password: opsclaw

# 직접 접속
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw
```

---

## 2. 마이그레이션 파일 목록

모든 마이그레이션은 `migrations/` 디렉토리에 있으며 순서대로 적용해야 한다.

| 파일 | 마일스톤 | 내용 |
|------|----------|------|
| `0001_init_core.sql` | M0 | 핵심 테이블: assets, projects, evidence, job_runs, validation_runs, master_reviews, reports, messages, audit_logs |
| `0002_registry.sql` | M0 | 레지스트리: tools, skills, playbooks, playbook_steps, playbook_bindings |
| `0003_history_and_experience.sql` | M6 | 4계층 메모리: histories, task_memories, experiences, retrieval_documents |
| `0004_scheduler_and_watch.sql` | M8 | 배치/감시: schedules, watch_jobs, watch_events, incidents |
| `0005_rbac.sql` | M9 | 접근 제어: roles, actor_roles + 기본 역할 seed |
| `0006_notifications.sql` | M10 | 알림: notification_channels, notification_rules, notification_logs |
| `0007_completion_reports.sql` | M14 | 완료보고서: completion_reports |
| `0008_master_mode.sql` | M15 | projects.master_mode 컬럼 추가 |
| `0009_proof_of_work.sql` | M18 | 블록체인: proof_of_work, task_reward, reward_ledger |
| `0010_pow_nonce_difficulty.sql` | M18 | PoW nonce/difficulty 컬럼 추가 |
| `0011_playbook_versions.sql` | M22 | Playbook 버전관리: playbook_versions |
| `0012_async_tasks.sql` | M23 | 비동기 작업: async_jobs |
| `0013_pow_ts_raw.sql` | M27 | PoW ts_raw 컬럼 + 기존 데이터 backfill |

```bash
# 전체 마이그레이션 적용 (순서대로)
for f in $(ls migrations/*.sql | sort); do
  echo "Applying $f..."
  PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -f "$f"
done
```

---

## 3. 테이블 관계도 (ASCII)

```
                                ┌─────────────┐
                                │   assets    │
                                │─────────────│
                                │ id (PK)     │
                                │ name        │
                                │ type        │
                                │ platform    │
                                │ env         │
                                │ mgmt_ip     │
                                └──────┬──────┘
                                       │
                          ┌────────────┼────────────┐
                          │            │            │
                   ┌──────▼──────┐     │     ┌──────▼──────┐
                   │asset_       │     │     │  targets    │
                   │endpoints    │     │     │─────────────│
                   │─────────────│     │     │ asset_id FK │
                   │ asset_id FK │     │     │ base_url    │
                   │ endpoint_   │     │     │ health      │
                   │ type        │     │     └──────┬──────┘
                   └─────────────┘     │            │
                                       │            │
┌──────────────┐              ┌────────▼────────┐   │
│   playbooks  │◄─────────────│    projects     │   │
│──────────────│  playbook_id │────────────────│   │
│ id (PK)      │              │ id (PK)        │   │
│ name         │              │ name           │   │
│ version      │              │ request_text   │   │
│ category     │              │ status         │   │
│ steps[]      │              │ current_stage  │   │
└──────┬───────┘              │ mode           │   │
       │                      │ master_mode    │   │
       │                      │ priority       │   │
       │                      │ risk_level     │   │
       │                      └───┬──┬──┬──────┘   │
       │                          │  │  │          │
       │          ┌───────────────┘  │  └──────┐   │
       │          │                  │         │   │
       │   ┌──────▼──────┐   ┌──────▼──────┐  │   │
       │   │  job_runs   │   │  evidence   │  │   │
       │   │─────────────│   │─────────────│  │   │
       │   │ project_id  │   │ project_id  │  │   │
       │   │ asset_id    │   │ job_run_id  │  │   │
       │   │ skill_id    │   │ agent_role  │  │   │
       │   │ status      │   │ tool_name   │  │   │
       │   └─────────────┘   │ command_text│  │   │
       │                     │ stdout_ref  │  │   │
       │                     │ exit_code   │  │   │
       │                     └──────┬──────┘  │   │
       │                            │         │   │
       │                     ┌──────▼──────┐  │   │
       │                     │proof_of_work│  │   │
       │                     │─────────────│  │   │
       │                     │ project_id  │  │   │
       │                     │ agent_id    │  │   │
       │                     │ evidence_   │  │   │
       │                     │ hash        │  │   │
       │                     │ block_hash  │  │   │
       │                     │ prev_hash   │  │   │
       │                     └──────┬──────┘  │   │
       │                            │         │   │
       │                     ┌──────▼──────┐  │   │
       │                     │task_reward  │  │   │
       │                     │─────────────│  │   │
       │                     │ pow_id FK   │  │   │
       │                     │ agent_id    │  │   │
       │                     │ total_reward│  │   │
       │                     │ risk_level  │  │   │
       │                     └─────────────┘  │   │
       │                                      │   │
       │          ┌───────────────────────────┘   │
       │          │                               │
       │   ┌──────▼──────────┐  ┌────────────────▼┐
       │   │completion_      │  │ project_assets  │
       │   │reports          │  │─────────────────│
       │   │─────────────────│  │ project_id FK   │
       │   │ project_id FK   │  │ asset_id FK     │
       │   │ playbook_id FK  │  │ scope_role      │
       │   │ outcome         │  └─────────────────┘
       │   │ summary         │
       │   └─────────────────┘
       │
┌──────▼───────┐
│playbook_     │
│versions      │
│──────────────│
│ playbook_id  │
│ version_     │
│ number       │
│ snapshot_json│
└──────────────┘
```

---

## 4. 핵심 테이블 상세

### 4.1 projects

프로젝트는 OpsClaw의 최상위 작업 단위다.

```sql
CREATE TABLE projects (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    request_text  TEXT NOT NULL,
    requester_type TEXT NOT NULL DEFAULT 'human',
    status        TEXT NOT NULL,
    -- CHECK: created|planned|running|blocked|failed|completed|closed
    current_stage TEXT NOT NULL,
    mode          TEXT NOT NULL,
    -- CHECK: one_shot|batch|continuous
    playbook_id   TEXT,
    priority      TEXT NOT NULL DEFAULT 'normal',
    -- CHECK: low|normal|high|critical
    risk_level    TEXT NOT NULL DEFAULT 'medium',
    -- CHECK: low|medium|high|critical
    master_mode   TEXT NOT NULL DEFAULT 'native',
    -- CHECK: native|external
    summary       TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at     TIMESTAMPTZ
);
```

**master_mode 설명:**
- `native`: OpsClaw 내장 LLM(Master Service)이 계획 수립/실행 지시
- `external`: 외부 AI(Claude Code 등)가 Manager API를 직접 호출

### 4.2 evidence

모든 명령 실행 결과가 저장되는 핵심 테이블이다.

```sql
CREATE TABLE evidence (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL REFERENCES projects(id),
    job_run_id      TEXT REFERENCES job_runs(id),
    asset_id        TEXT REFERENCES assets(id),
    target_id       TEXT REFERENCES targets(id),
    agent_role      TEXT NOT NULL,
    -- CHECK: manager|subagent|master
    agent_id        TEXT,
    tool_name       TEXT NOT NULL,
    command_text    TEXT,
    input_payload_ref TEXT,
    stdout_ref      TEXT,
    stderr_ref      TEXT,
    exit_code       INTEGER,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    evidence_type   TEXT NOT NULL,
    -- CHECK: command|file_diff|api_call|probe|report_fragment
    metadata        JSONB NOT NULL DEFAULT '{}'
);
```

**stdout_ref 형식:** `inline://stdout/ev_xxxx:실제출력내용`

### 4.3 proof_of_work

블록체인 작업증명 테이블이다. 에이전트별로 체인을 형성한다.

```sql
CREATE TABLE proof_of_work (
    id             TEXT PRIMARY KEY,
    agent_id       TEXT NOT NULL,
    project_id     TEXT NOT NULL REFERENCES projects(id),
    task_order     INT NOT NULL,
    task_title     TEXT NOT NULL DEFAULT '',
    evidence_hash  TEXT NOT NULL,   -- sha256(stdout+stderr+exit_code)
    prev_hash      TEXT NOT NULL,   -- 이전 block_hash (첫 블록: '0'*64)
    block_hash     TEXT NOT NULL,   -- sha256(prev_hash+evidence_hash+ts)
    ts             TIMESTAMPTZ NOT NULL DEFAULT now(),
    ts_raw         TEXT,            -- 원본 timestamp 문자열
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 4.4 task_reward

Task별 RL 보상 신호를 저장한다.

```sql
CREATE TABLE task_reward (
    id             TEXT PRIMARY KEY,
    pow_id         TEXT NOT NULL REFERENCES proof_of_work(id),
    project_id     TEXT NOT NULL,
    agent_id       TEXT NOT NULL,
    task_order     INT NOT NULL,
    task_title     TEXT NOT NULL DEFAULT '',
    base_score     FLOAT NOT NULL,       -- +1.0 성공 / -1.0 실패
    speed_bonus    FLOAT NOT NULL DEFAULT 0,
    risk_penalty   FLOAT NOT NULL DEFAULT 0,
    quality_bonus  FLOAT NOT NULL DEFAULT 0,
    total_reward   FLOAT NOT NULL,
    exit_code      INT NOT NULL,
    duration_s     FLOAT NOT NULL DEFAULT 0,
    risk_level     TEXT NOT NULL DEFAULT 'low',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 4.5 reward_ledger

에이전트별 누적 보상 잔액이다.

```sql
CREATE TABLE reward_ledger (
    agent_id       TEXT PRIMARY KEY,
    balance        FLOAT NOT NULL DEFAULT 0,
    total_tasks    INT NOT NULL DEFAULT 0,
    success_count  INT NOT NULL DEFAULT 0,
    fail_count     INT NOT NULL DEFAULT 0,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 4.6 assets

관리 대상 서버/인프라 자산이다.

```sql
CREATE TABLE assets (
    id                     TEXT PRIMARY KEY,
    name                   TEXT NOT NULL UNIQUE,
    type                   TEXT NOT NULL,
    platform               TEXT NOT NULL,
    env                    TEXT NOT NULL,
    mgmt_ip                INET NOT NULL,
    roles                  JSONB NOT NULL DEFAULT '[]',
    agent_id               TEXT,
    subagent_status        TEXT NOT NULL DEFAULT 'unknown',
    -- CHECK: unknown|healthy|unhealthy|missing
    expected_subagent_port INTEGER,
    auth_ref               TEXT,
    metadata               JSONB NOT NULL DEFAULT '{}',
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.7 playbooks / playbook_steps

자동화 작업 정의와 실행 단계이다.

```sql
CREATE TABLE playbooks (
    id                   TEXT PRIMARY KEY,
    version              TEXT NOT NULL,
    name                 TEXT NOT NULL,
    category             TEXT,
    description          TEXT,
    execution_mode       TEXT,  -- one_shot|batch|continuous
    default_risk_level   TEXT,
    dry_run_supported    BOOLEAN DEFAULT false,
    explain_supported    BOOLEAN DEFAULT false,
    required_asset_roles JSONB,
    failure_policy       JSONB,
    enabled              BOOLEAN DEFAULT true,
    metadata             JSONB,
    created_at           TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE playbook_steps (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    playbook_id     TEXT NOT NULL REFERENCES playbooks(id),
    step_order      INTEGER NOT NULL,
    step_type       TEXT NOT NULL,      -- tool|skill|playbook|shell
    ref_id          TEXT,               -- 참조할 tool/skill/playbook ID
    name            TEXT,
    condition_expr  TEXT,               -- 조건부 실행
    retry_policy    JSONB,
    on_failure_action TEXT,             -- stop|skip|retry
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

### 4.8 experiences / task_memories

4계층 메모리의 2-3층이다.

```sql
CREATE TABLE task_memories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id  TEXT NOT NULL REFERENCES projects(id),
    job_run_id  TEXT REFERENCES job_runs(id),
    summary     TEXT NOT NULL,
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE experiences (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category             TEXT NOT NULL,
    title                TEXT NOT NULL,
    summary              TEXT NOT NULL,
    outcome              TEXT,
    asset_id             TEXT REFERENCES assets(id),
    linked_evidence_ids  JSONB DEFAULT '[]',
    metadata             JSONB,
    created_at           TIMESTAMPTZ DEFAULT now()
);
```

### 4.9 schedules / watch_jobs / incidents

배치 스케줄과 감시 작업이다.

```sql
CREATE TABLE schedules (
    id             UUID PRIMARY KEY,
    project_id     TEXT NOT NULL REFERENCES projects(id),
    schedule_type  TEXT NOT NULL,
    cron_expr      TEXT,
    next_run       TIMESTAMPTZ,
    last_run       TIMESTAMPTZ,
    enabled        BOOLEAN DEFAULT true,
    metadata       JSONB,
    created_at     TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE watch_jobs (
    id          UUID PRIMARY KEY,
    project_id  TEXT NOT NULL REFERENCES projects(id),
    watch_type  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'running',
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE incidents (
    id          UUID PRIMARY KEY,
    project_id  TEXT REFERENCES projects(id),
    severity    TEXT NOT NULL,
    summary     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'open',
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);
```

### 4.10 notification_channels / notification_rules

알림 채널과 라우팅 규칙이다.

```sql
CREATE TABLE notification_channels (
    id            UUID PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    channel_type  TEXT NOT NULL,  -- webhook|email|slack|log
    config        JSONB NOT NULL DEFAULT '{}',
    enabled       BOOLEAN NOT NULL DEFAULT true,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE notification_rules (
    id                 UUID PRIMARY KEY,
    name               TEXT NOT NULL,
    event_type         TEXT NOT NULL,  -- incident.created|schedule.failed|*|...
    channel_id         UUID NOT NULL REFERENCES notification_channels(id),
    filter_conditions  JSONB NOT NULL DEFAULT '{}',
    enabled            BOOLEAN NOT NULL DEFAULT true,
    created_at         TIMESTAMPTZ DEFAULT now()
);
```

### 4.11 roles / actor_roles (RBAC)

역할 기반 접근 제어이다.

```sql
CREATE TABLE roles (
    id           UUID PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE,
    permissions  JSONB NOT NULL DEFAULT '[]',
    description  TEXT,
    created_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE actor_roles (
    id         UUID PRIMARY KEY,
    actor_id   TEXT NOT NULL,
    actor_type TEXT NOT NULL DEFAULT 'user',
    role_id    UUID NOT NULL REFERENCES roles(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(actor_id, role_id)
);
```

**기본 역할:**

| 역할 | 권한 |
|------|------|
| admin | `["*"]` (전체 접근) |
| operator | project/asset/evidence/schedule 읽기+쓰기 |
| viewer | project/asset/evidence/schedule/experience 읽기 전용 |
| auditor | audit 읽기+내보내기 + project/evidence 읽기 |

### 4.12 audit_logs

모든 시스템 이벤트가 기록되는 감사 로그이다.

```sql
CREATE TABLE audit_logs (
    id          TEXT PRIMARY KEY,
    event_type  TEXT NOT NULL,
    actor_type  TEXT NOT NULL,
    actor_id    TEXT NOT NULL,
    project_id  TEXT REFERENCES projects(id),
    asset_id    TEXT REFERENCES assets(id),
    ref_id      TEXT,
    payload     JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 4.13 async_jobs

비동기 실행 상태 추적 테이블이다.

```sql
CREATE TABLE async_jobs (
    id            TEXT PRIMARY KEY,
    project_id    TEXT NOT NULL REFERENCES projects(id),
    job_type      TEXT NOT NULL DEFAULT 'execute_plan',
    status        TEXT NOT NULL DEFAULT 'queued',
    -- CHECK: queued|running|completed|failed
    payload_json  JSONB,
    result_json   JSONB,
    error_message TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ
);
```

### 4.14 playbook_versions

Playbook 스냅샷/롤백을 위한 버전 관리 테이블이다.

```sql
CREATE TABLE playbook_versions (
    id              TEXT PRIMARY KEY,
    playbook_id     TEXT NOT NULL REFERENCES playbooks(id),
    version_number  INTEGER NOT NULL,
    snapshot_json   JSONB NOT NULL,  -- {playbook: {...}, steps: [...]}
    note            TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(playbook_id, version_number)
);
```

---

## 5. 주요 쿼리 예시

### 5.1 프로젝트별 Evidence 통계

```sql
SELECT
    p.id, p.name, p.status,
    COUNT(e.id) AS evidence_count,
    SUM(CASE WHEN e.exit_code = 0 THEN 1 ELSE 0 END) AS success,
    SUM(CASE WHEN e.exit_code != 0 THEN 1 ELSE 0 END) AS failed
FROM projects p
LEFT JOIN evidence e ON e.project_id = p.id
GROUP BY p.id, p.name, p.status
ORDER BY p.created_at DESC
LIMIT 20;
```

### 5.2 에이전트별 보상 현황

```sql
SELECT
    rl.agent_id,
    rl.balance,
    rl.total_tasks,
    rl.success_count,
    rl.fail_count,
    ROUND(rl.success_count::numeric / NULLIF(rl.total_tasks, 0) * 100, 1) AS success_rate
FROM reward_ledger rl
ORDER BY rl.balance DESC;
```

### 5.3 PoW 체인 최근 블록

```sql
SELECT
    pw.id, pw.agent_id, pw.task_title,
    pw.block_hash,
    LEFT(pw.prev_hash, 12) || '...' AS prev_hash_short,
    pw.ts
FROM proof_of_work pw
ORDER BY pw.ts DESC
LIMIT 10;
```

### 5.4 알림 발송 이력

```sql
SELECT
    nl.id, nl.event_type, nl.status,
    nc.name AS channel_name, nc.channel_type,
    nl.error, nl.sent_at
FROM notification_logs nl
JOIN notification_channels nc ON nc.id = nl.channel_id
ORDER BY nl.sent_at DESC
LIMIT 20;
```

### 5.5 Playbook 실행 현황

```sql
SELECT
    pb.name, pb.version, pb.category,
    COUNT(DISTINCT cr.id) AS completion_reports,
    SUM(CASE WHEN cr.outcome = 'success' THEN 1 ELSE 0 END) AS successes,
    SUM(CASE WHEN cr.outcome = 'failed' THEN 1 ELSE 0 END) AS failures
FROM playbooks pb
LEFT JOIN completion_reports cr ON cr.playbook_id = pb.id
GROUP BY pb.name, pb.version, pb.category
ORDER BY completion_reports DESC;
```

### 5.6 감사 로그 검색

```sql
-- 특정 프로젝트의 모든 감사 이벤트
SELECT event_type, actor_id, payload, created_at
FROM audit_logs
WHERE project_id = 'proj_xxx'
ORDER BY created_at DESC;

-- 최근 1시간 내 모든 write 이벤트
SELECT *
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '1 hour'
  AND event_type LIKE '%write%'
ORDER BY created_at DESC;
```

---

## 6. 인덱스 전략

성능 최적화를 위해 다음 인덱스가 생성되어 있다.

| 테이블 | 인덱스 | 용도 |
|--------|--------|------|
| projects | `idx_projects_status` | 상태별 필터링 |
| projects | `idx_projects_created_at` | 시간순 정렬 |
| projects | `idx_projects_master_mode` | 모드별 필터링 |
| evidence | `idx_evidence_project_id` | 프로젝트별 조회 |
| proof_of_work | `idx_pow_agent_id` | 에이전트별 체인 |
| proof_of_work | `idx_pow_agent_ts` | 에이전트+시간 복합 |
| task_reward | `idx_task_reward_agent` | 에이전트별 보상 |
| audit_logs | `idx_audit_logs_created_at` | 시간순 조회 |
| notification_rules | `idx_notif_rules_event_type` | 이벤트 매칭 |

---

## 7. 백업과 복구

```bash
# 데이터베이스 백업 (API)
curl -X POST http://localhost:8000/admin/backup -H "X-API-Key: $OPSCLAW_API_KEY"

# 백업 목록
curl http://localhost:8000/admin/backups -H "X-API-Key: $OPSCLAW_API_KEY"

# 수동 pg_dump
PGPASSWORD=opsclaw pg_dump -h 127.0.0.1 -U opsclaw -d opsclaw -F c -f backup.dump

# 복구
PGPASSWORD=opsclaw pg_restore -h 127.0.0.1 -U opsclaw -d opsclaw -c backup.dump
```
