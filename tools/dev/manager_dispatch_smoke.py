#!/usr/bin/env python3
"""
Smoke test: Manager -> SubAgent dispatch path
- Manager uses TestClient (no port needed)
- SubAgent must be running on :8001 (real HTTP)
"""
import importlib.util
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

SUBAGENT_URL = "http://127.0.0.1:8001"


def load_app(rel_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, Path(rel_path).resolve())
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(label: str, cond: bool, detail: str = "") -> None:
    mark = "OK" if cond else "FAIL"
    print(f"  [{mark}] {label}{': ' + detail if detail else ''}")
    if not cond:
        sys.exit(1)


def main() -> None:
    print("=== Manager Dispatch Smoke Test ===")

    mod = load_app("apps/manager-api/src/main.py", "opsclaw_manager_main")
    client = TestClient(mod.create_app())

    # Create project
    print("\n[1] POST /projects (create)")
    r = client.post("/projects", json={"name": "dispatch-smoke", "request_text": "test dispatch"})
    check("status 200", r.status_code == 200)
    project_id = r.json()["project"]["id"]
    check("project_id", bool(project_id))
    print(f"       project_id = {project_id}")

    # Plan
    print("\n[2] POST /projects/{id}/plan")
    r = client.post(f"/projects/{project_id}/plan")
    check("status 200", r.status_code == 200)
    check("stage=plan", r.json()["project"]["current_stage"] == "plan")

    # Execute
    print("\n[3] POST /projects/{id}/execute")
    r = client.post(f"/projects/{project_id}/execute")
    check("status 200", r.status_code == 200)
    check("stage=execute", r.json()["result"]["project"]["current_stage"] == "execute")

    # Dispatch command to subagent
    print("\n[4] POST /projects/{id}/dispatch (echo from subagent)")
    r = client.post(
        f"/projects/{project_id}/dispatch",
        json={"command": "echo 'hello from subagent' && uname -s", "subagent_url": SUBAGENT_URL, "timeout_s": 15},
    )
    check("status 200", r.status_code == 200, str(r.text[:300]))
    result = r.json()["result"]
    check("dispatch status=ok", result["status"] == "ok", str(result.get("status")))
    check("stdout contains 'hello'", "hello" in result["stdout"])
    check("exit_code=0", result["exit_code"] == 0)
    check("evidence_id exists", bool(result.get("evidence_id")))
    print(f"       evidence_id = {result['evidence_id']}")
    print(f"       stdout = {result['stdout'].strip()!r}")

    # Evidence auto-recorded
    print("\n[5] GET /projects/{id}/evidence (verify auto-recorded)")
    r = client.get(f"/projects/{project_id}/evidence")
    check("status 200", r.status_code == 200)
    items = r.json()["items"]
    check("at least 1 evidence item", len(items) >= 1, f"count={len(items)}")
    ev = items[-1]
    check("evidence body_ref contains command", "echo" in (ev.get("body_ref") or ""))

    print("\n=== Manager Dispatch Smoke: ALL PASSED ===")


if __name__ == "__main__":
    main()
