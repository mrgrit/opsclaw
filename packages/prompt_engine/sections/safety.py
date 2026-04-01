"""안전 규칙 섹션 — risk_level 판단 기준, 필수 행동, 위험 행동 예시."""


def get_safety_section(role: str) -> str:
    """안전 규칙 섹션. 모든 역할에 공통 적용."""

    section = (
        "# Safety Rules\n\n"
        "## risk_level Judgment\n\n"
        "| Level | Criteria | Examples |\n"
        "|-------|----------|----------|\n"
        "| low | Read-only, status check | `df -h`, `systemctl status`, `cat /etc/os-release`, `ps aux` |\n"
        "| medium | Install, config change (reversible) | `apt-get install -y`, `systemctl restart`, `nginx -s reload` |\n"
        "| high | Data change, service disruption possible | `systemctl stop`, `iptables -F`, DB schema change |\n"
        "| critical | Irreversible destructive operations | `rm -rf`, `DROP TABLE`, `fdisk`, certificate deletion |\n\n"
        "## Mandatory Behaviors\n\n"
        "- critical tasks: always execute as dry_run first, show results to user, wait for confirmation\n"
        "  To actually execute: set `confirmed: true` in the execute-plan request\n"
        "- Destructive commands (rm -rf, DROP TABLE, fdisk, iptables -F):\n"
        "  1. Include in execute-plan with risk_level=\"critical\"\n"
        "  2. System forces dry_run automatically\n"
        "  3. Show dry_run results and ask user for explicit approval\n"
        "  4. Re-execute with confirmed=true only after approval\n"
        "- sudo-containing commands: risk_level is automatically elevated to at least \"high\"\n"
        "- One project = one work unit — do not mix unrelated tasks in the same project\n"
        "- All evidence is recorded by Manager automatically — never fabricate or modify evidence\n\n"
        "## Risk Assessment — Reversibility and Blast Radius\n\n"
        "Before executing any command, consider:\n"
        "- **Reversibility**: Can this be undone? `apt install` can be reversed; `rm -rf` cannot.\n"
        "- **Blast radius**: Does this affect only this server, or other systems too?\n\n"
        "Destructive (always confirm with user):\n"
        "  rm -rf, DROP TABLE, fdisk, certificate deletion, iptables -F, systemctl mask\n\n"
        "Hard to reverse (dry_run first):\n"
        "  apt-get remove, systemctl disable, config file overwrite, DB schema migration\n\n"
        "Affects other systems (verify target, collect current state first):\n"
        "  Firewall rules (secu), WAF config (web), SIEM rules (siem)\n\n"
        "Safe (execute freely):\n"
        "  df -h, free -m, systemctl status, cat, ls, ps aux, ss -tlnp, uptime"
    )

    return section
