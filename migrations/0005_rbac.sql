BEGIN;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_roles_name ON roles(name);

CREATE TABLE actor_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id TEXT NOT NULL,
    actor_type TEXT NOT NULL DEFAULT 'user',
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(actor_id, role_id)
);

CREATE INDEX idx_actor_roles_actor_id ON actor_roles(actor_id);
CREATE INDEX idx_actor_roles_role_id ON actor_roles(role_id);

-- Seed: built-in roles
INSERT INTO roles (name, permissions, description) VALUES
  ('admin',    '["*"]',
   'Full system access'),
  ('operator', '["project:read","project:write","asset:read","asset:write","evidence:read","evidence:write","schedule:read","schedule:write"]',
   'Standard operations access'),
  ('viewer',   '["project:read","asset:read","evidence:read","schedule:read","experience:read"]',
   'Read-only access'),
  ('auditor',  '["audit:read","audit:export","project:read","evidence:read"]',
   'Audit and compliance access');

COMMIT;
