"""central-server — OpsClaw 중앙 관리 서버 (:7000)

모든 opsclaw/bastion/CCC 인스턴스를 통합 관리한다.
- 인스턴스 등록/하트비트/상태
- 통합 블록체인 (블록 수신/검증/리더보드)
- CTF 서버 (문제 관리/채점/스코어보드)
- 배포 패키지 관리
"""
from __future__ import annotations
import os
import uuid
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Config ─────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")
API_KEY = os.getenv("CENTRAL_API_KEY", "central-api-key-2026")

# ── Models ─────────────────────────────────────────
class InstanceRegister(BaseModel):
    instance_id: str
    instance_type: str  # opsclaw | bastion | ccc
    name: str
    api_url: str
    version: str = "1.0.0"
    metadata: dict[str, Any] = {}

class HeartbeatPayload(BaseModel):
    instance_id: str
    status: str = "healthy"
    metrics: dict[str, Any] = {}

class BlockSync(BaseModel):
    instance_id: str
    agent_id: str
    block_index: int
    block_hash: str
    prev_hash: str
    nonce: int = 0
    difficulty: int = 4
    task_id: str | None = None
    project_id: str | None = None
    reward_amount: float = 0.0
    timestamp: str = ""
    metadata: dict[str, Any] = {}

class CTFChallengeCreate(BaseModel):
    title: str
    category: str  # attack | defense | infra | ai
    description: str = ""
    flag: str
    points: int = 100
    difficulty: str = "medium"

class CTFFlagSubmit(BaseModel):
    instance_id: str
    student_id: str
    challenge_id: str
    flag: str

# ── Auth ───────────────────────────────────────────
def verify_key(request: Request):
    key = request.headers.get("X-API-Key", "")
    if key != API_KEY:
        raise HTTPException(401, "Invalid API key")

# ── DB ─────────────────────────────────────────────
import psycopg2
from psycopg2.extras import RealDictCursor, Json

def _conn():
    return psycopg2.connect(DATABASE_URL)

def _init_db():
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                -- 인스턴스
                CREATE TABLE IF NOT EXISTS central_instances (
                    instance_id TEXT PRIMARY KEY,
                    instance_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    api_url TEXT NOT NULL,
                    version TEXT DEFAULT '1.0.0',
                    status TEXT DEFAULT 'registered',
                    metadata JSONB DEFAULT '{}',
                    last_heartbeat TIMESTAMPTZ,
                    registered_at TIMESTAMPTZ DEFAULT now()
                );
                -- 통합 블록체인
                CREATE TABLE IF NOT EXISTS unified_blocks (
                    id SERIAL PRIMARY KEY,
                    instance_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    block_index INT NOT NULL,
                    block_hash TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    nonce INT DEFAULT 0,
                    difficulty INT DEFAULT 4,
                    task_id TEXT,
                    project_id TEXT,
                    reward_amount REAL DEFAULT 0,
                    original_ts TEXT,
                    metadata JSONB DEFAULT '{}',
                    synced_at TIMESTAMPTZ DEFAULT now()
                );
                -- CTF 문제
                CREATE TABLE IF NOT EXISTS ctf_challenges (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    flag TEXT NOT NULL,
                    points INT DEFAULT 100,
                    difficulty TEXT DEFAULT 'medium',
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                -- CTF 제출
                CREATE TABLE IF NOT EXISTS ctf_submissions (
                    id TEXT PRIMARY KEY,
                    instance_id TEXT,
                    student_id TEXT NOT NULL,
                    challenge_id TEXT REFERENCES ctf_challenges(id),
                    flag TEXT NOT NULL,
                    correct BOOLEAN DEFAULT false,
                    points INT DEFAULT 0,
                    submitted_at TIMESTAMPTZ DEFAULT now()
                );
                -- 중앙 설정 (Config)
                CREATE TABLE IF NOT EXISTS central_config (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    description TEXT DEFAULT '',
                    updated_at TIMESTAMPTZ DEFAULT now()
                );
                -- 배포 패키지
                CREATE TABLE IF NOT EXISTS deploy_packages (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    pkg_type TEXT NOT NULL,
                    version TEXT NOT NULL,
                    file_path TEXT,
                    checksum TEXT,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT now(),
                    UNIQUE(name, version)
                );
            """)
            conn.commit()

# ── Config Defaults (기본값 시딩) ──────────────────
DEFAULT_CONFIG = {
    # 인프라 서버
    "infra.opsclaw.ip": {"value": "10.20.30.201", "description": "OpsClaw control plane IP"},
    "infra.opsclaw.external_ip": {"value": "192.168.0.107", "description": "OpsClaw 외부 IP (WiFi)"},
    "infra.secu.ip": {"value": "10.20.30.1", "description": "secu 서버 IP (nftables+Suricata)"},
    "infra.secu.external_ip": {"value": "192.168.208.150", "description": "secu 외부 IP"},
    "infra.web.ip": {"value": "10.20.30.80", "description": "web 서버 IP (WAF+JuiceShop)"},
    "infra.web.external_ip": {"value": "192.168.208.151", "description": "web 외부 IP"},
    "infra.siem.ip": {"value": "10.20.30.100", "description": "siem 서버 IP (Wazuh)"},
    "infra.siem.external_ip": {"value": "192.168.208.152", "description": "siem 외부 IP"},
    "infra.dgx.ip": {"value": "192.168.0.105", "description": "DGX-Spark GPU 서버 IP"},
    "infra.network.cidr": {"value": "10.20.30.0/24", "description": "내부 네트워크 CIDR"},
    # 가상 서버
    "infra.v-secu.ip": {"value": "192.168.0.108", "description": "v-secu VM IP"},
    "infra.v-web.ip": {"value": "192.168.0.110", "description": "v-web VM IP"},
    "infra.v-siem.ip": {"value": "192.168.0.109", "description": "v-siem VM IP"},
    # 서비스 포트
    "service.manager.port": {"value": 8000, "description": "Manager API 포트"},
    "service.master.port": {"value": 8001, "description": "Master Service 포트"},
    "service.subagent.port": {"value": 8002, "description": "SubAgent 포트"},
    "service.central.port": {"value": 7000, "description": "Central Server 포트"},
    "service.bastion.port": {"value": 9000, "description": "Bastion API 포트"},
    "service.ccc.port": {"value": 9100, "description": "CCC API 포트"},
    "service.ctfd.port": {"value": 8080, "description": "CTFd 포트"},
    # SubAgent URL 매핑
    "subagent.local": {"value": "http://localhost:8002", "description": "로컬 SubAgent URL"},
    "subagent.secu": {"value": "http://10.20.30.1:8002", "description": "secu SubAgent URL"},
    "subagent.web": {"value": "http://10.20.30.80:8002", "description": "web SubAgent URL"},
    "subagent.siem": {"value": "http://10.20.30.100:8002", "description": "siem SubAgent URL"},
    "subagent.dgx": {"value": "http://192.168.0.105:8002", "description": "dgx-spark SubAgent URL"},
    # LLM
    "llm.ollama.url": {"value": "http://192.168.0.105:11434", "description": "Ollama LLM 서버 URL"},
    "llm.ollama.api_url": {"value": "http://192.168.0.105:11434/v1", "description": "Ollama OpenAI 호환 API URL"},
    "llm.default_model": {"value": "gpt-oss:120b", "description": "기본 LLM 모델"},
    # DB
    "db.opsclaw.url": {"value": "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw", "description": "OpsClaw DB 연결"},
    "db.bastion.url": {"value": "postgresql://opsclaw:opsclaw@127.0.0.1:5432/bastion", "description": "Bastion DB 연결"},
    "db.ccc.url": {"value": "postgresql://opsclaw:opsclaw@127.0.0.1:5432/ccc", "description": "CCC DB 연결"},
    # API 키
    "auth.opsclaw.api_key": {"value": "opsclaw-api-key-2026", "description": "OpsClaw API 키"},
    "auth.bastion.api_key": {"value": "bastion-api-key-2026", "description": "Bastion API 키"},
    "auth.ccc.api_key": {"value": "ccc-api-key-2026", "description": "CCC API 키"},
    "auth.central.api_key": {"value": "central-api-key-2026", "description": "Central API 키"},
    # SSH
    "ssh.default_user": {"value": "opsclaw", "description": "SSH 기본 사용자"},
    "ssh.default_port": {"value": 22, "description": "SSH 기본 포트"},
    # DB 자격증명
    "db.postgres.host": {"value": "127.0.0.1", "description": "PostgreSQL 호스트"},
    "db.postgres.port": {"value": 5432, "description": "PostgreSQL 포트"},
    "db.postgres.user": {"value": "opsclaw", "description": "PostgreSQL 사용자"},
    "db.postgres.password": {"value": "opsclaw", "description": "PostgreSQL 비밀번호"},
    # 서버별 SSH 자격증명
    "ssh.secu.user": {"value": "opsclaw", "description": "secu SSH 사용자"},
    "ssh.secu.password": {"value": "1", "description": "secu SSH/sudo 비밀번호"},
    "ssh.web.user": {"value": "opsclaw", "description": "web SSH 사용자"},
    "ssh.web.password": {"value": "1", "description": "web SSH/sudo 비밀번호"},
    "ssh.siem.user": {"value": "opsclaw", "description": "siem SSH 사용자"},
    "ssh.siem.password": {"value": "1", "description": "siem SSH/sudo 비밀번호"},
    # 포털 관리자
    "auth.portal.admin_user": {"value": "admin", "description": "포털 관리자 아이디"},
    "auth.portal.admin_password": {"value": "admin2026", "description": "포털 관리자 비밀번호"},
}

def _seed_config():
    """기본 설정값을 DB에 시딩 (이미 있으면 건너뜀)"""
    with _conn() as conn:
        with conn.cursor() as cur:
            for key, cfg in DEFAULT_CONFIG.items():
                cur.execute(
                    """INSERT INTO central_config (key, value, description)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (key) DO NOTHING""",
                    (key, Json(cfg["value"]), cfg["description"]),
                )
            conn.commit()

# ── Lifespan ───────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        _init_db()
        _seed_config()
    except Exception as e:
        print(f"[central] DB init warning: {e}")
    yield

# ── App ────────────────────────────────────────────
app = FastAPI(
    title="OpsClaw Central Server",
    description="통합 관리 서버 — 인스턴스/블록체인/CTF/배포",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/app/")

@app.get("/health")
def health():
    return {"status": "ok", "service": "central-server"}

# ══════════════════════════════════════════════════
#  Instances (인스턴스 관리)
# ══════════════════════════════════════════════════
@app.post("/instances/register", dependencies=[Depends(verify_key)])
def register_instance(body: InstanceRegister):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO central_instances (instance_id, instance_type, name, api_url, version, metadata, last_heartbeat)
                   VALUES (%s,%s,%s,%s,%s,%s,now())
                   ON CONFLICT (instance_id) DO UPDATE SET
                     api_url=EXCLUDED.api_url, version=EXCLUDED.version,
                     metadata=EXCLUDED.metadata, status='registered', last_heartbeat=now()
                   RETURNING *""",
                (body.instance_id, body.instance_type, body.name, body.api_url, body.version, Json(body.metadata)),
            )
            conn.commit()
            row = cur.fetchone()
    return {"instance": dict(row)}

@app.post("/instances/heartbeat", dependencies=[Depends(verify_key)])
def heartbeat(body: HeartbeatPayload):
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE central_instances SET status=%s, last_heartbeat=now(), metadata=metadata||%s WHERE instance_id=%s",
                (body.status, Json(body.metrics), body.instance_id),
            )
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(404, "Instance not registered")
    return {"status": "ok", "instance_id": body.instance_id}

@app.get("/instances", dependencies=[Depends(verify_key)])
def list_instances(instance_type: str | None = None):
    q = "SELECT * FROM central_instances"
    params: list = []
    if instance_type:
        q += " WHERE instance_type=%s"; params.append(instance_type)
    q += " ORDER BY registered_at DESC"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"instances": [dict(r) for r in rows]}

@app.get("/instances/{iid}", dependencies=[Depends(verify_key)])
def get_instance(iid: str):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM central_instances WHERE instance_id=%s", (iid,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Instance not found")
    return {"instance": dict(row)}

# ══════════════════════════════════════════════════
#  Blockchain (통합 블록체인)
# ══════════════════════════════════════════════════
@app.post("/blockchain/sync", dependencies=[Depends(verify_key)])
def sync_block(body: BlockSync):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO unified_blocks
                   (instance_id, agent_id, block_index, block_hash, prev_hash, nonce, difficulty,
                    task_id, project_id, reward_amount, original_ts, metadata)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (body.instance_id, body.agent_id, body.block_index, body.block_hash,
                 body.prev_hash, body.nonce, body.difficulty, body.task_id,
                 body.project_id, body.reward_amount, body.timestamp, Json(body.metadata)),
            )
            conn.commit()
            row = cur.fetchone()
    return {"synced": True, "unified_id": row["id"]}

@app.get("/blockchain/blocks", dependencies=[Depends(verify_key)])
def list_unified_blocks(instance_id: str | None = None, agent_id: str | None = None, limit: int = 100):
    q = "SELECT * FROM unified_blocks WHERE 1=1"
    params: list = []
    if instance_id:
        q += " AND instance_id=%s"; params.append(instance_id)
    if agent_id:
        q += " AND agent_id=%s"; params.append(agent_id)
    q += " ORDER BY synced_at DESC LIMIT %s"; params.append(limit)
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"blocks": [dict(r) for r in rows]}

@app.get("/blockchain/verify", dependencies=[Depends(verify_key)])
def verify_unified(instance_id: str | None = None):
    q = "SELECT * FROM unified_blocks"
    params: list = []
    if instance_id:
        q += " WHERE instance_id=%s"; params.append(instance_id)
    q += " ORDER BY instance_id, block_index ASC"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    # 인스턴스별 검증
    by_instance: dict[str, list] = {}
    for r in rows:
        by_instance.setdefault(r["instance_id"], []).append(r)
    results = {}
    for iid, blocks in by_instance.items():
        valid = True
        tampered = []
        for i in range(1, len(blocks)):
            if blocks[i]["prev_hash"] != blocks[i-1]["block_hash"]:
                valid = False
                tampered.append(blocks[i]["block_index"])
        results[iid] = {"valid": valid, "blocks": len(blocks), "tampered": tampered}
    return {"verification": results, "total_blocks": len(rows)}

@app.get("/blockchain/leaderboard", dependencies=[Depends(verify_key)])
def unified_leaderboard():
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT instance_id, agent_id, count(*) as blocks, sum(reward_amount) as total_reward
                FROM unified_blocks GROUP BY instance_id, agent_id
                ORDER BY total_reward DESC
            """)
            rows = cur.fetchall()
    return {"leaderboard": [dict(r) for r in rows]}

# ══════════════════════════════════════════════════
#  CTF Server
# ══════════════════════════════════════════════════
@app.post("/ctf/challenges", dependencies=[Depends(verify_key)])
def create_challenge(body: CTFChallengeCreate):
    cid = str(uuid.uuid4())[:8]
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO ctf_challenges (id, title, category, description, flag, points, difficulty)
                   VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                (cid, body.title, body.category, body.description, body.flag, body.points, body.difficulty),
            )
            conn.commit()
            row = cur.fetchone()
    # flag는 응답에서 제외
    d = dict(row)
    d.pop("flag", None)
    return {"challenge": d}

@app.get("/ctf/challenges", dependencies=[Depends(verify_key)])
def list_challenges(category: str | None = None):
    q = "SELECT id, title, category, description, points, difficulty, created_at FROM ctf_challenges"
    params: list = []
    if category:
        q += " WHERE category=%s"; params.append(category)
    q += " ORDER BY created_at DESC"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"challenges": [dict(r) for r in rows]}

@app.post("/ctf/submit", dependencies=[Depends(verify_key)])
def submit_flag(body: CTFFlagSubmit):
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM ctf_challenges WHERE id=%s", (body.challenge_id,))
            ch = cur.fetchone()
            if not ch:
                raise HTTPException(404, "Challenge not found")
            correct = (body.flag.strip() == ch["flag"].strip())
            points = ch["points"] if correct else 0
            sid = str(uuid.uuid4())[:8]
            cur.execute(
                """INSERT INTO ctf_submissions (id, instance_id, student_id, challenge_id, flag, correct, points)
                   VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                (sid, body.instance_id, body.student_id, body.challenge_id, body.flag, correct, points),
            )
            conn.commit()
            row = cur.fetchone()
    return {"submission": dict(row), "correct": correct, "points": points}

@app.get("/ctf/scoreboard", dependencies=[Depends(verify_key)])
def ctf_scoreboard():
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT student_id, instance_id, sum(points) as total_points,
                       count(*) FILTER (WHERE correct) as solved
                FROM ctf_submissions GROUP BY student_id, instance_id
                ORDER BY total_points DESC
            """)
            rows = cur.fetchall()
    return {"scoreboard": [dict(r) for r in rows]}

# ══════════════════════════════════════════════════
#  Packages (배포 패키지)
# ══════════════════════════════════════════════════
@app.get("/packages/", dependencies=[Depends(verify_key)])
def list_packages(pkg_type: str | None = None):
    q = "SELECT * FROM deploy_packages"
    params: list = []
    if pkg_type:
        q += " WHERE pkg_type=%s"; params.append(pkg_type)
    q += " ORDER BY created_at DESC"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return {"packages": [dict(r) for r in rows]}

# ══════════════════════════════════════════════════
#  Config (중앙 설정 관리)
# ══════════════════════════════════════════════════
class ConfigUpdate(BaseModel):
    value: Any
    description: str | None = None

@app.get("/config", dependencies=[Depends(verify_key)])
def list_config(prefix: str | None = None):
    """설정 목록 (prefix 필터 가능: infra, service, subagent, llm, db, auth, ssh)"""
    q = "SELECT key, value, description, updated_at FROM central_config"
    params: list = []
    if prefix:
        q += " WHERE key LIKE %s"; params.append(f"{prefix}%")
    q += " ORDER BY key"
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    config = {}
    for r in rows:
        config[r["key"]] = {"value": r["value"], "description": r["description"], "updated_at": str(r["updated_at"])}
    return {"config": config, "total": len(config)}

@app.get("/config/{key:path}", dependencies=[Depends(verify_key)])
def get_config(key: str):
    """단일 설정 조회"""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM central_config WHERE key=%s", (key,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, f"Config key '{key}' not found")
    return {"key": row["key"], "value": row["value"], "description": row["description"], "updated_at": str(row["updated_at"])}

@app.put("/config/{key:path}", dependencies=[Depends(verify_key)])
def update_config(key: str, body: ConfigUpdate):
    """설정 수정"""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            sets = ["value=%s", "updated_at=now()"]
            params: list = [Json(body.value)]
            if body.description is not None:
                sets.append("description=%s")
                params.append(body.description)
            params.append(key)
            cur.execute(f"UPDATE central_config SET {','.join(sets)} WHERE key=%s RETURNING *", params)
            row = cur.fetchone()
            if not row:
                # 없으면 새로 생성
                cur.execute(
                    "INSERT INTO central_config (key, value, description) VALUES (%s, %s, %s) RETURNING *",
                    (key, Json(body.value), body.description or ""),
                )
                row = cur.fetchone()
            conn.commit()
    return {"key": row["key"], "value": row["value"], "description": row["description"]}

@app.delete("/config/{key:path}", dependencies=[Depends(verify_key)])
def delete_config(key: str):
    """설정 삭제"""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM central_config WHERE key=%s", (key,))
            conn.commit()
            if cur.rowcount == 0:
                raise HTTPException(404, f"Config key '{key}' not found")
    return {"deleted": key}

@app.get("/config-bundle/{instance_type}", dependencies=[Depends(verify_key)])
def get_config_bundle(instance_type: str):
    """인스턴스 타입별 설정 번들 (시스템 기동 시 한 번에 가져감)
    instance_type: opsclaw | bastion | ccc | all
    """
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT key, value FROM central_config ORDER BY key")
            rows = cur.fetchall()
    all_config = {r["key"]: r["value"] for r in rows}

    # 공통 설정 (모든 시스템)
    bundle = {}
    for k, v in all_config.items():
        if k.startswith("infra.") or k.startswith("llm.") or k.startswith("ssh."):
            bundle[k] = v

    # 시스템별 추가
    if instance_type in ("opsclaw", "all"):
        bundle["db.url"] = all_config.get("db.opsclaw.url")
        bundle["api_key"] = all_config.get("auth.opsclaw.api_key")
        bundle["service.port"] = all_config.get("service.manager.port")
    elif instance_type == "bastion":
        bundle["db.url"] = all_config.get("db.bastion.url")
        bundle["api_key"] = all_config.get("auth.bastion.api_key")
        bundle["service.port"] = all_config.get("service.bastion.port")
    elif instance_type == "ccc":
        bundle["db.url"] = all_config.get("db.ccc.url")
        bundle["api_key"] = all_config.get("auth.ccc.api_key")
        bundle["service.port"] = all_config.get("service.ccc.port")

    # SubAgent URL들
    for k, v in all_config.items():
        if k.startswith("subagent."):
            bundle[k] = v
    # 서비스 포트들
    for k, v in all_config.items():
        if k.startswith("service."):
            bundle[k] = v

    return {"instance_type": instance_type, "config": bundle}

# ══════════════════════════════════════════════════
#  Dashboard
# ══════════════════════════════════════════════════
@app.get("/admin/dashboard", dependencies=[Depends(verify_key)])
def admin_dashboard():
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT count(*) as cnt FROM central_instances")
            instances = cur.fetchone()["cnt"]
            cur.execute("SELECT instance_type, count(*) as cnt FROM central_instances GROUP BY instance_type")
            by_type = {r["instance_type"]: r["cnt"] for r in cur.fetchall()}
            cur.execute("SELECT count(*) as cnt FROM unified_blocks")
            blocks = cur.fetchone()["cnt"]
            cur.execute("SELECT count(*) as cnt FROM ctf_challenges")
            challenges = cur.fetchone()["cnt"]
    return {
        "instances": {"total": instances, "by_type": by_type},
        "blockchain": {"total_blocks": blocks},
        "ctf": {"challenges": challenges},
    }

# ══════════════════════════════════════════════════
#  NMS (Network Management)
# ══════════════════════════════════════════════════
@app.get("/nms/status", dependencies=[Depends(verify_key)])
def nms_status():
    """모든 인스턴스 네트워크 상태"""
    import httpx as _httpx
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM central_instances ORDER BY registered_at")
            instances = cur.fetchall()
    results = []
    for inst in instances:
        entry = {"instance_id": inst["instance_id"], "name": inst["name"], "type": inst["instance_type"], "api_url": inst["api_url"], "registered_status": inst["status"]}
        try:
            r = _httpx.get(f"{inst['api_url']}/health", timeout=5.0)
            entry["reachable"] = r.status_code == 200
            entry["health"] = r.json() if r.status_code == 200 else None
            entry["latency_ms"] = round(r.elapsed.total_seconds() * 1000, 1)
        except Exception as e:
            entry["reachable"] = False
            entry["health"] = None
            entry["latency_ms"] = None
            entry["error"] = str(e)
        results.append(entry)
    return {"instances": results, "total": len(results), "reachable": sum(1 for r in results if r["reachable"])}

# ══════════════════════════════════════════════════
#  SMS (System Management)
# ══════════════════════════════════════════════════
@app.get("/sms/metrics", dependencies=[Depends(verify_key)])
def sms_metrics():
    """인스턴스별 시스템 메트릭 (하트비트 metadata에서 추출)"""
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT instance_id, name, instance_type, status, metadata, last_heartbeat FROM central_instances ORDER BY name")
            rows = cur.fetchall()
    metrics = []
    for r in rows:
        m = dict(r)
        meta = r.get("metadata", {}) or {}
        m["cpu"] = meta.get("cpu")
        m["mem"] = meta.get("mem")
        m["disk"] = meta.get("disk")
        m["agents"] = meta.get("agents")
        m["uptime"] = meta.get("uptime")
        metrics.append(m)
    return {"metrics": metrics}

@app.get("/sms/alerts", dependencies=[Depends(verify_key)])
def sms_alerts():
    """인스턴스 알림 (하트비트 timeout 등)"""
    import datetime
    threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)
    with _conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM central_instances WHERE last_heartbeat < %s OR status != 'healthy'", (threshold,))
            rows = cur.fetchall()
    alerts = []
    for r in rows:
        alerts.append({
            "instance_id": r["instance_id"], "name": r["name"],
            "type": "heartbeat_timeout" if r["status"] == "healthy" else "unhealthy",
            "status": r["status"], "last_heartbeat": str(r["last_heartbeat"]),
        })
    return {"alerts": alerts, "total": len(alerts)}

# ── Static files (central-ui) ─────────────────────
import pathlib
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_ui_dist = pathlib.Path(__file__).parent.parent.parent / "central-ui" / "dist"
if _ui_dist.exists():
    @app.get("/app/{path:path}")
    def spa_fallback(path: str):
        fpath = _ui_dist / path
        if fpath.is_file():
            return FileResponse(str(fpath))
        return FileResponse(str(_ui_dist / "index.html"))
    app.mount("/app", StaticFiles(directory=str(_ui_dist), html=True), name="ui")
