"""LLM 사용량 추적 및 예산 관리."""

import os
import time
from dataclasses import dataclass, field
from typing import Any

import psycopg2
import psycopg2.extras


_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)


def _get_conn():
    return psycopg2.connect(_DATABASE_URL)


def _ensure_table():
    """llm_usage 테이블 생성."""
    ddl = """
    CREATE TABLE IF NOT EXISTS llm_usage (
        id          SERIAL PRIMARY KEY,
        model       VARCHAR(128) NOT NULL,
        input_tokens    INTEGER NOT NULL DEFAULT 0,
        output_tokens   INTEGER NOT NULL DEFAULT 0,
        duration_ms     INTEGER NOT NULL DEFAULT 0,
        project_id      VARCHAR(64),
        agent_id        VARCHAR(256),
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_llm_usage_project ON llm_usage(project_id);
    CREATE INDEX IF NOT EXISTS idx_llm_usage_agent ON llm_usage(agent_id);
    CREATE INDEX IF NOT EXISTS idx_llm_usage_created ON llm_usage(created_at);
    """
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
        conn.close()
    except Exception:
        pass


_ensure_table()


@dataclass
class LLMUsage:
    """단일 LLM 호출의 사용량."""
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    project_id: str | None = None
    agent_id: str | None = None


def track_usage(usage: LLMUsage) -> None:
    """LLM 사용량을 DB에 기록한다."""
    try:
        conn = _get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO llm_usage
                    (model, input_tokens, output_tokens, duration_ms, project_id, agent_id)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        usage.model, usage.input_tokens, usage.output_tokens,
                        usage.duration_ms, usage.project_id, usage.agent_id,
                    ),
                )
        conn.close()
    except Exception:
        pass  # 추적 실패가 작업 실행을 방해하지 않음


def get_project_cost(project_id: str) -> dict[str, Any]:
    """프로젝트별 누적 사용량을 반환한다."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT
                    COUNT(*) as call_count,
                    COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                    COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                    COALESCE(SUM(duration_ms), 0) as total_duration_ms
                FROM llm_usage WHERE project_id = %s""",
                (project_id,),
            )
            row = dict(cur.fetchone())
            row["project_id"] = project_id
            row["total_tokens"] = row["total_input_tokens"] + row["total_output_tokens"]
            return row
    finally:
        conn.close()


def get_agent_cost(agent_id: str) -> dict[str, Any]:
    """에이전트별 누적 사용량을 반환한다."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT
                    COUNT(*) as call_count,
                    COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                    COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                    COALESCE(SUM(duration_ms), 0) as total_duration_ms
                FROM llm_usage WHERE agent_id = %s""",
                (agent_id,),
            )
            row = dict(cur.fetchone())
            row["agent_id"] = agent_id
            row["total_tokens"] = row["total_input_tokens"] + row["total_output_tokens"]
            return row
    finally:
        conn.close()


def get_total_cost() -> dict[str, Any]:
    """전체 시스템 누적 사용량을 반환한다."""
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT
                    COUNT(*) as call_count,
                    COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                    COALESCE(SUM(output_tokens), 0) as total_output_tokens,
                    COALESCE(SUM(duration_ms), 0) as total_duration_ms,
                    COUNT(DISTINCT model) as models_used,
                    COUNT(DISTINCT project_id) as projects_served
                FROM llm_usage""",
            )
            row = dict(cur.fetchone())
            row["total_tokens"] = row["total_input_tokens"] + row["total_output_tokens"]
            return row
    finally:
        conn.close()


def check_budget(
    project_id: str,
    max_tokens: int | None = None,
    max_calls: int | None = None,
) -> dict[str, Any]:
    """프로젝트 예산 초과 여부를 확인한다.

    Returns:
        {"within_budget": bool, "current": {...}, "limits": {...}}
    """
    current = get_project_cost(project_id)
    result: dict[str, Any] = {
        "within_budget": True,
        "current": current,
        "limits": {"max_tokens": max_tokens, "max_calls": max_calls},
        "violations": [],
    }

    if max_tokens and current["total_tokens"] >= max_tokens:
        result["within_budget"] = False
        result["violations"].append(
            f"Token limit exceeded: {current['total_tokens']}/{max_tokens}"
        )

    if max_calls and current["call_count"] >= max_calls:
        result["within_budget"] = False
        result["violations"].append(
            f"Call limit exceeded: {current['call_count']}/{max_calls}"
        )

    return result
