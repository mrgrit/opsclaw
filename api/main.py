from datetime import datetime
import os, uuid, re
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal

from state_store import ensure_dirs, init_project, load_json, project_path, append_run, update_project, save_json
from a2a import run_script
from mastergate import mastergate_scan
from audit_store import append_audit
from master_clients import call_master, Provider
from workflows.basic_graph import build_graph
from evidence_pack import build_evidence_zip

STATE_DIR = os.getenv("STATE_DIR", "/data/state")
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "/data/artifacts")
EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "/data/evidence")
AUDIT_DIR = os.getenv("AUDIT_DIR", "/data/audit")
SUBAGENT_URL = os.getenv("SUBAGENT_URL", "http://subagent:55123")
MASTERGATE_PROFILE = os.getenv("MASTERGATE_PROFILE", "enterprise-default")

APPROVAL_DIR = os.path.join(STATE_DIR, "_approvals")
ensure_dirs(STATE_DIR, ARTIFACT_DIR, EVIDENCE_DIR, AUDIT_DIR, APPROVAL_DIR)

app = FastAPI(title="OpsClaw Manager API", version="0.7.0")

# ---------------- Models ----------------
class Target(BaseModel):
    id: str
    host: str = "local"
    notes: Optional[str] = None

class CreateProjectReq(BaseModel):
    project_type: str = "generic"
    targets: List[Target] = Field(default_factory=list)
    request_text: str = "run basic check"

class RunReq(BaseModel):
    command: str
    timeout_s: int = 60
    approval_required: bool = False

Decision = Literal["approve", "reject"]

class MasterGateRequest(BaseModel):
    title: str = "Ask Master"
    draft_prompt: str
    context_snippets: str = ""
    require_approval: bool = True

class MasterGateDecisionReq(BaseModel):
    decision: Decision
    actor: str = "admin"
    reason: str = ""

class AskMasterReq(BaseModel):
    provider: Provider = "ollama"

class ApplyFeedbackReq(BaseModel):
    actor: str = "system"
    max_commands: int = 6
    timeout_s: int = 60
    stop_on_fail: bool = True

class WorkflowReq(BaseModel):
    request_text: str = "basic health check"
    timeout_s: int = 60
    max_retries: int = 2

# ---------------- Approval Helpers ----------------
def _approval_path(approval_id: str) -> str:
    return os.path.join(APPROVAL_DIR, f"{approval_id}.json")

def _save_approval(obj: Dict[str, Any]) -> Dict[str, Any]:
    save_json(_approval_path(obj["approval_id"]), obj)
    return obj

def _load_approval(approval_id: str) -> Dict[str, Any]:
    p = _approval_path(approval_id)
    if not os.path.exists(p):
        raise HTTPException(404, "approval not found")
    return load_json(p, {})

# ---------------- ApplyFeedback helpers ----------------
_DENY = [
    re.compile(r"rm\s+-rf\s+/", re.I),
    re.compile(r"\bmkfs\.", re.I),
    re.compile(r"\bdd\s+if=.*\s+of=/dev/", re.I),
    re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*;\s*\}\s*;:", re.I),
]

def _is_safe_cmd(cmd: str) -> (bool, str):
    c = cmd.strip()
    if not c:
        return False, "empty"
    if len(c) > 500:
        return False, "too long"
    for p in _DENY:
        if p.search(c):
            return False, f"blocked({p.pattern})"
    return True, ""

def _extract_verification_commands(master_reply: Any) -> List[str]:
    """
    Robust extractor (v2):
    - Handles dict replies with .text containing JSON
    - Accepts key variants: verification_commands / "verification commands" / "verification-commands" / commands / checks
    - Parses fenced blocks, numbered/bulleted lists as fallback
    """
    import json, re

    def uniq(seq):
        seen=set(); out=[]
        for x in seq:
            x=str(x).strip()
            if not x: 
                continue
            if x not in seen:
                out.append(x); seen.add(x)
        return out

    def normalize_key(k: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", (k or "").strip().lower()).strip("_")

    def pick_from_dict(d: dict) -> list[str]:
        # direct known keys
        for k in list(d.keys()):
            nk = normalize_key(k)
            if nk in ("verification_commands","commands","command_list","checks","verification"):
                v=d.get(k)
                if isinstance(v, list):
                    return [str(x).strip() for x in v if str(x).strip()]
        return []

    def try_json_text(text: str) -> list[str]:
        text=(text or "").strip()
        if not text:
            return []
        # try fenced json
        for block in re.findall(r"```json\s*(\{.*?\})\s*```", text, flags=re.S|re.I):
            try:
                obj=json.loads(block)
                got=pick_from_dict(obj)
                if got: return got
            except Exception:
                pass
        # try first {...}
        m=re.search(r"(\{.*\})", text, flags=re.S)
        if m:
            cand=m.group(1)
            try:
                obj=json.loads(cand)
                got=pick_from_dict(obj)
                if got: return got
            except Exception:
                pass
        # sometimes it is already a pure json string without extra
        try:
            obj=json.loads(text)
            if isinstance(obj, dict):
                got=pick_from_dict(obj)
                if got: return got
        except Exception:
            pass
        return []

    cmds: list[str] = []

    # 1) dict reply
    if isinstance(master_reply, dict):
        cmds = pick_from_dict(master_reply)
        if cmds: 
            return uniq(cmds)

        # common wrapper: {"text": "...json..."}
        txt = str(master_reply.get("text") or master_reply.get("content") or "")
        cmds = try_json_text(txt)
        if cmds:
            return uniq(cmds)

        # nested wrappers
        for k in ("raw","message","response","result","data"):
            v = master_reply.get(k)
            if isinstance(v, dict):
                cmds = pick_from_dict(v)
                if cmds: return uniq(cmds)
                t = str(v.get("text") or v.get("content") or "")
                cmds = try_json_text(t)
                if cmds: return uniq(cmds)

    # 2) string reply
    text = master_reply if isinstance(master_reply, str) else str(master_reply or "")
    text = text.strip()

    # bash/sh fenced blocks
    for block in re.findall(r"```(?:bash|sh)?\s*\n(.*?)```", text, flags=re.S|re.I):
        for line in block.splitlines():
            line=line.strip()
            if line and not line.startswith("#"):
                cmds.append(line)
    if cmds:
        return uniq(cmds)

    # json in text
    cmds = try_json_text(text)
    if cmds:
        return uniq(cmds)

    # numbered/bulleted list fallback
    for line in text.splitlines():
        s=line.strip()
        if not s: 
            continue
        s=re.sub(r"^(\d+[\.\)]\s+)", "", s)
        s=re.sub(r"^[-*]\s+", "", s)
        if re.match(r"^(docker|ss|netstat|journalctl|ps|df|free|cat|grep|tail|head|curl|ip|ping|getent|test)\b", s):
            cmds.append(s)

    return uniq(cmds)# ---------------- Core ----------------
@app.get("/health")
def health():
    return {"ok": True, "subagent": SUBAGENT_URL}

# ---------- Projects ----------
@app.post("/projects")
def create_project(req: CreateProjectReq):
    project_id = str(uuid.uuid4())
    st = init_project(STATE_DIR, project_id, req.model_dump())
    st["todos"] = [{"id":"T1","status":"todo","title":"Execute command via subagent","detail":req.request_text}]
    st.setdefault("workflow_runs", [])
    update_project(STATE_DIR, project_id, st)
    return {"project_id": project_id, "state": st}

@app.get("/projects/{project_id}")
def get_project(project_id: str):
    p = project_path(STATE_DIR, project_id)
    return load_json(p, {})

@app.post("/projects/{project_id}/run")
def run_project_command(project_id: str, req: RunReq):
    run_id = str(uuid.uuid4())
    run_req = {
        "run_id": run_id,
        "target_id": "local-agent-1",
        "script": req.command,
        "timeout_s": req.timeout_s,
        "approval_required": req.approval_required,
        "evidence_requests": ["uname", "uptime", "df", "ss_listen"],
    }
    result = run_script(SUBAGENT_URL, run_req, timeout_s=req.timeout_s + 20)

    run_obj = {
        "run_id": run_id,
        "command": req.command,
        "exit_code": result.get("exit_code"),
        "stdout": (result.get("stdout", "") or "")[:200000],
        "stderr": (result.get("stderr", "") or "")[:200000],
        "evidence_refs": result.get("evidence_refs", []),
    }
    append_run(STATE_DIR, project_id, run_obj)

    st = load_json(project_path(STATE_DIR, project_id), {})
    st.setdefault("tests", [])
    st["tests"].append({"name": "exit_code_zero", "pass": run_obj["exit_code"] == 0})
    update_project(STATE_DIR, project_id, st)

    append_audit(AUDIT_DIR, {
        "type": "RUN_COMMAND",
        "project_id": project_id,
        "run_id": run_id,
        "command": req.command,
        "exit_code": run_obj["exit_code"],
    })
    return {"run": run_obj, "tests": st["tests"][-1]}

# ---------- LangGraph Workflow (Diagnose/Decide/Fix/Retry) ----------
@app.post("/projects/{project_id}/run_workflow")
def run_workflow(project_id: str, req: WorkflowReq):
    st = load_json(project_path(STATE_DIR, project_id), {})
    if not st:
        raise HTTPException(404, "project not found")

    wf_id = str(uuid.uuid4())

    def dispatch_fn(cmd: str, timeout_s: int) -> Dict[str, Any]:
        run_id = str(uuid.uuid4())
        run_req = {
            "run_id": run_id,
            "target_id": "local-agent-1",
            "script": cmd,
            "timeout_s": int(timeout_s),
            "approval_required": False,
            "evidence_requests": [],
        }
        result = run_script(SUBAGENT_URL, run_req, timeout_s=int(timeout_s) + 20)
        result["run_id"] = run_id
        return result

    graph = build_graph(dispatch_fn)
    state_in = {
        "project_id": project_id,
        "request_text": req.request_text,
        "timeout_s": int(req.timeout_s),
        "max_retries": int(req.max_retries),
        "retry_count": 0,
    }
    state_out = graph.invoke(state_in)

    st.setdefault("workflow_runs", [])
    st["workflow_runs"].append({
        "wf_id": wf_id,
        "request_text": req.request_text,
        "plan": state_out.get("plan"),
        "commands": state_out.get("commands"),
        "dispatch_runs": state_out.get("dispatch_runs"),
        "validate": state_out.get("validate"),
        "diagnosis": state_out.get("diagnosis"),
        "fix_commands": state_out.get("fix_commands"),
        "fix_runs": state_out.get("fix_runs"),
        "retry_count": state_out.get("retry_count"),
        "step_log": state_out.get("step_log"),
        "error": state_out.get("error"),
    })
    update_project(STATE_DIR, project_id, st)

    append_audit(AUDIT_DIR, {
        "type": "WORKFLOW_RUN",
        "project_id": project_id,
        "wf_id": wf_id,
        "pass": (state_out.get("validate") or {}).get("pass"),
        "retry_count": state_out.get("retry_count"),
        "diagnosis": state_out.get("diagnosis"),
    })

    # ✅ 요약만 반환(대용량 응답 방지)
    summary = {
        "wf_id": wf_id,
        "pass": (state_out.get("validate") or {}).get("pass"),
        "retry_count": state_out.get("retry_count"),
        "diagnosis": state_out.get("diagnosis"),
        "fix_commands": state_out.get("fix_commands"),
        "error": state_out.get("error"),
        "failed_steps": ((state_out.get("validate") or {}).get("failed_steps") or [])[:10],
    }
    return summary

# ---------- Evidence Pack ZIP ----------
def _cleanup_file(path: str):
    try:
        os.remove(path)
    except Exception:
        pass

@app.get("/projects/{project_id}/evidence.zip")
def download_evidence_zip(project_id: str, background_tasks: BackgroundTasks):
    st = load_json(project_path(STATE_DIR, project_id), {})
    if not st:
        raise HTTPException(404, "project not found")

    audit_path = os.path.join(AUDIT_DIR, "audit.jsonl")
    zip_path = build_evidence_zip(
        project_id=project_id,
        project_state=st,
        evidence_dir=EVIDENCE_DIR,
        audit_jsonl_path=audit_path,
        out_dir="/tmp",
    )
    background_tasks.add_task(_cleanup_file, zip_path)

    # 브라우저/CLI에 다운로드 파일명 제공
    filename = f"opsclaw_evidence_{project_id}.zip"
    return FileResponse(zip_path, media_type="application/zip", filename=filename)

# ---------- MasterGate scan ----------
@app.post("/mastergate/scan")
def mastergate_scan_api(draft_prompt: str, context_snippets: str = ""):
    gr = mastergate_scan(draft_prompt, context_snippets, MASTERGATE_PROFILE)
    return gr.__dict__

# ---------- MasterGate request ----------
@app.post("/mastergate/request")
def mastergate_request(req: MasterGateRequest):
    gr = mastergate_scan(req.draft_prompt, req.context_snippets, MASTERGATE_PROFILE)

    approval_id = str(uuid.uuid4())
    obj = {
        "approval_id": approval_id,
        "title": req.title,
        "policy_profile": MASTERGATE_PROFILE,
        "decision_state": "PENDING" if req.require_approval else "AUTO",
        "draft_prompt": req.draft_prompt,
        "context_snippets": req.context_snippets,
        "gate": gr.__dict__,
        "final_prompt": gr.transformed_prompt if gr.decision in ("ALLOW", "TRANSFORM") else "",
        "actor": None,
        "reason": None,
        "master_provider": None,
        "master_reply": None,
        "apply_feedback_runs": [],
    }
    _save_approval(obj)

    append_audit(AUDIT_DIR, {
        "type": "MASTERGATE_REQUEST",
        "approval_id": approval_id,
        "title": req.title,
        "gate_decision": gr.decision,
        "prompt_hash": gr.prompt_hash,
        "findings": gr.findings,
    })

    if not req.require_approval:
        if gr.decision == "BLOCK":
            obj["decision_state"] = "REJECTED"
            obj["actor"] = "system"
            obj["reason"] = gr.required_action or "Blocked by policy"
        else:
            obj["decision_state"] = "APPROVED"
            obj["actor"] = "system"
            obj["reason"] = "Auto-approved (no approval required)"
        _save_approval(obj)

    return obj

@app.get("/approvals")
def list_approvals():
    # Summary list only (avoid huge payloads)
    items = []
    for fn in sorted(os.listdir(APPROVAL_DIR)):
        if fn.endswith(".json"):
            path = os.path.join(APPROVAL_DIR, fn)
            obj = load_json(path, {})
            if not obj.get('created_at'):
                try:
                    from pathlib import Path
                    import datetime
                    ts=Path(path).stat().st_mtime
                    obj['created_at']=datetime.datetime.utcfromtimestamp(ts).isoformat()+'Z'
                except Exception:
                    pass
            items.append({
                "approval_id": obj.get("approval_id"),
                "title": obj.get("title"),
                "created_at": obj.get("created_at"),
                "decision_state": obj.get("decision_state"),
                "gate": {"decision": (obj.get("gate") or {}).get("decision")},
                "master_provider": obj.get("master_provider"),
                "has_master_reply": bool(obj.get("master_reply")),
                "has_apply_feedback_validate": bool(obj.get("apply_feedback_validate")),
            })
    items.reverse()
    return {"items": items[:200]}
@app.get("/approvals/{approval_id}")
def get_approval(approval_id: str):
    return _load_approval(approval_id)

@app.post("/approvals/{approval_id}/decide")
def decide_approval(approval_id: str, req: MasterGateDecisionReq):
    obj = _load_approval(approval_id)
    if obj.get("decision_state") not in ("PENDING", "AUTO"):
        return obj

    if req.decision == "reject":
        obj["decision_state"] = "REJECTED"
        obj["actor"] = req.actor
        obj["reason"] = req.reason or "Rejected"
    else:
        if obj.get("gate", {}).get("decision") == "BLOCK":
            raise HTTPException(400, "Cannot approve: MasterGate decision is BLOCK")
        obj["decision_state"] = "APPROVED"
        obj["actor"] = req.actor
        obj["reason"] = req.reason or "Approved"

    _save_approval(obj)

    append_audit(AUDIT_DIR, {
        "type": "MASTERGATE_DECISION",
        "approval_id": approval_id,
        "decision": obj["decision_state"],
        "actor": obj["actor"],
        "reason": obj["reason"],
        "prompt_hash": obj.get("gate", {}).get("prompt_hash"),
    })
    return obj

# ---------- Ask Master ----------
@app.post("/approvals/{approval_id}/ask_master")
def ask_master(approval_id: str, req: AskMasterReq):
    obj = _load_approval(approval_id)

    if obj.get("decision_state") != "APPROVED":
        raise HTTPException(400, "Approval must be APPROVED to call master")
    if obj.get("gate", {}).get("decision") == "BLOCK":
        raise HTTPException(400, "Blocked by MasterGate")

    final_prompt = (obj.get("final_prompt") or "").strip()
    if not final_prompt:
        raise HTTPException(400, "final_prompt is empty")

    # timeout: env 기반(없으면 60)
    try:
        timeout_s = int(os.getenv("MASTER_TIMEOUT_S", "60"))
    except Exception:
        timeout_s = 60

    try:
        # master_clients.py에서 timeout을 읽도록 되어있지 않다면,
        # call_master 내부가 requests timeout을 자체 사용(현 코드 기준)하므로
        # 여기서는 예외만 잡아서 안정적으로 반환한다.
        reply = call_master(req.provider, final_prompt)
    except Exception as e:
        # 상태 저장(실패 이유 남기기)
        obj["master_provider"] = req.provider
        obj["master_reply"] = None
        obj["master_error"] = str(e)[:2000]
        _save_approval(obj)

        append_audit(AUDIT_DIR, {
            "type": "MASTER_CALL_FAILED",
            "approval_id": approval_id,
            "provider": req.provider,
            "timeout_s": timeout_s,
            "error": str(e)[:2000],
        })

        # 502로 “호출 실패”를 명확히
        raise HTTPException(502, f"Master call failed: {str(e)[:200]}")

    obj["master_provider"] = req.provider
    obj["master_reply"] = reply
    obj["master_error"] = None
    _save_approval(obj)

    append_audit(AUDIT_DIR, {
        "type": "MASTER_CALL",
        "approval_id": approval_id,
        "provider": req.provider,
        "model": reply.get("model") if isinstance(reply, dict) else None,
        "prompt_hash": obj.get("gate", {}).get("prompt_hash"),
    })

    # 요약 반환(대용량 방지)
    return {"approval_id": approval_id, "ok": True}# ---------- Apply Feedback ----------
@app.post("/approvals/{approval_id}/apply_feedback")
def apply_feedback(approval_id: str, req: ApplyFeedbackReq):
    obj = _load_approval(approval_id)
    if obj.get("decision_state") != "APPROVED":
        raise HTTPException(400, "Approval must be APPROVED")
    if obj.get("master_reply") is None:
        raise HTTPException(400, "master_reply is empty. Call master first.")

    commands = _extract_verification_commands(obj.get("master_reply"))
    if not commands:
        raise HTTPException(400, "No verification commands found in master_reply")
    commands = commands[: max(1, int(req.max_commands))]

    append_audit(AUDIT_DIR, {"type": "APPLY_FEEDBACK_STARTED", "approval_id": approval_id, "actor": req.actor, "commands": commands})

    runs: List[Dict[str, Any]] = obj.get("apply_feedback_runs") or []
    for idx, cmd in enumerate(commands, start=1):
        ok, reason = _is_safe_cmd(cmd)
        run_id = str(uuid.uuid4())

        if not ok:
            step = {"run_id": run_id, "step": idx, "command": cmd, "blocked": True, "block_reason": reason, "exit_code": 126, "stdout": "", "stderr": f"Blocked by server filter: {reason}", "evidence_refs": []}
            runs.append(step)
            append_audit(AUDIT_DIR, {"type": "APPLY_FEEDBACK_STEP", "approval_id": approval_id, "run_id": run_id, "step": idx, "blocked": True, "reason": reason})
            if req.stop_on_fail:
                break
            continue

        run_req = {"run_id": run_id, "target_id": "local-agent-1", "script": cmd, "timeout_s": int(req.timeout_s), "approval_required": False, "evidence_requests": []}
        result = run_script(SUBAGENT_URL, run_req, timeout_s=int(req.timeout_s) + 20)
        step = {"run_id": run_id, "step": idx, "command": cmd, "blocked": False, "exit_code": result.get("exit_code"), "stdout": (result.get("stdout", "") or "")[:200000], "stderr": (result.get("stderr", "") or "")[:200000], "evidence_refs": result.get("evidence_refs", [])}
        runs.append(step)
        append_audit(AUDIT_DIR, {"type": "APPLY_FEEDBACK_STEP", "approval_id": approval_id, "run_id": run_id, "step": idx, "command": cmd, "exit_code": step["exit_code"]})
        if req.stop_on_fail and step["exit_code"] != 0:
            break

    obj["apply_feedback_runs"] = runs
    _save_approval(obj)
    append_audit(AUDIT_DIR, {"type": "APPLY_FEEDBACK_DONE", "approval_id": approval_id, "actor": req.actor, "steps": len(runs)})
    return {"approval_id": approval_id, "apply_feedback_runs": runs[-len(commands):]}

# ===========================
# M2-1 Settings Status
# ===========================
@app.get("/settings/status")
def settings_status():
    """
    Always returns 200 with best-effort status.
    Never raises (to avoid web "socket hang up").
    """
    import requests

    openai_key_set = bool(os.getenv("OPENAI_API_KEY", "").strip())
    anthropic_key_set = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())

    ollama_base = (os.getenv("OLLAMA_BASE_URL", "") or "").strip().rstrip("/")
    ollama_model = os.getenv("OLLAMA_MODEL", "")

    ollama = {"configured": bool(ollama_base), "ok": False, "model": ollama_model, "url": None, "error": None, "status_code": None}
    if ollama_base:
        url = f"{ollama_base}/api/tags"
        ollama["url"] = url
        try:
            # keep this very small; ollama can be slow
            r = requests.get(url, timeout=2)
            ollama["status_code"] = r.status_code
            if r.status_code == 200:
                ollama["ok"] = True
            else:
                ollama["error"] = (r.text[:200] if r.text else f"HTTP {r.status_code}")
        except Exception as e:
            ollama["error"] = str(e)[:200]

    return {
        "openai": {"configured": openai_key_set, "model": os.getenv("OPENAI_MODEL", ""), "note": "Key presence only"},
        "anthropic": {"configured": anthropic_key_set, "model": os.getenv("ANTHROPIC_MODEL", ""), "note": "Key presence only"},
        "ollama": ollama,
    }

# ===========================
# M2-2 ApplyFeedback + Validate (closed loop)
# ===========================
@app.post("/approvals/{approval_id}/apply_feedback_and_validate")
def apply_feedback_and_validate(approval_id: str, req: ApplyFeedbackReq):
    obj = _load_approval(approval_id)

    if obj.get("decision_state") != "APPROVED":
        raise HTTPException(400, "Approval must be APPROVED")
    if obj.get("master_reply") is None:
        raise HTTPException(400, "master_reply is empty. Call master first.")

    commands = _extract_verification_commands(obj.get("master_reply"))
    if not commands:
        raise HTTPException(400, "No verification commands found in master_reply")
    commands = commands[: max(1, int(req.max_commands))]

    append_audit(AUDIT_DIR, {
        "type": "APPLY_FEEDBACK_VALIDATE_STARTED",
        "approval_id": approval_id,
        "actor": req.actor,
        "commands": commands,
        "timeout_s": int(req.timeout_s),
        "stop_on_fail": bool(req.stop_on_fail),
    })

    runs: List[Dict[str, Any]] = obj.get("apply_feedback_runs") or []
    new_runs: List[Dict[str, Any]] = []

    for idx, cmd in enumerate(commands, start=1):
        ok, reason = _is_safe_cmd(cmd)
        run_id = str(uuid.uuid4())

        if not ok:
            step = {
                "run_id": run_id, "step": idx, "command": cmd,
                "blocked": True, "block_reason": reason,
                "exit_code": 126, "stdout": "", "stderr": f"Blocked: {reason}",
                "evidence_refs": [],
            }
            runs.append(step); new_runs.append(step)
            append_audit(AUDIT_DIR, {"type": "APPLY_FEEDBACK_VALIDATE_STEP", "approval_id": approval_id, "run_id": run_id, "step": idx, "blocked": True, "reason": reason})
            if req.stop_on_fail: break
            continue

        run_req = {
            "run_id": run_id,
            "target_id": "local-agent-1",
            "script": cmd,
            "timeout_s": int(req.timeout_s),
            "approval_required": False,
            "evidence_requests": [],
        }
        result = run_script(SUBAGENT_URL, run_req, timeout_s=int(req.timeout_s) + 20)

        step = {
            "run_id": run_id, "step": idx, "command": cmd,
            "blocked": False,
            "exit_code": result.get("exit_code"),
            "stdout": (result.get("stdout", "") or "")[:200000],
            "stderr": (result.get("stderr", "") or "")[:200000],
            "evidence_refs": result.get("evidence_refs", []),
        }
        runs.append(step); new_runs.append(step)
        append_audit(AUDIT_DIR, {"type": "APPLY_FEEDBACK_VALIDATE_STEP", "approval_id": approval_id, "run_id": run_id, "step": idx, "command": cmd, "exit_code": step["exit_code"]})
        if req.stop_on_fail and step["exit_code"] != 0:
            break

    failed_steps = []
    for r in new_runs:
        if r.get("blocked") or r.get("exit_code") != 0:
            failed_steps.append({
                "step": r.get("step"),
                "command": r.get("command"),
                "exit_code": r.get("exit_code"),
                "reason": (r.get("block_reason") or (r.get("stderr") or "")[:200] or "failed"),
            })

    validate_obj = {
        "pass": len(failed_steps) == 0,
        "failed_steps": failed_steps[:50],
        "evaluated_commands": commands,
        "evaluated_count": len(new_runs),
    }

    obj["apply_feedback_runs"] = runs
    obj["apply_feedback_validate"] = validate_obj
    _save_approval(obj)

    append_audit(AUDIT_DIR, {"type": "APPLY_FEEDBACK_VALIDATE_DONE", "approval_id": approval_id, "actor": req.actor, "pass": validate_obj["pass"], "failed_count": len(failed_steps)})

    return {"approval_id": approval_id, "pass": validate_obj["pass"], "failed_steps": validate_obj["failed_steps"], "evaluated_count": validate_obj["evaluated_count"]}

@app.post("/approvals/{approval_id}/apply_feedback_and_validate/")
def apply_feedback_and_validate_slash(approval_id: str, req: ApplyFeedbackReq):
    return apply_feedback_and_validate(approval_id, req)

# ---------- Approval Evidence Pack ZIP (M2-3) ----------
@app.get("/approvals/{approval_id}/evidence.zip")
def download_approval_evidence_zip(approval_id: str, background_tasks: BackgroundTasks):
    obj = _load_approval(approval_id)

    audit_path = os.path.join(AUDIT_DIR, "audit.jsonl")
    from evidence_pack import build_approval_evidence_zip

    zip_path = build_approval_evidence_zip(
        approval_id=approval_id,
        approval_obj=obj,
        evidence_dir=EVIDENCE_DIR,
        audit_jsonl_path=audit_path,
        out_dir="/tmp",
    )
    background_tasks.add_task(_cleanup_file, zip_path)

    filename = f"opsclaw_approval_{approval_id}.zip"
    return FileResponse(zip_path, media_type="application/zip", filename=filename)

# ---------- M2-4: ensure created_at for approvals ----------
def _ensure_created_at(obj: Dict[str, Any]) -> None:
    if not obj.get("created_at"):
        obj["created_at"] = datetime.utcnow().isoformat() + "Z"

# ---------- M2-4: wrap _save_approval to inject created_at ----------
_save_approval_orig = _save_approval
def _save_approval(obj: Dict[str, Any]) -> None:  # type: ignore
    _ensure_created_at(obj)
    _save_approval_orig(obj)

# ---------- M2-6: Bulk Decide ----------
class BulkDecideReq(BaseModel):
    approval_ids: List[str]
    decision: str  # approve|reject
    actor: str = "admin"
    reason: str = ""

@app.post("/approvals/bulk_decide")
def approvals_bulk_decide(req: BulkDecideReq):
    decision = (req.decision or "").strip().lower()
    if decision not in ("approve", "reject"):
        raise HTTPException(400, "decision must be approve|reject")

    ids = [x.strip() for x in (req.approval_ids or []) if (x or "").strip()]
    if not ids:
        raise HTTPException(400, "approval_ids is empty")
    if len(ids) > 200:
        raise HTTPException(400, "too many approval_ids (max 200)")

    actor = (req.actor or "").strip() or "admin"
    reason = (req.reason or "").strip()

    results = []
    approved = 0
    rejected = 0
    skipped = 0

    for aid in ids:
        try:
            obj = _load_approval(aid)
        except Exception:
            results.append({"approval_id": aid, "ok": False, "error": "not found"})
            continue

        st = (obj.get("decision_state") or "PENDING").upper()
        if st != "PENDING":
            skipped += 1
            results.append({"approval_id": aid, "ok": False, "status": st, "error": "not PENDING"})
            continue

        if decision == "approve":
            obj["decision_state"] = "APPROVED"
        else:
            obj["decision_state"] = "REJECTED"

        obj["actor"] = actor
        obj["reason"] = reason
        # keep created_at if exists, don't force-create here
        _save_approval(obj)

        results.append({"approval_id": aid, "ok": True, "status": obj["decision_state"]})
        if decision == "approve":
            approved += 1
        else:
            rejected += 1

    append_audit(AUDIT_DIR, {
        "type": "MASTERGATE_BULK_DECISION",
        "decision": decision.upper(),
        "actor": actor,
        "reason": reason,
        "requested": len(ids),
        "approved": approved,
        "rejected": rejected,
        "skipped": skipped,
    })

    return {
        "ok": True,
        "decision": decision,
        "actor": actor,
        "reason": reason,
        "results": results,
        "approved": approved,
        "rejected": rejected,
        "skipped": skipped,
    }

# ---------- M2-6: Bulk Decide ----------
class BulkDecideReq(BaseModel):
    approval_ids: List[str]
    decision: str  # approve|reject
    actor: str = "admin"
    reason: str = ""

@app.post("/approvals/bulk_decide")
def approvals_bulk_decide(req: BulkDecideReq):
    decision = (req.decision or "").strip().lower()
    if decision not in ("approve", "reject"):
        raise HTTPException(400, "decision must be approve|reject")

    ids = [x.strip() for x in (req.approval_ids or []) if (x or "").strip()]
    if not ids:
        raise HTTPException(400, "approval_ids is empty")
    if len(ids) > 200:
        raise HTTPException(400, "too many approval_ids (max 200)")

    actor = (req.actor or "").strip() or "admin"
    reason = (req.reason or "").strip()

    results = []
    approved = rejected = skipped = 0

    for aid in ids:
        try:
            obj = _load_approval(aid)
        except Exception:
            results.append({"approval_id": aid, "ok": False, "error": "not found"})
            continue

        st = (obj.get("decision_state") or "PENDING").upper()
        if st != "PENDING":
            skipped += 1
            results.append({"approval_id": aid, "ok": False, "status": st, "error": "not PENDING"})
            continue

        obj["decision_state"] = "APPROVED" if decision == "approve" else "REJECTED"
        obj["actor"] = actor
        obj["reason"] = reason
        _save_approval(obj)

        results.append({"approval_id": aid, "ok": True, "status": obj["decision_state"]})
        if decision == "approve":
            approved += 1
        else:
            rejected += 1

    append_audit(AUDIT_DIR, {
        "type": "MASTERGATE_BULK_DECISION",
        "decision": decision.upper(),
        "actor": actor,
        "reason": reason,
        "requested": len(ids),
        "approved": approved,
        "rejected": rejected,
        "skipped": skipped,
    })

    return {
        "ok": True,
        "decision": decision,
        "actor": actor,
        "reason": reason,
        "approved": approved,
        "rejected": rejected,
        "skipped": skipped,
        "results": results,
    }
