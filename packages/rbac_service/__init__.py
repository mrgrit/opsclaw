"""OpsClaw RBAC Service — role-based access control.

Tables: roles, actor_roles (from migration 0005_rbac.sql)

Permission model:
  - roles carry a list of permission strings (e.g. "project:read", "asset:write")
  - the special permission "*" grants everything
  - actors (users, api-keys, agents) are assigned one or more roles
  - check_permission(actor_id, permission) resolves via all assigned roles
"""
from __future__ import annotations

import os
import psycopg2
from psycopg2.extras import Json, RealDictCursor

DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


def _conn(database_url=None):
    return psycopg2.connect(database_url or DB_URL)


# ── Role CRUD ─────────────────────────────────────────────────────────────────

def create_role(
    name: str,
    permissions: list[str],
    description: str | None = None,
    database_url: str | None = None,
) -> dict:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO roles (name, permissions, description) VALUES (%s, %s, %s) RETURNING *",
                (name, Json(permissions), description),
            )
            return dict(cur.fetchone())


def get_role(role_id: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM roles WHERE id = %s", (role_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_role_by_name(name: str, database_url: str | None = None) -> dict | None:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM roles WHERE name = %s", (name,))
            row = cur.fetchone()
            return dict(row) if row else None


def list_roles(database_url: str | None = None) -> list[dict]:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM roles ORDER BY name")
            return [dict(r) for r in cur.fetchall()]


def update_role_permissions(
    role_id: str,
    permissions: list[str],
    database_url: str | None = None,
) -> dict:
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "UPDATE roles SET permissions = %s WHERE id = %s RETURNING *",
                (Json(permissions), role_id),
            )
            return dict(cur.fetchone())


def delete_role(role_id: str, database_url: str | None = None) -> bool:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM roles WHERE id = %s", (role_id,))
            return cur.rowcount > 0


# ── Actor–Role Assignment ─────────────────────────────────────────────────────

def assign_role(
    actor_id: str,
    role_id: str,
    actor_type: str = "user",
    database_url: str | None = None,
) -> dict:
    """Assign a role to an actor. Idempotent (ON CONFLICT DO NOTHING)."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO actor_roles (actor_id, actor_type, role_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (actor_id, role_id) DO UPDATE
                  SET actor_type = EXCLUDED.actor_type
                RETURNING *
                """,
                (actor_id, actor_type, role_id),
            )
            return dict(cur.fetchone())


def revoke_role(
    actor_id: str,
    role_id: str,
    database_url: str | None = None,
) -> bool:
    with _conn(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM actor_roles WHERE actor_id = %s AND role_id = %s",
                (actor_id, role_id),
            )
            return cur.rowcount > 0


def get_actor_roles(
    actor_id: str,
    database_url: str | None = None,
) -> list[dict]:
    """Return all roles assigned to an actor."""
    with _conn(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT r.* FROM roles r
                JOIN actor_roles ar ON ar.role_id = r.id
                WHERE ar.actor_id = %s
                ORDER BY r.name
                """,
                (actor_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def get_actor_permissions(
    actor_id: str,
    database_url: str | None = None,
) -> list[str]:
    """Return the flattened permission list for an actor across all roles."""
    roles = get_actor_roles(actor_id, database_url=database_url)
    perms: set[str] = set()
    for role in roles:
        for p in (role.get("permissions") or []):
            perms.add(p)
    return sorted(perms)


def check_permission(
    actor_id: str,
    permission: str,
    database_url: str | None = None,
) -> bool:
    """Return True if the actor has the given permission (or '*')."""
    perms = get_actor_permissions(actor_id, database_url=database_url)
    return "*" in perms or permission in perms
