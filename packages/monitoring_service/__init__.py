"""OpsClaw Monitoring Service — DB-based system health and operational metrics.

No external metrics infrastructure required. All metrics are derived from
live PostgreSQL queries, making them always accurate without separate collection.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


def _conn(database_url=None):
    return psycopg2.connect(database_url or DB_URL)


def get_system_health(database_url: str | None = None) -> dict:
    """Return a comprehensive system health snapshot.

    Counts active resources by category and surfaces any anomalies.
    """
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Projects by status
            cur.execute("SELECT status, COUNT(*) AS cnt FROM projects GROUP BY status ORDER BY cnt DESC")
            projects_by_status = {r["status"]: r["cnt"] for r in cur.fetchall()}

            # Projects by stage
            cur.execute("SELECT current_stage, COUNT(*) AS cnt FROM projects GROUP BY current_stage ORDER BY cnt DESC")
            projects_by_stage = {r["current_stage"]: r["cnt"] for r in cur.fetchall()}

            # Assets by status
            cur.execute("SELECT subagent_status, COUNT(*) AS cnt FROM assets GROUP BY subagent_status ORDER BY cnt DESC")
            assets_by_status = {r["subagent_status"] or "unknown": r["cnt"] for r in cur.fetchall()}

            # Open incidents
            cur.execute("SELECT severity, COUNT(*) AS cnt FROM incidents WHERE status = 'open' GROUP BY severity")
            open_incidents = {r["severity"]: r["cnt"] for r in cur.fetchall()}

            # Enabled schedules
            cur.execute("SELECT COUNT(*) AS cnt FROM schedules WHERE enabled = true")
            enabled_schedules = cur.fetchone()["cnt"]

            # Running watch_jobs
            cur.execute("SELECT COUNT(*) AS cnt FROM watch_jobs WHERE status = 'running'")
            running_watchers = cur.fetchone()["cnt"]

            # Evidence counts last 24h
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM evidence WHERE started_at >= NOW() - INTERVAL '24 hours'"
            )
            evidence_24h = cur.fetchone()["cnt"]

            # Failed evidence last 24h
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM evidence WHERE exit_code != 0 AND started_at >= NOW() - INTERVAL '24 hours'"
            )
            evidence_failed_24h = cur.fetchone()["cnt"]

            # Unresolved incidents total
            cur.execute("SELECT COUNT(*) AS cnt FROM incidents WHERE status = 'open'")
            total_open_incidents = cur.fetchone()["cnt"]

    # Determine overall status
    overall = "healthy"
    warnings = []
    if total_open_incidents > 0:
        warnings.append(f"{total_open_incidents} open incident(s)")
    if evidence_failed_24h > 0:
        warnings.append(f"{evidence_failed_24h} failed evidence record(s) in last 24h")
    if warnings:
        overall = "degraded"

    return {
        "status": overall,
        "warnings": warnings,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "projects": {
            "by_status": projects_by_status,
            "by_stage": projects_by_stage,
            "total": sum(projects_by_status.values()),
        },
        "assets": {
            "by_status": assets_by_status,
            "total": sum(assets_by_status.values()),
        },
        "incidents": {
            "open_by_severity": open_incidents,
            "total_open": total_open_incidents,
        },
        "schedules": {
            "enabled": enabled_schedules,
        },
        "watchers": {
            "running": running_watchers,
        },
        "evidence_24h": {
            "total": evidence_24h,
            "failed": evidence_failed_24h,
        },
    }


def get_operational_metrics(database_url: str | None = None) -> dict:
    """Return key operational metrics: success rates, recent activity, top assets."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Overall evidence success rate
            cur.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN exit_code = 0 THEN 1 ELSE 0 END) AS success FROM evidence")
            ev = cur.fetchone()
            total_ev = ev["total"] or 0
            success_ev = ev["success"] or 0
            evidence_success_rate = round(success_ev / total_ev * 100, 1) if total_ev > 0 else None

            # Validation pass rate
            cur.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) AS passed FROM validation_runs")
            vr = cur.fetchone()
            total_vr = vr["total"] or 0
            passed_vr = vr["passed"] or 0
            validation_pass_rate = round(passed_vr / total_vr * 100, 1) if total_vr > 0 else None

            # Recent projects (last 7 days)
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM projects WHERE created_at >= NOW() - INTERVAL '7 days'"
            )
            recent_projects = cur.fetchone()["cnt"]

            # Recent evidence (last 7 days)
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM evidence WHERE started_at >= NOW() - INTERVAL '7 days'"
            )
            recent_evidence = cur.fetchone()["cnt"]

            # Top assets by evidence count
            cur.execute(
                """
                SELECT a.name, a.type, COUNT(e.id) AS evidence_count
                FROM assets a
                LEFT JOIN evidence e ON e.asset_id = a.id
                GROUP BY a.id, a.name, a.type
                ORDER BY evidence_count DESC
                LIMIT 5
                """
            )
            top_assets = [dict(r) for r in cur.fetchall()]

            # Recently resolved incidents
            cur.execute(
                "SELECT COUNT(*) AS cnt FROM incidents WHERE status = 'resolved'"
            )
            resolved_incidents = cur.fetchone()["cnt"]

            # Total audit events
            cur.execute("SELECT COUNT(*) AS cnt FROM audit_logs")
            total_audit = cur.fetchone()["cnt"]

            # Task memories
            cur.execute("SELECT COUNT(*) AS cnt FROM task_memories")
            total_task_memories = cur.fetchone()["cnt"]

            # Experiences
            cur.execute("SELECT COUNT(*) AS cnt FROM experiences")
            total_experiences = cur.fetchone()["cnt"]

    return {
        "evidence": {
            "total": total_ev,
            "success_rate_pct": evidence_success_rate,
        },
        "validation": {
            "total": total_vr,
            "pass_rate_pct": validation_pass_rate,
        },
        "recent_7d": {
            "projects": recent_projects,
            "evidence": recent_evidence,
        },
        "top_assets_by_evidence": top_assets,
        "incidents": {
            "resolved": resolved_incidents,
        },
        "audit": {
            "total_events": total_audit,
        },
        "memory": {
            "task_memories": total_task_memories,
            "experiences": total_experiences,
        },
    }
