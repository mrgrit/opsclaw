from __future__ import annotations

from datetime import datetime
import os, uuid, re
from typing import Any, Dict, List, Optional, Literal, Tuple

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from state_store import ensure_dirs, init_project, load_json, project_path, append_run, update_project, save_json
from a2a import run_script
from mastergate import mastergate_scan
from audit_store import append_audit
from master_clients import call_master, Provider
from workflows.basic_graph import build_graph
from evidence_pack import build_evidence_zip

# ============================================================
# Paths / Env
# ============================================================
STATE_DIR = os.getenv("STATE_DIR", "/data/state")
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "/data/artifacts")
EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "/data/evidence")
AUDIT_DIR = os.getenv("AUDIT_DIR", "/data/audit")
SUBAGENT_URL = os.getenv("SUBAGENT_URL", "http://subagent:55123")
MASTERGATE_PROFILE = os.getenv("MASTERGATE_PROFILE", "enterprise-default")

APPROVAL_DIR = os.path.join(STATE_DIR, "_approvals")
ensure_dirs(STATE_DIR, ARTIFACT_DIR, EVIDENCE_DIR, AUDIT_DIR, APPROVAL_DIR)

app = FastAPI(title="OpsClaw Manager API", version="0.7.2")

# ============================================================
# M3-2: Minimal RBAC/Auth + audit enrichment
# - If no tokens configured: allow everything (backward compatible)
# - If any token configured: require header "x-opsclaw-token"
# Roles: viewer < operator < approver < admin
# ============================================================

ROLE_ORDER = {"viewer": 0, "operator": 1, "approver": 2, "admin": 3}

def _token_role_map() -> Dict[str, str]:
    m: Dict[str, str] = {}
    for role, envk in [
        ("admin", "OPSCLAW_ADMIN_TOKEN"),
        ("approver", "OPSCLAW_APPROVER_TOKEN"),
        ("operator", "OPSCLAW_OPERATOR_TOKEN"),
        ("viewer", "OPSCLAW_VIEWER_TOKEN"),
    ]:
        tok = (os.getenv(envk, "") or "").strip()
        if tok:
            m[tok] = role
    return m

def _auth_enabled() -> bool:
    return bool(_token_role_map())

def authz(request: Request, min_role: str) -> Dict[str, Any]:
    """
    Returns {"role":..., "actor":...}
    Header:
      - x-opsclaw-token: required if auth enabled
      - x-opsclaw-actor: optional display name for audit (fallback: role)
    """
    if not _auth_enabled():
        # No tokens configured -> backward compatible
        actor = (request.headers.get("x-opsclaw-actor") or "admin").strip() or "admin"
        return {"role": "admin", "actor": actor}

    token = (request.headers.get("x-opsclaw-token") or "").strip()
    if not token:
        raise HTTPException(401, "missing x-opsclaw-token")
    role = _token_role_map().get(token)
    if not role:
        raise HTTPException(403, "invalid token")
    if ROLE_ORDER[role] < ROLE_ORDER[min_role]:
        raise HTTPException(403, f"insufficient role: need {min_role}, have {role}")

    actor = (request.headers.get("x-opsclaw-actor") or role).strip() or role
    return {"role": role, "actor": actor}

def append_audit_ex(request: Request, event: Dict[str, Any], auth: Optional[Dict[str, Any]] = None) -> None:
    e = dict(event)
    meta = dict(e.get("meta") or {})
    try:
        meta.setdefault("ip", request.client.host if request.client else None)
    except Exception:
        meta.setdefault("ip", None)
    meta.setdefault("user_agent", request.headers.get("user-agent"))
    if auth:
        meta.setdefault("role", auth.get("role"))
        meta.setdefault("actor", auth.get("actor"))
    e["meta"] = meta
    append_audit(AUDIT_DIR, e)

# ============================================================
# Common helpers
# ============================================================

def _iso_now() -> str:
    return datetime.utcnow().isoformat() + "Z"

def _ensure_archive_fields(obj: Dict[str, Any]) -> None:
    obj.setdefault("archived_at", None)     # ISO string or None
    obj.setdefault("archived_by", None)     # actor or None
    obj.setdefault("archived_reason", "")   # str

def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts[:-1])
        return datetime.fromisoformat(ts)
    except Exception:
        return None

def _ensure_created_at(obj: Dict[str, Any]) -> None:
    if not obj.get("created_at"):
        obj["created_at"] = _iso_now()
    _ensure_archive_fields(obj)

# ============================================================
# M3-3 hardening: container-safe + placeholder handling
# ============================================================
PLACEHOLDER_RE = re.compile(r"<[^>]+>")  # e.g. <service_name>, <port>

DENY_SUBSTR = [
    "systemctl", "journalctl", "service ",
    "sudo ", "reboot", "shutdown", "poweroff",
    "apt ", "apt-get ", "yum ", "dnf ",
]

def _is_denied_command(cmd: str) -> Optional[str]:
    c = (cmd or "").strip().lower()
    for s in DENY_SUBSTR:
        if s in c:
            return f"denied token: {s.strip()}"
    return None

def sanitize_master_reply_json(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize master reply JSON and enforce container-safe verification_commands:
    - Drop commands with placeholders (<...>)
    - Drop denylisted commands (systemctl/journalctl/etc.)
    - If commands become empty, inject safe defaults
    - Add next_questions and dropped_commands for visibility
    """
    if not isinstance(obj, dict):
        return obj

    cmds = obj.get("verification_commands") or []
    if not isinstance(cmds, list):
        cmds = []

    safe: List[str] = []
    dropped: List[Dict[str, str]] = []

    for raw in cmds:
        cmd = (raw or "").strip()
        if not cmd:
            continue
        if PLACEHOLDER_RE.search(cmd):
            dropped.append({"command": cmd, "reason": "placeholder detected"})
            continue
        why = _is_denied_command(cmd)
        if why:
            dropped.append({"command": cmd, "reason": why})
            continue
        safe.append(cmd)

    nq = obj.get("next_questions") or []
    if not isinstance(nq, list):
        nq = []

    if dropped:
        nq.extend([
            "What is the exact service or application name?",
            "Is this running inside a container (no systemd), or a full VM with systemd?",
            "Which port should the health endpoint use (if any)?",
            "Which log file paths are relevant (e.g., /var/log/app.log, /app/logs/*)?",
        ])
        notes = (obj.get("notes") or "").strip()
        dropped_txt = "; ".join([f"{x['reason']}: {x['command']}" for x in dropped[:6]])
        add = f"[M3-3 sanitize] dropped {len(dropped)} cmds (examples: {dropped_txt})"
        obj["notes"] = (notes + "\n" + add).strip() if notes else add

    if not safe:
        safe = [
            "uname -a",
            "date; uptime",
            "ps aux | head -n 30",
            "ss -lntp || netstat -lntp || true",
            "ls -la /var/log | head",
            "tail -n 80 /var/log/syslog 2>/dev/null || true",
            "tail -n 80 /var/log/messages 2>/dev/null || true",
            "env | sort | head -n 50",
        ]

    obj["verification_commands"] = safe
    obj["next_questions"] = nq
    obj["dropped_commands"] = dropped
    return obj

def sanitize_commands_list(commands: List[str]) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Apply the same guards to a raw list of commands (used by apply_feedback*).
    Returns (safe, dropped).
    """
    safe: List[str] = []
    dropped: List[Dict[str, str]] = []

    for raw in (commands or []):
        cmd = (raw or "").strip()
        if not cmd:
            continue
        if PLACEHOLDER_RE.search(cmd):
            dropped.append({"command": cmd, "reason": "placeholder detected"})
            continue
        why = _is_denied_command(cmd)
        if why:
            dropped.append({"command": cmd, "reason": why})
            continue
        safe.append(cmd)

    return safe, dropped

# ============================================================
# Models
# ============================================================
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

# ============================================================
# Approval helpers
# ============================================================
def _approval_path(approval_id: str) -> str:
    return os.path.join(APPROVAL_DIR, f"{approval_id}.json")

def _save_approval(obj: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_created_at(obj)
    save_json(_approval_path(obj["approval_id"]), obj)
    return obj

def _load_approval(approval_id: str) -> Dict[str, Any]:
    p = _approval_path(approval_id)
    if not os.path.exists(p):
        raise HTTPException(404, "approval not found")
    obj = load_json(p, {})
    _ensure_created_at(obj)
    return obj

# ============================================================
# ApplyFeedback command safety filter
# ============================================================
_DENY = [
    re.compile(r"rm\s+-rf\s+/", re.I),
    re.compile(r"\bmkfs\.", re.I),
    re.compile(r"\bdd\s+if=.*\s+of=/dev/", re.I),
    re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*;\s*\}\s*;:", re.I),
]

def _is_safe_cmd(cmd: str) -> Tuple[bool, str]:
    c = cmd.strip()
    if not c:
        return False, "empty"
    if len(c) > 500:
        return False, "too long"
    for p in _DENY:
        if p.search(c):
            return False, f"blocked({p.pattern})"
    return True, ""

# ============================================================
# M3-3: Master reply schema + parser stabilization
# ============================================================
MASTER_SCHEMA_VERSION = "m3-3.v1"

def _master_reply_schema_text() -> str:
    return (
        '{\n'
        '  "verification_commands": ["cmd1", "cmd2", "..."],\n'
        '  "notes": "short explanation / root-cause candidates",\n'
        '  "risk": "low|med|high",\n'
        '  "assumptions": ["..."],\n'
        '  "next_questions": ["..."]\n'
        '}'
    )

def _build_master_prompt(user_prompt: str) -> str:
    schema = _master_reply_schema_text()
    return (
        "You are OpsClaw Master. Return ONLY valid JSON. No markdown, no code fences, no extra keys.\n"
        f"Schema version: {MASTER_SCHEMA_VERSION}.\n"
        "Output MUST be a single JSON object matching this schema exactly:\n"
        f"{schema}\n"
        "\n"
        "Rules:\n"
        "- verification_commands: shell commands to verify hypotheses (string array).\n"
        "- notes: concise explanation (string).\n"
        "- risk: one of low|med|high.\n"
        "- assumptions: string array (can be empty).\n"
        "- next_questions: string array (can be empty).\n"
        "- If you are unsure, still return valid JSON with empty arrays and notes explaining uncertainty.\n"
        "\n"
        "User request:\n"
        + (user_prompt or "")
    )

def _extract_first_json_object(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.I)
    t = re.sub(r"```\s*$", "", t).strip()

    if t.startswith("{") and t.endswith("}"):
        return t

    start = t.find("{")
    if start < 0:
        return ""
    depth = 0
    for i in range(start, len(t)):
        ch = t[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return t[start:i+1]
    return ""

def _normalize_master_json(obj: Dict[str, Any]) -> Dict[str, Any]:
    def as_list(x):
        if x is None:
            return []
        if isinstance(x, list):
            return [str(i).strip() for i in x if str(i).strip()]
        if isinstance(x, str):
            s = x.strip()
            return [s] if s else []
        return [str(x).strip()] if str(x).strip() else []

    def as_str(x):
        return "" if x is None else str(x)

    out = {
        "verification_commands": as_list(obj.get("verification_commands")),
        "notes": as_str(obj.get("notes")).strip(),
        "risk": as_str(obj.get("risk")).strip().lower(),
        "assumptions": as_list(obj.get("assumptions")),
        "next_questions": as_list(obj.get("next_questions")),
    }

    if out["risk"] not in ("low", "med", "high"):
        r = out["risk"]
        if r in ("medium", "mid", "moderate"):
            out["risk"] = "med"
        elif r in ("l", "lo"):
            out["risk"] = "low"
        elif r in ("h", "hi"):
            out["risk"] = "high"
        else:
            out["risk"] = "med" if out["risk"] else "low"

    return out

def _parse_master_reply_json(text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    import json
    blob = _extract_first_json_object(text)
    if not blob:
        return None, "no_json_object_found"
    try:
        obj = json.loads(blob)
    except Exception as e:
        return None, f"json_load_failed: {type(e).__name__}: {e}"
    if not isinstance(obj, dict):
        return None, "json_not_object"
    try:
        norm = _normalize_master_json(obj)
    except Exception as e:
        return None, f"normalize_failed: {type(e).__name__}: {e}"
    return norm, None

def _repair_prompt(bad_text: str, err: str) -> str:
    schema = _master_reply_schema_text()
    clipped = (bad_text or "")[:4000]
    return (
        "Your previous output was invalid or did not match schema.\n"
        f"Error: {err}\n"
        "Return ONLY a valid JSON object matching this schema exactly. No markdown.\n"
        f"{schema}\n"
        "\nPrevious output (for reference):\n"
        + clipped
    )

def _extract_verification_commands(master_reply: Any) -> List[str]:
    """
    Robust extractor:
    - dict JSON form: verification_commands/commands/checks
    - dict wrapper with "text"/"content" containing JSON or fenced blocks
    - string fallback: fenced bash/sh blocks, numbered lists
    """
    import json

    def uniq(seq):
        seen=set()
        out=[]
        for x in seq:
            x=str(x).strip()
            if not x:
                continue
            if x not in seen:
                out.append(x); seen.add(x)
        return out

    def normalize_key(k: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", (k or "").strip().lower()).strip("_")

    def pick_from_dict(d: dict) -> List[str]:
        for k in list(d.keys()):
            nk = normalize_key(k)
            if nk in ("verification_commands","commands","command_list","checks","verification"):
                v = d.get(k)
                if isinstance(v, list):
                    return [str(x).strip() for x in v if str(x).strip()]
        return []

    def try_json_text(text: str) -> List[str]:
        text=(text or "").strip()
        if not text:
            return []
        for block in re.findall(r"```json\s*(\{.*?\})\s*```", text, flags=re.S|re.I):
            try:
                obj=json.loads(block)
                got=pick_from_dict(obj)
                if got:
                    return got
            except Exception:
                pass
        m=re.search(r"(\{.*\})", text, flags=re.S)
        if m:
            cand=m.group(1)
            try:
                obj=json.loads(cand)
                got=pick_from_dict(obj)
                if got:
                    return got
            except Exception:
                pass
        try:
            obj=json.loads(text)
            if isinstance(obj, dict):
                got=pick_from_dict(obj)
                if got:
                    return got
        except Exception:
            pass
        return []

    # dict reply
    if isinstance(master_reply, dict):
        cmds = pick_from_dict(master_reply)
        if cmds:
            return uniq(cmds)
        txt = str(master_reply.get("text") or master_reply.get("content") or "")
        cmds = try_json_text(txt)
        if cmds:
            return uniq(cmds)
        for k in ("raw","message","response","result","data"):
            v = master_reply.get(k)
            if isinstance(v, dict):
                cmds = pick_from_dict(v)
                if cmds:
                    return uniq(cmds)
                t = str(v.get("text") or v.get("content") or "")
                cmds = try_json_text(t)
                if cmds:
                    return uniq(cmds)

    # string reply
    text = master_reply if isinstance(master_reply, str) else str(master_reply or "")
    text = text.strip()

    cmds: List[str] = []
    for block in re.findall(r"```(?:bash|sh)?\s*\n(.*?)```", text, flags=re.S|re.I):
        for line in block.splitlines():
            line=line.strip()
            if line and not line.startswith("#"):
                cmds.append(line)
    if cmds:
        return uniq(cmds)

    cmds = try_json_text(text)
    if cmds:
        return uniq(cmds)

    for line in text.splitlines():
        s=line.strip()
        if not s:
            continue
        s=re.sub(r"^(\d+[\.\)]\s+)", "", s)
        s=re.sub(r"^[-*]\s+", "", s)
        if re.match(r"^(docker|ss|netstat|ps|df|free|cat|grep|tail|head|curl|ip|ping|getent|test)\b", s):
            cmds.append(s)

    return uniq(cmds)

# ============================================================
# Core
# ============================================================
@app.get("/health")
def health():
    return {"ok": True, "subagent": SUBAGENT_URL}

# ============================================================
# Projects
# ============================================================
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
    return load_json(project_path(STATE_DIR, project_id), {})

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

# ---------- LangGraph Workflow ----------
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

    return {
        "wf_id": wf_id,
        "pass": (state_out.get("validate") or {}).get("pass"),
        "retry_count": state_out.get("retry_count"),
        "diagnosis": state_out.get("diagnosis"),
        "fix_commands": state_out.get("fix_commands"),
        "error": state_out.get("error"),
        "failed_steps": ((state_out.get("validate") or {}).get("failed_steps") or [])[:10],
    }

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
    filename = f"opsclaw_evidence_{project_id}.zip"
    return FileResponse(zip_path, media_type="application/zip", filename=filename)

# ============================================================
# MasterGate
# ============================================================
@app.post("/mastergate/scan")
def mastergate_scan_api(draft_prompt: str, context_snippets: str = ""):
    gr = mastergate_scan(draft_prompt, context_snippets, MASTERGATE_PROFILE)
    return gr.__dict__

@app.post("/mastergate/request")
def mastergate_request(req: MasterGateRequest):
    gr = mastergate_scan(req.draft_prompt, req.context_snippets, MASTERGATE_PROFILE)
    approval_id = str(uuid.uuid4())

    obj: Dict[str, Any] = {
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
        "master_reply_json": None,
        "master_reply_schema_version": None,
        "master_reply_parse_error": None,
        "master_error": None,
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

# ============================================================
# M3-1: Approval Queue list (archive filters)
# ============================================================
@app.get("/approvals")
def list_approvals(include_archived: bool = False, only_archived: bool = False):
    items: List[Dict[str, Any]] = []
    for fn in sorted(os.listdir(APPROVAL_DIR)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(APPROVAL_DIR, fn)
        obj = load_json(path, {})

        # backfill created_at from mtime if missing
        if not obj.get("created_at"):
            try:
                from pathlib import Path
                ts = Path(path).stat().st_mtime
                obj["created_at"] = datetime.utcfromtimestamp(ts).isoformat() + "Z"
            except Exception:
                obj["created_at"] = _iso_now()

        _ensure_archive_fields(obj)

        is_archived = bool(obj.get("archived_at"))
        if only_archived and not is_archived:
            continue
        if (not include_archived) and (not only_archived) and is_archived:
            continue

        items.append({
            "approval_id": obj.get("approval_id"),
            "title": obj.get("title"),
            "created_at": obj.get("created_at"),
            "decision_state": obj.get("decision_state"),
            "gate": {"decision": (obj.get("gate") or {}).get("decision")},
            "master_provider": obj.get("master_provider"),
            "has_master_reply": bool(obj.get("master_reply")),
            "has_apply_feedback_validate": bool(obj.get("apply_feedback_validate")),
            "archived_at": obj.get("archived_at"),
            "archived_by": obj.get("archived_by"),
        })

    items.reverse()
    return {"items": items[:200]}

@app.get("/approvals/{approval_id}")
def get_approval(approval_id: str):
    return _load_approval(approval_id)

@app.post("/approvals/{approval_id}/decide")
def decide_approval(request: Request, approval_id: str, req: MasterGateDecisionReq):
    auth = authz(request, "approver")
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

    append_audit_ex(request, {
        "type": "MASTERGATE_DECISION",
        "approval_id": approval_id,
        "decision": obj["decision_state"],
        "actor": obj["actor"],
        "reason": obj["reason"],
        "prompt_hash": obj.get("gate", {}).get("prompt_hash"),
    }, auth)
    return obj

# ============================================================
# M3-1: Archive / Restore
# ============================================================
class ArchiveReq(BaseModel):
    actor: str = "admin"
    reason: str = ""

@app.post("/approvals/{approval_id}/archive")
def archive_approval(request: Request, approval_id: str, req: ArchiveReq):
    auth = authz(request, "approver")
    obj = _load_approval(approval_id)
    if obj.get("archived_at"):
        return obj
    obj["archived_at"] = _iso_now()
    obj["archived_by"] = (req.actor or "admin").strip() or "admin"
    obj["archived_reason"] = (req.reason or "").strip()
    _save_approval(obj)

    append_audit_ex(request, {
        "type": "APPROVAL_ARCHIVE",
        "approval_id": approval_id,
        "actor": obj["archived_by"],
        "reason": obj.get("archived_reason") or "",
    }, auth)
    return obj

@app.post("/approvals/{approval_id}/restore")
def restore_approval(request: Request, approval_id: str, req: ArchiveReq):
    auth = authz(request, "approver")
    obj = _load_approval(approval_id)
    if not obj.get("archived_at"):
        return obj
    prev = obj.get("archived_at")
    obj["archived_at"] = None
    obj["archived_by"] = None
    obj["archived_reason"] = ""
    _save_approval(obj)

    append_audit_ex(request, {
        "type": "APPROVAL_RESTORE",
        "approval_id": approval_id,
        "actor": (req.actor or "admin").strip() or "admin",
        "prev_archived_at": prev,
        "reason": (req.reason or "").strip(),
    }, auth)
    return obj

# ============================================================
# M3-1: Retention + Purge (file-based)
# ============================================================
RETENTION_PATH = os.path.join(STATE_DIR, "_retention.json")

def _load_retention() -> Dict[str, Any]:
    obj = load_json(RETENTION_PATH, {})
    obj.setdefault("enabled", True)
    obj.setdefault("approvals_purge_after_days", int(os.getenv("APPROVALS_PURGE_AFTER_DAYS", "365")))
    obj.setdefault("updated_at", _iso_now())
    return obj

def _save_retention(obj: Dict[str, Any]) -> Dict[str, Any]:
    obj["updated_at"] = _iso_now()
    save_json(RETENTION_PATH, obj)
    return obj

class RetentionUpdateReq(BaseModel):
    enabled: Optional[bool] = None
    approvals_purge_after_days: Optional[int] = None

class PurgeReq(BaseModel):
    dry_run: bool = True

@app.get("/retention")
def get_retention():
    return _load_retention()

@app.post("/retention")
def update_retention(request: Request, req: RetentionUpdateReq):
    auth = authz(request, "admin")
    cur = _load_retention()
    if req.enabled is not None:
        cur["enabled"] = bool(req.enabled)
    if req.approvals_purge_after_days is not None:
        d = int(req.approvals_purge_after_days)
        if d < 1 or d > 36500:
            raise HTTPException(400, "approvals_purge_after_days must be 1..36500")
        cur["approvals_purge_after_days"] = d
    _save_retention(cur)

    append_audit_ex(request, {
        "type": "RETENTION_UPDATE",
        "enabled": cur["enabled"],
        "approvals_purge_after_days": cur["approvals_purge_after_days"],
    }, auth)
    return cur

@app.post("/retention/purge")
def purge_retention(request: Request, req: PurgeReq):
    auth = authz(request, "admin")
    cfg = _load_retention()
    if not cfg.get("enabled", True):
        return {"ok": True, "skipped": True, "reason": "retention disabled"}

    days = int(cfg.get("approvals_purge_after_days", 365))
    cutoff = datetime.utcnow().timestamp() - (days * 86400)

    to_delete = []
    for fn in os.listdir(APPROVAL_DIR):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(APPROVAL_DIR, fn)
        obj = load_json(path, {})
        _ensure_archive_fields(obj)
        dt = _parse_iso(obj.get("archived_at"))
        if not dt:
            continue
        if dt.timestamp() < cutoff:
            to_delete.append({
                "approval_id": obj.get("approval_id"),
                "archived_at": obj.get("archived_at"),
                "path": path
            })

    if req.dry_run:
        return {"ok": True, "dry_run": True, "purge_after_days": days, "candidates": len(to_delete), "sample": to_delete[:10]}

    deleted = 0
    for it in to_delete:
        try:
            os.remove(it["path"])
            deleted += 1
        except Exception:
            pass

    append_audit_ex(request, {
        "type": "RETENTION_PURGE",
        "dry_run": False,
        "purge_after_days": days,
        "candidates": len(to_delete),
        "deleted": deleted,
    }, auth)
    return {"ok": True, "dry_run": False, "purge_after_days": days, "candidates": len(to_delete), "deleted": deleted}

# ============================================================
# Ask Master (M3-3 + M3-3.2)
# ============================================================
@app.post("/approvals/{approval_id}/ask_master")
def ask_master(request: Request, approval_id: str, req: AskMasterReq):
    auth = authz(request, "approver")
    obj = _load_approval(approval_id)

    if obj.get("decision_state") != "APPROVED":
        raise HTTPException(400, "Approval must be APPROVED to call master")
    if obj.get("gate", {}).get("decision") == "BLOCK":
        raise HTTPException(400, "Blocked by MasterGate")

    final_prompt = (obj.get("final_prompt") or "").strip()
    if not final_prompt:
        raise HTTPException(400, "final_prompt is empty")

    try:
        timeout_s = int(os.getenv("MASTER_TIMEOUT_S", "60"))
    except Exception:
        timeout_s = 60

    schema_prompt = _build_master_prompt(final_prompt)
    max_retry = int(os.getenv("MASTER_JSON_RETRY", "2"))

    last_err: Optional[str] = None
    last_reply: Any = None
    parsed: Optional[Dict[str, Any]] = None
    attempt = 0

    for attempt in range(max_retry + 1):
        try:
            if attempt == 0:
                prompt_to_send = schema_prompt
            else:
                prev_txt = (last_reply or {}).get("text") if isinstance(last_reply, dict) else str(last_reply or "")
                prompt_to_send = _repair_prompt(prev_txt, str(last_err))
            last_reply = call_master(req.provider, prompt_to_send)
        except Exception as e:
            obj["master_provider"] = req.provider
            obj["master_reply"] = None
            obj["master_reply_json"] = None
            obj["master_reply_schema_version"] = MASTER_SCHEMA_VERSION
            obj["master_reply_parse_error"] = None
            obj["master_error"] = str(e)[:2000]
            _save_approval(obj)

            append_audit_ex(request, {
                "type": "MASTER_CALL_FAILED",
                "approval_id": approval_id,
                "provider": req.provider,
                "timeout_s": timeout_s,
                "error": str(e)[:2000],
            }, auth)
            raise HTTPException(502, f"Master call failed: {str(e)[:200]}")

        text = str(last_reply.get("text") or "") if isinstance(last_reply, dict) else str(last_reply or "")
        parsed, last_err = _parse_master_reply_json(text)
        if parsed is not None:
            parsed = sanitize_master_reply_json(parsed)
            break

    obj["master_provider"] = req.provider
    obj["master_reply"] = last_reply
    obj["master_reply_json"] = parsed
    obj["master_reply_schema_version"] = MASTER_SCHEMA_VERSION
    obj["master_reply_parse_error"] = last_err
    obj["master_error"] = None
    _save_approval(obj)

    append_audit_ex(request, {
        "type": "MASTER_CALL",
        "approval_id": approval_id,
        "provider": req.provider,
        "model": last_reply.get("model") if isinstance(last_reply, dict) else None,
        "prompt_hash": obj.get("gate", {}).get("prompt_hash"),
        "schema_version": MASTER_SCHEMA_VERSION,
        "parse_ok": parsed is not None,
        "parse_error": last_err,
        "attempts": (attempt + 1),
    }, auth)

    return {"approval_id": approval_id, "ok": True, "schema_version": MASTER_SCHEMA_VERSION, "parse_ok": parsed is not None, "parse_error": last_err}

# ============================================================
# Apply Feedback
# ============================================================
@app.post("/approvals/{approval_id}/apply_feedback")
def apply_feedback(request: Request, approval_id: str, req: ApplyFeedbackReq):
    auth = authz(request, "operator")
    obj = _load_approval(approval_id)
    if obj.get("decision_state") != "APPROVED":
        raise HTTPException(400, "Approval must be APPROVED")
    if obj.get("master_reply") is None:
        raise HTTPException(400, "master_reply is empty. Call master first.")

    commands = _extract_verification_commands((obj.get("master_reply_json") or obj.get("master_reply")))
    if not commands:
        raise HTTPException(400, "No verification commands found in master_reply")

    commands, dropped = sanitize_commands_list(commands)
    if dropped:
        append_audit_ex(request, {"type": "MASTER_REPLY_COMMANDS_DROPPED", "approval_id": approval_id, "count": len(dropped), "examples": dropped[:5]}, auth)
    if not commands:
        raise HTTPException(400, f"All commands were dropped by container-safe filter. dropped={len(dropped)}")

    commands = commands[: max(1, int(req.max_commands))]

    append_audit_ex(request, {"type": "APPLY_FEEDBACK_STARTED", "approval_id": approval_id, "actor": req.actor, "commands": commands}, auth)

    runs: List[Dict[str, Any]] = obj.get("apply_feedback_runs") or []
    for idx, cmd in enumerate(commands, start=1):
        ok, reason = _is_safe_cmd(cmd)
        run_id = str(uuid.uuid4())

        if not ok:
            step = {"run_id": run_id, "step": idx, "command": cmd, "blocked": True, "block_reason": reason, "exit_code": 126, "stdout": "", "stderr": f"Blocked by server filter: {reason}", "evidence_refs": []}
            runs.append(step)
            append_audit_ex(request, {"type": "APPLY_FEEDBACK_STEP", "approval_id": approval_id, "run_id": run_id, "step": idx, "blocked": True, "reason": reason}, auth)
            if req.stop_on_fail:
                break
            continue

        run_req = {"run_id": run_id, "target_id": "local-agent-1", "script": cmd, "timeout_s": int(req.timeout_s), "approval_required": False, "evidence_requests": []}
        result = run_script(SUBAGENT_URL, run_req, timeout_s=int(req.timeout_s) + 20)
        step = {"run_id": run_id, "step": idx, "command": cmd, "blocked": False, "exit_code": result.get("exit_code"), "stdout": (result.get("stdout", "") or "")[:200000], "stderr": (result.get("stderr", "") or "")[:200000], "evidence_refs": result.get("evidence_refs", [])}
        runs.append(step)
        append_audit_ex(request, {"type": "APPLY_FEEDBACK_STEP", "approval_id": approval_id, "run_id": run_id, "step": idx, "command": cmd, "exit_code": step["exit_code"]}, auth)
        if req.stop_on_fail and step["exit_code"] != 0:
            break

    obj["apply_feedback_runs"] = runs
    _save_approval(obj)
    append_audit_ex(request, {"type": "APPLY_FEEDBACK_DONE", "approval_id": approval_id, "actor": req.actor, "steps": len(runs)}, auth)
    return {"approval_id": approval_id, "apply_feedback_runs": runs[-len(commands):]}

# ============================================================
# Settings Status (M2)
# ============================================================
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
            r = requests.get(url, timeout=2)
            ollama["status_code"] = r.status_code
            ollama["ok"] = (r.status_code == 200)
            if r.status_code != 200:
                ollama["error"] = (r.text[:200] if r.text else f"HTTP {r.status_code}")
        except Exception as e:
            ollama["error"] = str(e)[:200]

    return {
        "openai": {"configured": openai_key_set, "model": os.getenv("OPENAI_MODEL", ""), "note": "Key presence only"},
        "anthropic": {"configured": anthropic_key_set, "model": os.getenv("ANTHROPIC_MODEL", ""), "note": "Key presence only"},
        "ollama": ollama,
    }

# ============================================================
# ApplyFeedback + Validate (closed loop)
# ============================================================
@app.post("/approvals/{approval_id}/apply_feedback_and_validate")
def apply_feedback_and_validate(request: Request, approval_id: str, req: ApplyFeedbackReq):
    auth = authz(request, "operator")
    obj = _load_approval(approval_id)

    if obj.get("decision_state") != "APPROVED":
        raise HTTPException(400, "Approval must be APPROVED")
    if obj.get("master_reply") is None:
        raise HTTPException(400, "master_reply is empty. Call master first.")

    commands = _extract_verification_commands((obj.get("master_reply_json") or obj.get("master_reply")))
    if not commands:
        raise HTTPException(400, "No verification commands found in master_reply")

    commands, dropped = sanitize_commands_list(commands)
    if dropped:
        append_audit_ex(request, {"type": "MASTER_REPLY_COMMANDS_DROPPED", "approval_id": approval_id, "count": len(dropped), "examples": dropped[:5]}, auth)
    if not commands:
        raise HTTPException(400, f"All commands were dropped by container-safe filter. dropped={len(dropped)}")
    commands = commands[: max(1, int(req.max_commands))]

    append_audit_ex(request, {
        "type": "APPLY_FEEDBACK_VALIDATE_STARTED",
        "approval_id": approval_id,
        "actor": req.actor,
        "commands": commands,
        "timeout_s": int(req.timeout_s),
        "stop_on_fail": bool(req.stop_on_fail),
    }, auth)

    runs: List[Dict[str, Any]] = obj.get("apply_feedback_runs") or []
    new_runs: List[Dict[str, Any]] = []

    for idx, cmd in enumerate(commands, start=1):
        ok, reason = _is_safe_cmd(cmd)
        run_id = str(uuid.uuid4())

        if not ok:
            step = {"run_id": run_id, "step": idx, "command": cmd, "blocked": True, "block_reason": reason, "exit_code": 126, "stdout": "", "stderr": f"Blocked: {reason}", "evidence_refs": []}
            runs.append(step); new_runs.append(step)
            append_audit_ex(request, {"type": "APPLY_FEEDBACK_VALIDATE_STEP", "approval_id": approval_id, "run_id": run_id, "step": idx, "blocked": True, "reason": reason}, auth)
            if req.stop_on_fail:
                break
            continue

        run_req = {"run_id": run_id, "target_id": "local-agent-1", "script": cmd, "timeout_s": int(req.timeout_s), "approval_required": False, "evidence_requests": []}
        result = run_script(SUBAGENT_URL, run_req, timeout_s=int(req.timeout_s) + 20)

        step = {"run_id": run_id, "step": idx, "command": cmd, "blocked": False, "exit_code": result.get("exit_code"), "stdout": (result.get("stdout", "") or "")[:200000], "stderr": (result.get("stderr", "") or "")[:200000], "evidence_refs": result.get("evidence_refs", [])}
        runs.append(step); new_runs.append(step)
        append_audit_ex(request, {"type": "APPLY_FEEDBACK_VALIDATE_STEP", "approval_id": approval_id, "run_id": run_id, "step": idx, "command": cmd, "exit_code": step["exit_code"]}, auth)
        if req.stop_on_fail and step["exit_code"] != 0:
            break

    failed_steps = []
    for r in new_runs:
        if r.get("blocked") or r.get("exit_code") != 0:
            failed_steps.append({"step": r.get("step"), "command": r.get("command"), "exit_code": r.get("exit_code"), "reason": (r.get("block_reason") or (r.get("stderr") or "")[:200] or "failed")})

    validate_obj = {
        "pass": len(failed_steps) == 0,
        "failed_steps": failed_steps[:50],
        "evaluated_commands": commands,
        "evaluated_count": len(new_runs),
    }

    obj["apply_feedback_runs"] = runs
    obj["apply_feedback_validate"] = validate_obj
    _save_approval(obj)

    append_audit_ex(request, {"type": "APPLY_FEEDBACK_VALIDATE_DONE", "approval_id": approval_id, "actor": req.actor, "pass": validate_obj["pass"], "failed_count": len(failed_steps)}, auth)

    return {"approval_id": approval_id, "pass": validate_obj["pass"], "failed_steps": validate_obj["failed_steps"], "evaluated_count": validate_obj["evaluated_count"]}

@app.post("/approvals/{approval_id}/apply_feedback_and_validate/")
def apply_feedback_and_validate_slash(approval_id: str, req: ApplyFeedbackReq):
    return apply_feedback_and_validate(approval_id, req)

# ---------- Approval Evidence Pack ZIP ----------
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

# ============================================================
# Bulk Decide (single definition)
# ============================================================
class BulkDecideReq(BaseModel):
    approval_ids: List[str]
    decision: str  # approve|reject
    actor: str = "admin"
    reason: str = ""

@app.post("/approvals/bulk_decide")
def approvals_bulk_decide(request: Request, req: BulkDecideReq):
    auth = authz(request, "approver")
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

    append_audit_ex(request, {
        "type": "MASTERGATE_BULK_DECISION",
        "decision": decision.upper(),
        "actor": actor,
        "reason": reason,
        "requested": len(ids),
        "approved": approved,
        "rejected": rejected,
        "skipped": skipped,
    }, auth)

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
