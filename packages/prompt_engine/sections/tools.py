"""도구/스킬 섹션 — 활성화된 Tool/Skill을 프롬프트에 동적 삽입."""


def get_tools_section(
    tools: list[dict] | None = None,
    skills: list[dict] | None = None,
) -> str | None:
    """등록된 Tool/Skill 목록과 사용 가이드를 반환한다.

    Args:
        tools: [{"name": "run_command", "description": "...", "required_params": "command"}, ...]
        skills: [{"name": "probe_linux_host", "description": "..."}, ...]

    tools/skills가 모두 None이면 기본 내장 목록을 사용한다.
    """

    if tools is None:
        tools = _DEFAULT_TOOLS
    if skills is None:
        skills = _DEFAULT_SKILLS

    if not tools and not skills:
        return None

    lines = ["# Available Tools & Skills", ""]

    if tools:
        lines.append("## Tools (atomic operations)")
        lines.append("")
        lines.append("| Name | Description | Required Params |")
        lines.append("|------|-------------|----------------|")
        for t in tools:
            params = t.get("required_params", "-")
            lines.append(f"| `{t['name']}` | {t.get('description', '')} | {params} |")

    if skills:
        lines.append("")
        lines.append("## Skills (composite procedures)")
        lines.append("")
        lines.append("| Name | Description |")
        lines.append("|------|-------------|")
        for s in skills:
            lines.append(f"| `{s['name']}` | {s.get('description', '')} |")

    lines.extend([
        "",
        "## Execution Method Guide",
        "",
        "- Single status check (1 command) -> dispatch (mode=shell)",
        "  Example: systemctl status nginx, df -h, cat /etc/os-release",
        "- Multi-step work plan -> execute-plan (tasks array)",
        "  Example: server audit, package installation, security scan",
        "- Registered standard procedure -> playbook/run",
        "  Example: nightly_health_baseline_check, diagnose_web_latency",
        "",
        "When using a Playbook step:",
        '  {"step_order": 1, "step_type": "skill", "name": "probe_linux_host", "ref_id": "probe_linux_host"}',
        '  {"step_order": 2, "step_type": "tool", "name": "run_command", "ref_id": "run_command",',
        '   "params": {"command": "apt-get update -y"}}',
    ])

    return "\n".join(lines)


_DEFAULT_TOOLS = [
    {"name": "run_command", "description": "Execute arbitrary shell command", "required_params": "command"},
    {"name": "fetch_log", "description": "Read log file contents", "required_params": "log_path, lines"},
    {"name": "query_metric", "description": "Get CPU/memory/disk/network metrics", "required_params": "-"},
    {"name": "read_file", "description": "Read file contents", "required_params": "path"},
    {"name": "write_file", "description": "Write content to file", "required_params": "path, content"},
    {"name": "restart_service", "description": "Restart a systemd service", "required_params": "service"},
]

_DEFAULT_SKILLS = [
    {"name": "probe_linux_host", "description": "Comprehensive host info: hostname, uptime, kernel, disk, memory, processes, ports"},
    {"name": "check_tls_cert", "description": "Check TLS certificate validity and issuer"},
    {"name": "collect_web_latency_facts", "description": "Measure HTTP response time (3 samples)"},
    {"name": "monitor_disk_growth", "description": "Analyze disk usage trend for a directory"},
    {"name": "summarize_incident_timeline", "description": "Summarize system error log timeline"},
    {"name": "analyze_wazuh_alert_burst", "description": "Analyze Wazuh security alert burst causes"},
]
