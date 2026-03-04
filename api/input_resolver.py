# api/input_resolver.py
import re
from typing import Any, Dict, List

from a2a import run_script
from audit_store import append_audit

TEMPLATE_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

def extract_required_inputs(playbook: dict) -> List[str]:
    found = set()

    def scan(s: str):
        for m in TEMPLATE_RE.finditer(s or ""):
            found.add(m.group(1))

    # legacy steps
    for step in (playbook.get("steps") or []):
        for cmd in (step.get("commands") or []):
            scan(str(cmd))

    # jobs
    jobs = playbook.get("jobs") or {}
    if isinstance(jobs, dict):
        for _, spec in jobs.items():
            for step in (spec.get("steps") or []):
                scan(str(step.get("run") or ""))

    # declared inputs are also required
    ins = playbook.get("inputs") or {}
    if isinstance(ins, dict):
        for k in ins.keys():
            found.add(str(k))

    return sorted(found)

def _lines(stdout: str) -> List[str]:
    return [x.strip() for x in (stdout or "").splitlines() if x.strip()]

def resolve_inputs(
    *,
    audit_dir: str,
    project_id: str,
    playbook: dict,
    target_id: str,
    subagent_url: str,
    inputs: Dict[str, Any],
    timeout_s: int = 20,
) -> Dict[str, Any]:
    """
    returns:
      {status:'ready', inputs:{...}}
      or {status:'needs_clarification', missing_inputs:[...], next_questions:[...], choices:{k:[...]}, inputs:{...}}
    """
    reqs = extract_required_inputs(playbook)
    spec = playbook.get("inputs") or {}
    missing = [k for k in reqs if inputs.get(k) in (None, "", [])]

    append_audit(audit_dir, {"type":"INPUT_RESOLVE_START","project_id":project_id,"target_id":target_id,"missing":missing})

    choices: Dict[str, List[str]] = {}
    questions: List[str] = []

    for k in list(missing):
        if not (isinstance(spec, dict) and isinstance(spec.get(k), dict)):
            continue

        disc = (spec[k].get("discover") or {})
        cmds = disc.get("commands") or []
        if not cmds:
            continue

        # run discovery until candidates appear
        cands: List[str] = []
        for cmd in cmds:
            append_audit(audit_dir, {"type":"INPUT_DISCOVER","project_id":project_id,"key":k,"target_id":target_id,"command":cmd})
            res = run_script(subagent_url, {
                "run_id": f"discover-{project_id}-{k}",
                "target_id": target_id,
                "script": cmd,
                "timeout_s": timeout_s,
                "approval_required": False,
                "evidence_requests": [],
            }, timeout_s=timeout_s + 10)

            if res.get("exit_code") == 0:
                cands = _lines(res.get("stdout") or "")
                if cands:
                    break

        # optional exclude filter
        ex = set([x.lower() for x in (disc.get("filter") or {}).get("exclude", [])])
        cands = [c for c in cands if c.lower() not in ex]

        if len(cands) == 1:
            inputs[k] = cands[0]
            missing.remove(k)
            append_audit(audit_dir, {"type":"INPUT_AUTO_CHOSEN","project_id":project_id,"key":k,"value":cands[0],"target_id":target_id})
        elif len(cands) > 1:
            choices[k] = cands[:20]
            questions.append(((spec[k].get("question") or {}).get("prompt")) or f"{k} 값을 선택하세요.")
        else:
            questions.append(((spec[k].get("question") or {}).get("prompt")) or f"{k} 값을 입력하세요.")

    # re-check
    missing = [k for k in reqs if inputs.get(k) in (None, "", [])]
    if missing:
        append_audit(audit_dir, {"type":"INPUT_RESOLVE_NEEDS","project_id":project_id,"target_id":target_id,"missing":missing})
        return {
            "status": "needs_clarification",
            "inputs": inputs,
            "missing_inputs": missing,
            "next_questions": questions or [f"필수 입력값이 부족합니다: {', '.join(missing)}"],
            "choices": choices,
        }

    append_audit(audit_dir, {"type":"INPUT_RESOLVE_DONE","project_id":project_id,"target_id":target_id})
    return {"status": "ready", "inputs": inputs}