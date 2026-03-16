import json
import os
import uuid
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)


class ValidationError(Exception):
    pass


class ValidationNotFoundError(ValidationError):
    pass


def _conn(database_url: str | None = None):
    return psycopg2.connect(database_url or DEFAULT_DATABASE_URL)


def create_validation_run(
    project_id: str,
    validator_name: str,
    validation_type: str,
    status: str,
    expected_result: dict | None = None,
    actual_result: dict | None = None,
    evidence_id: str | None = None,
    asset_id: str | None = None,
    job_run_id: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Record a validation result directly (no execution)."""
    valid_statuses = ("passed", "failed", "inconclusive")
    if status not in valid_statuses:
        raise ValidationError(f"Invalid status: {status}. Must be one of {valid_statuses}")

    run_id = f"val_{uuid.uuid4().hex[:12]}"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO validation_runs (
                    id, project_id, job_run_id, asset_id,
                    validator_name, validation_type, status,
                    expected_result, actual_result, evidence_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    run_id, project_id, job_run_id, asset_id,
                    validator_name, validation_type, status,
                    json.dumps(expected_result or {}),
                    json.dumps(actual_result or {}),
                    evidence_id,
                ),
            )
            return dict(cur.fetchone())


def get_validation_runs(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM validation_runs WHERE project_id = %s ORDER BY executed_at ASC",
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def get_validation_status(
    project_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Return overall validation status for a project."""
    runs = get_validation_runs(project_id, database_url)
    if not runs:
        return {"project_id": project_id, "overall": "no_runs", "total": 0, "passed": 0, "failed": 0, "inconclusive": 0}

    passed = sum(1 for r in runs if r["status"] == "passed")
    failed = sum(1 for r in runs if r["status"] == "failed")
    inconclusive = sum(1 for r in runs if r["status"] == "inconclusive")

    if failed > 0:
        overall = "has_failures"
    elif inconclusive > 0:
        overall = "inconclusive"
    else:
        overall = "all_passed"

    return {
        "project_id": project_id,
        "overall": overall,
        "total": len(runs),
        "passed": passed,
        "failed": failed,
        "inconclusive": inconclusive,
    }


def run_validation_check(
    project_id: str,
    validator_name: str,
    command: str,
    expected_contains: str | None = None,
    expected_exit_code: int = 0,
    subagent_url: str | None = None,
    asset_id: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    Run a shell command (locally or via subagent), check output,
    record a validation_run, and return the result.
    """
    import subprocess

    from packages.a2a_protocol import (
        A2AClient,
        A2AClientConfig,
        A2AError,
        A2ARunRequest,
        SUBAGENT_DEFAULT_URL,
    )
    from packages.project_service import create_minimal_evidence_record

    job_run_id = f"job_{uuid.uuid4().hex[:12]}"

    # Execute command
    if subagent_url:
        try:
            client = A2AClient(A2AClientConfig(base_url=subagent_url))
            result = client.run_script(
                A2ARunRequest(project_id=project_id, job_run_id=job_run_id, script=command, timeout_s=30)
            )
            stdout, stderr, exit_code = result.stdout, result.stderr, result.exit_code
        except A2AError as exc:
            stdout, stderr, exit_code = "", str(exc), -1
    else:
        proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode

    # Determine pass/fail
    exit_ok = exit_code == expected_exit_code
    content_ok = (expected_contains is None) or (expected_contains in stdout)
    passed = exit_ok and content_ok

    validation_status = "passed" if passed else "failed"
    if exit_code == -1:
        validation_status = "inconclusive"

    # Record evidence
    evidence = create_minimal_evidence_record(
        project_id=project_id,
        command=command,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        database_url=database_url,
    )

    # Record validation_run
    expected_result = {"exit_code": expected_exit_code, "contains": expected_contains}
    actual_result = {
        "exit_code": exit_code,
        "stdout_snippet": stdout[:500],
        "stderr_snippet": stderr[:200],
        "exit_ok": exit_ok,
        "content_ok": content_ok,
    }
    validation_run = create_validation_run(
        project_id=project_id,
        validator_name=validator_name,
        validation_type="command_check",
        status=validation_status,
        expected_result=expected_result,
        actual_result=actual_result,
        evidence_id=evidence["id"],
        asset_id=asset_id,
        database_url=database_url,
    )

    return {
        "validation_run_id": validation_run["id"],
        "evidence_id": evidence["id"],
        "command": command,
        "status": validation_status,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "expected_exit_code": expected_exit_code,
        "expected_contains": expected_contains,
    }
