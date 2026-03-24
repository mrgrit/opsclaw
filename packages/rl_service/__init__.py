"""
rl_service — Lightweight Reinforcement Learning (Q-learning)

task_reward 데이터로 Q-table을 학습하여 작업 실행 전략(risk_level)을 추천한다.

설계:
  - State: (risk_level, agent_success_rate, task_order) → 48개 이산 상태
  - Action: risk_level 선택 → 4개 (low/medium/high/critical)
  - Reward: task_reward.total_reward
  - Q-learning: Q(s,a) ← Q(s,a) + α × (reward - Q(s,a))
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone
from typing import Any

import numpy as np
from psycopg2.extras import RealDictCursor

from packages.project_service import get_connection

# ── 상수 ──────────────────────────────────────────────────────────────────

NUM_STATES = 48          # 4 risk × 4 success_rate × 3 task_order
NUM_ACTIONS = 4          # low, medium, high, critical
ACTION_LABELS = ["low", "medium", "high", "critical"]
RISK_MAP = {"low": 0, "medium": 1, "high": 2, "critical": 3}

DEFAULT_POLICY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "rl_policy.json"
)
DEFAULT_ALPHA = 0.1      # learning rate
DEFAULT_GAMMA = 0.95     # discount factor (미래 확장용)
DEFAULT_EPSILON = 0.15   # exploration rate
MIN_EPISODES = 5         # 최소 에피소드 수


# ── 내부 유틸 ─────────────────────────────────────────────────────────────

def _encode_state(risk_level: str, success_rate: float, task_order: int) -> int:
    """(risk_level, success_rate, task_order) → 0~47 정수 인덱스."""
    risk_idx = RISK_MAP.get(risk_level, 1)
    sr_bucket = min(int(success_rate * 4), 3)
    order_bucket = 0 if task_order <= 3 else (1 if task_order <= 7 else 2)
    return risk_idx * 12 + sr_bucket * 3 + order_bucket


def _get_agent_success_rate(
    agent_id: str, database_url: str | None = None
) -> float:
    """에이전트의 성공률. 기록 없으면 0.5."""
    with get_connection(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT success_count, total_tasks FROM reward_ledger WHERE agent_id = %s",
                (agent_id,),
            )
            row = cur.fetchone()
            if not row or row[1] == 0:
                return 0.5
            return row[0] / row[1]


def _load_q_table(
    path: str | None = None,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Q-table + visit_counts + 메타데이터 로드. 파일 없으면 초기화."""
    path = path or DEFAULT_POLICY_PATH
    try:
        with open(path, "r") as f:
            data = json.load(f)
        q = np.array(data["q_table"], dtype=np.float64)
        vc = np.array(data.get("visit_counts", np.zeros((NUM_STATES, NUM_ACTIONS)).tolist()), dtype=np.float64)
        meta = data.get("metadata", {})
        return q, vc, meta
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return (
            np.zeros((NUM_STATES, NUM_ACTIONS), dtype=np.float64),
            np.zeros((NUM_STATES, NUM_ACTIONS), dtype=np.float64),
            {},
        )


def _save_q_table(
    q_table: np.ndarray, metadata: dict, path: str | None = None,
    visit_counts: np.ndarray | None = None,
) -> str:
    """Q-table + visit_counts를 JSON으로 저장."""
    path = path or DEFAULT_POLICY_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "q_table": q_table.tolist(),
        "visit_counts": visit_counts.tolist() if visit_counts is not None else np.zeros((NUM_STATES, NUM_ACTIONS)).tolist(),
        "metadata": metadata,
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    return path


# ── 공개 API ──────────────────────────────────────────────────────────────

def collect_episodes(
    limit: int = 500,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    """
    task_reward + reward_ledger에서 RL 에피소드 (state, action, reward) 추출.
    """
    sql = """
        SELECT
            tr.risk_level,
            tr.task_order,
            tr.total_reward,
            tr.agent_id,
            COALESCE(rl.success_count, 0) AS success_count,
            COALESCE(rl.total_tasks, 1)   AS total_tasks
        FROM task_reward tr
        LEFT JOIN reward_ledger rl ON rl.agent_id = tr.agent_id
        ORDER BY tr.created_at DESC
        LIMIT %s
    """
    with get_connection(database_url) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (limit,))
            rows = [dict(r) for r in cur.fetchall()]

    episodes = []
    for r in rows:
        success_rate = r["success_count"] / max(r["total_tasks"], 1)
        state = _encode_state(r["risk_level"], success_rate, r["task_order"])
        action = RISK_MAP.get(r["risk_level"], 1)
        episodes.append({
            "state": state,
            "action": action,
            "reward": float(r["total_reward"]),
            "agent_id": r["agent_id"],
        })
    return episodes


def train(
    alpha: float = DEFAULT_ALPHA,
    gamma: float = DEFAULT_GAMMA,
    epsilon: float = DEFAULT_EPSILON,
    limit: int = 500,
    policy_path: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    에피소드 수집 → Q-table 업데이트 → JSON 저장.

    Q-learning 업데이트 (terminal episode):
        Q(s,a) ← Q(s,a) + α × (reward - Q(s,a))
    """
    episodes = collect_episodes(limit=limit, database_url=database_url)
    if len(episodes) < MIN_EPISODES:
        return {
            "status": "skipped",
            "reason": f"에피소드 부족 ({len(episodes)} < {MIN_EPISODES})",
            "episodes_found": len(episodes),
        }

    q_table, visit_counts, meta = _load_q_table(policy_path)
    updates = 0

    for ep in episodes:
        s, a, r = ep["state"], ep["action"], ep["reward"]
        old_q = q_table[s, a]
        q_table[s, a] = old_q + alpha * (r - old_q)
        visit_counts[s, a] += 1
        updates += 1

    train_count = meta.get("train_count", 0) + 1
    total_episodes = meta.get("episodes_trained", 0) + len(episodes)
    new_meta = {
        "episodes_trained": total_episodes,
        "train_count": train_count,
        "last_trained": datetime.now(timezone.utc).isoformat(),
        "alpha": alpha,
        "gamma": gamma,
        "epsilon": epsilon,
    }
    saved_path = _save_q_table(q_table, new_meta, policy_path, visit_counts=visit_counts)

    return {
        "status": "ok",
        "episodes_used": len(episodes),
        "updates": updates,
        "train_count": train_count,
        "policy_path": saved_path,
    }


def recommend(
    agent_id: str,
    risk_level: str = "medium",
    task_order: int = 1,
    exploration: str = "greedy",  # "greedy" | "ucb1" | "epsilon"
    ucb_c: float = 1.0,          # UCB1 탐색 계수
    policy_path: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    Q-table 기반 최적 action(risk_level) 추천.

    exploration:
      greedy — Q-value 최대 action (기본)
      ucb1   — UCB1 탐색: Q(s,a) + c√(ln(N)/n(s,a))
      epsilon — ε-greedy: ε 확률로 랜덤
    """
    q_table, visit_counts, meta = _load_q_table(policy_path)
    success_rate = _get_agent_success_rate(agent_id, database_url)
    state = _encode_state(risk_level, success_rate, task_order)

    q_values = q_table[state]

    if exploration == "ucb1":
        total_visits = max(float(visit_counts.sum()), 1.0)
        ucb_values = np.zeros(NUM_ACTIONS, dtype=np.float64)
        for a in range(NUM_ACTIONS):
            n_sa = max(float(visit_counts[state, a]), 1.0)
            ucb_bonus = ucb_c * math.sqrt(math.log(total_visits) / n_sa)
            ucb_values[a] = q_values[a] + ucb_bonus
        best_action = int(np.argmax(ucb_values))
        extra = {"exploration": "ucb1", "ucb_c": ucb_c, "ucb_values": {
            ACTION_LABELS[i]: round(float(ucb_values[i]), 4) for i in range(NUM_ACTIONS)
        }}
    elif exploration == "epsilon":
        eps = meta.get("epsilon", DEFAULT_EPSILON)
        if np.random.random() < eps:
            best_action = int(np.random.randint(NUM_ACTIONS))
        else:
            best_action = int(np.argmax(q_values))
        extra = {"exploration": "epsilon", "epsilon": eps}
    else:
        best_action = int(np.argmax(q_values))
        extra = {"exploration": "greedy"}

    return {
        "agent_id": agent_id,
        "state": state,
        "state_desc": {
            "risk_level": risk_level,
            "success_rate": round(success_rate, 4),
            "task_order": task_order,
        },
        "recommended_risk_level": ACTION_LABELS[best_action],
        "q_values": {
            ACTION_LABELS[i]: round(float(q_values[i]), 4)
            for i in range(NUM_ACTIONS)
        },
        "visit_counts": {
            ACTION_LABELS[i]: int(visit_counts[state, i])
            for i in range(NUM_ACTIONS)
        },
        "confidence": "trained" if meta.get("train_count", 0) > 0 else "untrained",
        **extra,
    }


def get_policy_stats(
    policy_path: str | None = None,
) -> dict[str, Any]:
    """현재 Q-table 통계, visit count, 학습 메타데이터."""
    q_table, visit_counts, meta = _load_q_table(policy_path)
    nonzero = int(np.count_nonzero(q_table))
    total_cells = NUM_STATES * NUM_ACTIONS
    visited = int(np.count_nonzero(visit_counts))
    unvisited = total_cells - visited
    return {
        "num_states": NUM_STATES,
        "num_actions": NUM_ACTIONS,
        "action_labels": ACTION_LABELS,
        "nonzero_entries": nonzero,
        "coverage_pct": round(nonzero / total_cells * 100, 1),
        "q_table_mean": round(float(np.mean(q_table)), 4),
        "q_table_max": round(float(np.max(q_table)), 4),
        "q_table_min": round(float(np.min(q_table)), 4),
        # M24: visit count 통계
        "visit_counts_total": int(visit_counts.sum()),
        "visited_count": visited,
        "unvisited_count": unvisited,
        "coverage_by_visits_pct": round(visited / total_cells * 100, 1),
        **meta,
    }
