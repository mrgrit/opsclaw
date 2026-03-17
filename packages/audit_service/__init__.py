"""OpsClaw Audit Service — structured audit trail via audit_logs table.

Covers: log_audit_event, query_audit_logs, export_audit_json, export_audit_csv.
The audit_logs table uses TEXT id (not UUID), so we generate our own.
"""
from __future__ import annotations

import csv
import io
import json
import os
import uuid

import psycopg2
from psycopg2.extras import Json, RealDictCursor

DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


def _conn(database_url=None):
    return psycopg2.connect(database_url or DB_URL)


# ── Write ─────────────────────────────────────────────────────────────────────

def log_audit_event(
    event_type: str,
    actor_type: str,
    actor_id: str,
    project_id: str | None = None,
    asset_id: str | None = None,
    ref_id: str | None = None,
    payload: dict | None = None,
    database_url: str | None = None,
) -> dict:
    """Insert a structured audit event into audit_logs."""
    log_id = f"aud_{uuid.uuid4().hex[:16]}"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO audit_logs (id, event_type, actor_type, actor_id,
                                        project_id, asset_id, ref_id, payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (log_id, event_type, actor_type, actor_id,
                 project_id, asset_id, ref_id, Json(payload or {})),
            )
            return dict(cur.fetchone())


# ── Read ──────────────────────────────────────────────────────────────────────

def query_audit_logs(
    event_type: str | None = None,
    actor_id: str | None = None,
    project_id: str | None = None,
    asset_id: str | None = None,
    limit: int = 100,
    database_url: str | None = None,
) -> list[dict]:
    """Query audit_logs with optional filters."""
    conditions = []
    params: list = []
    if event_type:
        conditions.append("event_type = %s")
        params.append(event_type)
    if actor_id:
        conditions.append("actor_id = %s")
        params.append(actor_id)
    if project_id:
        conditions.append("project_id = %s")
        params.append(project_id)
    if asset_id:
        conditions.append("asset_id = %s")
        params.append(asset_id)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT * FROM audit_logs {where} ORDER BY created_at DESC LIMIT %s",
                params,
            )
            return [dict(r) for r in cur.fetchall()]


def get_audit_event(log_id: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM audit_logs WHERE id = %s", (log_id,))
            row = cur.fetchone()
            return dict(row) if row else None


# ── Export ────────────────────────────────────────────────────────────────────

def export_audit_json(
    event_type: str | None = None,
    project_id: str | None = None,
    limit: int = 1000,
    database_url: str | None = None,
) -> str:
    """Export audit_logs as a JSON string."""
    rows = query_audit_logs(
        event_type=event_type,
        project_id=project_id,
        limit=limit,
        database_url=database_url,
    )
    # Convert non-serialisable types (datetime, UUID)
    def _default(obj):
        return str(obj)
    return json.dumps(rows, default=_default, ensure_ascii=False, indent=2)


def export_audit_csv(
    event_type: str | None = None,
    project_id: str | None = None,
    limit: int = 1000,
    database_url: str | None = None,
) -> str:
    """Export audit_logs as a CSV string."""
    rows = query_audit_logs(
        event_type=event_type,
        project_id=project_id,
        limit=limit,
        database_url=database_url,
    )
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow({k: str(v) if v is not None else "" for k, v in row.items()})
    return output.getvalue()
