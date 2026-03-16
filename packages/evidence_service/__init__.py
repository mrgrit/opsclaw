import os
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)


class EvidenceError(Exception):
    pass


class EvidenceNotFoundError(EvidenceError):
    pass


class EvidenceRequiredError(EvidenceError):
    """Raised when an action requires evidence but none exists."""
    pass


def _conn(database_url: str | None = None):
    return psycopg2.connect(database_url or DEFAULT_DATABASE_URL)


def _extract_inline(ref: str | None) -> str:
    """Extract content from inline://stdout/{id}:{content} format."""
    if not ref:
        return ""
    if ref.startswith("inline://"):
        # format: inline://stdout/{ev_id}:{content}
        colon_pos = ref.find(":", len("inline://"))
        if colon_pos != -1:
            return ref[colon_pos + 1:]
    return ref


def get_evidence(evidence_id: str, database_url: str | None = None) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM evidence WHERE id = %s", (evidence_id,))
            row = cur.fetchone()
            if row is None:
                raise EvidenceNotFoundError(f"Evidence not found: {evidence_id}")
            return dict(row)


def get_evidence_content(evidence_id: str, database_url: str | None = None) -> dict[str, Any]:
    """Return evidence with stdout/stderr content extracted from inline refs."""
    ev = get_evidence(evidence_id, database_url)
    return {
        **ev,
        "stdout": _extract_inline(ev.get("stdout_ref")),
        "stderr": _extract_inline(ev.get("stderr_ref")),
    }


def get_evidence_summary(project_id: str, database_url: str | None = None) -> dict[str, Any]:
    """Return evidence statistics for a project."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*)                                          AS total,
                    COUNT(*) FILTER (WHERE exit_code = 0)            AS success_count,
                    COUNT(*) FILTER (WHERE exit_code != 0)           AS failure_count,
                    COUNT(*) FILTER (WHERE exit_code IS NULL)        AS unknown_count,
                    array_agg(DISTINCT evidence_type)                AS types,
                    MIN(started_at)                                  AS first_at,
                    MAX(finished_at)                                 AS last_at
                FROM evidence
                WHERE project_id = %s
                """,
                (project_id,),
            )
            row = dict(cur.fetchone())

    total = row["total"] or 0
    success = row["success_count"] or 0
    return {
        "project_id": project_id,
        "total": total,
        "success_count": success,
        "failure_count": row["failure_count"] or 0,
        "unknown_count": row["unknown_count"] or 0,
        "success_rate": round(success / total, 2) if total > 0 else None,
        "types": [t for t in (row["types"] or []) if t],
        "first_at": row["first_at"],
        "last_at": row["last_at"],
    }


def require_evidence_for_close(project_id: str, database_url: str | None = None) -> None:
    """Raise EvidenceRequiredError if no evidence exists for the project."""
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM evidence WHERE project_id = %s",
                (project_id,),
            )
            count = cur.fetchone()[0]
    if count == 0:
        raise EvidenceRequiredError(
            f"Cannot close project {project_id}: no evidence recorded. "
            "At least one evidence item is required before closing."
        )
