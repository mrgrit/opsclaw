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

VALID_STATUSES = ("approved", "rejected", "needs_replan")


class MasterReviewError(Exception):
    pass


class MasterReviewNotFoundError(MasterReviewError):
    pass


def _conn(database_url: str | None = None):
    return psycopg2.connect(database_url or DEFAULT_DATABASE_URL)


def create_master_review(
    project_id: str,
    reviewer_agent_id: str,
    status: str,
    review_summary: str,
    findings: dict | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise MasterReviewError(f"Invalid status: {status}. Must be one of {VALID_STATUSES}")

    review_id = f"rev_{uuid.uuid4().hex[:12]}"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO master_reviews (
                    id, project_id, reviewer_agent_id, status,
                    review_summary, findings
                ) VALUES (%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    review_id, project_id, reviewer_agent_id, status,
                    review_summary,
                    json.dumps(findings or {}),
                ),
            )
            return dict(cur.fetchone())


def get_latest_master_review(
    project_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM master_reviews
                WHERE project_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (project_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise MasterReviewNotFoundError(f"No review found for project: {project_id}")
            return dict(row)


def get_all_master_reviews(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM master_reviews WHERE project_id = %s ORDER BY created_at ASC",
                (project_id,),
            )
            return [dict(row) for row in cur.fetchall()]
