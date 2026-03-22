"""
pow_service — Proof of Work & Blockchain Reward (M18)

Task 실행 결과를 해시 체인으로 기록하고 RL reward signal을 계산한다.

설계 원칙:
  - Task 단위 보상: Project보다 세밀, 데이터 풍부, RL credit assignment 명확
  - 자체 Merkle Chain: 외부 의존성 없음, 내부망 완전 독립
  - 자동 연동: execute-plan 완료 시 generate_proof() 자동 호출
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from psycopg2.extras import RealDictCursor

from packages.project_service import get_connection

# 첫 블록의 prev_hash (genesis)
GENESIS_HASH = "0" * 64


# ── 내부 유틸 ──────────────────────────────────────────────────────────────

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _get_prev_hash(agent_id: str, database_url: str | None = None) -> str:
    """에이전트의 가장 최근 block_hash 반환. 없으면 GENESIS_HASH."""
    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT block_hash FROM proof_of_work WHERE agent_id = %s ORDER BY ts DESC LIMIT 1",
                (agent_id,),
            )
            row = cur.fetchone()
            return row[0] if row else GENESIS_HASH


def _calculate_reward(
    exit_code: int,
    duration_s: float,
    risk_level: str,
) -> dict[str, float]:
    """
    RL reward signal 계산.

    base_score  : +1.0 성공 / -1.0 실패
    speed_bonus : 성공 시만 — <5s: +0.3 / <30s: +0.15 / <60s: +0.05
    risk_penalty: 실패 시만 — high: -0.1 / critical: -0.2
    quality_bonus: 0.0 (human feedback 연결 시 업데이트)
    """
    base_score = 1.0 if exit_code == 0 else -1.0

    speed_bonus = 0.0
    if exit_code == 0:
        if duration_s < 5:
            speed_bonus = 0.3
        elif duration_s < 30:
            speed_bonus = 0.15
        elif duration_s < 60:
            speed_bonus = 0.05

    risk_penalty = 0.0
    if exit_code != 0:
        risk_map = {"high": -0.1, "critical": -0.2}
        risk_penalty = risk_map.get(risk_level, 0.0)

    total = round(base_score + speed_bonus + risk_penalty, 4)
    return {
        "base_score": base_score,
        "speed_bonus": round(speed_bonus, 4),
        "risk_penalty": round(risk_penalty, 4),
        "quality_bonus": 0.0,
        "total_reward": total,
    }


# ── 공개 API ───────────────────────────────────────────────────────────────

def generate_proof(
    project_id: str,
    agent_id: str,
    task_order: int,
    task_title: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    duration_s: float,
    risk_level: str = "low",
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    Task 실행 결과 → PoW 블록 생성 + 보상 계산 + ledger UPSERT.
    execute-plan 엔드포인트에서 각 task 완료 후 자동 호출된다.
    """
    ts = datetime.now(timezone.utc).isoformat()
    evidence_hash = _sha256(f"{stdout}{stderr}{exit_code}")
    prev_hash = _get_prev_hash(agent_id, database_url)
    block_hash = _sha256(f"{prev_hash}{evidence_hash}{ts}")
    pow_id = f"pow_{uuid.uuid4().hex[:12]}"

    reward = _calculate_reward(exit_code, duration_s, risk_level)
    tr_id = f"tr_{uuid.uuid4().hex[:12]}"

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. PoW 블록
            cur.execute(
                """
                INSERT INTO proof_of_work
                    (id, agent_id, project_id, task_order, task_title,
                     evidence_hash, prev_hash, block_hash, ts)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (pow_id, agent_id, project_id, task_order, task_title,
                 evidence_hash, prev_hash, block_hash, ts),
            )
            pow_row = dict(cur.fetchone())

            # 2. 보상 기록
            cur.execute(
                """
                INSERT INTO task_reward
                    (id, pow_id, project_id, agent_id, task_order, task_title,
                     base_score, speed_bonus, risk_penalty, quality_bonus,
                     total_reward, exit_code, duration_s, risk_level)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (tr_id, pow_id, project_id, agent_id, task_order, task_title,
                 reward["base_score"], reward["speed_bonus"], reward["risk_penalty"],
                 reward["quality_bonus"], reward["total_reward"],
                 exit_code, duration_s, risk_level),
            )

            # 3. ledger UPSERT
            cur.execute(
                """
                INSERT INTO reward_ledger
                    (agent_id, balance, total_tasks, success_count, fail_count, updated_at)
                VALUES (%s, %s, 1, %s, %s, NOW())
                ON CONFLICT (agent_id) DO UPDATE SET
                    balance       = reward_ledger.balance       + EXCLUDED.balance,
                    total_tasks   = reward_ledger.total_tasks   + 1,
                    success_count = reward_ledger.success_count + EXCLUDED.success_count,
                    fail_count    = reward_ledger.fail_count    + EXCLUDED.fail_count,
                    updated_at    = NOW()
                """,
                (
                    agent_id,
                    reward["total_reward"],
                    1 if exit_code == 0 else 0,
                    0 if exit_code == 0 else 1,
                ),
            )

    return {
        "pow_id": pow_id,
        "block_hash": block_hash,
        "reward": reward,
    }


def verify_chain(
    agent_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    에이전트의 전체 블록 체인 무결성 검증.
    각 블록의 block_hash를 재계산하여 저장된 값과 비교한다.
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM proof_of_work WHERE agent_id = %s ORDER BY ts ASC",
                (agent_id,),
            )
            blocks = [dict(r) for r in cur.fetchall()]

    if not blocks:
        return {"agent_id": agent_id, "valid": True, "blocks": 0, "tampered": []}

    tampered = []
    for i, block in enumerate(blocks):
        ts_str = (
            block["ts"].isoformat()
            if hasattr(block["ts"], "isoformat")
            else str(block["ts"])
        )
        expected_block_hash = _sha256(
            f"{block['prev_hash']}{block['evidence_hash']}{ts_str}"
        )
        if expected_block_hash != block["block_hash"]:
            tampered.append({"id": block["id"], "reason": "block_hash_mismatch"})
            continue

        # prev_hash 체인 연결 검증
        if i > 0:
            expected_prev = blocks[i - 1]["block_hash"]
            if block["prev_hash"] != expected_prev:
                tampered.append({"id": block["id"], "reason": "chain_broken"})

    return {
        "agent_id": agent_id,
        "valid": len(tampered) == 0,
        "blocks": len(blocks),
        "tampered": tampered,
    }


def get_agent_stats(
    agent_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    """에이전트 잔액 + 최근 10건 보상 이력."""
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM reward_ledger WHERE agent_id = %s",
                (agent_id,),
            )
            ledger = cur.fetchone()
            cur.execute(
                """
                SELECT tr.*, pw.block_hash
                FROM task_reward tr
                JOIN proof_of_work pw ON pw.id = tr.pow_id
                WHERE tr.agent_id = %s
                ORDER BY tr.created_at DESC LIMIT 10
                """,
                (agent_id,),
            )
            history = [dict(r) for r in cur.fetchall()]

    return {
        "agent_id": agent_id,
        "ledger": dict(ledger) if ledger else {"balance": 0, "total_tasks": 0},
        "recent_rewards": history,
    }


def get_leaderboard(
    limit: int = 10,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    """보상 잔액 상위 에이전트 목록."""
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM reward_ledger ORDER BY balance DESC LIMIT %s",
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]


def get_project_pow(
    project_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    """프로젝트의 모든 PoW 블록."""
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT pw.*, tr.total_reward, tr.base_score, tr.speed_bonus
                FROM proof_of_work pw
                LEFT JOIN task_reward tr ON tr.pow_id = pw.id
                WHERE pw.project_id = %s
                ORDER BY pw.task_order ASC
                """,
                (project_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def get_project_replay(
    project_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    프로젝트 작업 타임라인 (Replay).
    각 Task의 실행 순서, 결과, 블록 해시를 시간 순으로 반환한다.
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    pw.task_order,
                    pw.task_title,
                    pw.ts,
                    pw.block_hash,
                    tr.exit_code,
                    tr.duration_s,
                    tr.risk_level,
                    tr.total_reward
                FROM proof_of_work pw
                LEFT JOIN task_reward tr ON tr.pow_id = pw.id
                WHERE pw.project_id = %s
                ORDER BY pw.task_order ASC
                """,
                (project_id,),
            )
            steps = [dict(r) for r in cur.fetchall()]

    total_reward = sum(s.get("total_reward") or 0 for s in steps)
    success = sum(1 for s in steps if (s.get("exit_code") or 1) == 0)

    return {
        "project_id": project_id,
        "steps_total": len(steps),
        "steps_success": success,
        "total_reward": round(total_reward, 4),
        "timeline": steps,
    }
