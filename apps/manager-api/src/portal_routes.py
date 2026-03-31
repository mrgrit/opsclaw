"""
OpsClaw Education Portal — Backend API Routes
================================================
Single-file FastAPI router for the education portal.
Include in Manager API main.py:  app.include_router(portal_router)
"""

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import List, Optional

import psycopg2
import psycopg2.extras
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    File,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

logger = logging.getLogger("portal")

# ── Config ────────────────────────────────────────────────────────────────────

JWT_SECRET = os.getenv("PORTAL_JWT_SECRET", "opsclaw-portal-secret-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = 60 * 60 * 24  # 24 hours

CONTENTS_BASE = Path("/home/opsclaw/opsclaw/contents")

# LLM Chat config
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://192.168.0.105:11434")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "")
ANTHROPIC_AUTH_TOKEN = os.getenv("ANTHROPIC_AUTH_TOKEN", "")

CHAT_MODELS = {
    "gpt-oss:120b": {"type": "ollama", "model": "gpt-oss:120b"},
    "claude": {"type": "claude", "model": "claude-sonnet-4-20250514"},
}

SSH_HOST_MAP = {
    "v-secu": "192.168.0.108",
    "v-web":  "192.168.0.110",
    "v-siem": "192.168.0.109",
}

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "opsclaw",
    "password": "opsclaw",
    "dbname": "opsclaw",
}

security = HTTPBearer(auto_error=False)

# ── DB helpers ────────────────────────────────────────────────────────────────


def _get_conn():
    return psycopg2.connect(**DB_CONFIG)


def _ensure_portal_tables():
    """Create portal_users table if it doesn't exist."""
    ddl = """
    CREATE TABLE IF NOT EXISTS portal_users (
        id          SERIAL PRIMARY KEY,
        username    VARCHAR(64) UNIQUE NOT NULL,
        email       VARCHAR(128) UNIQUE NOT NULL,
        password_hash     VARCHAR(128) NOT NULL,
        role        VARCHAR(16) NOT NULL DEFAULT 'student',
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        conn.close()
    except Exception as e:
        logger.warning("portal table init failed (will retry on first request): %s", e)


def _ensure_rag_table():
    """Create portal_rag_index table for RAG full-text search."""
    ddl = """
    CREATE TABLE IF NOT EXISTS portal_rag_index (
        id SERIAL PRIMARY KEY,
        source_type VARCHAR(20) NOT NULL,
        source_path VARCHAR(300) NOT NULL,
        title VARCHAR(300) DEFAULT '',
        content TEXT NOT NULL,
        content_tsv tsvector,
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(source_type, source_path)
    );
    CREATE INDEX IF NOT EXISTS idx_rag_tsv ON portal_rag_index USING gin(content_tsv);
    """
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        conn.close()
    except Exception as e:
        logger.warning("RAG table init failed: %s", e)


def _rag_index_all():
    """Index all education, novel, manual content for RAG search."""
    indexed = 0
    rows = []  # (source_type, source_path, title, content)

    # 1. Education: contents/education/**/lecture.md
    edu_dir = CONTENTS_BASE / "education"
    if edu_dir.is_dir():
        for course_dir in sorted(edu_dir.iterdir()):
            if not course_dir.is_dir() or course_dir.name.startswith((".", "00")):
                continue
            for week_dir in sorted(course_dir.iterdir()):
                if not week_dir.is_dir() or not week_dir.name.startswith("week"):
                    continue
                lf = week_dir / "lecture.md"
                if lf.is_file():
                    text = lf.read_text("utf-8", errors="replace")
                    first_line = text.split("\n", 1)[0]
                    title = first_line.lstrip("# ").strip() if first_line.startswith("#") else week_dir.name
                    source_path = f"{course_dir.name}/{week_dir.name}"
                    rows.append(("education", source_path, title, text))

    # 2. Novel: contents/novel/**/ch*.md
    novel_dir = CONTENTS_BASE / "novel"
    if novel_dir.is_dir():
        for vol_dir in sorted(novel_dir.iterdir()):
            if not vol_dir.is_dir() or not vol_dir.name.startswith("vol"):
                continue
            for f in sorted(vol_dir.iterdir()):
                if f.is_file() and f.suffix == ".md" and f.stem.startswith("ch"):
                    text = f.read_text("utf-8", errors="replace")
                    first_line = text.split("\n", 1)[0]
                    title = first_line.lstrip("# ").strip() if first_line.startswith("#") else f.stem
                    source_path = f"{vol_dir.name}/{f.stem}"
                    rows.append(("novel", source_path, title, text))

    # 3. Manual: contents/manual/**/*.md
    manual_dir = CONTENTS_BASE / "manual"
    if manual_dir.is_dir():
        for md_file in sorted(manual_dir.rglob("*.md")):
            if md_file.is_file():
                text = md_file.read_text("utf-8", errors="replace")
                first_line = text.split("\n", 1)[0]
                title = first_line.lstrip("# ").strip() if first_line.startswith("#") else md_file.stem
                source_path = str(md_file.relative_to(manual_dir))
                rows.append(("manual", source_path, title, text))

    if not rows:
        logger.info("RAG index: no content files found")
        return 0

    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                for source_type, source_path, title, content in rows:
                    cur.execute(
                        "INSERT INTO portal_rag_index "
                        "(source_type, source_path, title, content, content_tsv, updated_at) "
                        "VALUES (%s, %s, %s, %s, to_tsvector('simple', %s), NOW()) "
                        "ON CONFLICT (source_type, source_path) DO UPDATE SET "
                        "title = EXCLUDED.title, content = EXCLUDED.content, "
                        "content_tsv = to_tsvector('simple', EXCLUDED.content), "
                        "updated_at = NOW()",
                        (source_type, source_path, title, content, content),
                    )
                    indexed += 1
        conn.close()
    except Exception as e:
        logger.error("RAG indexing error: %s", e)
        return -1

    logger.info("RAG index: indexed %d documents", indexed)
    return indexed


def _rag_search(query: str, limit: int = 3) -> list:
    """Full-text search across all indexed RAG content."""
    if not query or not query.strip():
        return []
    query = query.strip()
    results = []
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT source_type, source_path, title, "
                "LEFT(content, 500) AS snippet "
                "FROM portal_rag_index "
                "WHERE content_tsv @@ plainto_tsquery('simple', %s) "
                "   OR content ILIKE %s "
                "ORDER BY "
                "  ts_rank(content_tsv, plainto_tsquery('simple', %s)) DESC "
                "LIMIT %s",
                (query, f"%{query}%", query, limit),
            )
            results = [dict(r) for r in cur.fetchall()]
        conn.close()
    except Exception as e:
        logger.warning("RAG search error: %s", e)
    return results


_ensure_portal_tables()

# Initialize RAG table and index on startup
try:
    _ensure_rag_table()
    _rag_index_all()
except Exception as e:
    logger.warning("RAG startup indexing skipped: %s", e)

# ── Password hashing ─────────────────────────────────────────────────────────


def _hash_password(password: str) -> str:
    """SHA-256 with a static salt prefix (simple, no bcrypt dep)."""
    salted = f"opsclaw:{password}:portal"
    return hashlib.sha256(salted.encode()).hexdigest()


# ── JWT helpers (manual, no PyJWT dependency) ─────────────────────────────────


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _jwt_encode(payload: dict) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    h = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig_input = f"{h}.{p}".encode()
    sig = hmac.new(JWT_SECRET.encode(), sig_input, hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url_encode(sig)}"


def _jwt_decode(token: str) -> dict:
    """Decode and verify a JWT. Raises ValueError on failure."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("invalid token format")
    h, p, s = parts
    sig_input = f"{h}.{p}".encode()
    expected = hmac.new(JWT_SECRET.encode(), sig_input, hashlib.sha256).digest()
    actual = _b64url_decode(s)
    if not hmac.compare_digest(expected, actual):
        raise ValueError("invalid signature")
    payload = json.loads(_b64url_decode(p))
    if payload.get("exp", 0) < time.time():
        raise ValueError("token expired")
    return payload


# ── Auth dependencies ─────────────────────────────────────────────────────────


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Decode JWT from Authorization: Bearer <token> header."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = _jwt_decode(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    user = {
        "user_id": payload["sub"],
        "username": payload["username"],
        "role": payload.get("role", "student"),
        "role_level": payload.get("role_level", "general"),
    }
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """Like get_current_user but returns None instead of raising."""
    if credentials is None:
        return None
    try:
        payload = _jwt_decode(credentials.credentials)
    except ValueError:
        return None
    return {
        "user_id": payload["sub"],
        "username": payload["username"],
        "role": payload.get("role", "student"),
        "role_level": payload.get("role_level", "general"),
    }


async def admin_required(user: dict = Depends(get_current_user)) -> dict:
    """Check that the authenticated user has admin role."""
    if user.get("role") != "admin" and user.get("role_level") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ── Pydantic models ──────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class UserInfo(BaseModel):
    user_id: int
    username: str
    email: str
    role: str


# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(tags=["portal"])

# ── Auth endpoints ────────────────────────────────────────────────────────────


@router.post("/portal/auth/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """Register a new portal user and return a JWT."""
    if len(req.username) < 2 or len(req.password) < 4:
        raise HTTPException(400, "Username min 2 chars, password min 4 chars")

    password_hash = _hash_password(req.password)
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO portal_users (username, email, password_hash) "
                    "VALUES (%s, %s, %s) RETURNING id, role, "
                    "COALESCE(role_level, 'general')",
                    (req.username, req.email, password_hash),
                )
                row = cur.fetchone()
        conn.close()
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(409, "Username or email already exists")
    except Exception as e:
        logger.error("register error: %s", e)
        raise HTTPException(500, "Database error")

    user_id, role, role_level = row
    token = _jwt_encode({
        "sub": user_id,
        "username": req.username,
        "role": role,
        "role_level": role_level,
        "exp": time.time() + JWT_EXPIRE_SECONDS,
    })
    return TokenResponse(access_token=token, username=req.username, role=role)


@router.post("/portal/auth/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate user and return a JWT."""
    password_hash = _hash_password(req.password)
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT id, username, role, "
                "COALESCE(role_level, 'general') AS role_level "
                "FROM portal_users "
                "WHERE username = %s AND password_hash = %s",
                (req.username, password_hash),
            )
            row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("login error: %s", e)
        raise HTTPException(500, "Database error")

    if not row:
        raise HTTPException(401, "Invalid username or password")

    token = _jwt_encode({
        "sub": row["id"],
        "username": row["username"],
        "role": row["role"],
        "role_level": row["role_level"],
        "exp": time.time() + JWT_EXPIRE_SECONDS,
    })
    return TokenResponse(
        access_token=token, username=row["username"], role=row["role"]
    )


@router.get("/portal/auth/me", response_model=UserInfo)
async def me(user: dict = Depends(get_current_user)):
    """Return current user info from JWT."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT id, username, email, role FROM portal_users WHERE id = %s",
                (user["user_id"],),
            )
            row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("me error: %s", e)
        raise HTTPException(500, "Database error")

    if not row:
        raise HTTPException(404, "User not found")
    return UserInfo(
        user_id=row["id"],
        username=row["username"],
        email=row["email"],
        role=row["role"],
    )


# ── Content endpoints ─────────────────────────────────────────────────────────


def _safe_path(base: Path, *parts: str) -> Path:
    """Resolve a path under base and ensure it doesn't escape."""
    resolved = base.joinpath(*parts).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise HTTPException(403, "Path traversal denied")
    return resolved


COURSE_META = {
    "course1-attack": {
        "title": "사이버 공격/해킹/침투 테스트",
        "group": "공격 기술",
        "icon": "⚔️",
        "color": "#f85149",
        "description": "SQL Injection, XSS, 권한 상승, 네트워크 공격 등 실제 해킹 기법을 학습하고, MITRE ATT&CK 프레임워크에 매핑하여 체계적으로 이해합니다.",
    },
    "course2-security-ops": {
        "title": "보안 시스템/솔루션 운영",
        "group": "방어 운영",
        "icon": "🛡️",
        "color": "#3fb950",
        "description": "nftables 방화벽, Suricata IPS, Wazuh SIEM, ModSecurity WAF, OpenCTI 등 실제 보안 솔루션을 설치하고 운영합니다.",
    },
    "course3-web-vuln": {
        "title": "웹 취약점 점검",
        "group": "공격 기술",
        "icon": "🕷️",
        "color": "#f85149",
        "description": "OWASP Top 10 기반 웹 취약점을 체계적으로 점검하고, JuiceShop에서 실습하며, 점검 보고서를 작성합니다.",
    },
    "course4-compliance": {
        "title": "보안 표준/컴플라이언스",
        "group": "거버넌스",
        "icon": "📋",
        "color": "#d29922",
        "description": "ISO 27001, ISMS-P, NIST CSF, SOC 2, HIPAA, GDPR 등 국내외 보안 표준과 인증 체계를 학습합니다.",
    },
    "course5-soc": {
        "title": "보안관제(SOC) 운영",
        "group": "방어 운영",
        "icon": "📊",
        "color": "#3fb950",
        "description": "SOC 분석가의 업무 — 로그 분석, 경보 분류, 인시던트 대응(NIST IR), SIGMA 룰, 위협 인텔리전스를 실습합니다.",
    },
    "course6-cloud-container": {
        "title": "클라우드/컨테이너 보안",
        "group": "인프라 보안",
        "icon": "☁️",
        "color": "#58a6ff",
        "description": "Docker 컨테이너 보안, Kubernetes 보안, 클라우드(AWS) 설정 오류, IaC 보안을 실습합니다.",
    },
    "course7-ai-security": {
        "title": "AI 보안 자동화",
        "group": "AI 보안",
        "icon": "🤖",
        "color": "#bc8cff",
        "description": "OpsClaw를 활용한 보안 자동화 — Ollama LLM, 프롬프트 엔지니어링, 탐지 룰 자동 생성, 자율 에이전트를 구축합니다.",
    },
    "course8-ai-safety": {
        "title": "AI Safety",
        "group": "AI 보안",
        "icon": "🧠",
        "color": "#bc8cff",
        "description": "LLM 탈옥, 프롬프트 인젝션, 가드레일, 적대적 입력, 모델 도난, RAG 보안, AI Red Teaming을 학습합니다.",
    },
    "course9-autonomous-security": {
        "title": "자율보안시스템",
        "group": "AI 보안",
        "icon": "⚡",
        "color": "#bc8cff",
        "description": "OpsClaw의 핵심 — PoW 작업증명, 강화학습(RL), Experience 메모리, 자율 Red/Blue/Purple Team을 구축합니다.",
    },
    "course10-ai-security-agent": {
        "title": "AI보안에이전트",
        "group": "AI 보안",
        "icon": "🕹️",
        "color": "#bc8cff",
        "description": "AI 에이전트 기본부터 하네스 구축(OpsClaw/Claude Code), 멀티에이전트, RAG, 에이전트 보안까지 실습 중심으로 학습합니다.",
    },
}


@router.get("/portal/content/education")
async def list_courses():
    """List all courses with metadata and grouping."""
    edu_dir = CONTENTS_BASE / "education"
    if not edu_dir.is_dir():
        return {"courses": [], "groups": []}

    courses = []
    for d in sorted(edu_dir.iterdir()):
        if d.is_dir() and not d.name.startswith((".", "00", "slides", "papers")):
            weeks = sorted(
                w.name for w in d.iterdir() if w.is_dir() and w.name.startswith("week")
            )
            meta = COURSE_META.get(d.name, {})
            courses.append({
                "name": d.name,
                "title": meta.get("title", d.name),
                "group": meta.get("group", "기타"),
                "icon": meta.get("icon", "📘"),
                "color": meta.get("color", "#58a6ff"),
                "description": meta.get("description", ""),
                "weeks": weeks,
                "week_count": len(weeks),
            })

    # 그룹 순서
    group_order = ["공격 기술", "방어 운영", "거버넌스", "인프라 보안", "AI 보안"]
    groups = []
    seen = set()
    for g in group_order:
        group_courses = [c for c in courses if c["group"] == g]
        if group_courses:
            groups.append({"name": g, "courses": group_courses})
            seen.add(g)
    # 나머지
    others = [c for c in courses if c["group"] not in seen]
    if others:
        groups.append({"name": "기타", "courses": others})

    return {"courses": courses, "groups": groups}


@router.get("/portal/content/education/{course}")
async def get_course_weeks(course: str):
    """List weeks for a specific course."""
    course_dir = CONTENTS_BASE / "education" / course
    if not course_dir.is_dir():
        raise HTTPException(404, f"Course not found: {course}")
    weeks = []
    for w in sorted(course_dir.iterdir()):
        if w.is_dir() and w.name.startswith("week"):
            # 주차 번호 추출
            num = w.name.replace("week", "")
            # lecture.md 첫 줄에서 제목 추출
            lf = w / "lecture.md"
            title = w.name
            if lf.is_file():
                first_line = lf.read_text("utf-8").split("\n", 1)[0]
                title = first_line.lstrip("# ").strip() if first_line.startswith("#") else w.name
            weeks.append({"week": num, "title": title, "id": w.name})
    return {"course": course, "weeks": weeks}


@router.get("/portal/content/education/{course}/{week}")
async def get_lecture(
    course: str,
    week: str,
):
    """Return the lecture.md content for a specific course/week."""
    lecture_path = _safe_path(CONTENTS_BASE / "education", course, week, "lecture.md")
    if not lecture_path.is_file():
        raise HTTPException(404, f"Lecture not found: {course}/{week}")
    return {"course": course, "week": week, "content": lecture_path.read_text("utf-8")}


@router.get("/portal/content/novel")
async def list_novels():
    """List all novel volumes under contents/novel/."""
    novel_dir = CONTENTS_BASE / "novel"
    if not novel_dir.is_dir():
        return {"volumes": []}

    volumes = []
    for d in sorted(novel_dir.iterdir()):
        if d.is_dir() and d.name.startswith("vol"):
            chapters = sorted(
                f.stem
                for f in d.iterdir()
                if f.is_file() and f.suffix == ".md" and not f.name.startswith("00")
            )
            volumes.append({
                "name": d.name,
                "chapters": chapters,
                "chapter_count": len(chapters),
            })
    return {"volumes": volumes}


@router.get("/portal/content/novel/{vol}")
async def get_volume_chapters(vol: str):
    """List chapters for a specific volume."""
    vol_dir = CONTENTS_BASE / "novel" / vol
    if not vol_dir.is_dir():
        raise HTTPException(404, f"Volume not found: {vol}")
    chapters = []
    for f in sorted(vol_dir.iterdir()):
        if f.is_file() and f.suffix == ".md" and not f.name.startswith("00"):
            first_line = f.read_text("utf-8").split("\n", 1)[0]
            title = first_line.lstrip("# ").strip() if first_line.startswith("#") else f.stem
            chapters.append({"id": f.stem, "title": title})
    return {"volume": vol, "chapters": chapters}


@router.get("/portal/content/novel/{vol}/{chapter}")
async def get_chapter(
    vol: str,
    chapter: str,
):
    """Return a novel chapter markdown."""
    # Accept both "ch01" and "ch01.md"
    filename = chapter if chapter.endswith(".md") else f"{chapter}.md"
    chapter_path = _safe_path(CONTENTS_BASE / "novel", vol, filename)
    if not chapter_path.is_file():
        raise HTTPException(404, f"Chapter not found: {vol}/{chapter}")
    return {"volume": vol, "chapter": chapter, "content": chapter_path.read_text("utf-8")}


@router.get("/portal/content/papers")
async def list_papers(_admin: dict = Depends(admin_required)):
    """List papers (admin only)."""
    paper_dir = CONTENTS_BASE / "paper"
    if not paper_dir.is_dir():
        return {"papers": []}

    papers = []
    for d in sorted(paper_dir.iterdir()):
        if d.is_dir() and d.name.startswith("paper"):
            files = sorted(
                f.name for f in d.iterdir() if f.is_file() and f.suffix == ".md"
            )
            papers.append({"name": d.name, "files": files})
    return {"papers": papers}


@router.get("/portal/content/papers/{paper}/{file}")
async def get_paper(
    paper: str,
    file: str,
    _admin: dict = Depends(admin_required),
):
    """Return a paper markdown file (admin only)."""
    filename = file if file.endswith(".md") else f"{file}.md"
    paper_path = _safe_path(CONTENTS_BASE / "paper", paper, filename)
    if not paper_path.is_file():
        raise HTTPException(404, f"Paper not found: {paper}/{file}")
    return {"paper": paper, "file": file, "content": paper_path.read_text("utf-8")}


# ── WebSocket terminal ────────────────────────────────────────────────────────


@router.websocket("/portal/ws/terminal")
async def ws_terminal(
    ws: WebSocket,
    host: str = Query(...),
    user: str = Query("root"),
    password: str = Query(""),
    token: str = Query(""),
):
    """
    WebSocket → SSH bridge.
    Authenticates via JWT token in query param, then spawns an SSH process
    and relays stdin/stdout between the WebSocket and the SSH session.
    """
    # Authenticate
    if not token:
        await ws.close(code=4001, reason="Missing token")
        return
    try:
        _jwt_decode(token)
    except ValueError as e:
        await ws.close(code=4001, reason=f"Auth failed: {e}")
        return

    # Resolve host
    ssh_ip = SSH_HOST_MAP.get(host)
    if not ssh_ip:
        await ws.accept()
        await ws.send_text(f"Error: unknown host '{host}'. Valid: {list(SSH_HOST_MAP.keys())}\r\n")
        await ws.close()
        return

    await ws.accept()

    # Spawn SSH process using sshpass for password auth
    ssh_cmd = [
        "sshpass", "-p", password,
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        "-tt",
        f"{user}@{ssh_ip}",
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *ssh_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except FileNotFoundError:
        await ws.send_text("Error: sshpass not installed on server\r\n")
        await ws.close()
        return
    except Exception as e:
        await ws.send_text(f"Error spawning SSH: {e}\r\n")
        await ws.close()
        return

    async def _read_ssh():
        """Read from SSH stdout and send to WebSocket."""
        try:
            while True:
                data = await proc.stdout.read(4096)
                if not data:
                    break
                await ws.send_text(data.decode("utf-8", errors="replace"))
        except (WebSocketDisconnect, ConnectionError):
            pass
        finally:
            if proc.returncode is None:
                proc.terminate()

    async def _write_ssh():
        """Read from WebSocket and write to SSH stdin."""
        try:
            while True:
                msg = await ws.receive_text()
                if proc.stdin and not proc.stdin.is_closing():
                    proc.stdin.write(msg.encode("utf-8"))
                    await proc.stdin.drain()
        except (WebSocketDisconnect, ConnectionError):
            pass
        finally:
            if proc.returncode is None:
                proc.terminate()

    # Run both directions concurrently
    read_task = asyncio.create_task(_read_ssh())
    write_task = asyncio.create_task(_write_ssh())

    try:
        await asyncio.gather(read_task, write_task, return_exceptions=True)
    finally:
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=3)
            except asyncio.TimeoutError:
                proc.kill()
        try:
            await ws.close()
        except Exception:
            pass


# ── Chat API ─────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    model: str = "gpt-oss:120b"
    messages: list  # [{"role":"user","content":"..."}]
    context: str = ""  # 현재 페이지의 마크다운 컨텍스트


@router.get("/portal/chat/models")
async def list_chat_models():
    """사용 가능한 챗봇 모델 목록."""
    models = []
    for name, cfg in CHAT_MODELS.items():
        models.append({"id": name, "type": cfg["type"], "name": name})
    return {"models": models}


@router.post("/portal/chat")
async def chat(req: ChatRequest):
    """페이지 컨텍스트 기반 LLM 채팅."""
    import httpx

    cfg = CHAT_MODELS.get(req.model)
    if not cfg:
        raise HTTPException(400, f"Unknown model: {req.model}. Available: {list(CHAT_MODELS.keys())}")

    # 시스템 프롬프트: 페이지 컨텍스트를 포함
    system_prompt = (
        "당신은 OpsClaw 보안 교육 플랫폼의 AI 튜터입니다. "
        "학생의 질문에 친절하고 정확하게 답변하세요. "
        "아래는 학생이 현재 보고 있는 페이지의 내용입니다. "
        "이 내용을 참고하여 답변하되, 필요하면 추가 설명도 해주세요.\n\n"
    )
    if req.context:
        # 컨텍스트가 너무 길면 잘라냄
        ctx = req.context[:8000]
        system_prompt += f"--- 현재 페이지 내용 ---\n{ctx}\n--- 끝 ---\n"

    # RAG: search for related content using the latest user message
    user_messages = [m for m in req.messages if m.get("role") == "user"]
    if user_messages:
        last_user_msg = user_messages[-1].get("content", "")
        rag_results = _rag_search(last_user_msg, limit=3)
        if rag_results:
            _type_labels = {
                "education": "교육과정",
                "novel": "시나리오",
                "manual": "매뉴얼",
            }
            rag_block = "\n--- 관련 학습 자료 ---\n"
            for r in rag_results:
                label = _type_labels.get(r["source_type"], r["source_type"])
                rag_block += f"[{label}: {r['source_path']}] {r['title']}\n"
                rag_block += f"{r['snippet']}\n\n"
            rag_block += "---\n"
            system_prompt += rag_block

    messages = [{"role": "system", "content": system_prompt}] + req.messages

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            if cfg["type"] == "ollama":
                resp = await client.post(
                    f"{OLLAMA_URL}/v1/chat/completions",
                    json={"model": cfg["model"], "messages": messages, "stream": False},
                )
                data = resp.json()
                answer = data["choices"][0]["message"]["content"]

            elif cfg["type"] == "claude":
                if not ANTHROPIC_BASE_URL or not ANTHROPIC_AUTH_TOKEN:
                    raise HTTPException(503, "Claude API not configured")
                # Claude Messages API
                headers = {
                    "x-api-key": ANTHROPIC_AUTH_TOKEN,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }
                # Claude는 system을 별도 필드로
                user_msgs = [m for m in messages if m["role"] != "system"]
                body = {
                    "model": cfg["model"],
                    "max_tokens": 4096,
                    "system": system_prompt,
                    "messages": user_msgs,
                }
                resp = await client.post(
                    f"{ANTHROPIC_BASE_URL}/v1/messages",
                    json=body,
                    headers=headers,
                )
                data = resp.json()
                if "content" in data:
                    answer = data["content"][0]["text"]
                else:
                    answer = data.get("error", {}).get("message", str(data))
            else:
                raise HTTPException(400, f"Unknown model type: {cfg['type']}")

    except httpx.TimeoutException:
        raise HTTPException(504, "LLM request timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("chat error: %s", e)
        raise HTTPException(500, f"Chat error: {str(e)}")

    return {"model": req.model, "answer": answer}


# ── RAG Admin endpoints ─────────────────────────────────────────────────────


@router.post("/portal/admin/rag/rebuild")
async def admin_rag_rebuild(_admin: dict = Depends(admin_required)):
    """Rebuild the RAG full-text index from all content files (admin only)."""
    count = _rag_index_all()
    if count < 0:
        raise HTTPException(500, "RAG indexing failed — check logs")
    return {"ok": True, "indexed": count}


@router.get("/portal/admin/rag/status")
async def admin_rag_status(_admin: dict = Depends(admin_required)):
    """RAG index statistics (admin only)."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT source_type, COUNT(*) AS doc_count, "
                "MAX(updated_at) AS last_updated "
                "FROM portal_rag_index GROUP BY source_type ORDER BY source_type"
            )
            by_type = [dict(r) for r in cur.fetchall()]
            cur.execute("SELECT COUNT(*) AS total FROM portal_rag_index")
            total = cur.fetchone()["total"]
            cur.execute("SELECT MAX(updated_at) AS last_updated FROM portal_rag_index")
            last = cur.fetchone()["last_updated"]
        conn.close()
    except Exception as e:
        logger.error("rag_status error: %s", e)
        raise HTTPException(500, "Database error")

    return {
        "total_documents": total,
        "last_updated": str(last) if last else None,
        "by_type": by_type,
    }


# ── Upload directories ───────────────────────────────────────────────────────

UPLOAD_POSTS_DIR = Path("/home/opsclaw/opsclaw/data/uploads/posts")
UPLOAD_PROFILES_DIR = Path("/home/opsclaw/opsclaw/data/uploads/profiles")
UPLOAD_POSTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_PROFILES_DIR.mkdir(parents=True, exist_ok=True)


# ── RBAC Pydantic models ────────────────────────────────────────────────────


class UpdateUserRoleRequest(BaseModel):
    role_level: str  # general, ycdc, admin, demo


class CreateGroupRequest(BaseModel):
    name: str
    description: str = ""
    permissions: dict = {}


class UpdateGroupRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[dict] = None


class AddMemberRequest(BaseModel):
    user_id: int


class CreatePostRequest(BaseModel):
    title: str
    content: str
    pinned: bool = False


class UpdatePostRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    pinned: Optional[bool] = None


class CreateCommentRequest(BaseModel):
    content: str


class UpdateProfileRequest(BaseModel):
    bio_md: str = ""


# ── Permission helper ────────────────────────────────────────────────────────

# All known course slugs and novel volume slugs (used for "all" grants)
ALL_COURSES = [
    "course1-attack", "course2-security-ops", "course3-network",
    "course4-cloud", "course5-forensics", "course6-compliance",
]
ALL_NOVELS = ["vol01", "vol02", "vol03", "vol04", "vol05"]

# Default permissions by role_level
ROLE_LEVEL_DEFAULTS = {
    "general": {
        "courses": ["course1-attack"],
        "novel": ["vol01"],
        "ctf": False,
        "terminal": False,
        "papers": False,
    },
    "demo": {
        "courses": ["course1-attack"],
        "novel": ["vol01"],
        "ctf": True,
        "terminal": False,
        "papers": False,
    },
    "ycdc": {
        "courses": ALL_COURSES[:],
        "novel": ALL_NOVELS[:],
        "ctf": True,
        "terminal": True,
        "papers": False,
    },
    "admin": {
        "courses": ALL_COURSES[:],
        "novel": ALL_NOVELS[:],
        "ctf": True,
        "terminal": True,
        "papers": True,
    },
}


def _merge_permissions(base: dict, group_perms: list[dict]) -> dict:
    """Merge base role permissions with additive group permissions."""
    result = {
        "courses": list(base.get("courses", [])),
        "novel": list(base.get("novel", [])),
        "ctf": base.get("ctf", False),
        "terminal": base.get("terminal", False),
        "papers": base.get("papers", False),
    }
    for gp in group_perms:
        if not gp:
            continue
        # Additive: union of list fields
        for key in ("courses", "novel"):
            extras = gp.get(key, [])
            if isinstance(extras, list):
                for item in extras:
                    if item not in result[key]:
                        result[key].append(item)
        # Boolean fields: OR
        for key in ("ctf", "terminal", "papers"):
            if gp.get(key):
                result[key] = True
    return result


def _get_user_permissions(user_id: int, role_level: str) -> dict:
    """Get effective permissions for a user: role defaults + group grants."""
    base = ROLE_LEVEL_DEFAULTS.get(role_level, ROLE_LEVEL_DEFAULTS["general"])
    # If admin, short-circuit
    if role_level == "admin":
        return base.copy()

    group_perms = []
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT g.permissions FROM portal_groups g "
                "JOIN portal_user_groups ug ON ug.group_id = g.id "
                "WHERE ug.user_id = %s",
                (user_id,),
            )
            for row in cur.fetchall():
                if row["permissions"]:
                    group_perms.append(row["permissions"])
        conn.close()
    except Exception as e:
        logger.warning("Failed to fetch group permissions: %s", e)

    return _merge_permissions(base, group_perms)


def _get_user_role_level(user_id: int) -> str:
    """Fetch role_level from DB for a user."""
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COALESCE(role_level, 'general') FROM portal_users WHERE id = %s",
                (user_id,),
            )
            row = cur.fetchone()
        conn.close()
        return row[0] if row else "general"
    except Exception:
        return "general"


# ── RBAC — Permission check endpoint ────────────────────────────────────────


@router.get("/portal/permissions")
async def get_permissions(user: dict = Depends(get_current_user)):
    """Return current user's effective permissions (role defaults + groups)."""
    role_level = user.get("role_level", "general")
    # Re-fetch from DB to ensure freshness
    db_role_level = _get_user_role_level(user["user_id"])
    if db_role_level:
        role_level = db_role_level
    perms = _get_user_permissions(user["user_id"], role_level)
    return perms


# ── RBAC — Admin user management ────────────────────────────────────────────


@router.get("/portal/admin/users")
async def admin_list_users(_admin: dict = Depends(admin_required)):
    """List all portal users (admin only)."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, email, role, "
                "COALESCE(role_level, 'general') AS role_level, "
                "created_at FROM portal_users ORDER BY id"
            )
            users = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error("admin_list_users error: %s", e)
        raise HTTPException(500, "Database error")

    # Convert datetime to string for JSON serialization
    for u in users:
        if u.get("created_at"):
            u["created_at"] = str(u["created_at"])
    return {"users": users}


@router.put("/portal/admin/users/{user_id}")
async def admin_update_user_role(
    user_id: int,
    req: UpdateUserRoleRequest,
    _admin: dict = Depends(admin_required),
):
    """Update a user's role_level (admin only)."""
    valid_levels = ("general", "ycdc", "admin", "demo")
    if req.role_level not in valid_levels:
        raise HTTPException(400, f"Invalid role_level. Must be one of: {valid_levels}")

    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE portal_users SET role_level = %s WHERE id = %s RETURNING id",
                    (req.role_level, user_id),
                )
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("admin_update_user_role error: %s", e)
        raise HTTPException(500, "Database error")

    if not row:
        raise HTTPException(404, "User not found")
    return {"ok": True, "user_id": user_id, "role_level": req.role_level}


# ── RBAC — Group management ─────────────────────────────────────────────────


@router.get("/portal/admin/groups")
async def admin_list_groups(user: dict = Depends(get_current_user)):
    """List all groups. Any authenticated user can view."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT g.id, g.name, g.description, g.permissions, "
                "COALESCE(array_agg(ug.user_id) FILTER (WHERE ug.user_id IS NOT NULL), '{}') AS member_ids "
                "FROM portal_groups g "
                "LEFT JOIN portal_user_groups ug ON ug.group_id = g.id "
                "GROUP BY g.id ORDER BY g.id"
            )
            groups = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error("admin_list_groups error: %s", e)
        raise HTTPException(500, "Database error")

    # Convert arrays
    for g in groups:
        if g.get("member_ids") and isinstance(g["member_ids"], list):
            g["member_ids"] = [int(x) for x in g["member_ids"] if x]
    return {"groups": groups}


@router.post("/portal/admin/groups")
async def admin_create_group(
    req: CreateGroupRequest,
    _admin: dict = Depends(admin_required),
):
    """Create a new group (admin only)."""
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "INSERT INTO portal_groups (name, description, permissions) "
                    "VALUES (%s, %s, %s) RETURNING id, name, description, permissions",
                    (req.name, req.description, json.dumps(req.permissions)),
                )
                group = cur.fetchone()
        conn.close()
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(409, "Group name already exists")
    except Exception as e:
        logger.error("admin_create_group error: %s", e)
        raise HTTPException(500, "Database error")

    return {"ok": True, "group": group}


@router.put("/portal/admin/groups/{group_id}")
async def admin_update_group(
    group_id: int,
    req: UpdateGroupRequest,
    _admin: dict = Depends(admin_required),
):
    """Update group name, description, or permissions (admin only)."""
    updates = []
    params = []
    if req.name is not None:
        updates.append("name = %s")
        params.append(req.name)
    if req.description is not None:
        updates.append("description = %s")
        params.append(req.description)
    if req.permissions is not None:
        updates.append("permissions = %s")
        params.append(json.dumps(req.permissions))

    if not updates:
        raise HTTPException(400, "No fields to update")

    params.append(group_id)
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"UPDATE portal_groups SET {', '.join(updates)} "
                    f"WHERE id = %s RETURNING id, name, description, permissions",
                    params,
                )
                group = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("admin_update_group error: %s", e)
        raise HTTPException(500, "Database error")

    if not group:
        raise HTTPException(404, "Group not found")
    return {"ok": True, "group": group}


@router.post("/portal/admin/groups/{group_id}/members")
async def admin_add_member(
    group_id: int,
    req: AddMemberRequest,
    _admin: dict = Depends(admin_required),
):
    """Add a user to a group (admin only)."""
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO portal_user_groups (user_id, group_id) "
                    "VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (req.user_id, group_id),
                )
        conn.close()
    except Exception as e:
        logger.error("admin_add_member error: %s", e)
        raise HTTPException(500, "Database error")

    return {"ok": True, "group_id": group_id, "user_id": req.user_id}


@router.delete("/portal/admin/groups/{group_id}/members/{user_id}")
async def admin_remove_member(
    group_id: int,
    user_id: int,
    _admin: dict = Depends(admin_required),
):
    """Remove a user from a group (admin only)."""
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM portal_user_groups "
                    "WHERE user_id = %s AND group_id = %s",
                    (user_id, group_id),
                )
                deleted = cur.rowcount
        conn.close()
    except Exception as e:
        logger.error("admin_remove_member error: %s", e)
        raise HTTPException(500, "Database error")

    if deleted == 0:
        raise HTTPException(404, "Membership not found")
    return {"ok": True, "group_id": group_id, "user_id": user_id}


# ── Community — Boards ───────────────────────────────────────────────────────

# Role level hierarchy for permission checks
ROLE_LEVEL_ORDER = {"general": 0, "demo": 1, "ycdc": 2, "admin": 3}


def _can_access_board(board_role: str, user_role_level: str) -> bool:
    """Check if user's role_level meets the board's required role."""
    if user_role_level == "admin":
        return True
    return ROLE_LEVEL_ORDER.get(user_role_level, 0) >= ROLE_LEVEL_ORDER.get(board_role, 0)


@router.get("/portal/boards")
async def list_boards(user: Optional[dict] = Depends(get_optional_user)):
    """List all boards filtered by read permission."""
    role_level = _get_user_role_level(user["user_id"]) if user else "general"
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, slug, name, description, board_type, theme, "
                "allow_upload, write_role, read_role, sort_order "
                "FROM portal_boards ORDER BY sort_order, id"
            )
            boards = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error("list_boards error: %s", e)
        raise HTTPException(500, "Database error")

    # Filter by read permission
    visible = [
        b for b in boards
        if _can_access_board(b.get("read_role", "general"), role_level)
    ]
    return {"boards": visible}


@router.get("/portal/boards/{slug}")
async def get_board(slug: str, user: Optional[dict] = Depends(get_optional_user)):
    """Get board detail + recent posts."""
    role_level = _get_user_role_level(user["user_id"]) if user else "general"
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, slug, name, description, board_type, theme, "
                "allow_upload, write_role, read_role, sort_order "
                "FROM portal_boards WHERE slug = %s",
                (slug,),
            )
            board = cur.fetchone()
            if not board:
                raise HTTPException(404, f"Board not found: {slug}")

            if not _can_access_board(board.get("read_role", "general"), role_level):
                raise HTTPException(403, "No read permission for this board")

            # Recent posts (latest 20)
            cur.execute(
                "SELECT p.id, p.title, p.pinned, p.view_count, "
                "p.created_at, p.updated_at, "
                "u.username AS author "
                "FROM portal_posts p "
                "JOIN portal_users u ON u.id = p.author_id "
                "WHERE p.board_id = %s "
                "ORDER BY p.pinned DESC, p.created_at DESC LIMIT 20",
                (board["id"],),
            )
            posts = cur.fetchall()
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_board error: %s", e)
        raise HTTPException(500, "Database error")

    for p in posts:
        for key in ("created_at", "updated_at"):
            if p.get(key):
                p[key] = str(p[key])

    return {"board": board, "posts": posts}


# ── Community — Posts ────────────────────────────────────────────────────────


@router.get("/portal/boards/{slug}/posts")
async def list_posts(
    slug: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: Optional[dict] = Depends(get_optional_user),
):
    """List posts in a board (paginated)."""
    role_level = _get_user_role_level(user["user_id"]) if user else "general"
    offset = (page - 1) * limit
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get board
            cur.execute(
                "SELECT id, read_role, write_role FROM portal_boards WHERE slug = %s",
                (slug,),
            )
            board = cur.fetchone()
            if not board:
                raise HTTPException(404, f"Board not found: {slug}")
            if not _can_access_board(board.get("read_role", "general"), role_level):
                raise HTTPException(403, "No read permission for this board")

            # Total count
            cur.execute(
                "SELECT COUNT(*) FROM portal_posts WHERE board_id = %s",
                (board["id"],),
            )
            total = cur.fetchone()["count"]

            # Posts
            cur.execute(
                "SELECT p.id, p.title, p.pinned, p.view_count, "
                "p.created_at, p.updated_at, "
                "u.username AS author "
                "FROM portal_posts p "
                "JOIN portal_users u ON u.id = p.author_id "
                "WHERE p.board_id = %s "
                "ORDER BY p.pinned DESC, p.created_at DESC "
                "LIMIT %s OFFSET %s",
                (board["id"], limit, offset),
            )
            posts = cur.fetchall()
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_posts error: %s", e)
        raise HTTPException(500, "Database error")

    for p in posts:
        for key in ("created_at", "updated_at"):
            if p.get(key):
                p[key] = str(p[key])

    return {
        "posts": posts,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 1,
    }


@router.post("/portal/boards/{slug}/posts")
async def create_post(
    slug: str,
    req: CreatePostRequest,
    user: dict = Depends(get_current_user),
):
    """Create a new post in a board."""
    role_level = _get_user_role_level(user["user_id"])
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, write_role FROM portal_boards WHERE slug = %s",
                    (slug,),
                )
                board = cur.fetchone()
                if not board:
                    raise HTTPException(404, f"Board not found: {slug}")
                if not _can_access_board(board.get("write_role", "general"), role_level):
                    raise HTTPException(403, "No write permission for this board")

                cur.execute(
                    "INSERT INTO portal_posts (board_id, author_id, title, content, pinned) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id, created_at",
                    (board["id"], user["user_id"], req.title, req.content, req.pinned),
                )
                row = cur.fetchone()
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_post error: %s", e)
        raise HTTPException(500, "Database error")

    return {
        "ok": True,
        "post_id": row["id"],
        "created_at": str(row["created_at"]),
    }


@router.get("/portal/posts/{post_id}")
async def get_post(post_id: int, user: Optional[dict] = Depends(get_optional_user)):
    """Get post detail + comments + files."""
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get post with author info
                cur.execute(
                    "SELECT p.id, p.board_id, p.title, p.content, p.pinned, "
                    "p.view_count, p.created_at, p.updated_at, "
                    "p.author_id, u.username AS author "
                    "FROM portal_posts p "
                    "JOIN portal_users u ON u.id = p.author_id "
                    "WHERE p.id = %s",
                    (post_id,),
                )
                post = cur.fetchone()
                if not post:
                    raise HTTPException(404, "Post not found")

                # Increment view count
                cur.execute(
                    "UPDATE portal_posts SET view_count = view_count + 1 WHERE id = %s",
                    (post_id,),
                )

                # Get comments
                cur.execute(
                    "SELECT c.id, c.content, c.created_at, "
                    "c.author_id, u.username AS author "
                    "FROM portal_comments c "
                    "JOIN portal_users u ON u.id = c.author_id "
                    "WHERE c.post_id = %s ORDER BY c.created_at",
                    (post_id,),
                )
                comments = cur.fetchall()

                # Get files
                cur.execute(
                    "SELECT id, filename, filesize, mimetype, uploaded_at "
                    "FROM portal_files WHERE post_id = %s ORDER BY uploaded_at",
                    (post_id,),
                )
                files = cur.fetchall()
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_post error: %s", e)
        raise HTTPException(500, "Database error")

    # Serialize datetimes
    for key in ("created_at", "updated_at"):
        if post.get(key):
            post[key] = str(post[key])
    for c in comments:
        if c.get("created_at"):
            c["created_at"] = str(c["created_at"])
    for f in files:
        if f.get("uploaded_at"):
            f["uploaded_at"] = str(f["uploaded_at"])

    return {"post": post, "comments": comments, "files": files}


@router.put("/portal/posts/{post_id}")
async def update_post(
    post_id: int,
    req: UpdatePostRequest,
    user: dict = Depends(get_current_user),
):
    """Edit a post (author or admin only)."""
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT author_id FROM portal_posts WHERE id = %s",
                    (post_id,),
                )
                post = cur.fetchone()
                if not post:
                    raise HTTPException(404, "Post not found")

                role_level = _get_user_role_level(user["user_id"])
                if post["author_id"] != user["user_id"] and role_level != "admin":
                    raise HTTPException(403, "Only the author or admin can edit")

                updates = []
                params = []
                if req.title is not None:
                    updates.append("title = %s")
                    params.append(req.title)
                if req.content is not None:
                    updates.append("content = %s")
                    params.append(req.content)
                if req.pinned is not None:
                    updates.append("pinned = %s")
                    params.append(req.pinned)

                if not updates:
                    raise HTTPException(400, "No fields to update")

                updates.append("updated_at = now()")
                params.append(post_id)
                cur.execute(
                    f"UPDATE portal_posts SET {', '.join(updates)} "
                    f"WHERE id = %s RETURNING id, updated_at",
                    params,
                )
                row = cur.fetchone()
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_post error: %s", e)
        raise HTTPException(500, "Database error")

    return {"ok": True, "post_id": row["id"], "updated_at": str(row["updated_at"])}


@router.delete("/portal/posts/{post_id}")
async def delete_post(post_id: int, user: dict = Depends(get_current_user)):
    """Delete a post (author or admin only)."""
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT author_id FROM portal_posts WHERE id = %s",
                    (post_id,),
                )
                post = cur.fetchone()
                if not post:
                    raise HTTPException(404, "Post not found")

                role_level = _get_user_role_level(user["user_id"])
                if post["author_id"] != user["user_id"] and role_level != "admin":
                    raise HTTPException(403, "Only the author or admin can delete")

                # Delete associated comments and files first
                cur.execute("DELETE FROM portal_comments WHERE post_id = %s", (post_id,))
                cur.execute(
                    "SELECT filepath FROM portal_files WHERE post_id = %s",
                    (post_id,),
                )
                file_rows = cur.fetchall()
                cur.execute("DELETE FROM portal_files WHERE post_id = %s", (post_id,))
                cur.execute("DELETE FROM portal_posts WHERE id = %s", (post_id,))
        conn.close()

        # Remove physical files
        for fr in file_rows:
            fpath = Path(fr["filepath"])
            if fpath.is_file():
                fpath.unlink(missing_ok=True)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_post error: %s", e)
        raise HTTPException(500, "Database error")

    return {"ok": True, "post_id": post_id}


# ── Community — Comments ─────────────────────────────────────────────────────


@router.post("/portal/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    req: CreateCommentRequest,
    user: dict = Depends(get_current_user),
):
    """Add a comment to a post."""
    if not req.content.strip():
        raise HTTPException(400, "Comment content cannot be empty")

    try:
        conn = _get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Verify post exists
                cur.execute("SELECT id FROM portal_posts WHERE id = %s", (post_id,))
                if not cur.fetchone():
                    raise HTTPException(404, "Post not found")

                cur.execute(
                    "INSERT INTO portal_comments (post_id, author_id, content) "
                    "VALUES (%s, %s, %s) RETURNING id, created_at",
                    (post_id, user["user_id"], req.content),
                )
                row = cur.fetchone()
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_comment error: %s", e)
        raise HTTPException(500, "Database error")

    return {
        "ok": True,
        "comment_id": row["id"],
        "created_at": str(row["created_at"]),
    }


@router.delete("/portal/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    user: dict = Depends(get_current_user),
):
    """Delete a comment (author or admin only)."""
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT author_id FROM portal_comments WHERE id = %s",
                    (comment_id,),
                )
                comment = cur.fetchone()
                if not comment:
                    raise HTTPException(404, "Comment not found")

                role_level = _get_user_role_level(user["user_id"])
                if comment["author_id"] != user["user_id"] and role_level != "admin":
                    raise HTTPException(403, "Only the author or admin can delete")

                cur.execute("DELETE FROM portal_comments WHERE id = %s", (comment_id,))
        conn.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_comment error: %s", e)
        raise HTTPException(500, "Database error")

    return {"ok": True, "comment_id": comment_id}


# ── Community — File upload / download ───────────────────────────────────────


@router.post("/portal/posts/{post_id}/files")
async def upload_post_file(
    post_id: int,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a file attachment to a post."""
    # Verify post exists
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT p.id, p.board_id, b.allow_upload "
                "FROM portal_posts p "
                "JOIN portal_boards b ON b.id = p.board_id "
                "WHERE p.id = %s",
                (post_id,),
            )
            post = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("upload_post_file check error: %s", e)
        raise HTTPException(500, "Database error")

    if not post:
        raise HTTPException(404, "Post not found")
    if not post.get("allow_upload", True):
        raise HTTPException(403, "File upload not allowed on this board")

    # Max file size: 50MB
    max_size = 50 * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(413, "File too large (max 50MB)")

    # Save file
    file_uuid = str(uuid.uuid4())
    ext = Path(file.filename).suffix if file.filename else ""
    stored_name = f"{file_uuid}{ext}"
    post_dir = UPLOAD_POSTS_DIR / str(post_id)
    post_dir.mkdir(parents=True, exist_ok=True)
    dest = post_dir / stored_name
    dest.write_bytes(content)

    # Record in DB
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "INSERT INTO portal_files (post_id, filename, filepath, filesize, mimetype) "
                    "VALUES (%s, %s, %s, %s, %s) RETURNING id, uploaded_at",
                    (post_id, file.filename, str(dest), len(content), file.content_type),
                )
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("upload_post_file db error: %s", e)
        dest.unlink(missing_ok=True)
        raise HTTPException(500, "Database error")

    return {
        "ok": True,
        "file_id": row["id"],
        "filename": file.filename,
        "filesize": len(content),
        "uploaded_at": str(row["uploaded_at"]),
    }


@router.get("/portal/files/{file_id}/download")
async def download_file(file_id: int):
    """Download a file attachment."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT filename, filepath, mimetype FROM portal_files WHERE id = %s",
                (file_id,),
            )
            row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("download_file error: %s", e)
        raise HTTPException(500, "Database error")

    if not row:
        raise HTTPException(404, "File not found")

    fpath = Path(row["filepath"])
    if not fpath.is_file():
        raise HTTPException(404, "File missing from disk")

    return FileResponse(
        path=str(fpath),
        filename=row["filename"],
        media_type=row.get("mimetype", "application/octet-stream"),
    )


# ── Community — User Profile ────────────────────────────────────────────────


@router.get("/portal/profile/{username}")
async def get_profile(username: str):
    """Get a user's public profile."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT u.id, u.username, u.created_at, "
                "p.bio_md, p.photo_url, p.updated_at AS profile_updated_at "
                "FROM portal_users u "
                "LEFT JOIN portal_profiles p ON p.user_id = u.id "
                "WHERE u.username = %s",
                (username,),
            )
            row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("get_profile error: %s", e)
        raise HTTPException(500, "Database error")

    if not row:
        raise HTTPException(404, "User not found")

    for key in ("created_at", "profile_updated_at"):
        if row.get(key):
            row[key] = str(row[key])

    # Photo history (최근 10장)
    photos = []
    try:
        conn2 = _get_conn()
        with conn2.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur2:
            cur2.execute(
                "SELECT id, photo_url, uploaded_at FROM portal_profile_photos "
                "WHERE user_id = %s ORDER BY uploaded_at DESC LIMIT 10",
                (row["id"],),
            )
            photos = [dict(p) for p in cur2.fetchall()]
            for p in photos:
                if p.get("uploaded_at"):
                    p["uploaded_at"] = str(p["uploaded_at"])
        conn2.close()
    except Exception:
        pass

    # 프론트 호환 플랫 응답
    return {
        "username": row["username"],
        "email": row.get("email"),
        "bio": row.get("bio_md", ""),
        "photo_url": row.get("photo_url", ""),
        "role_level": row.get("role_level", "general"),
        "created_at": row.get("created_at", ""),
        "photos": photos,
    }


@router.put("/portal/profile")
async def update_profile(
    req: UpdateProfileRequest,
    user: dict = Depends(get_current_user),
):
    """Update own profile (bio_md)."""
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "INSERT INTO portal_profiles (user_id, bio_md, updated_at) "
                    "VALUES (%s, %s, now()) "
                    "ON CONFLICT (user_id) DO UPDATE SET bio_md = %s, updated_at = now() "
                    "RETURNING user_id, bio_md, updated_at",
                    (user["user_id"], req.bio_md, req.bio_md),
                )
                row = cur.fetchone()
        conn.close()
    except Exception as e:
        logger.error("update_profile error: %s", e)
        raise HTTPException(500, "Database error")

    if row.get("updated_at"):
        row["updated_at"] = str(row["updated_at"])
    return {"ok": True, "profile": row}


@router.post("/portal/profile/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload profile photo."""
    # Validate image type
    allowed_types = ("image/jpeg", "image/png", "image/gif", "image/webp")
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Invalid file type. Allowed: {allowed_types}")

    content = await file.read()
    max_size = 5 * 1024 * 1024  # 5MB
    if len(content) > max_size:
        raise HTTPException(413, "Photo too large (max 5MB)")

    # Save file with unique name
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    unique_name = f"user_{user['user_id']}_{uuid.uuid4().hex[:8]}{ext}"
    dest = UPLOAD_PROFILES_DIR / unique_name
    dest.write_bytes(content)

    # URL for serving (relative)
    photo_url = f"/portal/uploads/profiles/{unique_name}"

    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                # 프로필 테이블 업데이트 (현재 사진)
                cur.execute(
                    "INSERT INTO portal_profiles (user_id, photo_url, updated_at) "
                    "VALUES (%s, %s, now()) "
                    "ON CONFLICT (user_id) DO UPDATE SET photo_url = %s, updated_at = now()",
                    (user["user_id"], photo_url, photo_url),
                )
                # 사진 히스토리 추가
                cur.execute(
                    "INSERT INTO portal_profile_photos (user_id, photo_url) VALUES (%s, %s)",
                    (user["user_id"], photo_url),
                )
                # 10장 초과 시 오래된 것 삭제
                cur.execute(
                    "DELETE FROM portal_profile_photos WHERE id IN ("
                    "  SELECT id FROM portal_profile_photos WHERE user_id = %s "
                    "  ORDER BY uploaded_at DESC OFFSET 10"
                    ")",
                    (user["user_id"],),
                )
        conn.close()
    except Exception as e:
        logger.error("upload_profile_photo error: %s", e)
        raise HTTPException(500, "Database error")

    return {"ok": True, "photo_url": photo_url}


# ── Members list ─────────────────────────────────────────────────────────────

@router.get("/portal/members")
async def list_members():
    """모든 회원의 프로필 카드 목록 (카카오톡 스타일)."""
    try:
        conn = _get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT u.id, u.username, u.role_level, u.created_at, "
                "p.photo_url, p.bio_md "
                "FROM portal_users u "
                "LEFT JOIN portal_profiles p ON p.user_id = u.id "
                "ORDER BY u.created_at"
            )
            members = [dict(r) for r in cur.fetchall()]
        conn.close()
    except Exception as e:
        logger.error("list_members error: %s", e)
        raise HTTPException(500, "Database error")

    for m in members:
        if m.get("created_at"):
            m["created_at"] = str(m["created_at"])
        m["bio_short"] = (m.get("bio_md") or "")[:100]

    return {"members": members}


# ── Static file serving for uploads ──────────────────────────────────────────

UPLOAD_BASE = Path("/home/opsclaw/opsclaw/data/uploads")

@router.get("/portal/uploads/{path:path}")
async def serve_upload(path: str):
    """Serve uploaded files (profile photos, post attachments)."""
    file_path = (UPLOAD_BASE / path).resolve()
    if not str(file_path).startswith(str(UPLOAD_BASE.resolve())):
        raise HTTPException(403, "Access denied")
    if not file_path.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(str(file_path))
