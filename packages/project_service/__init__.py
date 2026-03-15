import os
import uuid
from dataclasses import dataclass
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw",
)


class ProjectServiceError(Exception):
    pass


class ProjectNotFoundError(ProjectServiceError):
    pass


@dataclass(frozen=True)
class ProjectServiceConfig:
    database_url: str = DEFAULT_DATABASE_URL


def get_connection(database_url: str | None = None):
    return psycopg2.connect(database_url or DEFAULT_DATABASE_URL)


def create_project_record(
    name: str,
    request_text: str,
    mode: str = "one_shot",
    database_url: str | None = None,
) -> dict[str, Any]:
    project_id = f"prj_{uuid.uuid4().hex[:12]}"
    sql = """
    INSERT INTO projects (
        id, name, request_text, requester_type, status, current_stage,
        mode, priority, risk_level, summary
    ) VALUES (
        %(id)s, %(name)s, %(request_text)s, %(requester_type)s, %(status)s,
        %(current_stage)s, %(mode)s, %(priority)s, %(risk_level)s, %(summary)s
    )
    RETURNING *
    """
    params = {
        "id": project_id,
        "name": name,
        "request_text": request_text,
        "requester_type": "human",
        "status": "created",
        "current_stage": "intake",
        "mode": mode,
        "priority": "normal",
        "risk_level": "medium",
        "summary": None,
    }

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row)


def get_project_record(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    sql = "SELECT * FROM projects WHERE id = %s"
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (project_id,))
            row = cur.fetchone()
            if row is None:
                raise ProjectNotFoundError(f"Project not found: {project_id}")
            return dict(row)


def execute_project_record(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    project = get_project_record(project_id, database_url=database_url)
    job_run_id = f"job_{uuid.uuid4().hex[:12]}"
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE projects
                SET status = %s,
                    current_stage = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *
                """,
                ("running", "execute", project_id),
            )
            updated_project = dict(cur.fetchone())

            cur.execute(
                """
                INSERT INTO job_runs (
                    id, project_id, parent_job_id, playbook_id, skill_id,
                    asset_id, target_id, assigned_agent_role, assigned_agent_id,
                    status, stage, started_at, finished_at, retry_count,
                    input_ref, output_ref
                ) VALUES (
                    %(id)s, %(project_id)s, NULL, NULL, NULL,
                    NULL, NULL, %(assigned_agent_role)s, %(assigned_agent_id)s,
                    %(status)s, %(stage)s, NOW(), NOW(), %(retry_count)s,
                    NULL, NULL
                )
                RETURNING *
                """,
                {
                    "id": job_run_id,
                    "project_id": project_id,
                    "assigned_agent_role": "manager",
                    "assigned_agent_id": "manager-api",
                    "status": "completed",
                    "stage": "execute",
                    "retry_count": 0,
                },
            )
            job_run = dict(cur.fetchone())

            cur.execute(
                """
                INSERT INTO reports (
                    id, project_id, report_type, body_ref, summary, created_by
                ) VALUES (
                    %(id)s, %(project_id)s, %(report_type)s, %(body_ref)s, %(summary)s, %(created_by)s
                )
                RETURNING *
                """,
                {
                    "id": report_id,
                    "project_id": project_id,
                    "report_type": "intermediate",
                    "body_ref": f"inline://projects/{project_id}/execute",
                    "summary": "Project moved to execute stage",
                    "created_by": "manager-api",
                },
            )
            report = dict(cur.fetchone())

    return {
        "project": updated_project,
        "job_run": job_run,
        "report": report,
    }


def get_project_report(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    sql = """
    SELECT *
    FROM reports
    WHERE project_id = %s
    ORDER BY created_at DESC
    LIMIT 1
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (project_id,))
            row = cur.fetchone()
            if row is None:
                raise ProjectNotFoundError(f"Report not found for project: {project_id}")
            return dict(row)
