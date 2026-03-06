# api/input_resolver.py
import re
from typing import Any, Dict, List, Optional

from a2a import run_script
from audit_store import append_audit
from resolution_types import ResolutionResult
import sys_fact_resolver

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

def _try_fact_resolver(
    *,
    audit_dir: str,
    project_id: str,
    playbook: dict,
    target_id: str,
    subagent_url: str,
    fact_key: str,
    fact_spec: Dict[str, Any],
    inputs: Dict[str, Any],
    timeout_s: int,
) -> Optional[ResolutionResult]:
    """
    M3-5.3 generic fact resolution hook.

    현재는 sys 계열 범용 fact 일부만 우선 연결:
    - target_os
    - pkg_manager

    나머지는 아직 None 반환하여 기존 generic discover/질문 흐름으로 fallback 한다.
    """
    append_audit(
        audit_dir,
        {
            "type": "FACT_RESOLVE_TRY",
            "project_id": project_id,
            "target_id": target_id,
            "fact_key": fact_key,
        },
    )

    result = sys_fact_resolver.resolve_fact(
        fact_key=fact_key,
        project_id=project_id,
        target_id=target_id,
        subagent_url=subagent_url,
        timeout_s=timeout_s,
        inputs=inputs,
    )

    if result:
        append_audit(
            audit_dir,
            {
                "type": "FACT_RESOLVE_RESULT",
                "project_id": project_id,
                "target_id": target_id,
                "fact_key": fact_key,
                "status": result.get("status"),
            },
        )

    return result


def _apply_resolution_result(
    *,
    result: Optional[ResolutionResult],
    fact_key: str,
    inputs: Dict[str, Any],
    missing: List[str],
    choices: Dict[str, List[str]],
    questions: List[str],
    approvals: List[Dict[str, Any]],
    rationales: Dict[str, List[str]],
    evidence_map: Dict[str, List[Dict[str, Any]]],
) -> bool:
    """
    공통 ResolutionResult를 기존 resolve_inputs 흐름에 반영한다.

    반환값:
      True  -> 이 fact는 처리 완료됨 (generic discover 건너뜀)
      False -> 처리 못했음 (기존 generic discover 계속 진행)
    """
    if not result:
        return False

    status = result.get("status")
    rationale = result.get("rationale") or []
    evidence_refs = result.get("evidence_refs") or []

    if rationale:
        rationales[fact_key] = [str(x) for x in rationale]
    if evidence_refs:
        evidence_map[fact_key] = evidence_refs

    if status == "resolved":
        value = result.get("value")
        if value not in (None, "", []):
            inputs[fact_key] = value
            if fact_key in missing:
                missing.remove(fact_key)
            return True
        return False

    if status == "needs_clarification":
        cands = result.get("choices") or []
        prompt = result.get("question") or f"{fact_key} 값을 선택하세요."
        if cands:
            choices[fact_key] = [str(x) for x in cands[:20]]
        questions.append(prompt)
        return True

    if status == "needs_approval":
        approval = result.get("approval") or {}
        approvals.append({
            "fact_key": fact_key,
            "action_summary": approval.get("action_summary") or fact_key,
            "risk": approval.get("risk") or "high",
            "rationale": rationales.get(fact_key, []),
        })
        return True

    if status == "insufficient_evidence":
        return False

    return False

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
    approvals: List[Dict[str, Any]] = []
    rationales: Dict[str, List[str]] = {}
    evidence_map: Dict[str, List[Dict[str, Any]]] = {}

    for k in list(missing):
        if not (isinstance(spec, dict) and isinstance(spec.get(k), dict)):
            continue

        fact_result = _try_fact_resolver(
            audit_dir=audit_dir,
            project_id=project_id,
            playbook=playbook,
            target_id=target_id,
            subagent_url=subagent_url,
            fact_key=k,
            fact_spec=spec[k],
            inputs=inputs,
            timeout_s=timeout_s,
        )
        if _apply_resolution_result(
            result=fact_result,
            fact_key=k,
            inputs=inputs,
            missing=missing,
            choices=choices,
            questions=questions,
            approvals=approvals,
            rationales=rationales,
            evidence_map=evidence_map,
        ):
            append_audit(
                audit_dir,
                {
                    "type": "FACT_RESOLUTION_APPLIED",
                    "project_id": project_id,
                    "target_id": target_id,
                    "fact_key": k,
                    "status": (fact_result or {}).get("status"),
                },
            )
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
            "approvals": approvals,
            "rationales": rationales,
            "evidence_map": evidence_map,
        }

    append_audit(audit_dir, {"type":"INPUT_RESOLVE_DONE","project_id":project_id,"target_id":target_id})
    return {
        "status": "ready",
        "inputs": inputs,
        "approvals": approvals,
        "rationales": rationales,
        "evidence_map": evidence_map,
    }