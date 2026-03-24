"""OpsClaw Experience Service — Layers 2 & 3 of the 4-layer memory structure.

Layer 2: Structured Task Memory (task_memories table)
Layer 3: Semantic Experience Memory (experiences table)
"""
from __future__ import annotations

import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor

DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


def _conn(database_url=None):
    return psycopg2.connect(database_url or DB_URL)


# ── Task Memory (Layer 2) ─────────────────────────────────────────────────────

def build_task_memory(project_id: str, database_url: str | None = None) -> dict:
    """Aggregate project + evidence + reports into a structured task_memory record.
    Idempotent: any existing task_memory for this project is replaced.
    """
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = cur.fetchone()
            if project is None:
                raise ValueError(f"Project not found: {project_id}")
            project = dict(project)

            cur.execute(
                "SELECT command_text, stdout_ref, exit_code, evidence_type FROM evidence WHERE project_id = %s ORDER BY started_at ASC",
                (project_id,),
            )
            evidence_rows = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT report_type, summary FROM reports WHERE project_id = %s ORDER BY created_at ASC",
                (project_id,),
            )
            report_rows = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT a.id, a.name, a.type FROM assets a JOIN project_assets pa ON pa.asset_id = a.id WHERE pa.project_id = %s",
                (project_id,),
            )
            asset_rows = [dict(r) for r in cur.fetchall()]

            # Playbook linked via projects.playbook_id
            playbook_name = None
            playbook_id = project.get("playbook_id")
            if playbook_id:
                cur.execute("SELECT name FROM playbooks WHERE id = %s", (playbook_id,))
                pb = cur.fetchone()
                playbook_name = pb["name"] if pb else playbook_id

    summary_parts = [
        f"Project: {project.get('name', project_id)}",
        f"Request: {project.get('request_text', '')[:200]}",
        f"Stage: {project.get('current_stage', 'unknown')} / Status: {project.get('status', 'unknown')}",
    ]
    if asset_rows:
        summary_parts.append("Assets: " + ", ".join(f"{a['name']}({a['type']})" for a in asset_rows))
    if playbook_name:
        summary_parts.append(f"Playbook: {playbook_name}")
    if evidence_rows:
        passed = sum(1 for e in evidence_rows if e.get("exit_code") == 0)
        summary_parts.append(f"Evidence: {len(evidence_rows)} records, {passed} successful")
    if report_rows:
        last = report_rows[-1]
        summary_parts.append(f"Last report: {(last.get('summary') or '')[:200]}")

    summary = " | ".join(summary_parts)
    metadata = {
        "evidence_count": len(evidence_rows),
        "report_count": len(report_rows),
        "asset_ids": [a["id"] for a in asset_rows],
        "playbook_id": playbook_id,
        "final_stage": project.get("current_stage"),
        "mode": project.get("mode"),
    }

    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM task_memories WHERE project_id = %s", (project_id,))
            cur.execute(
                "INSERT INTO task_memories (project_id, summary, metadata) VALUES (%s, %s, %s) RETURNING *",
                (project_id, summary, Json(metadata)),
            )
            return dict(cur.fetchone())


def get_task_memory(project_id: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM task_memories WHERE project_id = %s ORDER BY created_at DESC LIMIT 1",
                (project_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def list_task_memories(limit: int = 20, database_url: str | None = None) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM task_memories ORDER BY created_at DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]


# ── Experience Memory (Layer 3) ───────────────────────────────────────────────

def promote_to_experience(
    task_memory_id: str,
    category: str,
    title: str,
    outcome: str | None = None,
    asset_id: str | None = None,
    database_url: str | None = None,
) -> dict:
    """Promote a task_memory to an experience entry."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM task_memories WHERE id = %s", (task_memory_id,))
            tm = cur.fetchone()
            if tm is None:
                raise ValueError(f"TaskMemory not found: {task_memory_id}")
            tm = dict(tm)

            cur.execute(
                """
                INSERT INTO experiences (category, title, summary, outcome, asset_id, linked_evidence_ids, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    category, title, tm["summary"], outcome, asset_id,
                    Json([]),
                    Json({"source_task_memory_id": task_memory_id,
                          "source_project_id": tm.get("project_id")}),
                ),
            )
            exp = dict(cur.fetchone())

    # retrieval 인덱스에 자동 등록
    try:
        from packages.retrieval_service import index_document
        body = f"{tm.get('summary', '')}\noutcome: {outcome or ''}\ncategory: {category}"
        index_document(
            document_type="experience",
            ref_id=exp["id"],
            title=title,
            body=body,
            metadata={"category": category, "outcome": outcome,
                      "source_project_id": tm.get("project_id")},
            database_url=database_url,
        )
    except Exception:
        pass

    return exp


def create_experience(
    category: str,
    title: str,
    summary: str,
    outcome: str | None = None,
    asset_id: str | None = None,
    metadata: dict | None = None,
    database_url: str | None = None,
) -> dict:
    """Create an experience record directly."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO experiences (category, title, summary, outcome, asset_id, metadata) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
                (category, title, summary, outcome, asset_id, Json(metadata or {})),
            )
            exp = dict(cur.fetchone())

    # retrieval 인덱스에 자동 등록 — search_documents()로 검색 가능하게
    try:
        from packages.retrieval_service import index_document
        body = f"{summary or ''}\noutcome: {outcome or ''}\ncategory: {category}"
        index_document(
            document_type="experience",
            ref_id=exp["id"],
            title=title,
            body=body,
            metadata={"category": category, "outcome": outcome},
            database_url=database_url,
        )
    except Exception:
        pass  # 인덱싱 실패가 experience 생성을 막지 않도록

    return exp


def list_experiences(category: str | None = None, limit: int = 20, database_url: str | None = None) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if category is not None:
                cur.execute(
                    "SELECT * FROM experiences WHERE category = %s ORDER BY created_at DESC LIMIT %s",
                    (category, limit),
                )
            else:
                cur.execute("SELECT * FROM experiences ORDER BY created_at DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]


def get_experience(experience_id: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM experiences WHERE id = %s", (experience_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def auto_promote_experience(
    project_id: str,
    database_url: str | None = None,
) -> dict:
    """Build task_memory then use pi LLM to generate title/summary/outcome and promote.

    Returns the created experience record, or raises if no task_memory exists.
    """
    tm = build_task_memory(project_id, database_url=database_url)

    # Use pi to generate a meaningful experience narrative
    from packages.pi_adapter.runtime import PiRuntimeClient, PiRuntimeConfig
    client = PiRuntimeClient(PiRuntimeConfig(default_role="manager"))
    prompt = (
        f"다음은 OpsClaw 프로젝트 실행 기록이다:\n\n"
        f"{tm['summary']}\n\n"
        f"이 작업에서 배울 수 있는 핵심 교훈을 JSON으로 반환하라. "
        f"형식: {{\"title\": \"<20자 이내>\", \"category\": \"<operations|security|monitoring>\", "
        f"\"outcome\": \"<성공/실패/부분성공>\", \"lesson\": \"<2~3문장>\"}}"
    )
    try:
        result = client.invoke_model(prompt, {"role": "manager"})
        import json, re
        raw = result.get("stdout", "") or ""
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        parsed = json.loads(m.group(0)) if m else {}
        title = parsed.get("title", f"작업: {tm.get('summary', '')[:30]}")
        category = parsed.get("category", "operations")
        outcome = parsed.get("outcome", "")
        lesson = parsed.get("lesson", tm.get("summary", "")[:300])
    except Exception:
        title = f"작업: {tm.get('summary', '')[:30]}"
        category = "operations"
        outcome = "unknown"
        lesson = tm.get("summary", "")[:300]

    return promote_to_experience(
        task_memory_id=tm["id"],
        category=category,
        title=title,
        outcome=f"{outcome}: {lesson}",
        database_url=database_url,
    )


# ── 자동 경험 승급 (M24) ──────────────────────────────────────────────────

def auto_promote_high_reward(
    project_id: str,
    reward_threshold: float = 1.1,
    database_url: str | None = None,
) -> dict:
    """
    프로젝트의 task_reward 평균이 threshold 이상이면 자동 experience 생성.
    이미 해당 프로젝트의 task_memory가 experience로 승급된 적 있으면 skip.

    Returns: {"promoted": True/False, "avg_reward": ..., ...}
    """
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 해당 프로젝트의 task_reward 평균 조회
            cur.execute(
                "SELECT AVG(total_reward) AS avg_reward, COUNT(*) AS cnt FROM task_reward WHERE project_id = %s",
                (project_id,),
            )
            row = cur.fetchone()
            avg_reward = float(row["avg_reward"]) if row and row["avg_reward"] is not None else 0.0
            cnt = int(row["cnt"]) if row else 0

            if cnt == 0 or avg_reward < reward_threshold:
                return {"promoted": False, "avg_reward": round(avg_reward, 4), "reason": "below_threshold"}

            # 이미 task_memory 존재 시 experience 승급 여부 확인
            cur.execute(
                "SELECT id FROM task_memories WHERE project_id = %s LIMIT 1",
                (project_id,),
            )
            existing_tm = cur.fetchone()

            # experience에 이미 이 프로젝트 기반 항목 있는지 확인
            if existing_tm:
                cur.execute(
                    "SELECT id FROM experiences WHERE metadata->>'task_memory_id' = %s LIMIT 1",
                    (str(existing_tm["id"]),),
                )
                if cur.fetchone():
                    return {"promoted": False, "avg_reward": round(avg_reward, 4), "reason": "already_promoted"}

    # threshold 충족 + 미승급 → 자동 승급
    try:
        tm = build_task_memory(project_id, database_url)
        exp = promote_to_experience(
            task_memory_id=tm["id"],
            category="operations",
            title=f"[Auto] {tm.get('summary', '')[:60]}",
            outcome=f"avg_reward={round(avg_reward, 4)}, tasks={cnt}",
            database_url=database_url,
        )
        return {"promoted": True, "avg_reward": round(avg_reward, 4), "experience_id": exp.get("id")}
    except Exception as exc:
        return {"promoted": False, "avg_reward": round(avg_reward, 4), "reason": f"error: {exc}"}
