"""Approval Engine — risk-based approval gate for high-risk operations.

Design principle: Human-minimized, not Human-eliminated.
High/critical risk projects must have an approved master_review before execute.
"""
import os
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)

# Risk levels that require an approved master_review before execute
APPROVAL_REQUIRED_FOR: frozenset[str] = frozenset({"high", "critical"})


# ── Exceptions ────────────────────────────────────────────────────────────────

class ApprovalError(Exception):
    pass


class ApprovalNotClearedError(ApprovalError):
    """Approval is required but has not been granted."""
    pass


# ── Helpers ───────────────────────────────────────────────────────────────────

def _conn(database_url: str | None = None):
    return psycopg2.connect(database_url or DEFAULT_DATABASE_URL)


def _get_project_risk(project_id: str, database_url: str | None) -> str:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT risk_level FROM projects WHERE id = %s", (project_id,)
            )
            row = cur.fetchone()
            if row is None:
                raise ApprovalError(f"Project not found: {project_id}")
            return row["risk_level"] or "medium"


# ── Public API ────────────────────────────────────────────────────────────────

def check_requires_approval(
    project_id: str,
    database_url: str | None = None,
) -> bool:
    """Return True if this project requires approval before execute."""
    risk_level = _get_project_risk(project_id, database_url)
    return risk_level in APPROVAL_REQUIRED_FOR


def require_approval_cleared(
    project_id: str,
    database_url: str | None = None,
) -> None:
    """Raise ApprovalNotClearedError if approval is required but not granted.

    Low/medium risk projects pass through without check.
    High/critical risk projects must have an approved master_review.
    """
    if not check_requires_approval(project_id, database_url=database_url):
        return  # no approval required for low/medium risk

    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id FROM master_reviews
                WHERE project_id = %s AND status = 'approved'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (project_id,),
            )
            row = cur.fetchone()

    if row is None:
        risk_level = _get_project_risk(project_id, database_url)
        raise ApprovalNotClearedError(
            f"Project {project_id} has risk_level='{risk_level}' which requires approval. "
            "Submit a review via POST /projects/{id}/review (master-service) with "
            "status='approved' before proceeding to execute."
        )


def get_approval_status(
    project_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Return approval status summary for a project."""
    requires = check_requires_approval(project_id, database_url=database_url)

    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, status, reviewer_agent_id, review_summary, created_at
                FROM master_reviews
                WHERE project_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (project_id,),
            )
            row = cur.fetchone()
            latest_review = dict(row) if row else None

    cleared = (
        latest_review is not None and latest_review["status"] == "approved"
    ) if requires else True

    if not requires:
        message = "Approval not required (low/medium risk)"
    elif cleared:
        message = "Approved"
    else:
        message = "Pending approval — submit a review with status='approved'"

    return {
        "project_id": project_id,
        "requires_approval": requires,
        "cleared": cleared,
        "latest_review": latest_review,
        "message": message,
    }
