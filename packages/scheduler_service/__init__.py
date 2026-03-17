"""OpsClaw Scheduler Service — schedule CRUD + batch execution logic."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from croniter import croniter

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)


def _conn(database_url: str | None = None):
    return psycopg2.connect(database_url or DB_URL)


def _next_run(cron_expr: str) -> datetime:
    """Compute next UTC datetime for a cron expression."""
    it = croniter(cron_expr, datetime.now(timezone.utc))
    return it.get_next(datetime)


# ── Schedule CRUD ─────────────────────────────────────────────────────────────

def create_schedule(
    project_id: str,
    schedule_type: str,
    cron_expr: str | None = None,
    metadata: dict | None = None,
    database_url: str | None = None,
) -> dict:
    next_run = _next_run(cron_expr) if cron_expr else None
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO schedules (project_id, schedule_type, cron_expr, next_run, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (project_id, schedule_type, cron_expr, next_run, psycopg2.extras.Json(metadata or {})),
            )
            return dict(cur.fetchone())


def get_schedule(schedule_id: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM schedules WHERE id = %s", (schedule_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def list_schedules(enabled_only: bool = True, database_url: str | None = None) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if enabled_only:
                cur.execute("SELECT * FROM schedules WHERE enabled = true ORDER BY created_at")
            else:
                cur.execute("SELECT * FROM schedules ORDER BY created_at")
            return [dict(r) for r in cur.fetchall()]


def update_schedule(
    schedule_id: str,
    *,
    enabled: bool | None = None,
    cron_expr: str | None = None,
    database_url: str | None = None,
) -> dict:
    sets = []
    params: list[Any] = []
    if enabled is not None:
        sets.append("enabled = %s")
        params.append(enabled)
    if cron_expr is not None:
        sets.append("cron_expr = %s")
        params.append(cron_expr)
        sets.append("next_run = %s")
        params.append(_next_run(cron_expr))
    if not sets:
        row = get_schedule(schedule_id, database_url=database_url)
        if row is None:
            raise ValueError(f"Schedule not found: {schedule_id}")
        return row
    params.append(schedule_id)
    sql = f"UPDATE schedules SET {', '.join(sets)} WHERE id = %s RETURNING *"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return dict(cur.fetchone())


def delete_schedule(schedule_id: str, database_url: str | None = None) -> bool:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
            return cur.rowcount > 0


def get_due_schedules(database_url: str | None = None) -> list[dict]:
    """Return enabled schedules whose next_run is <= now()."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM schedules
                WHERE enabled = true AND next_run <= now()
                ORDER BY next_run
                """
            )
            return [dict(r) for r in cur.fetchall()]


def mark_schedule_ran(schedule_id: str, database_url: str | None = None) -> None:
    """Update last_run=now() and advance next_run by cron_expr."""
    row = get_schedule(schedule_id, database_url=database_url)
    if row is None:
        return
    next_run = _next_run(row["cron_expr"]) if row.get("cron_expr") else None
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE schedules SET last_run = NOW(), next_run = %s WHERE id = %s",
                (next_run, schedule_id),
            )


# ── Batch Execution ───────────────────────────────────────────────────────────

def execute_due_schedule(schedule: dict, database_url: str | None = None) -> dict:
    """Run one plan→execute→validate→report cycle for a batch schedule.

    If the project is already in execute/validate/report stage, replan it first.
    Records minimal evidence and advances next_run.
    """
    from packages.project_service import (
        ProjectNotFoundError,
        ProjectServiceError,
        create_minimal_evidence_record,
        execute_project_record,
        finalize_report_stage_record,
        get_project_record,
        plan_project_record,
        replan_project,
        validate_project_record,
    )

    schedule_id = str(schedule["id"])
    project_id = str(schedule["project_id"])
    cycle_result: dict[str, Any] = {}
    error: str | None = None

    try:
        project = get_project_record(project_id, database_url=database_url)
        stage = project.get("current_stage", "draft")

        # If stuck in execute/validate/report, replan first
        if stage in ("execute", "validate", "report"):
            replan_project(project_id, reason="batch_cycle_replan", database_url=database_url)
            stage = "plan"

        # plan
        if stage in ("draft", "plan"):
            if stage == "draft":
                plan_project_record(project_id, database_url=database_url)
        else:
            plan_project_record(project_id, database_url=database_url)

        # execute
        exec_result = execute_project_record(project_id, database_url=database_url)

        # validate
        val_result = validate_project_record(project_id, database_url=database_url)

        # report
        rpt_result = finalize_report_stage_record(project_id, database_url=database_url)

        # minimal evidence
        create_minimal_evidence_record(
            project_id=project_id,
            command="batch_cycle",
            stdout=f"batch cycle completed for schedule {schedule_id}",
            stderr="",
            exit_code=0,
            database_url=database_url,
        )

        cycle_result = {
            "stage_after": "report",
            "job_run_id": exec_result.get("job_run", {}).get("id"),
            "report_id": rpt_result.get("report", {}).get("id"),
        }

    except (ProjectNotFoundError, ProjectServiceError, Exception) as exc:
        error = str(exc)
        try:
            from packages.notification_service import fire_event as _fire
            _fire(
                "schedule.failed",
                {"schedule_id": schedule_id, "project_id": project_id, "error": error},
                database_url=database_url,
            )
        except Exception:
            pass

    mark_schedule_ran(schedule_id, database_url=database_url)

    return {
        "schedule_id": schedule_id,
        "project_id": project_id,
        "cycle_result": cycle_result,
        "error": error,
    }
