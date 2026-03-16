#!/usr/bin/env python3
"""
Smoke test: Asset CRUD + onboard via Manager API (TestClient)
"""
import importlib.util
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient


def load_app():
    spec = importlib.util.spec_from_file_location(
        "opsclaw_manager_main",
        Path("apps/manager-api/src/main.py").resolve(),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.create_app()


def check(label: str, cond: bool, detail: str = "") -> None:
    mark = "OK" if cond else "FAIL"
    print(f"  [{mark}] {label}{': ' + detail if detail else ''}")
    if not cond:
        sys.exit(1)


def main() -> None:
    print("=== Manager Asset CRUD HTTP Smoke Test ===")
    client = TestClient(load_app())
    suffix = uuid.uuid4().hex[:6]
    name = f"http-smoke-{suffix}"

    # [1] POST /assets (create)
    print("\n[1] POST /assets")
    r = client.post("/assets", json={
        "name": name, "type": "vm", "platform": "linux",
        "env": "dev", "mgmt_ip": "127.0.0.1", "expected_subagent_port": 8001,
    })
    check("status 200", r.status_code == 200, str(r.text[:200]))
    asset_id = r.json()["asset"]["id"]
    check("asset_id present", bool(asset_id))
    print(f"       asset_id = {asset_id}")

    # [2] GET /assets
    print("\n[2] GET /assets")
    r = client.get("/assets")
    check("status 200", r.status_code == 200)
    check("list not empty", len(r.json()["items"]) >= 1)

    # [3] GET /assets/{id}
    print("\n[3] GET /assets/{id}")
    r = client.get(f"/assets/{asset_id}")
    check("status 200", r.status_code == 200)
    check("id matches", r.json()["asset"]["id"] == asset_id)

    # [4] PUT /assets/{id}
    print("\n[4] PUT /assets/{id} (update platform)")
    r = client.put(f"/assets/{asset_id}", json={"platform": "ubuntu"})
    check("status 200", r.status_code == 200)
    check("platform updated", r.json()["asset"]["platform"] == "ubuntu")

    # [5] POST /assets/{id}/resolve
    print("\n[5] POST /assets/{id}/resolve")
    r = client.post(f"/assets/{asset_id}/resolve")
    check("status 200", r.status_code == 200)
    result = r.json()
    check("target present", "target" in result)
    print(f"       subagent_status = {result.get('subagent_status')}")

    # [6] GET /assets/{id}/health
    print("\n[6] GET /assets/{id}/health")
    r = client.get(f"/assets/{asset_id}/health")
    check("status 200", r.status_code == 200)
    check("subagent_status present", "subagent_status" in r.json())

    # [7] POST /assets/onboard (existing)
    print("\n[7] POST /assets/onboard (existing identity)")
    r = client.post("/assets/onboard", json={
        "name": name, "type": "vm", "platform": "linux",
        "env": "dev", "mgmt_ip": "127.0.0.1",
    })
    check("status 200", r.status_code == 200)
    check("action=existing", r.json()["action"] == "existing")

    # [8] POST /assets/onboard (new)
    print("\n[8] POST /assets/onboard (new asset)")
    new_name = f"http-new-{suffix}"
    r = client.post("/assets/onboard", json={
        "name": new_name, "type": "server", "platform": "linux",
        "env": "prod", "mgmt_ip": "127.0.0.1",
    })
    check("status 200", r.status_code == 200)
    check("action=created", r.json()["action"] == "created")
    new_id = r.json()["asset"]["id"]

    # [9] 409 conflict
    print("\n[9] POST /assets conflict")
    r = client.post("/assets", json={
        "name": name, "type": "vm", "platform": "linux",
        "env": "dev", "mgmt_ip": "127.0.0.1",
    })
    check("status 409", r.status_code == 409)

    # [10] DELETE /assets/{id}
    print("\n[10] DELETE /assets/{id}")
    r = client.delete(f"/assets/{asset_id}")
    check("status 200", r.status_code == 200)
    r = client.delete(f"/assets/{new_id}")
    check("status 200 (new)", r.status_code == 200)
    r = client.get(f"/assets/{asset_id}")
    check("404 after delete", r.status_code == 404)

    print("\n=== Manager Asset CRUD HTTP Smoke: ALL PASSED ===")


if __name__ == "__main__":
    main()
