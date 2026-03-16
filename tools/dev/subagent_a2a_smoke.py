#!/usr/bin/env python3
"""
Smoke test: SubAgent A2A run_script direct call
Requires subagent-runtime running on :8001
"""
import sys

import httpx

BASE = "http://127.0.0.1:8001"


def check(label: str, cond: bool, detail: str = "") -> None:
    mark = "OK" if cond else "FAIL"
    print(f"  [{mark}] {label}{': ' + detail if detail else ''}")
    if not cond:
        sys.exit(1)


def main() -> None:
    print("=== SubAgent A2A Smoke Test ===")

    # health
    print("\n[1] GET /health")
    r = httpx.get(f"{BASE}/health", timeout=5)
    check("status 200", r.status_code == 200)
    check("service=subagent-runtime", r.json().get("service") == "subagent-runtime")

    # capabilities
    print("\n[2] GET /capabilities")
    r = httpx.get(f"{BASE}/capabilities", timeout=5)
    check("status 200", r.status_code == 200)
    caps = r.json().get("capabilities", [])
    check("run_script in capabilities", "run_script" in caps, str(caps))

    # run_script - success
    print("\n[3] POST /a2a/run_script (echo hello)")
    r = httpx.post(
        f"{BASE}/a2a/run_script",
        json={"project_id": "prj_smoke", "job_run_id": "job_smoke_1", "script": "echo hello", "timeout_s": 10},
        timeout=15,
    )
    check("status 200", r.status_code == 200)
    data = r.json()
    check("status=ok", data.get("status") == "ok", str(data.get("status")))
    check("stdout contains 'hello'", "hello" in data.get("detail", {}).get("stdout", ""))
    check("exit_code=0", data["detail"]["exit_code"] == 0)

    # run_script - error exit code
    print("\n[4] POST /a2a/run_script (exit 1)")
    r = httpx.post(
        f"{BASE}/a2a/run_script",
        json={"project_id": "prj_smoke", "job_run_id": "job_smoke_2", "script": "exit 1", "timeout_s": 10},
        timeout=15,
    )
    check("status 200", r.status_code == 200)
    data = r.json()
    check("status=error on non-zero exit", data.get("status") == "error")
    check("exit_code=1", data["detail"]["exit_code"] == 1)

    # run_script - multiline
    print("\n[5] POST /a2a/run_script (uname + hostname)")
    r = httpx.post(
        f"{BASE}/a2a/run_script",
        json={
            "project_id": "prj_smoke",
            "job_run_id": "job_smoke_3",
            "script": "uname -s && hostname",
            "timeout_s": 10,
        },
        timeout=15,
    )
    check("status 200", r.status_code == 200)
    data = r.json()
    check("status=ok", data["status"] == "ok")
    check("stdout not empty", bool(data["detail"]["stdout"].strip()))

    print("\n=== SubAgent A2A Smoke: ALL PASSED ===")


if __name__ == "__main__":
    main()
