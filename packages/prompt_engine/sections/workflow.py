"""작업 흐름 섹션 — 필수 작업 순서, stage 전이, API 사용법."""


def get_workflow_section(role: str) -> str:
    """역할에 따른 작업 흐름 섹션."""

    if role == "subagent":
        return (
            "# Workflow\n\n"
            "You receive commands from the Manager API. For each command:\n"
            "1. Execute the command exactly as given\n"
            "2. Capture stdout, stderr, and exit_code\n"
            "3. Return results in the standard response format\n"
            "4. Do not interpret results or take follow-up actions unless instructed"
        )

    if role == "tutor":
        return ""  # 튜터는 작업 흐름 불필요

    # master / manager 공통
    return (
        "# Workflow\n\n"
        "## Mandatory Execution Order\n\n"
        "All tasks must follow this sequence. Skipping stages causes a 400 error.\n\n"
        "```\n"
        "1. POST /projects              → Create project (master_mode: \"external\")\n"
        "2. POST /projects/{id}/plan    → Enter planning stage\n"
        "3. POST /projects/{id}/execute → Enter execution stage\n"
        "4. [Choose execution method]   → See below\n"
        "5. GET  /projects/{id}/evidence/summary → Check results\n"
        "6. POST /projects/{id}/completion-report → Submit report\n"
        "7. POST /projects/{id}/close   → Close project (optional)\n"
        "```\n\n"
        "## Execution Method Selection\n\n"
        "Choose the method that fits the task:\n\n"
        "### Method A — execute-plan (recommended for multi-step tasks)\n"
        "Use when: you analyzed the request and built a task list yourself.\n"
        "```json\n"
        "POST /projects/{id}/execute-plan\n"
        "{\"tasks\": [{\"order\": 1, \"title\": \"...\", \"instruction_prompt\": \"df -h\", "
        "\"risk_level\": \"low\"}], \"subagent_url\": \"http://localhost:8002\"}\n"
        "```\n\n"
        "### Method B — dispatch (single command, quick check)\n"
        "Use when: one-off status check or diagnostic.\n"
        "```json\n"
        "POST /projects/{id}/dispatch\n"
        "{\"command\": \"systemctl status nginx\", \"subagent_url\": \"http://localhost:8002\"}\n"
        "```\n\n"
        "### Method C — playbook/run (registered standard procedure)\n"
        "Use when: a matching playbook already exists.\n"
        "```\n"
        "GET /playbooks                              → Find matching playbook\n"
        "POST /projects/{id}/playbooks/{pb_id}       → Link playbook\n"
        "POST /projects/{id}/playbook/run            → Execute\n"
        "```\n\n"
        "Do NOT use dispatch mode=auto in production — LLM translation accuracy is not guaranteed.\n\n"
        "## Authentication\n\n"
        "All API calls require: `-H \"X-API-Key: $OPSCLAW_API_KEY\"`"
    )
