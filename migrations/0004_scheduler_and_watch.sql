-- 0004_scheduler_and_watch.sql
-- Scheduler and watch tables for background processing and monitoring

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE watch_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    job_type TEXT NOT NULL,
    schedule_id UUID REFERENCES schedules(id) ON DELETE SET NULL,
    status TEXT NOT NULL,
    last_checked TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE watch_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    watch_job_id UUID REFERENCES watch_jobs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
