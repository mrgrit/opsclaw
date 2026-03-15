from packages.project_service import (
    create_project_record,
    execute_project_record,
    get_project_record,
    get_project_report,
)


def main() -> int:
    project = create_project_record(
        name="smoke-project",
        request_text="run smoke",
        mode="one_shot",
    )
    project_id = project["id"]
    loaded = get_project_record(project_id)
    executed = execute_project_record(project_id)
    report = get_project_report(project_id)

    print("PROJECT_ID:", project_id)
    print("PROJECT_STATUS:", loaded["status"])
    print("EXECUTE_STAGE:", executed["project"]["current_stage"])
    print("JOB_RUN_ID:", executed["job_run"]["id"])
    print("REPORT_ID:", report["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
