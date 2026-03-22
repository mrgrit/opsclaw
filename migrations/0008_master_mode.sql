-- Migration 0008: projects.master_mode 컬럼 추가 (M15 Platform Modes)
-- master_mode: 누가 오케스트레이션하는지
--   native   — OpsClaw 내장 LLM (Master-service)이 계획 수립 및 실행 지시
--   external — 외부 AI (Claude Code 등)가 Manager API를 직접 호출하여 오케스트레이션

ALTER TABLE projects
  ADD COLUMN IF NOT EXISTS master_mode TEXT NOT NULL DEFAULT 'native'
  CONSTRAINT projects_master_mode_check CHECK (master_mode IN ('native', 'external'));

CREATE INDEX IF NOT EXISTS idx_projects_master_mode ON projects (master_mode);

COMMENT ON COLUMN projects.master_mode IS
  'native: 내장 LLM 오케스트레이션 / external: 외부 AI(Claude Code 등) 직접 API 호출';
