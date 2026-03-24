import json
import os
import uuid
from typing import Any

import psycopg2
import psycopg2.errors
from psycopg2.extras import RealDictCursor

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)


class RegistryError(Exception):
    pass


class RegistryNotFoundError(RegistryError):
    pass


class RegistryConflictError(RegistryError):
    pass


def _conn(db: str | None = None):
    return psycopg2.connect(db or DEFAULT_DATABASE_URL)


def _j(v: Any) -> str:
    return json.dumps(v) if v is not None else None


# ── Tools ─────────────────────────────────────────────────────────────────────

def upsert_tool(
    name: str, version: str,
    description: str | None = None,
    runtime_type: str | None = None,
    risk_level: str | None = None,
    policy_tags: list | None = None,
    enabled: bool = True,
    metadata: dict | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    tool_id = f"tool_{uuid.uuid4().hex[:12]}"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO tools (id,version,name,description,runtime_type,risk_level,
                    policy_tags,enabled,metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (name,version) DO UPDATE SET
                    description=EXCLUDED.description,
                    runtime_type=EXCLUDED.runtime_type,
                    risk_level=EXCLUDED.risk_level,
                    policy_tags=EXCLUDED.policy_tags,
                    enabled=EXCLUDED.enabled,
                    metadata=EXCLUDED.metadata
                RETURNING *
                """,
                (tool_id, version, name, description, runtime_type, risk_level,
                 _j(policy_tags), enabled, _j(metadata or {})),
            )
            return dict(cur.fetchone())


def get_tool(tool_id: str, database_url: str | None = None) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM tools WHERE id=%s", (tool_id,))
            row = cur.fetchone()
            if row is None:
                raise RegistryNotFoundError(f"Tool not found: {tool_id}")
            return dict(row)


def get_tool_by_name(name: str, version: str | None = None, database_url: str | None = None) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if version:
                cur.execute("SELECT * FROM tools WHERE name=%s AND version=%s", (name, version))
            else:
                cur.execute("SELECT * FROM tools WHERE name=%s ORDER BY version DESC LIMIT 1", (name,))
            row = cur.fetchone()
            if row is None:
                raise RegistryNotFoundError(f"Tool not found: {name}@{version or 'latest'}")
            return dict(row)


def list_tools(enabled: bool | None = None, database_url: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM tools"
    params: list = []
    if enabled is not None:
        sql += " WHERE enabled=%s"
        params.append(enabled)
    sql += " ORDER BY name, version"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


# ── Skills ────────────────────────────────────────────────────────────────────

def upsert_skill(
    name: str, version: str,
    category: str | None = None,
    description: str | None = None,
    required_tools: list | None = None,
    optional_tools: list | None = None,
    default_validation: dict | None = None,
    enabled: bool = True,
    metadata: dict | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    skill_id = f"skill_{uuid.uuid4().hex[:12]}"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO skills (id,version,name,category,description,
                    required_tools,optional_tools,default_validation,enabled,metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (name,version) DO UPDATE SET
                    category=EXCLUDED.category,
                    description=EXCLUDED.description,
                    required_tools=EXCLUDED.required_tools,
                    optional_tools=EXCLUDED.optional_tools,
                    default_validation=EXCLUDED.default_validation,
                    enabled=EXCLUDED.enabled,
                    metadata=EXCLUDED.metadata
                RETURNING *
                """,
                (skill_id, version, name, category, description,
                 _j(required_tools or []), _j(optional_tools or []),
                 _j(default_validation or {}), enabled, _j(metadata or {})),
            )
            return dict(cur.fetchone())


def get_skill(skill_id: str, database_url: str | None = None) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM skills WHERE id=%s", (skill_id,))
            row = cur.fetchone()
            if row is None:
                raise RegistryNotFoundError(f"Skill not found: {skill_id}")
            return dict(row)


def get_skill_by_name(name: str, version: str | None = None, database_url: str | None = None) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if version:
                cur.execute("SELECT * FROM skills WHERE name=%s AND version=%s", (name, version))
            else:
                cur.execute("SELECT * FROM skills WHERE name=%s ORDER BY version DESC LIMIT 1", (name,))
            row = cur.fetchone()
            if row is None:
                raise RegistryNotFoundError(f"Skill not found: {name}@{version or 'latest'}")
            return dict(row)


def list_skills(category: str | None = None, database_url: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM skills"
    params: list = []
    if category:
        sql += " WHERE category=%s"
        params.append(category)
    sql += " ORDER BY name, version"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


# ── Playbooks ─────────────────────────────────────────────────────────────────

def upsert_playbook(
    name: str, version: str,
    category: str | None = None,
    description: str | None = None,
    execution_mode: str = "one_shot",
    default_risk_level: str = "medium",
    dry_run_supported: bool = False,
    explain_supported: bool = True,
    required_asset_roles: list | None = None,
    failure_policy: dict | None = None,
    enabled: bool = True,
    metadata: dict | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    pb_id = f"pb_{uuid.uuid4().hex[:12]}"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO playbooks (id,version,name,category,description,
                    execution_mode,default_risk_level,dry_run_supported,explain_supported,
                    required_asset_roles,failure_policy,enabled,metadata)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (name,version) DO UPDATE SET
                    category=EXCLUDED.category,
                    description=EXCLUDED.description,
                    execution_mode=EXCLUDED.execution_mode,
                    default_risk_level=EXCLUDED.default_risk_level,
                    dry_run_supported=EXCLUDED.dry_run_supported,
                    explain_supported=EXCLUDED.explain_supported,
                    required_asset_roles=EXCLUDED.required_asset_roles,
                    failure_policy=EXCLUDED.failure_policy,
                    enabled=EXCLUDED.enabled,
                    metadata=EXCLUDED.metadata
                RETURNING *
                """,
                (pb_id, version, name, category, description,
                 execution_mode, default_risk_level,
                 dry_run_supported, explain_supported,
                 _j(required_asset_roles or []),
                 _j(failure_policy or {}),
                 enabled, _j(metadata or {})),
            )
            return dict(cur.fetchone())


def get_playbook(playbook_id: str, database_url: str | None = None) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM playbooks WHERE id=%s", (playbook_id,))
            row = cur.fetchone()
            if row is None:
                raise RegistryNotFoundError(f"Playbook not found: {playbook_id}")
            return dict(row)


def get_playbook_by_name(name: str, version: str | None = None, database_url: str | None = None) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if version:
                cur.execute("SELECT * FROM playbooks WHERE name=%s AND version=%s", (name, version))
            else:
                cur.execute("SELECT * FROM playbooks WHERE name=%s ORDER BY version DESC LIMIT 1", (name,))
            row = cur.fetchone()
            if row is None:
                raise RegistryNotFoundError(f"Playbook not found: {name}@{version or 'latest'}")
            return dict(row)


def list_playbooks(
    category: str | None = None,
    enabled: bool | None = None,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM playbooks"
    params: list = []
    where: list[str] = []
    if category:
        where.append("category=%s")
        params.append(category)
    if enabled is not None:
        where.append("enabled=%s")
        params.append(enabled)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY name, version"
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


# ── Playbook Steps ─────────────────────────────────────────────────────────────

def upsert_playbook_steps(
    playbook_id: str,
    steps: list[dict[str, Any]],
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    """Replace all steps for a playbook."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("DELETE FROM playbook_steps WHERE playbook_id=%s", (playbook_id,))
            result = []
            for s in steps:
                cur.execute(
                    """
                    INSERT INTO playbook_steps (
                        playbook_id, step_order, step_type, ref_id, name,
                        condition_expr, retry_policy, on_failure_action, metadata
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING *
                    """,
                    (
                        playbook_id,
                        s["order"],
                        s["type"],
                        s.get("ref"),
                        s.get("name"),
                        s.get("condition"),
                        _j(s.get("retry_policy")),
                        s.get("on_failure", "abort"),
                        _j(s.get("metadata") or s.get("params")),  # B-03: metadata/params 모두 허용
                    ),
                )
                result.append(dict(cur.fetchone()))
            return result


def get_playbook_steps(playbook_id: str, database_url: str | None = None) -> list[dict[str, Any]]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM playbook_steps WHERE playbook_id=%s ORDER BY step_order",
                (playbook_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def delete_playbook(playbook_id: str, database_url: str | None = None) -> None:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM playbook_steps WHERE playbook_id=%s", (playbook_id,))
            cur.execute("DELETE FROM playbooks WHERE id=%s", (playbook_id,))
            if cur.rowcount == 0:
                raise RegistryNotFoundError(f"Playbook not found: {playbook_id}")


def add_playbook_step(
    playbook_id: str,
    step_order: int,
    step_type: str,
    name: str | None = None,
    ref_id: str | None = None,
    params: dict | None = None,
    on_failure: str = "abort",
    database_url: str | None = None,
) -> dict[str, Any]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 기존 step_order 있으면 업데이트, 없으면 삽입
            cur.execute(
                "SELECT id FROM playbook_steps WHERE playbook_id=%s AND step_order=%s",
                (playbook_id, step_order),
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    """
                    UPDATE playbook_steps SET
                        step_type=%s, name=%s, ref_id=%s,
                        on_failure_action=%s, metadata=%s
                    WHERE playbook_id=%s AND step_order=%s
                    RETURNING *
                    """,
                    (step_type, name, ref_id, on_failure, _j(params or {}),
                     playbook_id, step_order),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO playbook_steps
                        (playbook_id, step_order, step_type, name, ref_id,
                         on_failure_action, metadata)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    RETURNING *
                    """,
                    (playbook_id, step_order, step_type, name,
                     ref_id, on_failure, _j(params or {})),
                )
            return dict(cur.fetchone())


# ── Composition Engine ────────────────────────────────────────────────────────

def resolve_playbook(playbook_id: str, database_url: str | None = None) -> dict[str, Any]:
    """
    Resolve a playbook into its full step → skill/tool tree.
    Returns a structured plan without executing anything.
    """
    pb = get_playbook(playbook_id, database_url)
    steps = get_playbook_steps(playbook_id, database_url)

    resolved_steps = []
    for step in steps:
        ref = step.get("ref_id")
        step_type = step["step_type"]
        resolved: dict[str, Any] = {
            "order": step["step_order"],
            "type": step_type,
            "name": step["name"] or ref,
            "ref": ref,
            "on_failure": step.get("on_failure_action", "abort"),
            "metadata": step.get("metadata") or {},  # WORK-63: params/metadata 전달
        }

        if step_type == "skill" and ref:
            try:
                skill = get_skill_by_name(ref, database_url=database_url)
                required = skill.get("required_tools") or []
                if isinstance(required, str):
                    import json as _json
                    required = _json.loads(required)
                tools = []
                for t_name in required:
                    try:
                        tools.append(get_tool_by_name(t_name, database_url=database_url))
                    except RegistryNotFoundError:
                        tools.append({"name": t_name, "status": "not_found"})
                resolved["skill"] = skill
                resolved["tools"] = tools
            except RegistryNotFoundError:
                resolved["skill"] = {"name": ref, "status": "not_found"}
                resolved["tools"] = []

        elif step_type == "tool" and ref:
            try:
                resolved["tool"] = get_tool_by_name(ref, database_url=database_url)
            except RegistryNotFoundError:
                resolved["tool"] = {"name": ref, "status": "not_found"}

        resolved_steps.append(resolved)

    return {
        "playbook": pb,
        "steps": resolved_steps,
        "total_steps": len(resolved_steps),
    }


def explain_playbook(playbook_id: str, database_url: str | None = None) -> dict[str, Any]:
    """Return human-readable explanation of what a playbook does."""
    plan = resolve_playbook(playbook_id, database_url)
    pb = plan["playbook"]

    lines = [
        f"# {pb['name']} v{pb['version']}",
        f"**Category**: {pb.get('category') or 'general'}",
        f"**Mode**: {pb.get('execution_mode', 'one_shot')}",
        f"**Risk**: {pb.get('default_risk_level', 'medium')}",
        f"**Dry-run**: {'yes' if pb.get('dry_run_supported') else 'no'}",
        "",
        f"{pb.get('description') or ''}",
        "",
        f"## Steps ({plan['total_steps']})",
    ]

    for step in plan["steps"]:
        prefix = f"{step['order']}. [{step['type'].upper()}] {step['name']}"
        lines.append(prefix)
        if step["type"] == "skill":
            skill = step.get("skill", {})
            lines.append(f"   Skill: {skill.get('name', step['ref'])} — {skill.get('description', '')}")
            for t in step.get("tools", []):
                lines.append(f"   → Tool: {t.get('name')} ({t.get('runtime_type', 'unknown')} / risk: {t.get('risk_level', '?')})")
        elif step["type"] == "tool":
            tool = step.get("tool", {})
            lines.append(f"   Tool: {tool.get('name', step['ref'])} — {tool.get('description', '')}")
        lines.append(f"   On failure: {step['on_failure']}")

    return {
        "playbook_id": playbook_id,
        "name": pb["name"],
        "version": pb["version"],
        "explanation": "\n".join(lines),
        "plan": plan,
    }


# ── Playbook 버전 관리 (M22) ────────────────────────────────────────────────

def snapshot_playbook(
    playbook_id: str,
    note: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    현재 Playbook + Steps 상태를 스냅샷으로 저장한다.
    version_number는 해당 Playbook의 현재 최대값 + 1.
    """
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM playbooks WHERE id = %s", (playbook_id,))
            pb = cur.fetchone()
            if pb is None:
                raise RegistryNotFoundError(f"Playbook not found: {playbook_id}")
            cur.execute(
                "SELECT * FROM playbook_steps WHERE playbook_id = %s ORDER BY step_order",
                (playbook_id,),
            )
            steps = [dict(r) for r in cur.fetchall()]

            cur.execute(
                "SELECT COALESCE(MAX(version_number), 0) FROM playbook_versions WHERE playbook_id = %s",
                (playbook_id,),
            )
            next_version = (cur.fetchone()[0] or 0) + 1

            snap_id = f"pbv_{uuid.uuid4().hex[:12]}"
            snapshot_json = {"playbook": dict(pb), "steps": steps}
            cur.execute(
                """
                INSERT INTO playbook_versions (id, playbook_id, version_number, snapshot_json, note)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (snap_id, playbook_id, next_version, json.dumps(snapshot_json), note),
            )
            row = dict(cur.fetchone())
    return {
        "id": row["id"],
        "playbook_id": playbook_id,
        "version_number": next_version,
        "note": note,
        "created_at": str(row["created_at"]),
    }


def list_playbook_versions(
    playbook_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    """버전 목록 조회 (최신순)."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, playbook_id, version_number, note, created_at
                FROM playbook_versions
                WHERE playbook_id = %s
                ORDER BY version_number DESC
                """,
                (playbook_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def rollback_playbook(
    playbook_id: str,
    version_number: int,
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    지정한 버전의 스냅샷으로 Playbook과 Steps를 복원한다.
    복원 전 현재 상태를 자동 스냅샷 저장 (rollback 이력 보존).
    """
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT snapshot_json FROM playbook_versions WHERE playbook_id=%s AND version_number=%s",
                (playbook_id, version_number),
            )
            row = cur.fetchone()
            if row is None:
                raise RegistryNotFoundError(
                    f"Version {version_number} not found for playbook {playbook_id}"
                )
            snap = row["snapshot_json"]
            pb_snap = snap["playbook"]
            steps_snap = snap["steps"]

            # Playbook 메타 복원
            cur.execute(
                """
                UPDATE playbooks SET
                    name=%(name)s, version=%(version)s, description=%(description)s,
                    category=%(category)s, execution_mode=%(execution_mode)s,
                    default_risk_level=%(default_risk_level)s, enabled=%(enabled)s,
                    metadata=%(metadata)s, updated_at=NOW()
                WHERE id=%(id)s
                """,
                {k: pb_snap.get(k) for k in (
                    "id", "name", "version", "description", "category",
                    "execution_mode", "default_risk_level", "enabled", "metadata",
                )},
            )

            # Steps 복원: 기존 삭제 후 재삽입
            cur.execute("DELETE FROM playbook_steps WHERE playbook_id = %s", (playbook_id,))
            for s in steps_snap:
                cur.execute(
                    """
                    INSERT INTO playbook_steps
                        (id, playbook_id, step_order, step_type, ref_id, name,
                         condition_expr, retry_policy, on_failure_action, metadata)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        s["id"], playbook_id, s["step_order"], s["step_type"],
                        s.get("ref_id"), s.get("name"), s.get("condition_expr"),
                        json.dumps(s.get("retry_policy")) if s.get("retry_policy") else None,
                        s.get("on_failure_action", "abort"),
                        json.dumps(s.get("metadata")) if s.get("metadata") else None,
                    ),
                )

    return {
        "playbook_id": playbook_id,
        "restored_version": version_number,
        "steps_restored": len(steps_snap),
    }
