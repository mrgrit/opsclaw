"""OpsClaw Retrieval Service — Layer 4: Working Context via smart retrieval.

Uses PostgreSQL full-text search (to_tsvector / plainto_tsquery) on retrieval_documents.
No external vector DB required. Retrieval axes: asset, playbook, error, experience.
"""
from __future__ import annotations

import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor

DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


def _conn(database_url=None):
    return psycopg2.connect(database_url or DB_URL)


# ── Document Indexing ─────────────────────────────────────────────────────────

def index_document(
    document_type: str,
    ref_id: str | None,
    title: str,
    body: str,
    metadata: dict | None = None,
    database_url: str | None = None,
) -> dict:
    """Index a document for full-text retrieval.

    document_type: 'report', 'evidence_summary', 'experience', 'playbook', 'asset', etc.
    ref_id: the id of the source record (project_id, experience_id, etc.)
    """
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO retrieval_documents (document_type, ref_id, title, body, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (document_type, ref_id, title, body, Json(metadata or {})),
            )
            return dict(cur.fetchone())


def search_documents(
    query: str,
    document_type: str | None = None,
    limit: int = 10,
    database_url: str | None = None,
) -> list[dict]:
    """Full-text search across retrieval_documents using PostgreSQL plainto_tsquery.

    Falls back to ILIKE if query produces no FTS results.
    """
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if document_type is not None:
                cur.execute(
                    """
                    SELECT *, ts_rank(to_tsvector('english', title || ' ' || body),
                                     plainto_tsquery('english', %s)) AS rank
                    FROM retrieval_documents
                    WHERE document_type = %s
                      AND to_tsvector('english', title || ' ' || body)
                          @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT %s
                    """,
                    (query, document_type, query, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT *, ts_rank(to_tsvector('english', title || ' ' || body),
                                     plainto_tsquery('english', %s)) AS rank
                    FROM retrieval_documents
                    WHERE to_tsvector('english', title || ' ' || body)
                          @@ plainto_tsquery('english', %s)
                    ORDER BY rank DESC
                    LIMIT %s
                    """,
                    (query, query, limit),
                )
            rows = [dict(r) for r in cur.fetchall()]

        # Fallback: ILIKE if FTS returns nothing
        if not rows:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                pattern = f"%{query}%"
                if document_type is not None:
                    cur.execute(
                        """
                        SELECT * FROM retrieval_documents
                        WHERE document_type = %s
                          AND (title ILIKE %s OR body ILIKE %s)
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (document_type, pattern, pattern, limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT * FROM retrieval_documents
                        WHERE title ILIKE %s OR body ILIKE %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (pattern, pattern, limit),
                    )
                rows = [dict(r) for r in cur.fetchall()]

    return rows


def get_retrieval_document(doc_id: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM retrieval_documents WHERE id = %s", (doc_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def list_retrieval_documents(
    document_type: str | None = None,
    limit: int = 50,
    database_url: str | None = None,
) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if document_type:
                cur.execute(
                    "SELECT * FROM retrieval_documents WHERE document_type = %s ORDER BY created_at DESC LIMIT %s",
                    (document_type, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM retrieval_documents ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
            return [dict(r) for r in cur.fetchall()]


# ── Project Reindexing ────────────────────────────────────────────────────────

def reindex_project(project_id: str, database_url: str | None = None) -> dict:
    """Index all evidence and reports for a project into retrieval_documents.

    Returns {"indexed_count": N}.
    """
    indexed = 0
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = cur.fetchone()
            if project is None:
                raise ValueError(f"Project not found: {project_id}")
            project = dict(project)

            cur.execute(
                "SELECT id, command_text, stdout_ref, evidence_type FROM evidence WHERE project_id = %s",
                (project_id,),
            )
            evidence_rows = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT id, report_type, summary FROM reports WHERE project_id = %s",
                (project_id,),
            )
            report_rows = [dict(r) for r in cur.fetchall()]

    for ev in evidence_rows:
        body = f"{ev.get('command_text', '')} {ev.get('stdout_ref', '')}"
        if body.strip():
            index_document(
                document_type="evidence",
                ref_id=project_id,
                title=f"Evidence [{ev.get('evidence_type', 'cmd')}] for {project.get('name')}",
                body=body,
                metadata={"evidence_id": str(ev["id"]), "project_id": project_id},
                database_url=database_url,
            )
            indexed += 1

    for rpt in report_rows:
        body = rpt.get("summary") or ""
        if body.strip():
            index_document(
                document_type="report",
                ref_id=project_id,
                title=f"Report [{rpt.get('report_type')}] for {project.get('name')}",
                body=body,
                metadata={"report_id": str(rpt["id"]), "project_id": project_id},
                database_url=database_url,
            )
            indexed += 1

    return {"indexed_count": indexed, "project_id": project_id}


# ── Working Context Assembly (Layer 4) ────────────────────────────────────────

def get_context_for_project(
    project_id: str,
    database_url: str | None = None,
) -> dict:
    """Assemble working context for a project from all retrieval axes.

    Returns:
      asset_history: recent history events for linked assets
      experiences: relevant experience records
      documents: relevant retrieval_documents (FTS on request_text)
    """
    from packages.history_service import get_asset_history
    from packages.experience_service import list_experiences

    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = cur.fetchone()
            if project is None:
                raise ValueError(f"Project not found: {project_id}")
            project = dict(project)

            cur.execute(
                "SELECT asset_id FROM project_assets WHERE project_id = %s LIMIT 5",
                (project_id,),
            )
            asset_ids = [r["asset_id"] for r in cur.fetchall()]

    # Asset axis: past work on linked assets
    asset_history: list[dict] = []
    for aid in asset_ids:
        asset_history.extend(get_asset_history(aid, limit=3, database_url=database_url))

    # Experience axis: recent experiences (up to 5)
    experiences = list_experiences(limit=5, database_url=database_url)

    # Document axis: FTS on project's request_text
    request_text = project.get("request_text") or project.get("name") or ""
    documents: list[dict] = []
    if request_text.strip():
        documents = search_documents(request_text[:100], limit=5, database_url=database_url)

    return {
        "project_id": project_id,
        "project_name": project.get("name"),
        "asset_history": asset_history,
        "experiences": experiences,
        "documents": documents,
    }
