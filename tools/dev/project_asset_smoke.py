from packages.project_service import (
    get_assets,
    create_project_record,
    link_asset_to_project,
    get_project_assets,
    get_project_report_evidence_summary,
)


def main() -> int:
    # 1. asset list
    assets = get_assets()
    asset_count = len(assets)
    if asset_count == 0:
        # Insert a dummy asset for testing
        from packages.project_service import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO assets (id, name, type, platform, env, mgmt_ip, roles, subagent_status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        'ast_dummy',
                        'dummy_asset',
                        'dummy_type',
                        'dummy_platform',
                        'dev',
                        '127.0.0.1',
                        '[]',
                        'unknown',
                    ),
                )
                conn.commit()
        assets = get_assets()
        asset_count = len(assets)
    first_asset = assets[0]
    asset_id = first_asset["id"]

    # 2. create project
    project = create_project_record(name="asset-smoke", request_text="asset smoke", mode="one_shot")
    project_id = project["id"]

    # 3. link asset to project
    link_result = link_asset_to_project(project_id, asset_id)

    # 4. get linked assets
    linked_assets = get_project_assets(project_id)
    linked_count = len(linked_assets)

    # 5. summary includes assets
    summary = get_project_report_evidence_summary(project_id)
    summary_asset_count = len(summary.get("assets", []))

    print("ASSET_COUNT:", asset_count)
    print("PROJECT_ID:", project_id)
    print("LINKED_ASSET_ID:", asset_id)
    print("PROJECT_ASSET_COUNT:", linked_count)
    print("SUMMARY_ASSET_COUNT:", summary_asset_count)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
