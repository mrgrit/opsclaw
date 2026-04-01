"""출력 형식 섹션 — 보고서, JSON 출력, 효율성 지시."""


def get_output_section(role: str) -> str:
    """역할에 따른 출력 형식/효율성 지시."""

    if role == "tutor":
        return (
            "# Output Rules\n\n"
            "- Answer in Korean, clearly and accurately\n"
            "- When the answer is in the provided context, cite the source\n"
            "- When speculating beyond the context, explicitly say so\n"
            "- Use markdown for formatting: headers, code blocks, tables\n"
            "- Keep explanations appropriate to the student's apparent level"
        )

    if role == "subagent":
        return (
            "# Output Rules\n\n"
            "Report results exactly as produced. Do not summarize, interpret, or filter stdout/stderr.\n"
            "If exit_code != 0, include the full stderr in your response."
        )

    # master / manager
    return (
        "# Output Rules\n\n"
        "## General\n"
        "- Lead with the answer or action, not the reasoning\n"
        "- If you can say it in one sentence, do not use three\n"
        "- Skip filler words, preamble, and unnecessary transitions\n"
        "- Korean for user communication, English for API calls and commands\n\n"
        "## completion-report Format\n"
        "```json\n"
        "{\n"
        '  "summary": "One sentence. Conclusion first, rationale second.",\n'
        '  "outcome": "success | partial | failed",\n'
        '  "work_details": ["Executed command and exit code only. No explanation."],\n'
        '  "issues": ["Failures and anomalies only. No speculation."],\n'
        '  "next_steps": ["Concrete actions only. No vague \'monitor\' statements."]\n'
        "}\n"
        "```\n\n"
        "## Evidence Interpretation\n"
        "- exit_code=0 → success. Do not reinterpret stdout.\n"
        "- exit_code!=0 → check stderr, summarize cause in one sentence.\n"
        "- success_rate < 1.0 → report only the failed evidence stderr.\n\n"
        "## Error Handling\n"
        "| Situation | Cause | Action |\n"
        "|-----------|-------|--------|\n"
        "| 400 stage must be plan | Skipped /plan before execute-plan | Call /plan then /execute first |\n"
        "| 404 project not found | Wrong project_id | GET /projects to re-check |\n"
        "| step status: failed | SubAgent command failed | Check evidence stderr, fix and retry |\n"
        "| overall: partial | Some steps failed | Keep successful results, retry failed only |\n"
        "| SubAgent unreachable | Network/service down | GET http://<host>:8002/health to diagnose |"
    )


def get_mission_output_section() -> str:
    """자율 미션(mission) 전용 JSON 출력 형식."""

    return (
        "# Output Format\n\n"
        "Each turn, respond with ONLY a JSON object. No markdown, no explanation.\n\n"
        "Example 1 — Execute a command:\n"
        '{"action":"check disk usage","command":"df -h","done":false}\n\n'
        "Example 2 — Handle error and retry:\n"
        '{"action":"retry with sudo","command":"echo 1 | sudo -S df -h","done":false}\n\n'
        "Example 3 — Mission complete:\n"
        '{"action":"done","command":"","done":true,"summary":"Disk usage normal at 45% on /dev/sda1"}\n\n'
        "Example 4 — Cannot proceed:\n"
        '{"action":"blocked","command":"","done":true,"summary":"Target port 8080 closed, cannot reach service"}'
    )


def get_explore_output_section() -> str:
    """서버 탐색(explore) 전용 JSON 출력 형식."""

    return (
        "# Output Format\n\n"
        "Respond ONLY with valid JSON:\n"
        "```json\n"
        "{\n"
        '  "watch_targets": [\n'
        '    {"name": "disk_usage", "command": "df -h / | tail -1", "interval_s": 60, "alert_pattern": "9[0-9]%"}\n'
        "  ],\n"
        '  "baseline": {"disk_pct": 45, "mem_pct": 62, "services_count": 12},\n'
        '  "security_risks": ["SSH root login enabled", "No fail2ban installed"],\n'
        '  "summary": "Server is a web frontend running nginx with moderate resource usage"\n'
        "}\n"
        "```"
    )


def get_daemon_output_section() -> str:
    """감시 데몬(daemon) THINK 단계 전용 JSON 출력 형식."""

    return (
        "# Output Format\n\n"
        "Respond ONLY with valid JSON:\n"
        "```json\n"
        "{\n"
        '  "severity": "normal | warning | critical",\n'
        '  "action": "Brief description of what was detected",\n'
        '  "command": "Remediation command to execute, or empty string if none",\n'
        '  "report": "One-sentence summary for the operations log"\n'
        "}\n"
        "```\n\n"
        "Example — Normal:\n"
        '{"severity":"normal","action":"no issues","command":"","report":"All metrics within baseline"}\n\n'
        "Example — Warning:\n"
        '{"severity":"warning","action":"high memory usage detected","command":"systemctl restart nginx","report":"Memory at 92%, restarting nginx"}\n\n'
        "Example — Critical:\n"
        '{"severity":"critical","action":"unauthorized SSH login attempt","command":"","report":"5 failed SSH logins from 10.0.0.99 in 60s"}'
    )
