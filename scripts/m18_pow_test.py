#!/usr/bin/env python3
"""
M18 Proof of Work & Blockchain Reward 통합 테스트

9구간 검증:
  1. 테이블 존재 확인 (proof_of_work, task_reward, reward_ledger)
  2. execute-plan 실행 → PoW 자동 생성 확인
  3. 블록 해시 직접 계산 → 무결성 검증
  4. task_reward 내용 확인 (base_score, speed_bonus, total_reward)
  5. reward_ledger 에이전트 잔액 업데이트 확인
  6. verify_chain API 정상 동작
  7. leaderboard API
  8. Replay 타임라인 API
  9. 위변조 감지 (블록 변조 후 verify 실패 확인)
"""
import hashlib, json, os, sys, time
from urllib.parse import quote
import httpx
import psycopg2
from psycopg2.extras import RealDictCursor

MANAGER = "http://localhost:8000"
SUBAGENT = "http://localhost:8002"
DB_URL = os.environ.get("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


def post(path, body=None):
    r = httpx.post(f"{MANAGER}{path}", json=body or {}, timeout=60.0)
    return r.json()

def get(path, params=None):
    r = httpx.get(f"{MANAGER}{path}", params=params, timeout=10.0)
    return r.json()

def db_conn():
    return psycopg2.connect(DB_URL)

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def check(label, condition, detail=""):
    icon = "✅" if condition else "❌"
    print(f"  {icon} {label}" + (f" — {detail}" if detail else ""))
    return condition

results = []
print("\n" + "=" * 60)
print("M18 Proof of Work & Blockchain Reward 통합 테스트")
print("=" * 60)

# ── 1. 테이블 존재 확인 ────────────────────────────────────────
print("\n[1] DB 테이블 존재 확인")
with db_conn() as conn:
    with conn.cursor() as cur:
        for tbl in ("proof_of_work", "task_reward", "reward_ledger"):
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)",
                (tbl,),
            )
            exists = cur.fetchone()[0]
            results.append(check(f"테이블: {tbl}", exists))

# ── 2. execute-plan → PoW 자동 생성 ──────────────────────────
print("\n[2] execute-plan 실행 → PoW 자동 생성")
proj = post("/projects", {
    "name": "m18-pow-test",
    "request_text": "PoW 테스트",
    "master_mode": "external",
})
pid = proj.get("project", {}).get("id", "")
results.append(check("프로젝트 생성", bool(pid), pid))

post(f"/projects/{pid}/plan")
post(f"/projects/{pid}/execute")

run = post(f"/projects/{pid}/execute-plan", {
    "tasks": [
        {"order": 1, "title": "현황 수집",   "instruction_prompt": "hostname && uptime", "risk_level": "low"},
        {"order": 2, "title": "디스크 확인", "instruction_prompt": "df -h",             "risk_level": "low"},
        {"order": 3, "title": "메모리 확인", "instruction_prompt": "free -m",           "risk_level": "medium"},
    ],
    "subagent_url": SUBAGENT,
    "dry_run": False,
})
overall = run.get("overall", "")
results.append(check("execute-plan 성공", overall == "success", overall))

time.sleep(0.5)  # DB 커밋 대기

pow_resp = get(f"/projects/{pid}/pow")
pow_blocks = pow_resp.get("blocks", [])
results.append(check("PoW 블록 3개 생성", len(pow_blocks) == 3, f"{len(pow_blocks)}개"))

# ── 3. 블록 해시 무결성 직접 검증 ─────────────────────────────
print("\n[3] 블록 해시 직접 계산 검증")
with db_conn() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM proof_of_work WHERE project_id=%s ORDER BY task_order ASC",
            (pid,),
        )
        blocks = [dict(r) for r in cur.fetchall()]

hash_ok = 0
for b in blocks:
    ts_str = b["ts"].isoformat() if hasattr(b["ts"], "isoformat") else str(b["ts"])
    expected = sha256(f"{b['prev_hash']}{b['evidence_hash']}{ts_str}")
    if expected == b["block_hash"]:
        hash_ok += 1

results.append(check(f"블록 해시 검증 ({hash_ok}/{len(blocks)})", hash_ok == len(blocks)))

# prev_hash 체인 연결 확인
chain_ok = True
for i in range(1, len(blocks)):
    if blocks[i]["prev_hash"] != blocks[i - 1]["block_hash"]:
        chain_ok = False
results.append(check("prev_hash 체인 연결", chain_ok))

# ── 4. task_reward 내용 확인 ──────────────────────────────────
print("\n[4] task_reward 보상 내용 확인")
with db_conn() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM task_reward WHERE project_id=%s ORDER BY task_order ASC",
            (pid,),
        )
        rewards = [dict(r) for r in cur.fetchall()]

results.append(check("task_reward 3개 생성", len(rewards) == 3, f"{len(rewards)}개"))
if rewards:
    r0 = rewards[0]
    results.append(check("base_score=+1.0 (성공)", r0.get("base_score") == 1.0, str(r0.get("base_score"))))
    results.append(check("total_reward > 0", (r0.get("total_reward") or 0) > 0, str(r0.get("total_reward"))))
    speed = r0.get("speed_bonus", 0)
    results.append(check("speed_bonus 계산됨", speed >= 0, f"{speed}"))

# ── 5. reward_ledger 잔액 확인 ────────────────────────────────
print("\n[5] reward_ledger 에이전트 잔액 확인")
agent_id = SUBAGENT
stats = get("/rewards/agents", params={"agent_id": agent_id})
ledger = stats.get("ledger", {})
results.append(check("reward_ledger 생성", bool(ledger.get("balance") is not None), str(ledger.get("balance"))))
results.append(check("total_tasks >= 3", (ledger.get("total_tasks") or 0) >= 3, str(ledger.get("total_tasks"))))
results.append(check("balance > 0", (ledger.get("balance") or 0) > 0, f"{ledger.get('balance'):.4f}"))

# ── 6. verify_chain API ───────────────────────────────────────
print("\n[6] verify_chain API")
vr = get("/pow/verify", params={"agent_id": agent_id})
result = vr.get("result", {})
results.append(check("chain valid=True", result.get("valid") is True, str(result.get("valid"))))
results.append(check("blocks >= 3", (result.get("blocks") or 0) >= 3, str(result.get("blocks"))))
results.append(check("tampered=[]", result.get("tampered") == [], str(result.get("tampered"))))

# ── 7. leaderboard ────────────────────────────────────────────
print("\n[7] Leaderboard API")
lb = get("/pow/leaderboard")
board = lb.get("leaderboard", [])
results.append(check("leaderboard 반환", len(board) > 0, f"{len(board)}개 에이전트"))
results.append(check("잔액 내림차순 정렬", all(
    board[i]["balance"] >= board[i + 1]["balance"]
    for i in range(len(board) - 1)
), ""))

# ── 8. Replay 타임라인 ────────────────────────────────────────
print("\n[8] Replay 타임라인 API")
replay = get(f"/projects/{pid}/replay")
results.append(check("steps_total=3", replay.get("steps_total") == 3, str(replay.get("steps_total"))))
results.append(check("total_reward > 0", (replay.get("total_reward") or 0) > 0, str(replay.get("total_reward"))))
timeline = replay.get("timeline", [])
results.append(check("timeline 순서 정렬", [t["task_order"] for t in timeline] == [1, 2, 3],
                      str([t["task_order"] for t in timeline])))

# ── 9. 위변조 감지 ────────────────────────────────────────────
print("\n[9] 위변조 감지 테스트")
if blocks:
    with db_conn() as conn:
        with conn.cursor() as cur:
            # 첫 블록의 block_hash를 변조
            tampered_hash = "a" * 64
            cur.execute(
                "UPDATE proof_of_work SET block_hash=%s WHERE id=%s",
                (tampered_hash, blocks[0]["id"]),
            )
        conn.commit()

    vr2 = get("/pow/verify", params={"agent_id": agent_id})
    r2 = vr2.get("result", {})
    results.append(check("변조 후 valid=False", r2.get("valid") is False, str(r2.get("valid"))))
    results.append(check("tampered 블록 탐지", len(r2.get("tampered", [])) > 0,
                          str(r2.get("tampered"))))

    # 원복
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE proof_of_work SET block_hash=%s WHERE id=%s",
                (blocks[0]["block_hash"], blocks[0]["id"]),
            )
        conn.commit()

# ── 결과 요약 ─────────────────────────────────────────────────
total = len(results)
passed = sum(results)
failed = total - passed
print(f"\n{'=' * 60}")
print(f"결과: {passed}/{total} 통과, {failed}건 실패")
print("✅ PASS" if failed == 0 else f"❌ FAIL — {failed}건 실패")
print("=" * 60)

out = {"total": total, "passed": passed, "failed": failed, "project_id": pid}
out_path = os.path.join(os.path.dirname(__file__), "m18_pow_result.json")
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)
print(f"결과 저장: {out_path}")
