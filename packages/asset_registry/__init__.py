import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
import psycopg2
import psycopg2.errors
from psycopg2.extras import RealDictCursor

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)


class AssetRegistryError(Exception):
    pass


class AssetNotFoundError(AssetRegistryError):
    pass


class AssetConflictError(AssetRegistryError):
    pass


def _conn(database_url: str | None = None):
    return psycopg2.connect(database_url or DEFAULT_DATABASE_URL)


# ── CRUD ──────────────────────────────────────────────────────────────────────

def create_asset(
    name: str,
    type: str,
    platform: str,
    env: str,
    mgmt_ip: str,
    roles: list | None = None,
    expected_subagent_port: int = 8002,
    auth_ref: str | None = None,
    metadata: dict | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    asset_id = f"asset_{uuid.uuid4().hex[:12]}"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO assets (
                        id, name, type, platform, env, mgmt_ip, roles,
                        expected_subagent_port, auth_ref, metadata
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING *
                    """,
                    (
                        asset_id, name, type, platform, env, mgmt_ip,
                        json.dumps(roles or []),
                        expected_subagent_port,
                        auth_ref,
                        json.dumps(metadata or {}),
                    ),
                )
                return dict(cur.fetchone())
            except psycopg2.errors.UniqueViolation as exc:
                raise AssetConflictError(f"Asset already exists: {name}") from exc


def get_asset(asset_id: str, database_url: str | None = None) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM assets WHERE id = %s", (asset_id,))
            row = cur.fetchone()
            if row is None:
                raise AssetNotFoundError(f"Asset not found: {asset_id}")
            return dict(row)


def get_asset_by_name(name: str, database_url: str | None = None) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM assets WHERE name = %s", (name,))
            row = cur.fetchone()
            if row is None:
                raise AssetNotFoundError(f"Asset not found by name: {name}")
            return dict(row)


def update_asset(
    asset_id: str,
    updates: dict[str, Any],
    database_url: str | None = None,
) -> dict[str, Any]:
    allowed = {
        "name", "type", "platform", "env", "mgmt_ip",
        "roles", "expected_subagent_port", "auth_ref",
        "metadata", "subagent_status",
    }
    fields = {k: v for k, v in updates.items() if k in allowed}
    if not fields:
        return get_asset(asset_id, database_url)

    # JSON-encode JSONB fields
    values: list[Any] = []
    set_parts: list[str] = []
    for k, v in fields.items():
        set_parts.append(f"{k} = %s")
        if k in ("roles", "metadata"):
            values.append(json.dumps(v))
        else:
            values.append(v)
    set_parts.append("updated_at = NOW()")
    values.append(asset_id)

    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"UPDATE assets SET {', '.join(set_parts)} WHERE id = %s RETURNING *",
                values,
            )
            row = cur.fetchone()
            if row is None:
                raise AssetNotFoundError(f"Asset not found: {asset_id}")
            return dict(row)


def delete_asset(asset_id: str, database_url: str | None = None) -> None:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM assets WHERE id = %s RETURNING id", (asset_id,))
            if cur.fetchone() is None:
                raise AssetNotFoundError(f"Asset not found: {asset_id}")


def list_assets(
    env: str | None = None,
    type: str | None = None,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM assets"
    params: list[Any] = []
    where: list[str] = []
    if env:
        where.append("env = %s")
        params.append(env)
    if type:
        where.append("type = %s")
        params.append(type)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at ASC"

    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]


# ── Target resolve ─────────────────────────────────────────────────────────────

def resolve_target_from_asset(
    asset_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Ping subagent endpoint, upsert target record, update asset status."""
    asset = get_asset(asset_id, database_url)
    port = asset.get("expected_subagent_port") or 8002
    mgmt_ip = str(asset["mgmt_ip"])
    base_url = f"http://{mgmt_ip}:{port}"

    health = "unknown"
    try:
        resp = httpx.get(f"{base_url}/health", timeout=5.0)
        health = "ok" if resp.status_code == 200 else "degraded"
    except Exception:
        health = "failed"

    now = datetime.now(timezone.utc)

    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id FROM targets WHERE asset_id = %s ORDER BY resolved_at DESC LIMIT 1",
                (asset_id,),
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    """
                    UPDATE targets
                    SET base_url = %s, health = %s, resolved_at = %s, resolver_version = 'm4'
                    WHERE id = %s
                    RETURNING *
                    """,
                    (base_url, health, now, existing["id"]),
                )
            else:
                target_id = f"tgt_{uuid.uuid4().hex[:12]}"
                cur.execute(
                    """
                    INSERT INTO targets (id, asset_id, base_url, resolved_at, health, resolver_version)
                    VALUES (%s, %s, %s, %s, %s, 'm4')
                    RETURNING *
                    """,
                    (target_id, asset_id, base_url, now, health),
                )
            target = dict(cur.fetchone())

    subagent_status = (
        "healthy" if health == "ok"
        else ("unhealthy" if health in ("degraded", "failed") else "unknown")
    )
    update_asset(asset_id, {"subagent_status": subagent_status}, database_url)

    return {
        "asset_id": asset_id,
        "target": target,
        "subagent_url": base_url,
        "subagent_status": subagent_status,
    }


def check_asset_health(
    asset_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Ping subagent /health, update asset status, return result."""
    asset = get_asset(asset_id, database_url)
    port = asset.get("expected_subagent_port") or 8002
    mgmt_ip = str(asset["mgmt_ip"])
    base_url = f"http://{mgmt_ip}:{port}"

    health_data: dict[str, Any] = {}
    try:
        resp = httpx.get(f"{base_url}/health", timeout=5.0)
        health_data = resp.json() if resp.status_code == 200 else {"status_code": resp.status_code}
        subagent_status = "healthy" if resp.status_code == 200 else "unhealthy"
    except Exception as exc:
        health_data = {"error": str(exc)}
        subagent_status = "unhealthy"

    update_asset(asset_id, {"subagent_status": subagent_status}, database_url)

    return {
        "asset_id": asset_id,
        "mgmt_ip": mgmt_ip,
        "subagent_port": port,
        "subagent_url": base_url,
        "subagent_status": subagent_status,
        "health_response": health_data,
    }


# ── Onboarding ─────────────────────────────────────────────────────────────────

def onboard_asset(
    name: str,
    type: str,
    platform: str,
    env: str,
    mgmt_ip: str,
    roles: list | None = None,
    expected_subagent_port: int = 8002,
    auth_ref: str | None = None,
    metadata: dict | None = None,
    bootstrap: bool = False,
    ssh_user: str = "root",
    ssh_port: int = 22,
    ssh_key_path: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    Full onboarding flow:
    1. Identity check by name → if exists, re-resolve and return
    2. Create asset record
    3. Optional bootstrap (SSH install)
    4. Resolve target (ping + upsert target record)
    5. Return asset + target + status
    """
    # 1. Identity check
    try:
        existing = get_asset_by_name(name, database_url)
        resolve_result = resolve_target_from_asset(existing["id"], database_url)
        return {
            "action": "existing",
            "asset": get_asset(existing["id"], database_url),
            **resolve_result,
        }
    except AssetNotFoundError:
        pass

    # 2. Create
    asset = create_asset(
        name=name, type=type, platform=platform, env=env,
        mgmt_ip=mgmt_ip, roles=roles,
        expected_subagent_port=expected_subagent_port,
        auth_ref=auth_ref, metadata=metadata,
        database_url=database_url,
    )

    # 3. Bootstrap
    bootstrap_result: dict[str, Any] | None = None
    if bootstrap:
        from packages.bootstrap_service import BootstrapConfig, bootstrap_asset as _bootstrap
        result = _bootstrap(
            mgmt_ip=mgmt_ip,
            config=BootstrapConfig(
                ssh_user=ssh_user,
                ssh_port=ssh_port,
                ssh_key_path=ssh_key_path,
                subagent_port=expected_subagent_port,
            ),
        )
        bootstrap_result = result

    # 4. Resolve target
    resolve_result = resolve_target_from_asset(asset["id"], database_url)

    return {
        "action": "created",
        "asset": get_asset(asset["id"], database_url),
        "bootstrap": bootstrap_result,
        **resolve_result,
    }
