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
import time
from pathlib import Path
from typing import Optional

import psycopg2
import psycopg2.extras
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

logger = logging.getLogger("portal")

# ── Config ────────────────────────────────────────────────────────────────────

JWT_SECRET = os.getenv("PORTAL_JWT_SECRET", "opsclaw-portal-secret-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = 60 * 60 * 24  # 24 hours

CONTENTS_BASE = Path("/home/opsclaw/opsclaw/contents")

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


_ensure_portal_tables()

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
    return {
        "user_id": payload["sub"],
        "username": payload["username"],
        "role": payload.get("role", "student"),
    }


async def admin_required(user: dict = Depends(get_current_user)) -> dict:
    """Check that the authenticated user has admin role."""
    if user.get("role") != "admin":
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
                    "VALUES (%s, %s, %s) RETURNING id, role",
                    (req.username, req.email, password_hash),
                )
                row = cur.fetchone()
        conn.close()
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(409, "Username or email already exists")
    except Exception as e:
        logger.error("register error: %s", e)
        raise HTTPException(500, "Database error")

    user_id, role = row
    token = _jwt_encode({
        "sub": user_id,
        "username": req.username,
        "role": role,
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
                "SELECT id, username, role FROM portal_users "
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


@router.get("/portal/content/education")
async def list_courses():
    """List all courses under contents/education/."""
    edu_dir = CONTENTS_BASE / "education"
    if not edu_dir.is_dir():
        return {"courses": []}

    courses = []
    for d in sorted(edu_dir.iterdir()):
        if d.is_dir() and not d.name.startswith((".", "00")):
            weeks = sorted(
                w.name for w in d.iterdir() if w.is_dir() and w.name.startswith("week")
            )
            courses.append({
                "name": d.name,
                "weeks": weeks,
                "week_count": len(weeks),
            })
    return {"courses": courses}


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
