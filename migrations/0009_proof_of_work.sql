-- Migration 0009: M18 Proof of Work & Blockchain Reward
-- Task 단위 작업증명 + 보상 시스템 (RL reward signal 기반 인프라)

-- ── proof_of_work: 태스크 1개 = 블록 1개 ────────────────────────────────
CREATE TABLE IF NOT EXISTS proof_of_work (
    id            TEXT PRIMARY KEY,
    agent_id      TEXT NOT NULL,
    project_id    TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_order    INT NOT NULL,
    task_title    TEXT NOT NULL DEFAULT '',
    evidence_hash TEXT NOT NULL,   -- sha256(stdout + stderr + str(exit_code))
    prev_hash     TEXT NOT NULL,   -- 이 에이전트의 이전 block_hash (첫 블록은 '0'*64)
    block_hash    TEXT NOT NULL,   -- sha256(prev_hash + evidence_hash + ts)
    ts            TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pow_agent_id    ON proof_of_work(agent_id);
CREATE INDEX IF NOT EXISTS idx_pow_project_id  ON proof_of_work(project_id);
CREATE INDEX IF NOT EXISTS idx_pow_agent_ts    ON proof_of_work(agent_id, ts DESC);

COMMENT ON TABLE proof_of_work IS 'Task 단위 작업증명 블록체인 — 위변조 불가 실행 증적';
COMMENT ON COLUMN proof_of_work.evidence_hash IS 'sha256(stdout+stderr+exit_code)';
COMMENT ON COLUMN proof_of_work.block_hash    IS 'sha256(prev_hash+evidence_hash+ts)';

-- ── task_reward: Task 단위 보상 (RL reward signal) ────────────────────────
CREATE TABLE IF NOT EXISTS task_reward (
    id            TEXT PRIMARY KEY,
    pow_id        TEXT NOT NULL REFERENCES proof_of_work(id) ON DELETE CASCADE,
    project_id    TEXT NOT NULL,
    agent_id      TEXT NOT NULL,
    task_order    INT NOT NULL,
    task_title    TEXT NOT NULL DEFAULT '',
    base_score    FLOAT NOT NULL,             -- +1.0 성공 / -1.0 실패
    speed_bonus   FLOAT NOT NULL DEFAULT 0,   -- 빠를수록 +0 ~ +0.3
    risk_penalty  FLOAT NOT NULL DEFAULT 0,   -- 실패+고위험 시 -0.1 ~ -0.2
    quality_bonus FLOAT NOT NULL DEFAULT 0,   -- human feedback (future use)
    total_reward  FLOAT NOT NULL,
    exit_code     INT NOT NULL,
    duration_s    FLOAT NOT NULL DEFAULT 0,
    risk_level    TEXT NOT NULL DEFAULT 'low',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_task_reward_agent   ON task_reward(agent_id);
CREATE INDEX IF NOT EXISTS idx_task_reward_project ON task_reward(project_id);

COMMENT ON TABLE task_reward IS 'Task별 RL 보상 신호 — 강화학습 policy 개선용 reward signal';

-- ── reward_ledger: 에이전트별 누적 잔액 ─────────────────────────────────
CREATE TABLE IF NOT EXISTS reward_ledger (
    agent_id      TEXT PRIMARY KEY,
    balance       FLOAT NOT NULL DEFAULT 0,
    total_tasks   INT   NOT NULL DEFAULT 0,
    success_count INT   NOT NULL DEFAULT 0,
    fail_count    INT   NOT NULL DEFAULT 0,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE reward_ledger IS '에이전트별 누적 보상 잔액 — 랭킹 및 RL 성과 추적';
