"""Pre-M7 Gap Resolution Smoke Test.

Coverage:
  A. LangGraph
     1. build_project_graph() compiles successfully
     2. run_project_graph() low-risk project: proceeds to execute (approval not needed)
     3. run_project_graph() high-risk project without review: stops at approval_blocked

  B. select_assets / resolve_targets
     4. POST /projects/{id}/select_assets — stage transitions to select_assets
     5. POST /projects/{id}/resolve_targets — stage transitions to resolve_targets
     6. Both stages linked back (targets list reflects asset links)

  C. Approval Engine
     7. GET /projects/{id}/approval — low risk: requires_approval=False, cleared=True
     8. GET /projects/{id}/approval — high risk, no review: requires_approval=True, cleared=False
     9. After submitting approved review: requires_approval=True, cleared=True
    10. POST /projects/{id}/execute — high risk without approval: 400 blocked

  D. Policy Engine (unit, no HTTP)
    11. get_policy("prod") → requires_approval includes "high"
    12. get_policy("lab") → requires_approval is empty
    13. check_policy(project_id, "execute") for low-risk project → allowed=True
    14. check_policy(project_id, "execute") for high-risk lab project → allowed=True (lab has no restriction)

  E. Regression — existing M5/M6 paths still work
    15. Full lifecycle (plan → execute → validate → report → close) for low-risk project via API
    16. Evidence gate still blocks close without evidence
    17. GET /playbooks returns seeded playbooks
    18. GET /tools returns seeded tools
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# ── Load apps via importlib ───────────────────────────────────────────────────

def load_app(app_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, app_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

manager_mod = load_app(ROOT / "apps" / "manager-api" / "src" / "main.py", "manager_api_main")
master_mod = load_app(ROOT / "apps" / "master-service" / "src" / "main.py", "master_service_main")

from fastapi.testclient import TestClient
manager = TestClient(manager_mod.app)
master = TestClient(master_mod.app)

passed = 0
failed = 0
_section = ""


def section(name: str):
    global _section
    _section = name
    print(f"\n=== {name} ===")


def check(label: str, cond: bool, detail: str = ""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))


def req(method: str, client: TestClient, path: str, **kwargs):
    fn = getattr(client, method)
    return fn(path, **kwargs)


# ── A. LangGraph ──────────────────────────────────────────────────────────────

section("A. LangGraph")

from packages.graph_runtime import build_project_graph, run_project_graph, VALID_TRANSITIONS

# 1. Graph compiles
try:
    g = build_project_graph()
    check("1. build_project_graph() compiles", True)
except Exception as e:
    check("1. build_project_graph() compiles", False, str(e))
    g = None

# 2. Valid transitions include new stages
check(
    "2. VALID_TRANSITIONS includes select_assets and resolve_targets",
    "select_assets" in VALID_TRANSITIONS and "resolve_targets" in VALID_TRANSITIONS,
)

# 3. plan → select_assets and plan → execute both allowed
check(
    "3. plan allows select_assets and execute (bypass)",
    "select_assets" in VALID_TRANSITIONS["plan"] and "execute" in VALID_TRANSITIONS["plan"],
)

# 4. run_project_graph low-risk: should reach execute (or beyond) without blocking
r = manager.post("/projects", json={"name": "langgraph-low-risk", "request_text": "test", "mode": "one_shot"})
prj_id_lg = r.json()["project"]["id"]
# Set risk_level to low by updating (use direct DB since no risk API)
import psycopg2
db_url = "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw"
with psycopg2.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE projects SET risk_level='low' WHERE id=%s", (prj_id_lg,))

state = run_project_graph(prj_id_lg, database_url=db_url)
check(
    "4. run_project_graph low-risk: not blocked by approval",
    state.get("stop_reason") != "approval_blocked",
    f"stop_reason={state.get('stop_reason')} error={state.get('error')}",
)

# 5. run_project_graph high-risk without review: stops at approval_blocked
r = manager.post("/projects", json={"name": "langgraph-high-risk", "request_text": "test", "mode": "one_shot"})
prj_id_hr = r.json()["project"]["id"]
with psycopg2.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE projects SET risk_level='high' WHERE id=%s", (prj_id_hr,))

state_hr = run_project_graph(prj_id_hr, database_url=db_url)
check(
    "5. run_project_graph high-risk no review: approval_blocked",
    state_hr.get("stop_reason") == "approval_blocked"
    or (state_hr.get("approval_required") and not state_hr.get("approval_cleared")),
    f"stop_reason={state_hr.get('stop_reason')} approval_required={state_hr.get('approval_required')}",
)


# ── B. select_assets / resolve_targets ───────────────────────────────────────

section("B. select_assets / resolve_targets Stages")

r = manager.post("/projects", json={"name": "stage-test", "request_text": "test stages", "mode": "one_shot"})
prj_sa = r.json()["project"]["id"]

# Plan first
manager.post(f"/projects/{prj_sa}/plan")

# 6. select_assets
r = manager.post(f"/projects/{prj_sa}/select_assets")
check(
    "6. POST /projects/{id}/select_assets → 200",
    r.status_code == 200,
    f"status={r.status_code} body={r.text[:200]}",
)
if r.status_code == 200:
    check(
        "7. stage transitions to select_assets",
        r.json().get("project", {}).get("current_stage") == "select_assets",
        str(r.json().get("project", {}).get("current_stage")),
    )

# 7. resolve_targets (no real subagent — failures allowed, stage must advance)
r = manager.post(f"/projects/{prj_sa}/resolve_targets")
check(
    "8. POST /projects/{id}/resolve_targets → 200",
    r.status_code == 200,
    f"status={r.status_code} body={r.text[:200]}",
)
if r.status_code == 200:
    check(
        "9. stage transitions to resolve_targets",
        r.json().get("project", {}).get("current_stage") == "resolve_targets",
        str(r.json().get("project", {}).get("current_stage")),
    )
    check(
        "10. resolve result has resolved/failed keys",
        "resolved" in r.json() and "failed" in r.json(),
    )


# ── C. Approval Engine ────────────────────────────────────────────────────────

section("C. Approval Engine")

# Low-risk project
r = manager.post("/projects", json={"name": "approval-low", "request_text": "t", "mode": "one_shot"})
prj_low = r.json()["project"]["id"]
with psycopg2.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE projects SET risk_level='low' WHERE id=%s", (prj_low,))

r = manager.get(f"/projects/{prj_low}/approval")
check("11. GET /approval low-risk → 200", r.status_code == 200)
if r.status_code == 200:
    data = r.json()
    check("12. low-risk: requires_approval=False", data.get("requires_approval") is False, str(data))
    check("13. low-risk: cleared=True", data.get("cleared") is True, str(data))

# High-risk project, no review
r = manager.post("/projects", json={"name": "approval-high", "request_text": "t", "mode": "one_shot"})
prj_high = r.json()["project"]["id"]
with psycopg2.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE projects SET risk_level='high' WHERE id=%s", (prj_high,))

r = manager.get(f"/projects/{prj_high}/approval")
check("14. GET /approval high-risk no review → 200", r.status_code == 200)
if r.status_code == 200:
    data = r.json()
    check("15. high-risk: requires_approval=True", data.get("requires_approval") is True, str(data))
    check("16. high-risk no review: cleared=False", data.get("cleared") is False, str(data))

# Try execute on high-risk without approval → should block
manager.post(f"/projects/{prj_high}/plan")
r = manager.post(f"/projects/{prj_high}/execute")
check(
    "17. POST /execute high-risk without approval → 400",
    r.status_code == 400,
    f"status={r.status_code}",
)

# Submit approved review and check again
master.post(f"/projects/{prj_high}/review", json={
    "reviewer_id": "master-agent",
    "review_status": "approved",
    "summary": "Approved for test",
})
r = manager.get(f"/projects/{prj_high}/approval")
if r.status_code == 200:
    check(
        "18. high-risk after approval: cleared=True",
        r.json().get("cleared") is True,
        str(r.json()),
    )

# Now execute should succeed
r = manager.post(f"/projects/{prj_high}/execute")
check(
    "19. POST /execute high-risk after approval → 200",
    r.status_code == 200,
    f"status={r.status_code} body={r.text[:200]}",
)


# ── D. Policy Engine Unit Tests ───────────────────────────────────────────────

section("D. Policy Engine (unit)")

from packages.policy_engine import get_policy, check_policy, PolicyViolation, enforce_policy

# 20. prod policy requires approval for high
prod_policy = get_policy("prod")
check(
    "20. get_policy('prod') requires_approval includes 'high'",
    "high" in prod_policy.get("requires_approval", []),
    str(prod_policy),
)

# 21. lab policy requires approval is empty
lab_policy = get_policy("lab")
check(
    "21. get_policy('lab') requires_approval is empty",
    lab_policy.get("requires_approval") == [],
    str(lab_policy),
)

# 22. check_policy on a low-risk project → allowed=True
r = manager.post("/projects", json={"name": "policy-low", "request_text": "t", "mode": "one_shot"})
prj_policy = r.json()["project"]["id"]
with psycopg2.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE projects SET risk_level='low' WHERE id=%s", (prj_policy,))

policy_result = check_policy(prj_policy, "execute", database_url=db_url)
check(
    "22. check_policy low-risk execute → allowed=True",
    policy_result["allowed"] is True,
    str(policy_result),
)

# 23. check_policy on high-risk project with prod env asset → violations
r = manager.post("/projects", json={"name": "policy-high-prod", "request_text": "t", "mode": "one_shot"})
prj_ph = r.json()["project"]["id"]
with psycopg2.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE projects SET risk_level='high' WHERE id=%s", (prj_ph,))
        # Create a prod env asset and link it
        asset_id = f"asset_policy_test_{prj_ph[:6]}"
        cur.execute(
            """
            INSERT INTO assets (id, name, type, platform, env, mgmt_ip, subagent_status)
            VALUES (%s, %s, 'vm', 'ubuntu', 'prod', '10.0.0.99', 'unknown')
            ON CONFLICT DO NOTHING
            """,
            (asset_id, f"policy-test-asset-{prj_ph[:6]}"),
        )
        cur.execute(
            "INSERT INTO project_assets (project_id, asset_id, scope_role) VALUES (%s, %s, 'primary') ON CONFLICT DO NOTHING",
            (prj_ph, asset_id),
        )

policy_result2 = check_policy(prj_ph, "execute", database_url=db_url)
check(
    "23. check_policy high-risk prod-env execute → allowed=False",
    policy_result2["allowed"] is False,
    str(policy_result2),
)

# 24. enforce_policy raises PolicyViolation for the above
try:
    enforce_policy(prj_ph, "execute", database_url=db_url)
    check("24. enforce_policy high-risk prod raises PolicyViolation", False, "no exception raised")
except PolicyViolation:
    check("24. enforce_policy high-risk prod raises PolicyViolation", True)


# ── E. Regression ─────────────────────────────────────────────────────────────

section("E. Regression — existing paths")

# 25. Full lifecycle low-risk project
r = manager.post("/projects", json={"name": "regression-lifecycle", "request_text": "test", "mode": "one_shot"})
prj_r = r.json()["project"]["id"]
with psycopg2.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE projects SET risk_level='low' WHERE id=%s", (prj_r,))

manager.post(f"/projects/{prj_r}/plan")
r_exec = manager.post(f"/projects/{prj_r}/execute")
check("25. low-risk execute (bypass) → 200", r_exec.status_code == 200, r_exec.text[:200])

manager.post(f"/projects/{prj_r}/validate")
manager.post(f"/projects/{prj_r}/report/finalize")

# Add evidence
manager.post(f"/projects/{prj_r}/evidence/minimal", json={
    "command": "echo regression", "stdout": "regression", "stderr": "", "exit_code": 0
})

r_close = manager.post(f"/projects/{prj_r}/close")
check("26. lifecycle close → 200", r_close.status_code == 200, r_close.text[:200])
check(
    "27. final stage is close",
    r_close.json().get("project", {}).get("current_stage") == "close",
)

# 26. Evidence gate still works
r = manager.post("/projects", json={"name": "regression-gate", "request_text": "t", "mode": "one_shot"})
prj_gate = r.json()["project"]["id"]
with psycopg2.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE projects SET risk_level='low' WHERE id=%s", (prj_gate,))
manager.post(f"/projects/{prj_gate}/plan")
manager.post(f"/projects/{prj_gate}/execute")
manager.post(f"/projects/{prj_gate}/validate")
manager.post(f"/projects/{prj_gate}/report/finalize")
r_close_no_ev = manager.post(f"/projects/{prj_gate}/close")
check(
    "28. evidence gate: close without evidence → 400",
    r_close_no_ev.status_code == 400,
    f"status={r_close_no_ev.status_code}",
)

# 27. Registry still works
r = manager.get("/playbooks")
check("29. GET /playbooks still works", r.status_code == 200 and "items" in r.json())

r = manager.get("/tools")
check("30. GET /tools still works", r.status_code == 200 and "items" in r.json())


# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n{'='*55}")
total = passed + failed
print(f"Pre-M7 Smoke: {passed}/{total} passed, {failed} failed")
if failed:
    sys.exit(1)
