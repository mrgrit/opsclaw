import json
import re
from typing import Any, Dict, List

from a2a import run_script
from audit_store import append_audit
from master_clients import call_conn
import llm_registry


# --- JSON extraction (LLM output may contain extra text) ---
def _extract_json(text: str) -> Dict[str, Any]:
    """
    LLM 출력에서 JSON만 뽑아 파싱.
    - 우선 전체 json.loads 시도
    - 실패하면 가장 바깥 {...} 블록을 찾아 파싱
    """
    t = (text or "").strip()
    if not t:
        return {}
    try:
        obj = json.loads(t)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        pass

    m = re.search(r"\{.*\}", t, flags=re.DOTALL)
    if not m:
        return {}
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _master_call(*, role: str, target_id: str, prompt: str) -> Dict[str, Any]:
    conn = llm_registry.resolve_llm_conn_for_role(role, target_id)
    if not conn:
        raise RuntimeError(f"no llm connection bound for role={role}")
    # call_conn returns {"ok":bool,"provider":..,"model":..,"text":..} (or raises)
    return call_conn(conn, prompt)


def _run_shell_action(
    *,
    audit_dir: str,
    project_id: str,
    subagent_url: str,
    default_target_id: str,
    action: Dict[str, Any],
) -> Dict[str, Any]:
    rid = str(action.get("id") or "probe")
    tid = str(action.get("target_id") or default_target_id)
    timeout_s = int(action.get("timeout_s") or 20)
    script = (action.get("script") or "").strip()

    append_audit(audit_dir, {
        "type": "PROBE_ACTION_RUN",
        "project_id": project_id,
        "run_id": rid,
        "target_id": tid,
        "timeout_s": timeout_s,
        "script_preview": script[:400],
    })

    req = {
        "run_id": rid,
        "target_id": tid,
        "script": script,
        "timeout_s": timeout_s,
        "approval_required": False,
        "evidence_requests": [],
    }
    res = run_script(subagent_url, req, timeout_s=timeout_s + 10)

    return {
        "id": rid,
        "type": "shell",
        "target_id": tid,
        "exit_code": res.get("exit_code"),
        "stdout": (res.get("stdout") or "")[:200000],
        "stderr": (res.get("stderr") or "")[:200000],
        "evidence_refs": res.get("evidence_refs") or [],
    }


def _run_actions(
    *,
    audit_dir: str,
    project_id: str,
    subagent_url: str,
    target_id: str,
    actions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for a in actions or []:
        at = (a.get("type") or "").strip()
        if at != "shell":
            # v0: shell만 지원 (http는 나중에)
            continue
        script = (a.get("script") or "").strip()
        if not script:
            continue
        results.append(_run_shell_action(
            audit_dir=audit_dir,
            project_id=project_id,
            subagent_url=subagent_url,
            default_target_id=target_id,
            action=a,
        ))
    return results


# ---------------------------
# Probe loop: missing/ambiguous inputs 해결
# ---------------------------
def probe_resolve_inputs(
    *,
    audit_dir: str,
    project_id: str,
    request_text: str,
    target_id: str,
    subagent_url: str,
    missing_inputs: List[str],
    choices: Dict[str, List[str]],
    current_inputs: Dict[str, Any],
    max_iters: int = 2,
) -> Dict[str, Any]:
    """
    반환:
      - {"status":"ready","resolved_inputs":{...},"executions":[...]}
      - {"status":"needs_clarification","question":{next_questions,choices},"executions":[...]}
      - {"status":"failed","error":"...","executions":[...]}
    """
    executions: List[Dict[str, Any]] = []

    append_audit(audit_dir, {
        "type": "PROBE_LOOP_START",
        "project_id": project_id,
        "target_id": target_id,
        "missing_inputs": missing_inputs,
    })

    schema = {
        "note": "You MUST output ONLY JSON. No markdown. No extra text.",
        "allowed_keys": ["actions", "resolved_inputs", "question"],
        "actions": [{"id": "p1", "type": "shell", "target_id": "remote-1", "timeout_s": 30, "script": "ip -o link show"}],
        "resolved_inputs": {"iface_in": "ens33", "iface_out": "ens34"},
        "question": {"next_questions": ["iface_out 선택?"], "choices": {"iface_out": ["ens33", "ens34"]}},
    }

    ctx: Dict[str, Any] = {
        "request_text": request_text,
        "target_id": target_id,
        "missing_inputs": missing_inputs,
        "choices": choices,
        "current_inputs": current_inputs,
    }

    for _ in range(max_iters):
        prompt = (
            "You are OpsClaw Master.\n"
            "Goal: resolve missing/ambiguous inputs WITHOUT guessing.\n"
            "Use probe shell commands to learn facts, then output resolved_inputs.\n"
            "If still ambiguous, ask MINIMAL question (1~2).\n\n"
            f"OUTPUT_SCHEMA_EXAMPLE:\n{json.dumps(schema, ensure_ascii=False)}\n\n"
            f"CONTEXT:\n{json.dumps(ctx, ensure_ascii=False)}\n"
        )

        llm = _master_call(role="master", target_id=target_id, prompt=prompt)
        obj = _extract_json(llm.get("text") or "")
        if not obj:
            return {"status": "failed", "error": "LLM returned non-JSON", "executions": executions}

        if isinstance(obj.get("resolved_inputs"), dict) and obj["resolved_inputs"]:
            append_audit(audit_dir, {
                "type": "PROBE_LOOP_RESOLVED",
                "project_id": project_id,
                "resolved_keys": sorted(list(obj["resolved_inputs"].keys())),
            })
            return {"status": "ready", "resolved_inputs": obj["resolved_inputs"], "executions": executions}

        if isinstance(obj.get("question"), dict):
            append_audit(audit_dir, {"type": "PROBE_LOOP_ASK", "project_id": project_id})
            return {"status": "needs_clarification", "question": obj["question"], "executions": executions}

        actions = obj.get("actions") or []
        if not isinstance(actions, list) or not actions:
            return {"status": "failed", "error": "LLM returned neither actions nor resolved_inputs", "executions": executions}

        # execute probe actions
        res = _run_actions(
            audit_dir=audit_dir,
            project_id=project_id,
            subagent_url=subagent_url,
            target_id=target_id,
            actions=actions,
        )
        executions.extend(res)
        ctx["probe_results"] = res

    return {"status": "failed", "error": "probe loop exceeded max_iters", "executions": executions}


# ---------------------------
# Fix loop: validate fail -> probe/fix actions -> (caller가 재시도)
# ---------------------------
def probe_fix_and_retry(
    *,
    audit_dir: str,
    project_id: str,
    request_text: str,
    target_id: str,
    subagent_url: str,
    last_result: Dict[str, Any],
    max_iters: int = 1,
) -> Dict[str, Any]:
    """
    반환:
      - {"status":"done","executions":[...], "error"?: "..."}
      - {"status":"needs_clarification","question":..., "executions":[...]}
    """
    executions: List[Dict[str, Any]] = []
    append_audit(audit_dir, {"type": "FIX_LOOP_START", "project_id": project_id, "target_id": target_id})

    schema = {
        "note": "You MUST output ONLY JSON. No markdown. No extra text.",
        "allowed_keys": ["actions", "question"],
        "actions": [{"id": "f1", "type": "shell", "target_id": "remote-1", "timeout_s": 30, "script": "cat /etc/os-release"}],
        "question": {"next_questions": ["재시도 전에 무엇을 바꿀까요?"], "choices": {}},
    }

    ctx: Dict[str, Any] = {
        "request_text": request_text,
        "target_id": target_id,
        "last_validate": last_result.get("validate"),
        # steps 모드면 runs, jobs 모드면 jobs를 넣어준다
        "last_runs_or_jobs": last_result.get("runs") or last_result.get("jobs") or [],
    }

    for _ in range(max_iters):
        prompt = (
            "You are OpsClaw Master.\n"
            "Return JSON ONLY (single JSON object). No markdown. No extra text.\n"
            "You MUST NOT guess. If unsure, you MUST propose probe actions (read-only) to verify.\n"
            "\n"
            "# Hard Constraints (NON-NEGOTIABLE)\n"
            "1) Output must be valid JSON object.\n"
            "2) Do not assume interface names, paths, distro, package manager, service names.\n"
            "3) No destructive commands in probe stage: no reboot/shutdown, no firewall flush, no apt/yum installs.\n"
            "4) If selecting NICs: iface_in and iface_out MUST be different.\n"
            "   Exclude: lo, docker0, veth*, br-*, virbr*, tun*, tap* unless explicitly needed.\n"
            "   Prefer stable physical NIC names (ens*/enp*/eth* without '@if').\n"
            "   If only eth0@ifX appears, add probes to find better/stable interfaces.\n"
            "\n"
            "# Allowed probe examples\n"
            "- ip -o link show\n"
            "- ip -o addr show\n"
            "- ip route\n"
            "- ls /sys/class/net\n"
            "- readlink -f /sys/class/net/<iface>\n"
            "- cat /etc/os-release\n"
            "- uname -a\n"
            "\n"
            "# Output schema\n"
            "Choose ONE:\n"
            "A) {\"actions\":[{\"id\":\"p1\",\"kind\":\"shell\",\"target_id\":\"...\",\"timeout_s\":15,\"script\":\"...\"}],\"why\":\"...\"}\n"
            "B) {\"resolved_inputs\":{...},\"why\":\"...\",\"checks\":[...]}\n"
            "C) {\"question\":{\"text\":\"...\",\"choices\":{...}},\"why\":\"...\"}\n"
            "\n"
            f"OUTPUT_SCHEMA_EXAMPLE:\n{json.dumps(schema, ensure_ascii=False)}\n\n"
            f"CONTEXT:\n{json.dumps(ctx, ensure_ascii=False)}\n"
        )

        llm = _master_call(role="master", target_id=target_id, prompt=prompt)
        obj = _extract_json(llm.get("text") or "")
        if not obj:
            return {"status": "done", "executions": executions, "error": "LLM returned non-JSON"}

        if isinstance(obj.get("question"), dict):
            return {"status": "needs_clarification", "question": obj["question"], "executions": executions}

        actions = obj.get("actions") or []
        if not isinstance(actions, list) or not actions:
            return {"status": "done", "executions": executions, "error": "no actions"}

        res = _run_actions(
            audit_dir=audit_dir,
            project_id=project_id,
            subagent_url=subagent_url,
            target_id=target_id,
            actions=actions,
        )
        executions.extend(res)
        ctx["fix_results"] = res

    return {"status": "done", "executions": executions}
