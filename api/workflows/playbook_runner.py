import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from a2a import run_script
from audit_store import append_audit

TEMPLATE_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

def _render(template: str, ctx: Dict[str, Any]) -> str:
    def repl(m):
        key = m.group(1)
        return str(ctx.get(key, m.group(0)))
    return TEMPLATE_RE.sub(repl, template)

def _validate(playbook: Dict[str, Any], runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    rules = ((playbook.get("validate") or {}).get("pass_if") or [])
    # minimal ruleset
    if not rules:
        return {"pass": True, "rule": "none"}

    # rule: exit_code_all_zero
    for r in rules:
        if (r.get("rule") or "").strip() == "exit_code_all_zero":
            ok = all((x.get("exit_code") == 0) for x in runs if x.get("exit_code") is not None)
            return {"pass": ok, "rule": "exit_code_all_zero"}

        if (r.get("rule") or "").strip() == "at_least_one_command_succeeded":
            ok = any((x.get("exit_code") == 0) for x in runs if x.get("exit_code") is not None)
            return {"pass": ok, "rule": "at_least_one_command_succeeded"}

    # unknown rule -> soft pass
    return {"pass": True, "rule": "unknown-soft-pass"}

def run_playbook(
    *,
    audit_dir: str,
    subagent_url: str,
    project_id: str,
    playbook: Dict[str, Any],
    inputs: Dict[str, Any],
    target_id: str = "local-agent-1",
    timeout_s: Optional[int] = None,
) -> Dict[str, Any]:
    steps = playbook.get("steps") or []
    timeout = int(timeout_s or playbook.get("default_timeout_s", 60))

    runlog: List[Dict[str, Any]] = []
    append_audit(audit_dir, {"type": "PLAYBOOK_RUN_START", "project_id": project_id, "playbook_id": playbook.get("id"), "target_id": target_id})

    for idx, step in enumerate(steps, start=1):
        sid = step.get("id") or f"step{idx}"
        kind = step.get("kind") or "commands"
        commands = step.get("commands") or []

        if kind != "commands":
            runlog.append({"step": sid, "skipped": True, "reason": f"unsupported kind: {kind}"})
            continue

        for cidx, cmd_tpl in enumerate(commands, start=1):
            cmd = _render(str(cmd_tpl), inputs)
            run_id = str(uuid.uuid4())
            append_audit(audit_dir, {"type": "PLAYBOOK_STEP", "project_id": project_id, "step": sid, "run_id": run_id, "command": cmd, "target_id": target_id})

            req = {
                "run_id": run_id,
                "target_id": target_id,
                "script": cmd,
                "timeout_s": timeout,
                "approval_required": False,
                "evidence_requests": [],
            }
            result = run_script(subagent_url, req, timeout_s=timeout + 20)

            runlog.append({
                "step": sid,
                "run_id": run_id,
                "command": cmd,
                "exit_code": result.get("exit_code"),
                "stdout": (result.get("stdout") or "")[:200000],
                "stderr": (result.get("stderr") or "")[:200000],
                "evidence_refs": result.get("evidence_refs") or [],
            })

            if result.get("exit_code") != 0:
                # stop-on-fail MVP (later: policy-controlled)
                append_audit(audit_dir, {"type": "PLAYBOOK_RUN_STOP_ON_FAIL", "project_id": project_id, "step": sid, "run_id": run_id})
                validate = _validate(playbook, runlog)
                append_audit(audit_dir, {"type": "PLAYBOOK_RUN_DONE", "project_id": project_id, "pass": validate.get("pass"), "rule": validate.get("rule")})
                return {"runs": runlog, "validate": validate}

    validate = _validate(playbook, runlog)
    append_audit(audit_dir, {"type": "PLAYBOOK_RUN_DONE", "project_id": project_id, "pass": validate.get("pass"), "rule": validate.get("rule")})
    return {"runs": runlog, "validate": validate}