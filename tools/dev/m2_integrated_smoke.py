import sys
from packages.project_service import (
    get_assets,
    create_project_record,
    plan_project_record,
    execute_project_record,
    validate_project_record,
    finalize_report_stage_record,
    create_minimal_evidence_record,
    get_evidence_for_project,
    link_asset_to_project,
    get_project_assets,
    close_project,
    get_project_report_evidence_summary,
    get_connection,
)


def ensure_dummy_asset():
    assets = get_assets()
    if assets:
        return assets[0]["id"]
    # insert dummy asset
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
    return 'ast_dummy'


def main() -> int:
    # 1. asset list
    asset_id = ensure_dummy_asset()
    assets = get_assets()
    asset_count = len(assets)

    # 2. project creation & lifecycle
    project = create_project_record(name='m2_integrated', request_text='integrated smoke', mode='one_shot')
    project_id = project['id']
    plan_project_record(project_id)
    execute_project_record(project_id)
    validate_project_record(project_id)
    finalize_report_stage_record(project_id)

    # 3. minimal evidence
    create_minimal_evidence_record(project_id=project_id, command='echo OK', stdout='OK', stderr='', exit_code=0)
    evidence = get_evidence_for_project(project_id)
    evidence_count = len(evidence)

    # 4. link asset to project
    link_asset_to_project(project_id, asset_id)
    linked_assets = get_project_assets(project_id)
    linked_asset_count = len(linked_assets)

    # 5. close project
    close_project(project_id)

    # 6. summary check
    summary = get_project_report_evidence_summary(project_id)
    report_id = summary.get('report', {}).get('id') if summary.get('report') else None

    print('M2_PROJECT_ID:', project_id)
    print('M2_ASSET_COUNT:', asset_count)
    print('M2_EVIDENCE_COUNT:', evidence_count)
    print('M2_LINKED_ASSET_ID:', asset_id)
    print('M2_PROJECT_ASSET_COUNT:', linked_asset_count)
    print('M2_FINAL_STAGE:', summary.get('project', {}).get('current_stage'))
    print('M2_FINAL_STATUS:', summary.get('project', {}).get('status'))
    print('M2_REPORT_ID:', report_id)
    return 0

if __name__ == '__main__':
    sys.exit(main())
