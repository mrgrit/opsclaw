-- Portal Users table for education platform
CREATE TABLE IF NOT EXISTS portal_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(20) DEFAULT 'student',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Default admin user (password: admin2026, bcrypt hash)
INSERT INTO portal_users (username, email, password_hash, role)
VALUES ('admin', 'admin@opsclaw.local', '$2b$12$LJ3m4yPn0v8Xk.GQ.z0Cxe8J5Kj7Qq5K1L9N2M3O4P5Q6R7S8T9U', 'admin')
ON CONFLICT (username) DO NOTHING;
