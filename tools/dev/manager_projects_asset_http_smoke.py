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

    # GET assets
    assets_resp = client.get("/assets")
    assets_resp.raise_for_status()
    assets = assets_resp.json().get("items", [])
    asset_count = len(assets)
    if asset_count == 0:
        raise SystemExit(1)
    asset_id = assets[0]["id"]

    # create project
    create_resp = client.post(
        "/projects",
        json={"name": "asset-http-project", "request_text": "asset http", "mode": "one_shot"},
    )
    create_resp.raise_for_status()
    project_id = create_resp.json()["project"]["id"]

    # link asset
    link_resp = client.post(f"/projects/{project_id}/assets/{asset_id}")
    link_resp.raise_for_status()

    # get project assets
    proj_assets_resp = client.get(f"/projects/{project_id}/assets")
    proj_assets_resp.raise_for_status()
    proj_assets = proj_assets_resp.json().get("items", [])
    proj_asset_count = len(proj_assets)

    print("HTTP_ASSET_COUNT:", asset_count)
    print("HTTP_PROJECT_ID:", project_id)
    print("HTTP_LINKED_ASSET_ID:", asset_id)
    print("HTTP_PROJECT_ASSET_COUNT:", proj_asset_count)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
