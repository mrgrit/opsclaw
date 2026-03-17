"""Policy Engine — env/risk_level based policy rules.

Rules are code-based (dict), designed to be migrated to DB in a later milestone.
"""
import os
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)

# ── Policy Rule Table ─────────────────────────────────────────────────────────
# requires_approval: risk levels that must have an approved master_review before execute
# blocked_modes: execution modes not permitted in this env
# allowed_modes: permitted execution modes

DEFAULT_POLICIES: dict[str, dict[str, Any]] = {
    "prod": {
        "requires_approval": ["high", "critical"],
        "blocked_modes": [],
        "allowed_modes": ["one_shot"],
    },
    "staging": {
        "requires_approval": ["critical"],
        "blocked_modes": [],
        "allowed_modes": ["one_shot", "batch"],
    },
    "lab": {
        "requires_approval": [],
        "blocked_modes": [],
        "allowed_modes": ["one_shot", "batch", "continuous"],
    },
    "default": {
        "requires_approval": ["critical"],
        "blocked_modes": [],
        "allowed_modes": ["one_shot", "batch"],
    },
}


# ── Exceptions ────────────────────────────────────────────────────────────────

class PolicyError(Exception):
    pass


class PolicyViolation(PolicyError):
    pass


# ── Public API ────────────────────────────────────────────────────────────────

def get_policy(env: str) -> dict[str, Any]:
    """Return policy rules for the given environment."""
    return dict(DEFAULT_POLICIES.get(env) or DEFAULT_POLICIES["default"])


def _get_project_context(
    project_id: str, database_url: str | None
) -> dict[str, Any]:
    """Fetch project risk_level, mode, and linked asset envs."""
    db_url = database_url or DEFAULT_DATABASE_URL
    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT risk_level, mode FROM projects WHERE id = %s",
                (project_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise PolicyError(f"Project not found: {project_id}")
            risk_level = row["risk_level"] or "medium"
            mode = row["mode"] or "one_shot"

            cur.execute(
                """
                SELECT DISTINCT a.env
                FROM project_assets pa
                JOIN assets a ON pa.asset_id = a.id
                WHERE pa.project_id = %s AND a.env IS NOT NULL
                """,
                (project_id,),
            )
            envs = [r["env"] for r in cur.fetchall()]

    # Derive strictest env: prod > staging > lab > default
    env = "default"
    for candidate in ["prod", "staging", "lab"]:
        if candidate in envs:
            env = candidate
            break
    if env == "default" and envs:
        env = envs[0]

    return {"risk_level": risk_level, "mode": mode, "env": env}


def check_policy(
    project_id: str,
    stage: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Check policy compliance. Returns allowed/violations/warnings."""
    ctx = _get_project_context(project_id, database_url)
    risk_level = ctx["risk_level"]
    mode = ctx["mode"]
    env = ctx["env"]
    policy = get_policy(env)

    violations: list[str] = []
    warnings: list[str] = []

    if stage == "execute":
        if risk_level in policy.get("requires_approval", []):
            violations.append(
                f"Risk level '{risk_level}' requires approval in env '{env}' before execute"
            )
        if mode in policy.get("blocked_modes", []):
            violations.append(f"Mode '{mode}' is blocked in env '{env}'")
        if mode not in policy.get("allowed_modes", ["one_shot"]):
            warnings.append(
                f"Mode '{mode}' is not in allowed modes for env '{env}'"
            )

    return {
        "project_id": project_id,
        "stage": stage,
        "env": env,
        "risk_level": risk_level,
        "mode": mode,
        "policy": policy,
        "allowed": len(violations) == 0,
        "violations": violations,
        "warnings": warnings,
    }


def enforce_policy(
    project_id: str,
    stage: str,
    database_url: str | None = None,
) -> None:
    """Raise PolicyViolation if the project violates policy at the given stage."""
    result = check_policy(project_id, stage, database_url=database_url)
    if not result["allowed"]:
        raise PolicyViolation(
            f"Policy violation for project {project_id} at stage '{stage}': "
            + "; ".join(result["violations"])
        )
