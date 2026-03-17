"""OpsClaw History Service — raw history ingestion and retrieval."""
from __future__ import annotations
import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor

DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")

def _conn(database_url=None):
    return psycopg2.connect(database_url or DB_URL)

def ingest_event(project_id, event, context=None, job_run_id=None, database_url=None):
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO histories (project_id, job_run_id, event, context) VALUES (%s, %s, %s, %s) RETURNING *",
                (project_id, job_run_id, event, Json(context or {})),
            )
            return dict(cur.fetchone())

def ingest_stage_event(project_id, stage, status="ok", context=None, job_run_id=None, database_url=None):
    ctx = {"stage": stage, "status": status}
    if context:
        ctx.update(context)
    return ingest_event(project_id=project_id, event=f"stage:{stage}", context=ctx, job_run_id=job_run_id, database_url=database_url)

def get_project_history(project_id, limit=50, database_url=None):
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM histories WHERE project_id = %s ORDER BY created_at DESC LIMIT %s", (project_id, limit))
            return [dict(r) for r in cur.fetchall()]

def get_asset_history(asset_id, limit=50, database_url=None):
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM histories WHERE context->>'asset_id' = %s ORDER BY created_at DESC LIMIT %s", (asset_id, limit))
            return [dict(r) for r in cur.fetchall()]

def list_histories(limit=100, database_url=None):
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM histories ORDER BY created_at DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]

def get_history_event(history_id, database_url=None):
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM histories WHERE id = %s", (history_id,))
            row = cur.fetchone()
            return dict(row) if row else None
