-- 0003_history_and_experience.sql
-- Tables for storing history, experience, retrieval documents, and related concepts

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE histories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    job_run_id UUID REFERENCES job_runs(id) ON DELETE SET NULL,
    event TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE experiences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES assets(id) ON DELETE CASCADE,
    skill_id TEXT REFERENCES skills(id) ON DELETE SET NULL,
    outcome TEXT,
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE retrieval_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE task_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES job_runs(id) ON DELETE CASCADE,
    memory_type TEXT NOT NULL,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    severity TEXT,
    description TEXT,
    status TEXT,
    opened_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    closed_at TIMESTAMP WITH TIME ZONE
);
