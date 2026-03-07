from typing import Any, Dict, Optional

from a2a import run_script
from resolution_types import (
    ResolutionResult,
    resolved_result,
    insufficient_result,
)


def _run_probe(
    *,
    subagent_url: str,
    project_id: str,
    target_id: str,
    fact_key: str,
    script: str,
    timeout_s: int,
) -> Dict[str, Any]:
    return run_script(
        subagent_url,
        {
            "run_id": f"fact-{project_id}-{fact_key}",
            "target_id": target_id,
            "script": script,
            "timeout_s": timeout_s,
            "approval_required": False,
            "evidence_requests": [],
        },
        timeout_s=timeout_s + 10,
    )


def resolve_target_os(
    *,
    project_id: str,
    target_id: str,
    subagent_url: str,
    timeout_s: int,
) -> ResolutionResult:
    script = r'''sh -lc '
if [ -f /etc/os-release ]; then
  cat /etc/os-release
else
  uname -s
fi
' '''
    res = _run_probe(
        subagent_url=subagent_url,
        project_id=project_id,
        target_id=target_id,
        fact_key="target_os",
        script=script,
        timeout_s=timeout_s,
    )

    stdout = (res.get("stdout") or "").strip()
    if res.get("exit_code") != 0 or not stdout:
        return insufficient_result(
            fact_key="target_os",
            rationale=["os probe failed or returned empty output"],
            evidence_refs=[{"kind": "run_script", "fact_key": "target_os", "stdout": stdout, "stderr": res.get("stderr") or ""}],
        )

    low = stdout.lower()
    value = None

    if 'id=ubuntu' in low:
        value = "ubuntu"
    elif 'id=debian' in low:
        value = "debian"
    elif 'id=rocky' in low:
        value = "rocky"
    elif 'id=almalinux' in low:
        value = "almalinux"
    elif 'id=rhel' in low or 'id="rhel"' in low:
        value = "rhel"
    elif 'id=centos' in low:
        value = "centos"
    elif 'id_like=' in low:
        if any(x in low for x in ["debian", "ubuntu"]):
            value = "debian"
        elif any(x in low for x in ["rhel", "fedora", "centos", "rocky"]):
            value = "rhel"

    if not value:
        return insufficient_result(
            fact_key="target_os",
            rationale=["could not confidently map /etc/os-release to supported os family"],
            evidence_refs=[{"kind": "run_script", "fact_key": "target_os", "stdout": stdout, "stderr": res.get("stderr") or ""}],
        )

    return resolved_result(
        fact_key="target_os",
        value=value,
        rationale=[
            "read /etc/os-release from target host",
            f"mapped os metadata to '{value}'",
        ],
        evidence_refs=[{"kind": "run_script", "fact_key": "target_os", "stdout": stdout, "stderr": res.get("stderr") or ""}],
    )


def resolve_pkg_manager(
    *,
    project_id: str,
    target_id: str,
    subagent_url: str,
    timeout_s: int,
    inputs: Optional[Dict[str, Any]] = None,
) -> ResolutionResult:
    script = r'''sh -lc '
for x in apt dnf yum; do
  if command -v "$x" >/dev/null 2>&1; then
    echo "$x"
  fi
done
' '''
    res = _run_probe(
        subagent_url=subagent_url,
        project_id=project_id,
        target_id=target_id,
        fact_key="pkg_manager",
        script=script,
        timeout_s=timeout_s,
    )

    stdout = (res.get("stdout") or "").strip()
    lines = [x.strip() for x in stdout.splitlines() if x.strip()]

    if lines:
        chosen = lines[0]
        return resolved_result(
            fact_key="pkg_manager",
            value=chosen,
            rationale=[
                "checked available package manager binaries on target host",
                f"selected first detected supported package manager '{chosen}'",
            ],
            evidence_refs=[{"kind": "run_script", "fact_key": "pkg_manager", "stdout": stdout, "stderr": res.get("stderr") or ""}],
        )

    os_hint = ((inputs or {}).get("target_os") or "").lower()
    if os_hint in ("ubuntu", "debian"):
        chosen = "apt"
    elif os_hint in ("rhel", "rocky", "almalinux"):
        chosen = "dnf"
    elif os_hint == "centos":
        chosen = "yum"
    else:
        chosen = None

    if chosen:
        return resolved_result(
            fact_key="pkg_manager",
            value=chosen,
            rationale=[
                "no package manager binary detected directly",
                f"used target_os='{os_hint}' as fallback hint to infer '{chosen}'",
            ],
            evidence_refs=[{"kind": "run_script", "fact_key": "pkg_manager", "stdout": stdout, "stderr": res.get("stderr") or ""}],
        )

    return insufficient_result(
        fact_key="pkg_manager",
        rationale=["could not detect supported package manager from binaries or os hint"],
        evidence_refs=[{"kind": "run_script", "fact_key": "pkg_manager", "stdout": stdout, "stderr": res.get("stderr") or ""}],
    )


def resolve_fact(
    *,
    fact_key: str,
    project_id: str,
    target_id: str,
    subagent_url: str,
    timeout_s: int,
    inputs: Optional[Dict[str, Any]] = None,
) -> Optional[ResolutionResult]:
    if fact_key == "target_os":
        return resolve_target_os(
            project_id=project_id,
            target_id=target_id,
            subagent_url=subagent_url,
            timeout_s=timeout_s,
        )

    if fact_key == "pkg_manager":
        return resolve_pkg_manager(
            project_id=project_id,
            target_id=target_id,
            subagent_url=subagent_url,
            timeout_s=timeout_s,
            inputs=inputs,
        )

    return None