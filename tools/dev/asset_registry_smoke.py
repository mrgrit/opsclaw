#!/usr/bin/env python3
"""
Smoke test: Asset Registry CRUD + resolve + onboard (direct service call)
Requires DATABASE_URL env var.
"""
import sys
import uuid

sys.path.insert(0, ".")

from packages.asset_registry import (
    AssetConflictError,
    AssetNotFoundError,
    check_asset_health,
    create_asset,
    delete_asset,
    get_asset,
    get_asset_by_name,
    list_assets,
    onboard_asset,
    resolve_target_from_asset,
    update_asset,
)


def check(label: str, cond: bool, detail: str = "") -> None:
    mark = "OK" if cond else "FAIL"
    print(f"  [{mark}] {label}{': ' + detail if detail else ''}")
    if not cond:
        sys.exit(1)


def main() -> None:
    print("=== Asset Registry Smoke Test ===")
    suffix = uuid.uuid4().hex[:6]
    name = f"smoke-asset-{suffix}"

    # [1] Create
    print("\n[1] create_asset")
    asset = create_asset(
        name=name, type="vm", platform="linux", env="dev",
        mgmt_ip="127.0.0.1", expected_subagent_port=8001,
    )
    asset_id = asset["id"]
    check("id starts with asset_", asset_id.startswith("asset_"))
    check("name matches", asset["name"] == name)
    check("subagent_status=unknown", asset["subagent_status"] == "unknown")
    print(f"       asset_id = {asset_id}")

    # [2] Get
    print("\n[2] get_asset")
    fetched = get_asset(asset_id)
    check("id matches", fetched["id"] == asset_id)

    # [3] Get by name
    print("\n[3] get_asset_by_name")
    by_name = get_asset_by_name(name)
    check("id matches", by_name["id"] == asset_id)

    # [4] List
    print("\n[4] list_assets (env=dev)")
    items = list_assets(env="dev")
    check("at least 1 item", len(items) >= 1)
    check("our asset in list", any(a["id"] == asset_id for a in items))

    # [5] Update
    print("\n[5] update_asset (platform -> ubuntu)")
    updated = update_asset(asset_id, {"platform": "ubuntu"})
    check("platform updated", updated["platform"] == "ubuntu")

    # [6] Conflict check
    print("\n[6] create_asset conflict (same name)")
    conflict_raised = False
    try:
        create_asset(name=name, type="vm", platform="linux", env="dev", mgmt_ip="127.0.0.2")
    except AssetConflictError:
        conflict_raised = True
    check("AssetConflictError raised", conflict_raised)

    # [7] Resolve target (subagent on 127.0.0.1:8001)
    print("\n[7] resolve_target_from_asset")
    result = resolve_target_from_asset(asset_id)
    check("asset_id matches", result["asset_id"] == asset_id)
    check("target record present", "target" in result)
    check("subagent_url set", "127.0.0.1:8001" in result["subagent_url"])
    # Health may be ok or failed depending on whether subagent is running
    print(f"       subagent_status = {result['subagent_status']}")
    print(f"       target health   = {result['target']['health']}")

    # [8] Check health
    print("\n[8] check_asset_health")
    health = check_asset_health(asset_id)
    check("asset_id matches", health["asset_id"] == asset_id)
    check("subagent_url set", bool(health["subagent_url"]))
    print(f"       subagent_status = {health['subagent_status']}")

    # [9] Onboard (identity check - asset already exists)
    print("\n[9] onboard_asset (existing - identity check)")
    onboard_result = onboard_asset(
        name=name, type="vm", platform="linux", env="dev", mgmt_ip="127.0.0.1",
    )
    check("action=existing", onboard_result["action"] == "existing")
    check("asset_id matches", onboard_result["asset"]["id"] == asset_id)

    # [10] Onboard new asset
    print("\n[10] onboard_asset (new)")
    new_name = f"smoke-new-{suffix}"
    new_result = onboard_asset(
        name=new_name, type="vm", platform="linux", env="dev", mgmt_ip="127.0.0.1",
        expected_subagent_port=8001,
    )
    check("action=created", new_result["action"] == "created")
    check("asset created", bool(new_result["asset"]["id"]))
    new_asset_id = new_result["asset"]["id"]

    # [11] Not found error
    print("\n[11] get_asset not found")
    not_found = False
    try:
        get_asset("asset_doesnotexist")
    except AssetNotFoundError:
        not_found = True
    check("AssetNotFoundError raised", not_found)

    # [12] Delete
    print("\n[12] delete_asset")
    delete_asset(asset_id)
    delete_asset(new_asset_id)
    gone = False
    try:
        get_asset(asset_id)
    except AssetNotFoundError:
        gone = True
    check("asset deleted", gone)

    print("\n=== Asset Registry Smoke: ALL PASSED ===")


if __name__ == "__main__":
    main()
