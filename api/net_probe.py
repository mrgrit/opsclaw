import re
from typing import Any, Dict, List

from a2a import run_script


CONTAINER_NET_PATTERNS = [
    r"^docker",
    r"^br-",
    r"^veth",
]

PRIVATE_CONTAINER_NET = [
    "172.17.",
]


def _normalize_iface(name: str) -> str:
    if "@" in name:
        return name.split("@")[0]
    return name


def _run(subagent_url: str, script: str, timeout_s: int):

    res = run_script(
        subagent_url,
        {
            "run_id": "net-probe",
            "target_id": "probe",
            "script": script,
            "timeout_s": timeout_s,
            "approval_required": False,
            "evidence_requests": [],
        },
        timeout_s=timeout_s + 5,
    )

    if res.get("exit_code") != 0:
        return "", res

    return res.get("stdout", ""), res


def _looks_container_interface(iface: str) -> bool:

    for p in CONTAINER_NET_PATTERNS:
        if re.match(p, iface):
            return True

    return False


def _looks_container_ip(ip: str) -> bool:

    for p in PRIVATE_CONTAINER_NET:
        if ip.startswith(p):
            return True

    return False


def collect_net_probe(
    *,
    project_id: str,
    target_id: str,
    subagent_url: str,
    timeout_s: int = 20,
) -> Dict[str, Any]:

    facts: Dict[str, Any] = {
        "interfaces": [],
        "normalized_interfaces": [],
        "ipv4_addresses": {},
        "default_route_dev": None,
        "routes_summary": [],
        "candidate_iface_in": None,
        "candidate_iface_out": None,
        "network_context": None,
        "confidence": "low",
        "needs_human_confirmation": True,
    }

    rationale: List[str] = []
    evidence_refs: List[Dict[str, Any]] = []

    # interfaces
    out, ev = _run(
        subagent_url,
        "ip -o link show | awk -F': ' '{print $2}'",
        timeout_s,
    )

    if out:

        raw = [x.strip() for x in out.splitlines() if x.strip()]
        norm = [_normalize_iface(i) for i in raw]

        facts["interfaces"] = raw
        facts["normalized_interfaces"] = norm

        rationale.append(f"detected {len(raw)} interfaces")

        evidence_refs.append(
            {
                "kind": "run_script",
                "fact_key": "interfaces",
                "stdout": out,
                "stderr": ev.get("stderr"),
            }
        )

    # ipv4
    out, ev = _run(
        subagent_url,
        "ip -o -4 addr show",
        timeout_s,
    )

    if out:

        for l in out.splitlines():

            parts = l.split()

            iface = _normalize_iface(parts[1])
            ip = parts[3]

            facts["ipv4_addresses"].setdefault(iface, []).append(ip)

        rationale.append("collected ipv4 addresses")

        evidence_refs.append(
            {
                "kind": "run_script",
                "fact_key": "ipv4_addresses",
                "stdout": out,
                "stderr": ev.get("stderr"),
            }
        )

    # default route
    out, ev = _run(
        subagent_url,
        "ip route show default",
        timeout_s,
    )

    if out:

        parts = out.split()

        if "dev" in parts:

            idx = parts.index("dev")
            facts["default_route_dev"] = _normalize_iface(parts[idx + 1])

        rationale.append("detected default route")

        evidence_refs.append(
            {
                "kind": "run_script",
                "fact_key": "default_route",
                "stdout": out,
                "stderr": ev.get("stderr"),
            }
        )

    # routes
    out, ev = _run(
        subagent_url,
        "ip route",
        timeout_s,
    )

    if out:

        routes = [x.strip() for x in out.splitlines() if x.strip()]
        facts["routes_summary"] = routes[:20]

        rationale.append("collected route table")

        evidence_refs.append(
            {
                "kind": "run_script",
                "fact_key": "routes_summary",
                "stdout": out,
                "stderr": ev.get("stderr"),
            }
        )

    # network context 판단
    container_like = False

    for iface in facts["normalized_interfaces"]:

        if _looks_container_interface(iface):
            container_like = True

    for ips in facts["ipv4_addresses"].values():
        for ip in ips:
            if _looks_container_ip(ip):
                container_like = True

    if container_like:
        facts["network_context"] = "container_like"
        rationale.append("detected container-like network environment")
    else:
        facts["network_context"] = "host_like"

    # candidate interface 판단

    default_dev = facts["default_route_dev"]

    if default_dev and facts["network_context"] == "host_like":

        facts["candidate_iface_out"] = default_dev

        for i in facts["normalized_interfaces"]:
            if i != default_dev and i != "lo":
                facts["candidate_iface_in"] = i
                break

        facts["confidence"] = "medium"
        facts["needs_human_confirmation"] = True

    else:

        rationale.append("interface candidates uncertain")

    return {
        "status": "ok",
        "domain": "net.probe",
        "facts": facts,
        "rationale": rationale,
        "evidence_refs": evidence_refs,
    }