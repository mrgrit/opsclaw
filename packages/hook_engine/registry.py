"""Hook 레지스트리 — 인메모리 + DB 하이브리드 저장."""

import os
from typing import Any

import psycopg2
import psycopg2.extras

from packages.hook_engine.events import HOOK_EVENTS, BLOCKING_EVENTS
from packages.hook_engine.models import HookDefinition


_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)


def _get_conn():
    return psycopg2.connect(_DATABASE_URL)


def _ensure_table():
    """hooks 테이블이 없으면 생성."""
    ddl = """
    CREATE TABLE IF NOT EXISTS hooks (
        id          VARCHAR(64) PRIMARY KEY,
        name        VARCHAR(128) NOT NULL DEFAULT '',
        event       VARCHAR(64) NOT NULL,
        hook_type   VARCHAR(32) NOT NULL,
        target      TEXT NOT NULL,
        condition   TEXT,
        timeout_s   INTEGER NOT NULL DEFAULT 15,
        can_block   BOOLEAN NOT NULL DEFAULT FALSE,
        enabled     BOOLEAN NOT NULL DEFAULT TRUE,
        metadata    JSONB NOT NULL DEFAULT '{}',
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_hooks_event ON hooks(event);
    """
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        conn.close()
    except Exception:
        pass  # 테이블 이미 존재하거나 DB 미연결


_ensure_table()


def register_hook(hook: HookDefinition) -> HookDefinition:
    """Hook을 DB에 등록한다."""
    if hook.event not in HOOK_EVENTS:
        raise ValueError(f"Unknown hook event: {hook.event}. Valid: {HOOK_EVENTS}")
    if hook.can_block and hook.event not in BLOCKING_EVENTS:
        raise ValueError(f"can_block=True is only allowed for: {BLOCKING_EVENTS}")

    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO hooks (id, name, event, hook_type, target, condition,
                       timeout_s, can_block, enabled, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                       name=EXCLUDED.name, event=EXCLUDED.event, hook_type=EXCLUDED.hook_type,
                       target=EXCLUDED.target, condition=EXCLUDED.condition,
                       timeout_s=EXCLUDED.timeout_s, can_block=EXCLUDED.can_block,
                       enabled=EXCLUDED.enabled, metadata=EXCLUDED.metadata,
                       updated_at=now()
                    RETURNING id""",
                    (
                        hook.id, hook.name, hook.event, hook.hook_type,
                        hook.target, hook.condition, hook.timeout_s,
                        hook.can_block, hook.enabled,
                        psycopg2.extras.Json(hook.metadata),
                    ),
                )
        return hook
    finally:
        conn.close()


def unregister_hook(hook_id: str) -> bool:
    """Hook을 삭제한다."""
    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM hooks WHERE id = %s", (hook_id,))
                return cur.rowcount > 0
    finally:
        conn.close()


def list_hooks(event: str | None = None, enabled_only: bool = True) -> list[dict[str, Any]]:
    """등록된 Hook 목록을 반환한다."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if event:
                cur.execute(
                    "SELECT * FROM hooks WHERE event = %s"
                    + (" AND enabled = TRUE" if enabled_only else "")
                    + " ORDER BY created_at",
                    (event,),
                )
            else:
                cur.execute(
                    "SELECT * FROM hooks"
                    + (" WHERE enabled = TRUE" if enabled_only else "")
                    + " ORDER BY event, created_at",
                )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_hooks_for_event(event: str) -> list[dict[str, Any]]:
    """특정 이벤트에 등록된 활성 Hook만 반환한다."""
    return list_hooks(event=event, enabled_only=True)
