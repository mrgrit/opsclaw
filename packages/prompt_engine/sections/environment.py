"""환경 정보 섹션 — 인프라 매핑, SubAgent URL, 서비스 주소."""


_DEFAULT_INFRA = {
    "servers": [
        {"name": "opsclaw", "ip": "192.168.208.142", "role": "control plane (Manager API)", "subagent": "http://localhost:8002"},
        {"name": "secu", "ip": "192.168.208.150", "role": "nftables + Suricata IPS", "subagent": "http://192.168.208.150:8002"},
        {"name": "web", "ip": "192.168.208.151", "role": "BunkerWeb WAF + JuiceShop", "subagent": "http://192.168.208.151:8002"},
        {"name": "siem", "ip": "192.168.208.152", "role": "Wazuh 4.11.2", "subagent": "http://192.168.208.152:8002"},
        {"name": "dgx-spark", "ip": "192.168.0.105", "role": "GPU compute + Ollama LLM", "subagent": "http://192.168.0.105:8002"},
    ],
    "services": [
        {"name": "Manager API", "url": "http://localhost:8000", "role": "Main entry point"},
        {"name": "Master Service", "url": "http://localhost:8001", "role": "Native LLM planning (Mode A only)"},
        {"name": "SubAgent Runtime", "url": "http://localhost:8002", "role": "Command execution"},
    ],
}


def get_environment_section(
    server: str | None = None,
    infra: dict | None = None,
) -> str:
    """인프라 환경 정보 섹션을 반환한다.

    Args:
        server: 현재 대상 서버명 (강조 표시됨)
        infra: 커스텀 인프라 매핑 (None이면 기본값 사용)
    """
    infra = infra or _DEFAULT_INFRA
    lines = ["# Environment", ""]

    lines.append("## Infrastructure")
    lines.append("")
    lines.append("| Server | IP | Role | SubAgent URL |")
    lines.append("|--------|----|------|-------------|")
    for s in infra["servers"]:
        marker = " **[TARGET]**" if server and s["name"] == server else ""
        lines.append(f"| {s['name']}{marker} | {s['ip']} | {s['role']} | {s['subagent']} |")

    lines.append("")
    lines.append("## Service Addresses")
    lines.append("")
    lines.append("| Service | URL | Role |")
    lines.append("|---------|-----|------|")
    for svc in infra["services"]:
        lines.append(f"| {svc['name']} | {svc['url']} | {svc['role']} |")

    if server:
        # 대상 서버의 SubAgent URL을 명시적으로 강조
        target = next((s for s in infra["servers"] if s["name"] == server), None)
        if target:
            lines.extend([
                "",
                f"Current target: **{server}** ({target['ip']})",
                f"SubAgent URL for this target: `{target['subagent']}`",
            ])

    return "\n".join(lines)
