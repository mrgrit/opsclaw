"""
pow_service — Proof of Work & Blockchain Reward (M18)

Task 실행 결과를 해시 체인으로 기록하고 RL reward signal을 계산한다.

설계 원칙:
  - Task 단위 보상: Project보다 세밀, 데이터 풍부, RL credit assignment 명확
  - 자체 Merkle Chain: 외부 의존성 없음, 내부망 완전 독립
  - 자동 연동: execute-plan 완료 시 generate_proof() 자동 호출

체인 무결성 보장 (패치 M27):
  - ts_raw: 채굴 시 사용한 원본 timestamp 문자열을 TEXT로 저장
    → verify_chain에서 DB 세션 timezone 설정과 무관하게 동일 hash 재계산
  - linked-list traversal: ORDER BY ts 대신 prev_hash 링크를 따라 체인 재구성
    → 다른 세션에서 채굴한 블록이 섞여도 분기(orphan) 감지 후 longest-chain 선택
  - pg_advisory_xact_lock: 병렬 generate_proof() 호출 시 경쟁 조건 방지
"""
from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from psycopg2.extras import RealDictCursor

from packages.project_service import get_connection

# 첫 블록의 prev_hash (genesis)
GENESIS_HASH = "0" * 64

# PoW 난이도: leading zero hex 개수 (4 → 평균 65,536회 시행 ≈ 0.1초)
DEFAULT_DIFFICULTY = int(os.environ.get("OPSCLAW_POW_DIFFICULTY", "4"))
# 무한루프 방지 안전장치
MAX_NONCE = int(os.environ.get("OPSCLAW_POW_MAX_NONCE", "10000000"))


# ── 내부 유틸 ──────────────────────────────────────────────────────────────

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _mine_block(
    prev_hash: str, evidence_hash: str, ts: str, difficulty: int
) -> tuple[str, int]:
    """
    Nonce를 0부터 증가시키며 sha256(prev_hash + evidence_hash + ts + nonce)가
    difficulty개의 leading zero hex를 만족하는 값을 찾는다.

    Returns: (block_hash, nonce)
    """
    target_prefix = "0" * difficulty
    base = f"{prev_hash}{evidence_hash}{ts}"
    for nonce in range(MAX_NONCE):
        candidate = _sha256(f"{base}{nonce}")
        if candidate.startswith(target_prefix):
            return candidate, nonce
    # MAX_NONCE 도달 시 마지막 값 사용 (운영 안정성)
    return candidate, nonce


def _get_prev_hash(agent_id: str, database_url: str | None = None) -> str:
    """에이전트의 가장 최근 block_hash 반환. 없으면 GENESIS_HASH.
    created_at DESC 정렬: DB 서버 시간 기준으로 clock skew 없이 신뢰할 수 있음.
    """
    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT block_hash FROM proof_of_work WHERE agent_id = %s ORDER BY created_at DESC LIMIT 1",
                (agent_id,),
            )
            row = cur.fetchone()
            return row[0] if row else GENESIS_HASH


def _normalize_ts_fallback(ts_val: Any) -> str:
    """ts_raw 없는 레거시 블록의 ts 문자열 재구성.
    DB에서 읽은 datetime 객체를 항상 UTC +00:00 ISO 8601 포맷으로 변환.
    B-02 수정의 완전한 버전: aware datetime의 timezone offset도 정규화함.
    """
    if hasattr(ts_val, "isoformat"):
        dt = ts_val
        if dt.utcoffset() is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    return str(ts_val)


def _build_chain(all_blocks: dict[str, dict]) -> list[dict]:
    """prev_hash 링크를 따라 genesis에서 체인을 재구성.

    다른 세션에서 채굴한 블록이 DB에 섞여 분기(fork)가 발생해도
    longest-chain rule로 메인 체인을 선택하고, 나머지는 orphan으로 분류한다.

    Args:
        all_blocks: {block_hash: block_dict} 형태의 전체 블록 맵

    Returns:
        genesis → tip 순서로 정렬된 메인 체인 블록 목록
    """
    # prev_hash → [block] 역인덱스
    by_prev: dict[str, list[dict]] = {}
    for block in all_blocks.values():
        by_prev.setdefault(block["prev_hash"], []).append(block)

    # genesis에서 시작하는 linked-list 순회
    chain: list[dict] = []
    current_hash = GENESIS_HASH
    visited: set[str] = set()

    while current_hash in by_prev:
        nexts = by_prev[current_hash]
        if len(nexts) > 1:
            # 분기: ts_raw 기준 선입선출 (가장 먼저 채굴된 블록을 메인 체인으로)
            nexts.sort(key=lambda b: b.get("ts_raw") or str(b.get("ts", "")))
        next_block = nexts[0]
        bh = next_block["block_hash"]
        if bh in visited:
            break  # 순환 방지
        visited.add(bh)
        chain.append(next_block)
        current_hash = bh

    return chain


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

    M27 패치:
    - ts_raw: 채굴에 사용한 원본 timestamp 문자열을 TEXT로 저장
    - pg_advisory_xact_lock: 같은 agent_id로 병렬 호출 시 직렬화하여 체인 분기 방지
    - prev_hash 조회와 INSERT를 동일 트랜잭션 내에서 처리
    """
    ts = datetime.now(timezone.utc).isoformat()
    ts_raw = ts  # 채굴에 사용한 원본 문자열 — DB 왕복 후에도 변형 없이 재사용
    evidence_hash = _sha256(f"{stdout}{stderr}{exit_code}")
    difficulty = DEFAULT_DIFFICULTY
    pow_id = f"pow_{uuid.uuid4().hex[:12]}"
    reward = _calculate_reward(exit_code, duration_s, risk_level)
    tr_id = f"tr_{uuid.uuid4().hex[:12]}"

    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # advisory lock: agent_id 기반 정수 키 → 같은 agent 동시 채굴 직렬화
            # pg_advisory_xact_lock은 트랜잭션 종료 시 자동 해제됨
            lock_key = int(hashlib.sha256(agent_id.encode()).hexdigest()[:15], 16) % (2**63)
            cur.execute("SELECT pg_advisory_xact_lock(%s)", (lock_key,))

            # prev_hash 조회 (lock 획득 후, 같은 트랜잭션 내에서)
            cur.execute(
                "SELECT block_hash FROM proof_of_work WHERE agent_id = %s ORDER BY created_at DESC LIMIT 1",
                (agent_id,),
            )
            row = cur.fetchone()
            prev_hash = row["block_hash"] if row else GENESIS_HASH

            # 채굴 (lock 유지 중)
            block_hash, nonce = _mine_block(prev_hash, evidence_hash, ts, difficulty)

            # 1. PoW 블록 (ts_raw 포함)
            cur.execute(
                """
                INSERT INTO proof_of_work
                    (id, agent_id, project_id, task_order, task_title,
                     evidence_hash, prev_hash, block_hash, nonce, difficulty, ts, ts_raw)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (pow_id, agent_id, project_id, task_order, task_title,
                 evidence_hash, prev_hash, block_hash, nonce, difficulty, ts, ts_raw),
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
        # 트랜잭션 커밋 → advisory lock 자동 해제

    return {
        "pow_id": pow_id,
        "block_hash": block_hash,
        "nonce": nonce,
        "difficulty": difficulty,
        "reward": reward,
    }


def verify_chain(
    agent_id: str,
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    에이전트의 전체 블록 체인 무결성 검증.

    M27 패치:
    - ts_raw 우선 사용: DB 세션 timezone 설정과 무관하게 채굴 원본 문자열로 hash 재계산
    - linked-list traversal: ORDER BY ts 대신 prev_hash 링크로 체인 재구성
      → 다른 세션 채굴 블록이 섞여도 분기(orphan) 감지 후 longest-chain 검증
    - orphans: 메인 체인에서 벗어난 분기 블록 수 반환
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM proof_of_work WHERE agent_id = %s",
                (agent_id,),
            )
            all_blocks = {r["block_hash"]: dict(r) for r in cur.fetchall()}

    if not all_blocks:
        return {"agent_id": agent_id, "valid": True, "blocks": 0, "orphans": 0, "tampered": []}

    # prev_hash 링크를 따라 genesis에서 메인 체인 재구성 (분기 무관)
    blocks = _build_chain(all_blocks)
    orphan_count = len(all_blocks) - len(blocks)

    tampered = []
    for i, block in enumerate(blocks):
        # M27: ts_raw 우선 사용. 없으면 레거시 fallback (UTC 정규화)
        ts_str = block.get("ts_raw") or _normalize_ts_fallback(block["ts"])

        difficulty = block.get("difficulty") or 0
        nonce = block.get("nonce") or 0

        # 해시 재계산: difficulty>0이면 nonce 포함, 레거시(difficulty=0)는 기존 공식
        if difficulty > 0:
            expected_block_hash = _sha256(
                f"{block['prev_hash']}{block['evidence_hash']}{ts_str}{nonce}"
            )
        else:
            expected_block_hash = _sha256(
                f"{block['prev_hash']}{block['evidence_hash']}{ts_str}"
            )

        if expected_block_hash != block["block_hash"]:
            tampered.append({"id": block["id"], "reason": "block_hash_mismatch"})
            continue

        # difficulty 조건 검증 (신규 블록만)
        if difficulty > 0:
            target_prefix = "0" * difficulty
            if not block["block_hash"].startswith(target_prefix):
                tampered.append({"id": block["id"], "reason": "difficulty_not_met"})
                continue

        # prev_hash 체인 연결 검증 (linked-list 순서 기준)
        if i > 0:
            expected_prev = blocks[i - 1]["block_hash"]
            if block["prev_hash"] != expected_prev:
                tampered.append({"id": block["id"], "reason": "chain_broken"})

    return {
        "agent_id": agent_id,
        "valid": len(tampered) == 0,
        "blocks": len(blocks),
        "orphans": orphan_count,
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
