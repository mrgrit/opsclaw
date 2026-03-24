-- M23: 비동기 태스크 큐 — async_jobs 테이블
-- execute-plan의 async_mode=true 실행 상태를 추적한다.

CREATE TABLE IF NOT EXISTS async_jobs (
    id            TEXT PRIMARY KEY,
    project_id    TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_type      TEXT NOT NULL DEFAULT 'execute_plan',
    status        TEXT NOT NULL DEFAULT 'queued',
    payload_json  JSONB,
    result_json   JSONB,
    error_message TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    CONSTRAINT async_jobs_status_check
        CHECK (status IN ('queued', 'running', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_async_jobs_project ON async_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_async_jobs_status ON async_jobs(status);
