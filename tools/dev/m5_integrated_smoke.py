#!/usr/bin/env python3
"""
Smoke test: M5 integrated - Evidence gate + Validation + Master Review
Uses TestClient for manager-api and master-service.
"""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient


def load_app(rel_path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, Path(rel_path).resolve())
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.create_app()


def check(label: str, cond: bool, detail: str = "") -> None:
    mark = "OK" if cond else "FAIL"
    print(f"  [{mark}] {label}{': ' + detail if detail else ''}")
    if not cond:
        sys.exit(1)


def main() -> None:
    print("=== M5 Integrated Smoke Test ===")
    manager = TestClient(load_app("apps/manager-api/src/main.py", "manager"))
    master  = TestClient(load_app("apps/master-service/src/main.py", "master"))

    # ── Setup: create project through to execute ─────────────────────────────
    print("\n[setup] create → plan → execute")
    r = manager.post("/projects", json={"name": "m5-smoke", "request_text": "m5 test"})
    check("create 200", r.status_code == 200)
    pid = r.json()["project"]["id"]
    manager.post(f"/projects/{pid}/plan")
    manager.post(f"/projects/{pid}/execute")
    print(f"       project_id = {pid}")

    # ── [1] Evidence gate: close without evidence must fail ───────────────────
    print("\n[1] Evidence gate: validate → report → close (no evidence → blocked)")
    manager.post(f"/projects/{pid}/validate")
    manager.post(f"/projects/{pid}/report/finalize")
    r = manager.post(f"/projects/{pid}/close")
    check("close blocked (400)", r.status_code == 400, str(r.text[:200]))
    check("error mentions evidence", "evidence" in r.json()["detail"]["message"].lower())

    # ── [2] Replan from report stage ─────────────────────────────────────────
    print("\n[2] Replan from report stage")
    r = manager.post(f"/projects/{pid}/replan", json={"reason": "missing evidence"})
    check("replan 200", r.status_code == 200)
    check("stage=plan after replan", r.json()["project"]["current_stage"] == "plan")

    # ── [3] Run again through execute, add evidence ───────────────────────────
    print("\n[3] Execute + add evidence")
    manager.post(f"/projects/{pid}/execute")
    r = manager.post(f"/projects/{pid}/evidence/minimal", json={
        "command": "echo hello", "stdout": "hello\n", "stderr": "", "exit_code": 0,
    })
    check("evidence created", r.status_code == 200)
    ev_id = r.json()["evidence"]["id"]
    print(f"       evidence_id = {ev_id}")

    # ── [4] Evidence summary ──────────────────────────────────────────────────
    print("\n[4] GET /projects/{id}/evidence/summary")
    r = manager.get(f"/projects/{pid}/evidence/summary")
    check("200", r.status_code == 200)
    s = r.json()
    check("total >= 1", s["total"] >= 1)
    check("success_count >= 1", s["success_count"] >= 1)
    print(f"       total={s['total']}  success={s['success_count']}")

    # ── [5] Validation check ──────────────────────────────────────────────────
    print("\n[5] POST /projects/{id}/validate/check (local command)")
    r = manager.post(f"/projects/{pid}/validate/check", json={
        "validator_name": "echo-check",
        "command": "echo 'validation ok'",
        "expected_contains": "validation ok",
        "expected_exit_code": 0,
    })
    check("200", r.status_code == 200, str(r.text[:200]))
    res = r.json()["result"]
    check("status=passed", res["status"] == "passed")
    check("evidence_id present", bool(res.get("evidence_id")))
    check("validation_run_id present", bool(res.get("validation_run_id")))

    # ── [6] Validation check failure ─────────────────────────────────────────
    print("\n[6] POST /projects/{id}/validate/check (expected fail)")
    r = manager.post(f"/projects/{pid}/validate/check", json={
        "validator_name": "fail-check",
        "command": "echo 'wrong output'",
        "expected_contains": "THIS WILL NOT MATCH",
        "expected_exit_code": 0,
    })
    check("200", r.status_code == 200)
    check("status=failed", r.json()["result"]["status"] == "failed")

    # ── [7] GET /projects/{id}/validations ───────────────────────────────────
    print("\n[7] GET /projects/{id}/validations")
    r = manager.get(f"/projects/{pid}/validations")
    check("200", r.status_code == 200)
    data = r.json()
    check("items >= 2", len(data["items"]) >= 2)
    check("has_failures (one failed)", data["validation_status"]["overall"] == "has_failures")
    print(f"       validation_status = {data['validation_status']['overall']}")

    # ── [8] Master review: needs_replan + auto_replan ─────────────────────────
    print("\n[8] Master review: needs_replan + auto_replan")
    r = master.post(f"/projects/{pid}/review", json={
        "reviewer_id": "master-agent-1",
        "review_status": "needs_replan",
        "summary": "validation failures detected",
        "auto_replan": True,
    })
    check("200", r.status_code == 200, str(r.text[:200]))
    d = r.json()
    check("review recorded", bool(d.get("review")))
    check("replan triggered", d.get("replan") is not None)
    check("stage=plan after replan", d["replan"]["current_stage"] == "plan")

    # ── [9] GET /projects/{id}/review ────────────────────────────────────────
    print("\n[9] GET /projects/{id}/review (master-service)")
    r = master.get(f"/projects/{pid}/review")
    check("200", r.status_code == 200)
    check("status=needs_replan", r.json()["review"]["status"] == "needs_replan")

    # ── [10] Master approve flow ──────────────────────────────────────────────
    print("\n[10] Full flow: execute → evidence → validate → report → master approve → close")
    manager.post(f"/projects/{pid}/execute")
    manager.post(f"/projects/{pid}/evidence/minimal", json={
        "command": "echo final", "stdout": "final\n", "stderr": "", "exit_code": 0,
    })
    manager.post(f"/projects/{pid}/validate")
    manager.post(f"/projects/{pid}/report/finalize")

    r = master.post(f"/projects/{pid}/review", json={
        "reviewer_id": "master-agent-1",
        "review_status": "approved",
        "summary": "all checks passed",
    })
    check("approve 200", r.status_code == 200)
    check("review=approved", r.json()["review"]["status"] == "approved")

    r = manager.post(f"/projects/{pid}/close")
    check("close 200 (with evidence)", r.status_code == 200, str(r.text[:200]))
    check("stage=close", r.json()["project"]["current_stage"] == "close")

    # ── [11] Master status endpoint ───────────────────────────────────────────
    print("\n[11] GET /projects/{id}/status (master-service)")
    r = master.get(f"/projects/{pid}/status")
    check("200", r.status_code == 200)
    d = r.json()
    check("project.stage=close", d["project"]["current_stage"] == "close")
    check("latest_review present", d["latest_review"] is not None)

    print("\n=== M5 Integrated Smoke: ALL PASSED ===")


if __name__ == "__main__":
    main()
