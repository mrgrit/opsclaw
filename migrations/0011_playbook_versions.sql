-- M22: Playbook 버전 관리 (스냅샷 / 롤백)
-- 각 Playbook의 특정 시점 상태(playbook 메타 + steps 전체)를 JSON으로 저장한다.

CREATE TABLE IF NOT EXISTS playbook_versions (
    id          TEXT    PRIMARY KEY,
    playbook_id TEXT    NOT NULL REFERENCES playbooks(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    snapshot_json  JSONB  NOT NULL,   -- {playbook: {...}, steps: [...]}
    note        TEXT,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(playbook_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_playbook_versions_playbook_id
    ON playbook_versions(playbook_id);
