BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE notification_channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    channel_type TEXT NOT NULL,   -- 'webhook', 'email', 'slack', 'log'
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_notif_channels_type ON notification_channels(channel_type);

CREATE TABLE notification_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    event_type TEXT NOT NULL,     -- 'incident.created', 'schedule.failed', '*'
    channel_id UUID NOT NULL REFERENCES notification_channels(id) ON DELETE CASCADE,
    filter_conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_notif_rules_event_type ON notification_rules(event_type);
CREATE INDEX idx_notif_rules_channel_id ON notification_rules(channel_id);

CREATE TABLE notification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID REFERENCES notification_rules(id) ON DELETE SET NULL,
    channel_id UUID NOT NULL REFERENCES notification_channels(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'sent',   -- 'sent', 'failed'
    error TEXT,
    sent_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_notif_logs_event_type ON notification_logs(event_type);
CREATE INDEX idx_notif_logs_sent_at ON notification_logs(sent_at);

COMMIT;
