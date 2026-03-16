import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def load_manager_module():
    file_path = Path("apps/manager-api/src/main.py").resolve()
    spec = importlib.util.spec_from_file_location("opsclaw_manager_main", file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_manager_module()
    app = module.create_app()
    client = TestClient(app)

    targets_resp = client.get("/targets")
    targets_resp.raise_for_status()
    targets = targets_resp.json().get("items", [])
    if not targets:
        raise SystemExit(1)
    target_id = targets[0]["id"]

    create_resp = client.post(
        "/projects",
        json={"name": "target-http", "request_text": "target http", "mode": "one_shot"},
    )
    create_resp.raise_for_status()
    project_id = create_resp.json()["project"]["id"]

    link_resp = client.post(f"/projects/{project_id}/targets/{target_id}")
    link_resp.raise_for_status()

    proj_targets_resp = client.get(f"/projects/{project_id}/targets")
    proj_targets_resp.raise_for_status()
    proj_targets = proj_targets_resp.json().get("items", [])

    print("HTTP_TARGET_COUNT:", len(targets))
    print("HTTP_PROJECT_ID:", project_id)
    print("HTTP_LINKED_TARGET_ID:", target_id)
    print("HTTP_PROJECT_TARGET_COUNT:", len(proj_targets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
