"""메모리 용량 관리 — LRU 기반 오래된 메모리 정리.

Claude Code의 memdir 패턴: 200줄/25KB 용량 제한.
OpsClaw에서는 DB 기반이므로 행 수 기반 LRU를 적용한다.
"""

import os
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


_DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")

DEFAULT_MAX_TASK_MEMORIES = 200
DEFAULT_MAX_EXPERIENCES = 100
DEFAULT_MAX_LOCAL_KNOWLEDGE_ENTRIES = 30


def _conn():
    return psycopg2.connect(_DB_URL)


def enforce_capacity(
    max_task_memories: int = DEFAULT_MAX_TASK_MEMORIES,
    max_experiences: int = DEFAULT_MAX_EXPERIENCES,
) -> dict[str, int]:
    """오래된 메모리를 LRU 방식으로 정리한다.

    Returns:
        {"task_memories_deleted": N, "experiences_deleted": N}
    """
    result = {"task_memories_deleted": 0, "experiences_deleted": 0}

    conn = _conn()
    try:
        with conn:
            with conn.cursor() as cur:
                # task_memories: 오래된 것부터 삭제
                cur.execute("SELECT COUNT(*) FROM task_memories")
                count = cur.fetchone()[0]
                if count > max_task_memories:
                    excess = count - max_task_memories
                    cur.execute(
                        "DELETE FROM task_memories WHERE id IN "
                        "(SELECT id FROM task_memories ORDER BY created_at ASC LIMIT %s)",
                        (excess,),
                    )
                    result["task_memories_deleted"] = cur.rowcount

                # experiences: 오래된 것부터 삭제
                cur.execute("SELECT COUNT(*) FROM experiences")
                count = cur.fetchone()[0]
                if count > max_experiences:
                    excess = count - max_experiences
                    cur.execute(
                        "DELETE FROM experiences WHERE id IN "
                        "(SELECT id FROM experiences ORDER BY created_at ASC LIMIT %s)",
                        (excess,),
                    )
                    result["experiences_deleted"] = cur.rowcount
    finally:
        conn.close()

    return result


def enforce_local_knowledge_capacity(
    knowledge: dict,
    max_entries: int = DEFAULT_MAX_LOCAL_KNOWLEDGE_ENTRIES,
) -> dict:
    """로컬 지식(data/local_knowledge/*.json)의 experiences 항목을 LRU 정리.

    Args:
        knowledge: 로컬 지식 dict
        max_entries: 최대 경험 항목 수

    Returns:
        정리된 knowledge dict
    """
    exps = knowledge.get("experiences", [])
    if len(exps) > max_entries:
        knowledge["experiences"] = exps[-max_entries:]

    events = knowledge.get("daemon_events", [])
    if len(events) > 50:
        knowledge["daemon_events"] = events[-50:]

    return knowledge
