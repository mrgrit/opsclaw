"""OpsClaw Reporting Service — project report generation and evidence pack export.

Provides:
  generate_project_report(project_id) → full JSON aggregation of all project data
  export_evidence_pack(project_id)    → dict with evidence + validation + reports
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


def _conn(database_url=None):
    return psycopg2.connect(database_url or DB_URL)


def _default(obj):
    """JSON serialiser fallback for datetime etc."""
    return str(obj)


def generate_project_report(project_id: str, database_url: str | None = None) -> dict:
    """Aggregate all project data into a comprehensive structured report dict.

    Includes: project metadata, assets, evidence, validation_runs, reports,
    task_memory, job_runs, master_reviews.
    """
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = cur.fetchone()
            if project is None:
                raise ValueError(f"Project not found: {project_id}")
            project = dict(project)

            cur.execute(
                "SELECT a.id, a.name, a.type, a.env, a.subagent_status FROM assets a JOIN project_assets pa ON pa.asset_id = a.id WHERE pa.project_id = %s",
                (project_id,),
            )
            assets = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT id, evidence_type, command_text, stdout_ref, exit_code, started_at FROM evidence WHERE project_id = %s ORDER BY started_at",
                (project_id,),
            )
            evidence = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT id, validator_name, validation_type, status, expected_result, actual_result, executed_at FROM validation_runs WHERE project_id = %s ORDER BY executed_at",
                (project_id,),
            )
            validation_runs = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT id, report_type, summary, created_at FROM reports WHERE project_id = %s ORDER BY created_at",
                (project_id,),
            )
            reports = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT id, status, review_summary, reviewer_agent_id, created_at FROM master_reviews WHERE project_id = %s ORDER BY created_at",
                (project_id,),
            )
            master_reviews = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT id, status, stage, assigned_agent_role, started_at, finished_at FROM job_runs WHERE project_id = %s ORDER BY started_at",
                (project_id,),
            )
            job_runs = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT id, summary, metadata, created_at FROM task_memories WHERE project_id = %s ORDER BY created_at DESC LIMIT 1",
                (project_id,),
            )
            task_memory_row = cur.fetchone()
            task_memory = dict(task_memory_row) if task_memory_row else None

    # Summary statistics
    passed_ev = sum(1 for e in evidence if e.get("exit_code") == 0)
    passed_val = sum(1 for v in validation_runs if v.get("status") == "pass")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": project,
        "summary": {
            "assets_count": len(assets),
            "evidence_count": len(evidence),
            "evidence_passed": passed_ev,
            "evidence_failed": len(evidence) - passed_ev,
            "validation_count": len(validation_runs),
            "validation_passed": passed_val,
            "reports_count": len(reports),
            "job_runs_count": len(job_runs),
            "master_reviews_count": len(master_reviews),
        },
        "assets": assets,
        "evidence": evidence,
        "validation_runs": validation_runs,
        "reports": reports,
        "job_runs": job_runs,
        "master_reviews": master_reviews,
        "task_memory": task_memory,
    }


def export_evidence_pack(project_id: str, database_url: str | None = None) -> dict:
    """Export a self-contained evidence pack for a project.

    Suitable for compliance/audit purposes — contains all evidence,
    validation results, and the final report summary.
    """
    report = generate_project_report(project_id, database_url=database_url)
    return {
        "pack_type": "evidence_pack",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "project_id": project_id,
        "project_name": report["project"].get("name"),
        "final_stage": report["project"].get("current_stage"),
        "summary": report["summary"],
        "evidence": report["evidence"],
        "validation_runs": report["validation_runs"],
        "reports": report["reports"],
        "master_reviews": report["master_reviews"],
    }


def export_evidence_pack_json(project_id: str, database_url: str | None = None) -> str:
    """Return evidence pack as a JSON string."""
    pack = export_evidence_pack(project_id, database_url=database_url)
    return json.dumps(pack, default=_default, ensure_ascii=False, indent=2)
