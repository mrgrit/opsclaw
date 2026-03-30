-- ================================================
-- Portal RBAC: 등급 + 그룹
-- ================================================

-- 사용자 등급 추가 (기존 role 컬럼 활용, 값 확장)
-- role: general, ycdc, admin, demo
ALTER TABLE portal_users ADD COLUMN IF NOT EXISTS role_level VARCHAR(20) DEFAULT 'general';
UPDATE portal_users SET role_level = 'admin' WHERE role = 'admin';
UPDATE portal_users SET role_level = 'general' WHERE role_level IS NULL OR role_level = '';

-- 그룹
CREATE TABLE IF NOT EXISTS portal_groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    permissions JSONB DEFAULT '{}',  -- {"courses":["all"],"novel":true,"ctf":true,"terminal":true,"papers":false}
    created_at TIMESTAMP DEFAULT NOW()
);

-- 기본 그룹
INSERT INTO portal_groups (name, description, permissions) VALUES
    ('미분류', '신규 사용자 기본 그룹', '{"courses":["course1-attack"],"novel":["vol01"],"ctf":false,"terminal":false,"papers":false}'),
    ('YCDC', 'YCDC 회원', '{"courses":"all","novel":"all","ctf":true,"terminal":true,"papers":false}'),
    ('관리자', '전체 관리자', '{"courses":"all","novel":"all","ctf":true,"terminal":true,"papers":true}')
ON CONFLICT (name) DO NOTHING;

-- 사용자-그룹 매핑
CREATE TABLE IF NOT EXISTS portal_user_groups (
    user_id INTEGER REFERENCES portal_users(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES portal_groups(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, group_id)
);

-- 기존 admin 사용자를 관리자 그룹에
INSERT INTO portal_user_groups (user_id, group_id)
SELECT u.id, g.id FROM portal_users u, portal_groups g
WHERE u.username = 'admin' AND g.name = '관리자'
ON CONFLICT DO NOTHING;

-- ================================================
-- Community: 게시판 + 게시글 + 댓글 + 파일
-- ================================================

-- 게시판 정의
CREATE TABLE IF NOT EXISTS portal_boards (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,        -- URL 경로용 (notice, free, qna, ...)
    name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT '',
    board_type VARCHAR(20) DEFAULT 'board',   -- board, blog
    theme VARCHAR(30) DEFAULT 'default',      -- default, dark, minimal, card
    allow_upload BOOLEAN DEFAULT FALSE,
    write_role VARCHAR(20) DEFAULT 'general', -- general, ycdc, admin
    read_role VARCHAR(20) DEFAULT 'general',
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 기본 게시판 생성
INSERT INTO portal_boards (slug, name, description, board_type, allow_upload, write_role, sort_order) VALUES
    ('notice', '공지사항', '운영 공지사항', 'board', FALSE, 'admin', 1),
    ('free', '자유게시판', '자유로운 대화', 'board', FALSE, 'general', 2),
    ('qna', 'Q&A', '질문과 답변', 'board', FALSE, 'general', 3),
    ('security-info', '보안정보', '보안 관련 자료 공유', 'board', TRUE, 'general', 4),
    ('ai-info', 'AI정보', 'AI 관련 자료 공유', 'board', TRUE, 'general', 5),
    ('blog', '운영자 블로그', '운영자의 글', 'blog', TRUE, 'admin', 6)
ON CONFLICT (slug) DO NOTHING;

-- 게시글
CREATE TABLE IF NOT EXISTS portal_posts (
    id SERIAL PRIMARY KEY,
    board_id INTEGER REFERENCES portal_boards(id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES portal_users(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,                   -- 마크다운
    pinned BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 댓글
CREATE TABLE IF NOT EXISTS portal_comments (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES portal_posts(id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES portal_users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 첨부파일
CREATE TABLE IF NOT EXISTS portal_files (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES portal_posts(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(500) NOT NULL,
    filesize INTEGER DEFAULT 0,
    mimetype VARCHAR(100) DEFAULT '',
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- 사용자 프로필 페이지
CREATE TABLE IF NOT EXISTS portal_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES portal_users(id) ON DELETE CASCADE,
    bio_md TEXT DEFAULT '',                  -- 마크다운 자기소개
    photo_url VARCHAR(500) DEFAULT '',       -- 프로필 사진 경로
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_posts_board ON portal_posts(board_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_comments_post ON portal_comments(post_id, created_at);
CREATE INDEX IF NOT EXISTS idx_files_post ON portal_files(post_id);

