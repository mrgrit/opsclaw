import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def load_manager_module():
    file_path = Path("apps/manager-api/src/main.py").resolve()
    spec = importlib.util.spec_from_file_location("oldclaw_manager_main", file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main() -> int:
    module = load_manager_module()
    app = module.create_app()
    client = TestClient(app)

    create_response = client.post(
        "/projects",
        json={
            "name": "http-smoke-project",
            "request_text": "http smoke",
            "mode": "one_shot",
        },
    )
    create_response.raise_for_status()
    created = create_response.json()
    project_id = created["project"]["id"]

    get_response = client.get(f"/projects/{project_id}")
    get_response.raise_for_status()
    loaded = get_response.json()

    execute_response = client.post(f"/projects/{project_id}/execute")
    execute_response.raise_for_status()
    executed = execute_response.json()

    report_response = client.get(f"/projects/{project_id}/report")
    report_response.raise_for_status()
    report = report_response.json()

    print("HTTP_PROJECT_ID:", project_id)
    print("HTTP_GET_STATUS:", loaded["project"]["status"])
    print("HTTP_EXECUTE_STAGE:", executed["result"]["project"]["current_stage"])
    print("HTTP_REPORT_ID:", report["report"]["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
