"""OpsClaw Watch Service — watch_job / watch_event / incident CRUD + monitoring execution."""

from __future__ import annotations

import os
import subprocess
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)


def _conn(database_url: str | None = None):
    return psycopg2.connect(database_url or DB_URL)


# ── Watch Job CRUD ─────────────────────────────────────────────────────────────

def create_watch_job(
    project_id: str,
    watch_type: str,
    metadata: dict | None = None,
    database_url: str | None = None,
) -> dict:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO watch_jobs (project_id, watch_type, status, metadata)
                VALUES (%s, %s, 'running', %s)
                RETURNING *
                """,
                (project_id, watch_type, Json(metadata or {})),
            )
            return dict(cur.fetchone())


def get_watch_job(watch_job_id: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM watch_jobs WHERE id = %s", (watch_job_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def list_watch_jobs(status: str | None = None, database_url: str | None = None) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if status is not None:
                cur.execute(
                    "SELECT * FROM watch_jobs WHERE status = %s ORDER BY created_at",
                    (status,),
                )
            else:
                cur.execute("SELECT * FROM watch_jobs ORDER BY created_at")
            return [dict(r) for r in cur.fetchall()]


def update_watch_job_status(
    watch_job_id: str,
    status: str,
    database_url: str | None = None,
) -> dict:
    """Update status: running / paused / stopped."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE watch_jobs SET status = %s WHERE id = %s RETURNING *",
                (status, watch_job_id),
            )
            return dict(cur.fetchone())


def delete_watch_job(watch_job_id: str, database_url: str | None = None) -> bool:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM watch_jobs WHERE id = %s", (watch_job_id,))
            return cur.rowcount > 0


# ── Watch Event CRUD ──────────────────────────────────────────────────────────

def record_watch_event(
    watch_job_id: str,
    event_type: str,
    payload: dict | None = None,
    database_url: str | None = None,
) -> dict:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO watch_events (watch_job_id, event_type, payload)
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                (watch_job_id, event_type, Json(payload or {})),
            )
            return dict(cur.fetchone())


def list_watch_events(
    watch_job_id: str,
    limit: int = 50,
    database_url: str | None = None,
) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM watch_events
                WHERE watch_job_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (watch_job_id, limit),
            )
            return [dict(r) for r in cur.fetchall()]


# ── Incident CRUD ─────────────────────────────────────────────────────────────

def create_incident(
    project_id: str | None,
    severity: str,
    summary: str,
    metadata: dict | None = None,
    database_url: str | None = None,
) -> dict:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO incidents (project_id, severity, summary, status, metadata)
                VALUES (%s, %s, %s, 'open', %s)
                RETURNING *
                """,
                (project_id, severity, summary, Json(metadata or {})),
            )
            row = dict(cur.fetchone())
    try:
        from packages.notification_service import fire_event as _fire
        _fire(
            "incident.created",
            {
                "incident_id": str(row["id"]),
                "severity": severity,
                "summary": summary,
                "project_id": str(project_id) if project_id else None,
            },
            database_url=database_url,
        )
    except Exception:
        pass
    return row


def list_incidents(
    status: str | None = "open",
    database_url: str | None = None,
) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if status is not None:
                cur.execute(
                    "SELECT * FROM incidents WHERE status = %s ORDER BY created_at DESC",
                    (status,),
                )
            else:
                cur.execute("SELECT * FROM incidents ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]


def resolve_incident(incident_id: str, database_url: str | None = None) -> dict:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE incidents SET status = 'resolved' WHERE id = %s RETURNING *",
                (incident_id,),
            )
            return dict(cur.fetchone())


# ── Watch Check Execution ──────────────────────────────────────────────────────

def run_watch_check(watch_job: dict, database_url: str | None = None) -> dict:
    """Execute a check command, record event, raise incident on threshold breach.

    Expected watch_job["metadata"] keys:
      - check_command: str   — shell command to run
      - expected_contains: str | None  — substring that must appear in stdout
      - threshold: int  — consecutive failures before incident (default 3)
    """
    watch_job_id = str(watch_job["id"])
    project_id = str(watch_job.get("project_id") or "")
    meta = watch_job.get("metadata") or {}
    check_command: str = meta.get("check_command", "echo ok")
    expected_contains: str | None = meta.get("expected_contains")
    threshold: int = int(meta.get("threshold", 3))

    # Run the command
    try:
        proc = subprocess.run(
            check_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        stdout = proc.stdout
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        stdout = ""
        exit_code = -1

    # Determine ok/fail
    ok = exit_code == 0
    if ok and expected_contains is not None:
        ok = expected_contains in stdout

    event_type = "check_ok" if ok else "check_fail"
    event = record_watch_event(
        watch_job_id=watch_job_id,
        event_type=event_type,
        payload={"stdout": stdout[:2000], "exit_code": exit_code, "command": check_command},
        database_url=database_url,
    )
    event_id = str(event["id"])

    incident_id: str | None = None
    if not ok:
        # Count consecutive failures from recent events
        recent = list_watch_events(watch_job_id, limit=threshold + 5, database_url=database_url)
        consecutive = 0
        for ev in recent:
            if ev["event_type"] == "check_fail":
                consecutive += 1
            else:
                break
        if consecutive >= threshold:
            incident = create_incident(
                project_id=project_id if project_id else None,
                severity="warning",
                summary=f"Watch job {watch_job_id}: {consecutive} consecutive failures on '{check_command}'",
                metadata={"watch_job_id": watch_job_id, "consecutive_failures": consecutive},
                database_url=database_url,
            )
            incident_id = str(incident["id"])

    return {
        "watch_job_id": watch_job_id,
        "event_id": event_id,
        "ok": ok,
        "incident_id": incident_id,
    }
