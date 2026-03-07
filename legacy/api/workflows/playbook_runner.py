import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from a2a import run_script
from audit_store import append_audit

from collections import deque

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

def _toposort_jobs(jobs: Dict[str, Any]) -> List[str]:
    """
    Kahn's algorithm. Raises ValueError on cycle.
    jobs: {job_id: {depends_on?: [..]}}
    """
    indeg = {jid: 0 for jid in jobs.keys()}
    out = {jid: [] for jid in jobs.keys()}

    for jid, spec in jobs.items():
        deps = spec.get("depends_on") or []
        for d in deps:
            if d not in jobs:
                raise ValueError(f"job '{jid}' depends_on unknown job '{d}'")
            indeg[jid] += 1
            out[d].append(jid)

    q = deque([jid for jid, v in indeg.items() if v == 0])
    order: List[str] = []

    while q:
        n = q.popleft()
        order.append(n)
        for nxt in out.get(n, []):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)

    if len(order) != len(jobs):
        raise ValueError("cycle detected in jobs depends_on")
    return order

def run_playbook(
    *,
    audit_dir: str,
    subagent_url: str,
    project_id: str,
    playbook: Dict[str, Any],
    inputs: Dict[str, Any],
    target_id: str = "local-agent-1",
    timeout_s: Optional[int] = None,
    resolve_subagent_url_fn=None,  # NEW: callable(target_id)->url
) -> Dict[str, Any]:
    # --- common defaults ---
    defaults = playbook.get("defaults") or {}
    timeout = int(timeout_s or defaults.get("timeout_s") or playbook.get("default_timeout_s", 60))
    failure_policy = (defaults.get("failure_policy") or "fail_fast").strip()

    # =========================================================
    # JOBS / DAG MODE (M3-4.3)
    # =========================================================
    if playbook.get("jobs"):
        jobs = playbook["jobs"] or {}
        if not isinstance(jobs, dict) or not jobs:
            return {"mode": "jobs", "ok": True, "jobs": [], "validate": {"pass": True, "rule": "none"}}

        if resolve_subagent_url_fn is None:
            raise TypeError("resolve_subagent_url_fn is required for playbook.jobs mode")

        append_audit(audit_dir, {
            "type": "PLAYBOOK_RUN_START",
            "project_id": project_id,
            "playbook_id": playbook.get("id"),
            "mode": "jobs",
            "default_target_id": target_id
        })

        order = _toposort_jobs(jobs)
        job_results: List[Dict[str, Any]] = []
        job_status: Dict[str, str] = {}  # job_id -> ok|failed|skipped

        for job_id in order:
            spec = jobs[job_id] or {}
            deps = spec.get("depends_on") or []
            # if any dependency failed or skipped -> skip this job (v0 rule)
            if any(job_status.get(d) != "ok" for d in deps):
                job_status[job_id] = "skipped"
                job_results.append({
                    "job_id": job_id,
                    "target_id": spec.get("target_id") or defaults.get("target_id") or target_id,
                    "status": "skipped",
                    "reason": "dependency_not_ok",
                    "depends_on": deps,
                    "steps": [],
                })
                append_audit(audit_dir, {
                    "type": "PLAYBOOK_JOB_SKIPPED",
                    "project_id": project_id,
                    "job_id": job_id,
                    "reason": "dependency_not_ok",
                })
                continue

            jid_target = spec.get("target_id") or defaults.get("target_id") or target_id
            jid_url = resolve_subagent_url_fn(jid_target)

            steps = spec.get("steps") or []
            # steps are list of {id, run}
            status, step_runs = _run_job_steps(
                audit_dir=audit_dir,
                project_id=project_id,
                job_id=job_id,
                target_id=jid_target,
                subagent_url=jid_url,
                steps=steps,
                inputs=inputs,
                timeout=timeout,
            )

            job_status[job_id] = status
            job_results.append({
                "job_id": job_id,
                "target_id": jid_target,
                "status": status,
                "depends_on": deps,
                "steps": step_runs,
            })

            if status != "ok" and failure_policy == "fail_fast":
                append_audit(audit_dir, {
                    "type": "PLAYBOOK_RUN_STOP_ON_FAIL",
                    "project_id": project_id,
                    "job_id": job_id,
                    "policy": "fail_fast",
                })
                # validate: in jobs mode we can validate based on all step_runs flattened
                flat_runs = []
                for jr in job_results:
                    flat_runs.extend(jr.get("steps") or [])
                validate = _validate(playbook, flat_runs)
                append_audit(audit_dir, {
                    "type": "PLAYBOOK_RUN_DONE",
                    "project_id": project_id,
                    "pass": validate.get("pass"),
                    "rule": validate.get("rule"),
                    "mode": "jobs",
                })
                return {"mode": "jobs", "jobs": job_results, "validate": validate}

        # all done
        flat_runs = []
        for jr in job_results:
            flat_runs.extend(jr.get("steps") or [])
        validate = _validate(playbook, flat_runs)
        append_audit(audit_dir, {
            "type": "PLAYBOOK_RUN_DONE",
            "project_id": project_id,
            "pass": validate.get("pass"),
            "rule": validate.get("rule"),
            "mode": "jobs",
        })
        return {"mode": "jobs", "jobs": job_results, "validate": validate}

    # =========================================================
    # LEGACY STEPS MODE (M3-4.2 유지)
    # =========================================================
    steps = playbook.get("steps") or []
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
                append_audit(audit_dir, {"type": "PLAYBOOK_RUN_STOP_ON_FAIL", "project_id": project_id, "step": sid, "run_id": run_id})
                validate = _validate(playbook, runlog)
                append_audit(audit_dir, {"type": "PLAYBOOK_RUN_DONE", "project_id": project_id, "pass": validate.get("pass"), "rule": validate.get("rule")})
                return {"mode": "steps", "runs": runlog, "validate": validate}

    validate = _validate(playbook, runlog)
    append_audit(audit_dir, {"type": "PLAYBOOK_RUN_DONE", "project_id": project_id, "pass": validate.get("pass"), "rule": validate.get("rule")})
    return {"mode": "steps", "runs": runlog, "validate": validate}


def _run_job_steps(
    *,
    audit_dir: str,
    project_id: str,
    job_id: str,
    target_id: str,
    subagent_url: str,
    steps: List[Dict[str, Any]],
    inputs: Dict[str, Any],
    timeout: int,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    returns: (job_status, step_runs)
    job_status: ok|failed
    """
    step_runs: List[Dict[str, Any]] = []
    append_audit(audit_dir, {
        "type": "PLAYBOOK_JOB_START",
        "project_id": project_id,
        "job_id": job_id,
        "target_id": target_id,
    })

    for sidx, step in enumerate(steps, start=1):
        sid = step.get("id") or f"{job_id}.step{sidx}"
        cmd_tpl = step.get("run")  # DAG 모드에서는 step.run 사용
        if cmd_tpl is None:
            step_runs.append({"job_id": job_id, "step_id": sid, "skipped": True, "reason": "missing run"})
            continue

        cmd = _render(str(cmd_tpl), inputs)
        run_id = str(uuid.uuid4())
        append_audit(audit_dir, {
            "type": "PLAYBOOK_STEP",
            "project_id": project_id,
            "job_id": job_id,
            "step": sid,
            "run_id": run_id,
            "command": cmd,
            "target_id": target_id
        })

        req = {
            "run_id": run_id,
            "target_id": target_id,
            "script": cmd,
            "timeout_s": timeout,
            "approval_required": False,
            "evidence_requests": [],
        }
        result = run_script(subagent_url, req, timeout_s=timeout + 20)

        step_runs.append({
            "job_id": job_id,
            "step_id": sid,
            "run_id": run_id,
            "command": cmd,
            "exit_code": result.get("exit_code"),
            "stdout": (result.get("stdout") or "")[:200000],
            "stderr": (result.get("stderr") or "")[:200000],
            "evidence_refs": result.get("evidence_refs") or [],
        })

        if result.get("exit_code") != 0:
            append_audit(audit_dir, {
                "type": "PLAYBOOK_JOB_STEP_FAIL",
                "project_id": project_id,
                "job_id": job_id,
                "step": sid,
                "run_id": run_id,
                "target_id": target_id
            })
            append_audit(audit_dir, {
                "type": "PLAYBOOK_JOB_DONE",
                "project_id": project_id,
                "job_id": job_id,
                "target_id": target_id,
                "status": "failed"
            })
            return "failed", step_runs

    append_audit(audit_dir, {
        "type": "PLAYBOOK_JOB_DONE",
        "project_id": project_id,
        "job_id": job_id,
        "target_id": target_id,
        "status": "ok"
    })
    return "ok", step_runs