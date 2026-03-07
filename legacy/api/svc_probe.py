from typing import Any, Dict, List, Optional

from a2a import run_script


def _run_probe(
    *,
    subagent_url: str,
    project_id: str,
    target_id: str,
    probe_key: str,
    script: str,
    timeout_s: int,
) -> Dict[str, Any]:
    return run_script(
        subagent_url,
        {
            "run_id": f"svcprobe-{project_id}-{probe_key}",
            "target_id": target_id,
            "script": script,
            "timeout_s": timeout_s,
            "approval_required": False,
            "evidence_requests": [],
        },
        timeout_s=timeout_s + 10,
    )


def _ev(kind: str, stdout: str, stderr: str = "") -> Dict[str, Any]:
    return {
        "kind": "run_script",
        "fact_key": kind,
        "stdout": stdout or "",
        "stderr": stderr or "",
    }


def _detect_service_manager(stdout: str) -> Optional[str]:
    low = (stdout or "").lower()
    if "systemctl" in low:
        return "systemd"
    if "service" in low:
        return "service"
    return None


def _detect_service_active(stdout: str) -> Optional[bool]:
    low = (stdout or "").strip().lower()
    if low in ("active", "running"):
        return True
    if low in ("inactive", "failed", "dead", "stopped", "unknown", "not-found", ""):
        return False
    return None


def _detect_process_found(stdout: str) -> Optional[bool]:
    low = (stdout or "").strip().lower()
    if low == "found":
        return True
    if low == "not_found":
        return False
    return None


def _parse_listening_ports(stdout: str) -> List[str]:
    ports: List[str] = []
    for line in (stdout or "").splitlines():
        s = line.strip()
        if not s:
            continue
        ports.append(s)
    return ports


def _detect_health_ok(stdout: str) -> Optional[bool]:
    code = (stdout or "").strip()
    if code.startswith("2") or code.startswith("3"):
        return True
    if code.startswith("4") or code.startswith("5") or code == "000":
        return False
    return None


def collect_svc_probe(
    *,
    project_id: str,
    target_id: str,
    subagent_url: str,
    timeout_s: int,
    service_name: Optional[str] = None,
    health_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    svc.probe v0
    서비스/프로세스/포트/헬스 상태를 범용 관측 결과로 수집한다.
    """
    svc_mgr_res = _run_probe(
        subagent_url=subagent_url,
        project_id=project_id,
        target_id=target_id,
        probe_key="service_manager",
        script=r"""sh -lc '
if command -v systemctl >/dev/null 2>&1; then
  echo systemctl
elif command -v service >/dev/null 2>&1; then
  echo service
fi
'""",
        timeout_s=timeout_s,
    )

    listen_res = _run_probe(
        subagent_url=subagent_url,
        project_id=project_id,
        target_id=target_id,
        probe_key="listening_ports",
        script=r"""sh -lc '
if command -v ss >/dev/null 2>&1; then
  ss -lnt | awk "NR>1 {print \$4}"
elif command -v netstat >/dev/null 2>&1; then
  netstat -lnt 2>/dev/null | awk "NR>2 {print \$4}"
fi
'""",
        timeout_s=timeout_s,
    )

    service_active_res: Optional[Dict[str, Any]] = None
    process_found_res: Optional[Dict[str, Any]] = None
    health_res: Optional[Dict[str, Any]] = None

    if service_name:
        service_active_res = _run_probe(
            subagent_url=subagent_url,
            project_id=project_id,
            target_id=target_id,
            probe_key=f"service_active_{service_name}",
            script=rf"""sh -lc '
if command -v systemctl >/dev/null 2>&1; then
  systemctl is-active "{service_name}" 2>/dev/null || true
elif command -v service >/dev/null 2>&1; then
  service "{service_name}" status >/dev/null 2>&1 && echo running || echo stopped
else
  echo unknown
fi
'""",
            timeout_s=timeout_s,
        )

        process_found_res = _run_probe(
            subagent_url=subagent_url,
            project_id=project_id,
            target_id=target_id,
            probe_key=f"process_found_{service_name}",
            script=rf"""sh -lc '
if pgrep -fa "{service_name}" >/dev/null 2>&1; then
  echo found
else
  echo not_found
fi
'""",
            timeout_s=timeout_s,
        )

    if health_url:
        health_res = _run_probe(
            subagent_url=subagent_url,
            project_id=project_id,
            target_id=target_id,
            probe_key="health_url",
            script=rf"""sh -lc '
if command -v curl >/dev/null 2>&1; then
  curl -s -o /dev/null -w "%{{http_code}}" "{health_url}" || echo 000
elif command -v wget >/dev/null 2>&1; then
  wget -q -S --spider "{health_url}" 2>&1 | awk "/HTTP\// {{print \$2; exit}}" || echo 000
else
  echo 000
fi
'""",
            timeout_s=timeout_s,
        )

    svc_mgr_stdout = (svc_mgr_res.get("stdout") or "").strip()
    listen_stdout = (listen_res.get("stdout") or "").strip()

    service_manager = _detect_service_manager(svc_mgr_stdout)
    listening_ports = _parse_listening_ports(listen_stdout)

    service_active = None
    process_found = None
    health_ok = None

    if service_active_res is not None:
        service_active = _detect_service_active(service_active_res.get("stdout") or "")

    if process_found_res is not None:
        process_found = _detect_process_found(process_found_res.get("stdout") or "")

    if health_res is not None:
        health_ok = _detect_health_ok(health_res.get("stdout") or "")

    facts: Dict[str, Any] = {
        "service_manager": service_manager,
        "service_active": service_active,
        "process_found": process_found,
        "listening_ports": listening_ports,
        "health_ok": health_ok,
    }

    rationale: List[str] = []
    if service_manager:
        rationale.append(f"detected service manager '{service_manager}'")
    if listening_ports:
        rationale.append(f"collected {len(listening_ports)} listening socket entries")
    if service_name and service_active is not None:
        rationale.append(f"checked service active state for '{service_name}'")
    if service_name and process_found is not None:
        rationale.append(f"checked process existence for '{service_name}'")
    if health_url and health_ok is not None:
        rationale.append(f"checked health url '{health_url}'")

    unknowns = [k for k, v in facts.items() if v in (None, [], "")]
    evidence_refs: List[Dict[str, Any]] = [
        _ev("service_manager", svc_mgr_res.get("stdout") or "", svc_mgr_res.get("stderr") or ""),
        _ev("listening_ports", listen_res.get("stdout") or "", listen_res.get("stderr") or ""),
    ]

    if service_active_res is not None:
        evidence_refs.append(
            _ev("service_active", service_active_res.get("stdout") or "", service_active_res.get("stderr") or "")
        )

    if process_found_res is not None:
        evidence_refs.append(
            _ev("process_found", process_found_res.get("stdout") or "", process_found_res.get("stderr") or "")
        )

    if health_res is not None:
        evidence_refs.append(
            _ev("health_check", health_res.get("stdout") or "", health_res.get("stderr") or "")
        )

    return {
        "status": "ok" if not unknowns else "partial",
        "domain": "svc.probe",
        "facts": facts,
        "rationale": rationale,
        "evidence_refs": evidence_refs,
        "unknowns": unknowns,
    }