BEGIN;

-- Playbook 완료보고서: 작업 완료 후 Master 검수 + Manager가 생성
CREATE TABLE completion_reports (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id    TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    playbook_id   TEXT REFERENCES playbooks(id) ON DELETE SET NULL,
    playbook_name TEXT,

    -- 작업 요약
    request_text  TEXT,                      -- 원본 요구사항
    summary       TEXT,                      -- 작업 내역 요약
    outcome       TEXT NOT NULL DEFAULT 'unknown',  -- success|partial|failed|unknown

    -- 상세 내용 (JSON)
    work_details  JSONB NOT NULL DEFAULT '[]'::jsonb,   -- 수행한 작업 목록
    issues        JSONB NOT NULL DEFAULT '[]'::jsonb,   -- 발생 이슈
    next_steps    JSONB NOT NULL DEFAULT '[]'::jsonb,   -- 다음 작업 참고사항
    evidence_summary JSONB NOT NULL DEFAULT '{}'::jsonb, -- evidence 통계

    -- 메타데이터
    reviewer_id   TEXT,                      -- Master 검수자
    metadata      JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_completion_reports_project_id  ON completion_reports(project_id);
CREATE INDEX idx_completion_reports_playbook_id ON completion_reports(playbook_id);
CREATE INDEX idx_completion_reports_outcome     ON completion_reports(outcome);
CREATE INDEX idx_completion_reports_created_at  ON completion_reports(created_at DESC);

COMMIT;
