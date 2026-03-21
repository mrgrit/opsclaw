"""completion_report_service — Playbook 완료보고서 생성·조회·검색.

완료보고서는 Playbook 단위 작업이 끝난 후 Master 검수 완료 시 Manager가 자동 생성한다.
다음 유사 Playbook 생성 시 RAG 참조 자료로 활용된다.
"""
from __future__ import annotations

import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor

DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


def _conn(database_url: str | None = None):
    return psycopg2.connect(database_url or DB_URL)


def create_completion_report(
    project_id: str,
    summary: str,
    outcome: str = "unknown",
    playbook_id: str | None = None,
    playbook_name: str | None = None,
    request_text: str | None = None,
    work_details: list | None = None,
    issues: list | None = None,
    next_steps: list | None = None,
    evidence_summary: dict | None = None,
    reviewer_id: str | None = None,
    metadata: dict | None = None,
    database_url: str | None = None,
) -> dict:
    """완료보고서를 생성하고 retrieval index에 자동 등록한다."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO completion_reports
                  (project_id, playbook_id, playbook_name, request_text, summary, outcome,
                   work_details, issues, next_steps, evidence_summary, reviewer_id, metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    project_id, playbook_id, playbook_name, request_text, summary, outcome,
                    Json(work_details or []),
                    Json(issues or []),
                    Json(next_steps or []),
                    Json(evidence_summary or {}),
                    reviewer_id,
                    Json(metadata or {}),
                ),
            )
            report = dict(cur.fetchone())

    # retrieval index 자동 등록 — 다음 유사 Playbook 생성 시 RAG 참조
    try:
        from packages.retrieval_service import index_document
        body_parts = [summary]
        if work_details:
            body_parts.append("작업내역: " + "; ".join(str(w) for w in work_details))
        if issues:
            body_parts.append("이슈: " + "; ".join(str(i) for i in issues))
        if next_steps:
            body_parts.append("다음작업: " + "; ".join(str(s) for s in next_steps))
        index_document(
            document_type="completion_report",
            ref_id=report["id"],
            title=f"[{outcome}] {playbook_name or 'adhoc'}: {summary[:60]}",
            body="\n".join(body_parts),
            metadata={
                "project_id": project_id,
                "playbook_id": playbook_id,
                "playbook_name": playbook_name,
                "outcome": outcome,
            },
            database_url=database_url,
        )
    except Exception:
        pass

    return report


def get_completion_report(report_id: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM completion_reports WHERE id = %s", (report_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def list_completion_reports(
    project_id: str | None = None,
    playbook_name: str | None = None,
    outcome: str | None = None,
    limit: int = 20,
    database_url: str | None = None,
) -> list[dict]:
    where, params = [], []
    if project_id:
        where.append("project_id = %s"); params.append(project_id)
    if playbook_name:
        where.append("playbook_name = %s"); params.append(playbook_name)
    if outcome:
        where.append("outcome = %s"); params.append(outcome)
    params.append(limit)

    sql = "SELECT * FROM completion_reports"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT %s"

    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def auto_generate_report(
    project_id: str,
    database_url: str | None = None,
) -> dict:
    """프로젝트의 evidence·reports·playbook 정보로 완료보고서를 자동 생성한다."""
    import psycopg2.extras

    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 프로젝트 기본 정보
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = dict(cur.fetchone() or {})

            # evidence 통계
            cur.execute(
                "SELECT count(*) total, sum(case when exit_code=0 then 1 else 0 end) ok FROM evidence WHERE project_id=%s",
                (project_id,),
            )
            ev = dict(cur.fetchone() or {})

            # 연결된 playbook (binding_type='project', binding_ref=project_id)
            cur.execute(
                "SELECT pb.id, pb.name FROM playbooks pb JOIN playbook_bindings bb ON bb.playbook_id=pb.id WHERE bb.binding_ref=%s LIMIT 1",
                (project_id,),
            )
            pb_row = cur.fetchone()

            # 보고서 요약
            cur.execute(
                "SELECT summary FROM reports WHERE project_id=%s ORDER BY created_at DESC LIMIT 1",
                (project_id,),
            )
            rep_row = cur.fetchone()

    total = int(ev.get("total") or 0)
    ok = int(ev.get("ok") or 0)
    outcome = "success" if total > 0 and ok == total else ("partial" if ok > 0 else "failed")
    if total == 0:
        outcome = "unknown"

    summary = rep_row["summary"] if rep_row else f"프로젝트 {project.get('name')} 완료. evidence {ok}/{total} 성공."

    return create_completion_report(
        project_id=project_id,
        summary=summary,
        outcome=outcome,
        playbook_id=pb_row["id"] if pb_row else None,
        playbook_name=pb_row["name"] if pb_row else None,
        request_text=project.get("request_text"),
        evidence_summary={"total": total, "ok": ok, "success_rate": ok / total if total else 0},
        database_url=database_url,
    )
