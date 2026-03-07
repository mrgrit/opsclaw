from datetime import datetime
import os, uuid, re
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
import playbook_store
import state_store
import audit_store
from workflows import playbook_runner
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal

from state_store import ensure_dirs, init_project, load_json, project_path, append_run, update_project, save_json
from a2a import run_script
from mastergate import mastergate_scan
from audit_store import append_audit

from workflows.basic_graph import build_graph
from evidence_pack import build_evidence_zip

from targets_store import list_targets, get_target, upsert_target, delete_target

import planner_v0
import re
import input_resolver

from master_clients import call_master, call_conn, Provider
import llm_registry
import probe_loop

PB_TEMPLATE_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

STATE_DIR = os.getenv("STATE_DIR", "/data/state")
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "/data/artifacts")
EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "/data/evidence")
AUDIT_DIR = os.getenv("AUDIT_DIR", "/data/audit")
SUBAGENT_URL = os.getenv("SUBAGENT_URL", "http://subagent:55123")
MASTERGATE_PROFILE = os.getenv("MASTERGATE_PROFILE", "enterprise-default")

APPROVAL_DIR = os.path.join(STATE_DIR, "_approvals")
ensure_dirs(STATE_DIR, ARTIFACT_DIR, EVIDENCE_DIR, AUDIT_DIR, APPROVAL_DIR)

app = FastAPI(title="OpsClaw Manager API", version="0.7.0")

# --- M3-3 hardening: container-safe + placeholder handling ---
PLACEHOLDER_RE = re.compile(r"<[^>]+>")  # e.g. <service_name>, <port>

# denylist: container/agent 환경에서 거의 항상 실패/위험
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
    - Drop commands with placeholders (<...>)
    - Drop denylisted commands (systemctl/journalctl/etc.)
    - If commands become empty, provide safe fallback commands
    - Promote questions into next_questions
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

        # placeholder guard
        if PLACEHOLDER_RE.search(cmd):
            dropped.append({"command": cmd, "reason": "placeholder detected"})
            continue

        # denylist guard
        why = _is_denied_command(cmd)
        if why:
            dropped.append({"command": cmd, "reason": why})
            continue

        safe.append(cmd)

    # ensure next_questions
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

    # if safe becomes empty, inject container-safe defaults
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
    obj["dropped_commands"] = dropped  # debug visibility (optional)
    return obj


def sanitize_commands_list(commands: List[str]) -> (List[str], List[Dict[str, str]]):
    """
    Apply same guards to a raw command list:
    - drop placeholders (<...>)
    - drop denylisted tokens (systemctl/journalctl/etc.)
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

def extract_required_inputs(playbook: dict) -> list[str]:
    found = set()

    def scan_str(s: str):
        for m in PB_TEMPLATE_RE.finditer(s or ""):
            found.add(m.group(1))

    def scan_legacy_steps(pb: dict):
        # legacy: steps[].commands[]
        for step in (pb.get("steps") or []):
            for cmd in (step.get("commands") or []):
                scan_str(str(cmd))

    def scan_jobs(pb: dict):
        # jobs: jobs.*.steps[].run
        jobs = pb.get("jobs") or {}
        if isinstance(jobs, dict):
            for _, spec in jobs.items():
                for step in (spec.get("steps") or []):
                    scan_str(str(step.get("run") or ""))

    scan_legacy_steps(playbook)
    scan_jobs(playbook)
    return sorted(found)


# ---------------- Models ----------------
class Target(BaseModel):
    id: str
    host: str = "local"
    notes: Optional[str] = None

class TargetReg(BaseModel):
    id: str
    base_url: str
    name: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: str = ""
    llm_conn_id: Optional[str] = None

class LLMConnReq(BaseModel):
    id: str
    name: str
    provider: Literal["ollama", "openai", "anthropic", "yncai"]
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    timeout_s: int = 60
    headers: Dict[str, str] = Field(default_factory=dict)

class LLMRolesReq(BaseModel):
    master_conn_id: Optional[str] = None
    manager_conn_id: Optional[str] = None
    subagent_default_conn_id: Optional[str] = None

class CreateProjectReq(BaseModel):
    project_type: str = "generic"
    targets: List[Target] = Field(default_factory=list)
    request_text: str = "run basic check"

class RunReq(BaseModel):
    command: str
    timeout_s: int = 60
    approval_required: bool = False
    target_id: str = "local-agent-1"

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
    target_id: str = "local-agent-1"

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


# --- M3-3: Master reply JSON schema + parser stabilization ---
MASTER_SCHEMA_VERSION = "m3-3.v1"

def _master_reply_schema_text() -> str:
    # Keep schema small + deterministic to improve compliance.
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
    import re
    t = (text or "").strip()
    if not t:
        return ""
    # strip ```json fences if present
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.I)
    t = re.sub(r"```\s*$", "", t).strip()

    # If pure JSON, return directly
    if t.startswith("{") and t.endswith("}"):
        return t

    # Find first balanced {...} block
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
        # map common variants
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

def _parse_master_reply_json(text: str) -> (Optional[Dict[str, Any]], Optional[str]):
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

    return uniq(cmds)

def resolve_subagent_url(target_id: str) -> str:
    # target_id 없으면 기본 로컬 subagent
    if not target_id:
        return SUBAGENT_URL

    # 1) 먼저 registry에서 찾는다
    t = get_target(target_id)
    if t:
        base = (t.get("base_url") or "").strip().rstrip("/")
        if not base:
            raise HTTPException(400, f"target base_url is empty: {target_id}")
        return base

    # 2) registry에 없을 때만 로컬 fallback 허용
    if target_id in ("local-agent-1", "local", "localhost"):
        return SUBAGENT_URL

    raise HTTPException(404, f"target not found: {target_id}")

# ---------------- Core ----------------
@app.get("/health")
def health():
    return {"ok": True, "subagent": SUBAGENT_URL}

# ============================================================
# M3-4.1: Targets Registry
# ============================================================
@app.get("/targets")
def api_list_targets():
    return {"items": list_targets()}

@app.get("/targets/{target_id}")
def api_get_target(target_id: str):
    t = get_target(target_id)
    if not t:
        raise HTTPException(404, "target not found")
    return t

# ============================================================
# M3-5.1: LLM Connection Registry + Role Binding
# ============================================================
@app.get("/llm/connections")
def api_list_llm_connections():
    items = llm_registry.list_llm_conns()
    safe_items = []
    for x in items:
        y = dict(x)
        if y.get("api_key"):
            y["api_key"] = "***"
        safe_items.append(y)
    return {"items": safe_items}

@app.get("/llm/connections/{conn_id}")
def api_get_llm_connection(conn_id: str):
    x = llm_registry.get_llm_conn(conn_id)
    if not x:
        raise HTTPException(404, "llm connection not found")
    y = dict(x)
    if y.get("api_key"):
        y["api_key"] = "***"
    return y

@app.post("/llm/connections")
def api_upsert_llm_connection(req: LLMConnReq):
    obj = llm_registry.upsert_llm_conn(req.model_dump())
    append_audit(AUDIT_DIR, {
        "type": "LLM_CONN_UPSERT",
        "conn_id": obj.get("id"),
        "provider": obj.get("provider"),
        "model": obj.get("model"),
        "base_url": obj.get("base_url"),
    })
    out = dict(obj)
    if out.get("api_key"):
        out["api_key"] = "***"
    return out

@app.delete("/llm/connections/{conn_id}")
def api_delete_llm_connection(conn_id: str):
    ok = llm_registry.delete_llm_conn(conn_id)
    if not ok:
        raise HTTPException(404, "llm connection not found")
    append_audit(AUDIT_DIR, {
        "type": "LLM_CONN_DELETE",
        "conn_id": conn_id,
    })
    return {"ok": True}

@app.get("/llm/roles")
def api_get_llm_roles():
    return llm_registry.get_llm_roles()

@app.post("/llm/roles")
def api_set_llm_roles(req: LLMRolesReq):
    roles = llm_registry.set_llm_roles(req.model_dump())
    append_audit(AUDIT_DIR, {
        "type": "LLM_ROLES_SET",
        "master_conn_id": roles.get("master_conn_id"),
        "manager_conn_id": roles.get("manager_conn_id"),
        "subagent_default_conn_id": roles.get("subagent_default_conn_id"),
    })
    return roles

@app.post("/llm/test/{conn_id}")
def api_test_llm_connection(conn_id: str, prompt: str = "Say OK in one short sentence."):
    conn = llm_registry.get_llm_conn(conn_id)
    if not conn:
        raise HTTPException(404, "llm connection not found")
    try:
        reply = call_conn(conn, prompt)
        return {
            "ok": True,
            "provider": reply.get("provider"),
            "model": reply.get("model"),
            "text": (reply.get("text") or "")[:2000],
        }
    except Exception as e:
        raise HTTPException(502, f"llm test failed: {str(e)[:300]}")

@app.post("/targets")
def api_upsert_target(req: TargetReg):
    try:
        t = upsert_target(req.model_dump())
        append_audit(AUDIT_DIR, {
            "type": "TARGET_UPSERT",
            "target_id": t.get("id"),
            "base_url": t.get("base_url"),
        })
        return t
    except Exception as e:
        raise HTTPException(400, str(e))

@app.delete("/targets/{target_id}")
def api_delete_target(target_id: str):
    ok = delete_target(target_id)
    if not ok:
        raise HTTPException(404, "target not found")
    append_audit(AUDIT_DIR, {
        "type": "TARGET_DELETE",
        "target_id": target_id,
    })
    return {"ok": True}

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

    # target_id는 RunReq에 필드로 넣는 게 정석이지만,
    # 혹시 아직 모델 수정 전이면 getattr로 안전하게 처리
    target_id = getattr(req, "target_id", None) or "local-agent-1"

    subagent_url = resolve_subagent_url(target_id)

    run_req = {
        "run_id": run_id,
        "target_id": target_id,
        "script": req.command,
        "timeout_s": req.timeout_s,
        "approval_required": req.approval_required,
        "evidence_requests": ["uname", "uptime", "df", "ss_listen"],
    }

    result = run_script(subagent_url, run_req, timeout_s=req.timeout_s + 20)

    # result -> run_obj (state에 쌓는 형태로 정리)
    run_obj = {
        "run_id": run_id,
        "target_id": target_id,
        "command": req.command,
        "exit_code": result.get("exit_code"),
        "stdout": (result.get("stdout") or "")[:200000],
        "stderr": (result.get("stderr") or "")[:200000],
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
        "target_id": target_id,
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

    try:
        timeout_s = int(os.getenv("MASTER_TIMEOUT_S", "60"))
    except Exception:
        timeout_s = 60

    # M3-3: schema enforcement prompt
    schema_prompt = _build_master_prompt(final_prompt)

    # M3-3: parse+retry to stabilize JSON
    max_retry = int(os.getenv("MASTER_JSON_RETRY", "2"))
    last_err = None
    last_reply = None
    parsed = None

    for attempt in range(max_retry + 1):
        try:
            prompt_to_send = schema_prompt if attempt == 0 else _repair_prompt((last_reply or {}).get("text") if isinstance(last_reply, dict) else str(last_reply or ""), str(last_err))
            last_reply = call_master(req.provider, prompt_to_send)
        except Exception as e:
            obj["master_provider"] = req.provider
            obj["master_reply"] = None
            obj["master_reply_json"] = None
            obj["master_reply_schema_version"] = MASTER_SCHEMA_VERSION
            obj["master_reply_parse_error"] = None
            obj["master_error"] = str(e)[:2000]
            _save_approval(obj)

            append_audit(AUDIT_DIR, {
                "type": "MASTER_CALL_FAILED",
                "approval_id": approval_id,
                "provider": req.provider,
                "timeout_s": timeout_s,
                "error": str(e)[:2000],
            })
            raise HTTPException(502, f"Master call failed: {str(e)[:200]}")

        text = ""
        if isinstance(last_reply, dict):
            text = str(last_reply.get("text") or "")
        else:
            text = str(last_reply or "")

        parsed, last_err = _parse_master_reply_json(text)
        if parsed is not None:
            # M3-3.2: container-safe + placeholder sanitize
            parsed = sanitize_master_reply_json(parsed)
            break

    # store (always store raw reply; parsed may be None)
    obj["master_provider"] = req.provider
    obj["master_reply"] = last_reply
    obj["master_reply_json"] = parsed
    obj["master_reply_schema_version"] = MASTER_SCHEMA_VERSION
    obj["master_reply_parse_error"] = last_err
    obj["master_error"] = None
    _save_approval(obj)

    append_audit(AUDIT_DIR, {
        "type": "MASTER_CALL",
        "approval_id": approval_id,
        "provider": req.provider,
        "model": last_reply.get("model") if isinstance(last_reply, dict) else None,
        "prompt_hash": obj.get("gate", {}).get("prompt_hash"),
        "schema_version": MASTER_SCHEMA_VERSION,
        "parse_ok": parsed is not None,
        "parse_error": last_err,
        "attempts": (attempt + 1),
    })

    # summary
    return {"approval_id": approval_id, "ok": True, "schema_version": MASTER_SCHEMA_VERSION, "parse_ok": parsed is not None, "parse_error": last_err}

# ---------- Apply Feedback ----------
@app.post("/approvals/{approval_id}/apply_feedback")
def apply_feedback(approval_id: str, req: ApplyFeedbackReq):
    obj = _load_approval(approval_id)
    if obj.get("decision_state") != "APPROVED":
        raise HTTPException(400, "Approval must be APPROVED")
    if obj.get("master_reply") is None:
        raise HTTPException(400, "master_reply is empty. Call master first.")

    commands = _extract_verification_commands((obj.get("master_reply_json") or obj.get("master_reply")))
    if not commands:
        raise HTTPException(400, "No verification commands found in master_reply")

    # M3-3.2: drop placeholders + denylisted cmds before execution
    commands, dropped = sanitize_commands_list(commands)
    if dropped:
        append_audit(AUDIT_DIR, {
            "type": "MASTER_REPLY_COMMANDS_DROPPED",
            "approval_id": approval_id,
            "count": len(dropped),
            "examples": dropped[:5],
        })
    if not commands:
        raise HTTPException(400, f"All commands were dropped by container-safe filter. dropped={len(dropped)}")

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
        subagent_url = resolve_subagent_url(req.target_id)
        result = run_script(subagent_url, run_req, timeout_s=int(req.timeout_s) + 20)
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

    commands = _extract_verification_commands((obj.get("master_reply_json") or obj.get("master_reply")))
    if not commands:
        raise HTTPException(400, "No verification commands found in master_reply")

    # M3-3.2: drop placeholders + denylisted cmds before execution
    commands, dropped = sanitize_commands_list(commands)
    if dropped:
        append_audit(AUDIT_DIR, {
            "type": "MASTER_REPLY_COMMANDS_DROPPED",
            "approval_id": approval_id,
            "count": len(dropped),
            "examples": dropped[:5],
        })
    if not commands:
        raise HTTPException(400, f"All commands were dropped by container-safe filter. dropped={len(dropped)}")

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
        subagent_url = resolve_subagent_url(req.target_id)
        result = run_script(subagent_url, run_req, timeout_s=int(req.timeout_s) + 20)

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
# (duplicate BulkDecideReq/approvals_bulk_decide removed in M3-3.2 hardening)
class RunPlaybookReq(BaseModel):
    playbook_id: str
    inputs: dict = {}
    target_id: str = "local-agent-1"
    timeout_s: int = 60
    approval_required: bool = False

@app.get("/playbooks")
def list_playbooks():
    return playbook_store.list_playbooks()

@app.get("/playbooks/{playbook_id}")
def get_playbook(playbook_id: str):
    pb = playbook_store.load_playbook(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="playbook not found")
    return pb

@app.post("/projects/{project_id}/run_playbook")
def run_playbook(project_id: str, req: RunPlaybookReq):
    pb = playbook_store.load_playbook(req.playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="playbook not found")

    subagent_url = resolve_subagent_url(req.target_id)

    # runner 실행 (현재 runner 시그니처에 맞게 호출)
    result = playbook_runner.run_playbook(
        playbook=pb,
        subagent_url=subagent_url,
        inputs=req.inputs,
        timeout_s=req.timeout_s,
        project_id=project_id,
        audit_dir=AUDIT_DIR,
        target_id=req.target_id,
        resolve_subagent_url_fn=resolve_subagent_url,  # NEW
    )

    # state 저장: playbook_runs[] append (state_store에 함수 추가 권장)
    state_store.append_playbook_run(STATE_DIR, project_id, {
        "playbook_id": req.playbook_id,
        "target_id": req.target_id,
        "result": result,
    })

    audit_store.append_audit(project_id, {
        "type": "RUN_PLAYBOOK",
        "project_id": project_id,
        "playbook_id": req.playbook_id,
        "target_id": req.target_id,
        "ok": bool(result.get("ok", True)),
    })

    return result


class PlanReq(BaseModel):
    request_text: str | None = None
    default_target_id: str = "local-agent-1"
    min_score: int = 3
    margin: int = 2

@app.post("/projects/{project_id}/plan")
def plan_project(project_id: str, req: PlanReq):
    # load project state
    st = load_json(project_path(STATE_DIR, project_id), {})
    rt = (req.request_text or "").strip()
    if not rt:
        # 1) 프로젝트에 직접 request_text가 있으면 우선
        rt = (st.get("request_text") or "").strip()

    if not rt:
        # 2) 없으면 todos[0].detail을 request_text로 사용 (현재 프로젝트 구조가 이 방식)
        todos = st.get("todos") or []
        if isinstance(todos, list) and todos:
            first = todos[0] if isinstance(todos[0], dict) else {}
            rt = (first.get("detail") or "").strip()

    request_text = rt

    # gather data
    tmp = list_targets()
    targets = tmp.get("items", []) if isinstance(tmp, dict) else (tmp or [])
    playbooks = playbook_store.list_playbooks()

    plan = planner_v0.plan_request(
        request_text=request_text,
        targets=targets,
        playbooks=playbooks,
        default_target_id=req.default_target_id,
        min_score=req.min_score,
        margin=req.margin,
    )

    # save into state
    st["plan"] = plan
    st["plan"]["created_at"] = datetime.utcnow().isoformat() + "Z"
    update_project(STATE_DIR, project_id, st)

    append_audit(AUDIT_DIR, {
        "type": "PLAN_DONE",
        "project_id": project_id,
        "status": plan.get("status"),
        "selected_playbook_id": plan.get("selected_playbook_id"),
        "selected_target_ids": plan.get("selected_target_ids"),
    })

    return plan

class LLMConnReq(BaseModel):
    id: str
    name: str
    provider: Literal["ollama", "openai", "anthropic", "yncai"]
    base_url: str = ""
    api_key: str = ""
    model: str
    timeout_s: int = 60
    headers: Dict[str, str] = Field(default_factory=dict)

class LLMRolesReq(BaseModel):
    master_conn_id: Optional[str] = None
    manager_conn_id: Optional[str] = None
    subagent_default_conn_id: Optional[str] = None

class RunAutoReq(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict)
    target_id: Optional[str] = None
    playbook_id: Optional[str] = None


@app.post("/projects/{project_id}/run_auto")
def run_auto(project_id: str, req: RunAutoReq):
    # load project
    st = load_json(project_path(STATE_DIR, project_id), {})
    if not st:
        raise HTTPException(status_code=404, detail="project not found")

    # -------- helper: pick request_text from project --------
    def _get_request_text() -> str:
        rt = (st.get("request_text") or "").strip()
        if rt:
            return rt
        todos = st.get("todos") or []
        if isinstance(todos, list) and todos and isinstance(todos[0], dict):
            return (todos[0].get("detail") or "").strip()
        return ""

    # -------- ensure plan exists (or re-plan if missing) --------
    plan = st.get("plan")
    if not isinstance(plan, dict) or not plan.get("status"):
        request_text = _get_request_text()

        append_audit(AUDIT_DIR, {
            "type": "PLAN_START",
            "project_id": project_id,
            "request_text": request_text,
        })

        tmp = list_targets()
        targets = tmp.get("items", []) if isinstance(tmp, dict) else (tmp or [])
        playbooks = playbook_store.list_playbooks()

        plan = planner_v0.plan_request(
            request_text=request_text,
            targets=targets,
            playbooks=playbooks,
            default_target_id="local-agent-1",
            min_score=3,
            margin=2,
        )
        plan["created_at"] = datetime.utcnow().isoformat() + "Z"

        st["plan"] = plan
        update_project(STATE_DIR, project_id, st)

        append_audit(AUDIT_DIR, {
            "type": "PLAN_DONE",
            "project_id": project_id,
            "status": plan.get("status"),
            "selected_playbook_id": plan.get("selected_playbook_id"),
            "selected_target_ids": plan.get("selected_target_ids"),
        })

    # -------- resolve selection (allow overrides) --------
    selected_playbook_id = (req.playbook_id or plan.get("selected_playbook_id")) if isinstance(plan, dict) else req.playbook_id
    selected_targets = (plan.get("selected_target_ids") or []) if isinstance(plan, dict) else []
    target_id = req.target_id or (selected_targets[0] if selected_targets else "local-agent-1")

    # -------- build inputs (MUST NOT reset later) --------
    inputs: Dict[str, Any] = {}
    if isinstance(plan, dict):
        inputs.update(plan.get("inputs") or {})
    inputs.update(req.inputs or {})

    # plan 자체가 ready가 아니고, playbook 선택도 안되면 여기서 종료
    if not selected_playbook_id:
        plan2 = dict(plan) if isinstance(plan, dict) else {"status": "needs_clarification"}
        plan2["status"] = "needs_clarification"
        plan2["next_questions"] = (plan2.get("next_questions") or [])
        if "playbook_id를 선택할 수 없습니다. playbook_id를 지정해 주세요." not in plan2["next_questions"]:
            plan2["next_questions"].append("playbook_id를 선택할 수 없습니다. playbook_id를 지정해 주세요.")
        plan2["inputs"] = inputs
        plan2["created_at"] = datetime.utcnow().isoformat() + "Z"

        st["plan"] = plan2
        update_project(STATE_DIR, project_id, st)
        return {"status": "needs_clarification", "plan": plan2}

    # playbook load
    pb = playbook_store.load_playbook(selected_playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="playbook not found")

    # run target url
    subagent_url = resolve_subagent_url(target_id)

    # -------- input resolver (discover -> auto choose -> ask) --------
    rr = input_resolver.resolve_inputs(
        audit_dir=AUDIT_DIR,
        project_id=project_id,
        playbook=pb,
        target_id=target_id,
        subagent_url=subagent_url,
        inputs=inputs,
        timeout_s=20,
    )

    inputs = rr.get("inputs") or inputs
    
    existing_plan = plan if isinstance(plan, dict) else {}
    resolver_rationales = dict(existing_plan.get("input_rationales") or {})
    resolver_rationales.update(rr.get("rationales") or {})

    resolver_approvals = list(existing_plan.get("pending_approvals") or [])
    resolver_approvals.extend(rr.get("approvals") or [])

    resolver_evidence_map = dict(existing_plan.get("evidence_map") or {})
    resolver_evidence_map.update(rr.get("evidence_map") or {})

    if rr.get("status") != "ready":
        # ---- 보호 키: 사용자만 결정해야 하는 값은 LLM이 대신 결정하지 않음 ----
        protected = {"iface_in", "iface_out"}  # M3-5.3: critical decision -> ask user
        missing_inputs = rr.get("missing_inputs") or []
        if any(k in protected for k in missing_inputs):
            plan2 = dict(plan) if isinstance(plan, dict) else {}
            plan2["status"] = "needs_clarification"
            plan2["missing_inputs"] = missing_inputs
            plan2["next_questions"] = rr.get("next_questions") or ["추가 확인이 필요합니다."]
            plan2["choices"] = rr.get("choices") or {}
            plan2["inputs"] = rr.get("inputs") or inputs
            plan2["created_at"] = datetime.utcnow().isoformat() + "Z"
            plan2["input_rationales"] = resolver_rationales
            plan2["pending_approvals"] = resolver_approvals
            plan2["evidence_map"] = resolver_evidence_map

            st["plan"] = plan2
            update_project(STATE_DIR, project_id, st)
            return {"status": "needs_clarification", "plan": plan2}

        # 1) resolver가 못 풀면 -> Master-guided probe loop로 먼저 해결 시도
        pr = probe_loop.probe_resolve_inputs(
            audit_dir=AUDIT_DIR,
            project_id=project_id,
            request_text=_get_request_text(),
            target_id=target_id,
            subagent_url=subagent_url,
            missing_inputs=missing_inputs,
            choices=rr.get("choices") or {},
            current_inputs=inputs,
            max_iters=2,
        )

        if pr.get("status") == "ready":
            inputs.update(pr.get("resolved_inputs") or {})

            # 2) resolved_inputs 반영 후 resolver 한 번 더
            rr2 = input_resolver.resolve_inputs(
                audit_dir=AUDIT_DIR,
                project_id=project_id,
                playbook=pb,
                target_id=target_id,
                subagent_url=subagent_url,
                inputs=inputs,
                timeout_s=20,
            )

            inputs = rr2.get("inputs") or inputs
            resolver_rationales.update(rr2.get("rationales") or {})

            rr2_approvals = rr2.get("approvals") or []
            if rr2_approvals:
                resolver_approvals.extend(rr2_approvals)

            resolver_evidence_map.update(rr2.get("evidence_map") or {})

            if rr2.get("status") == "ready":
                inputs = rr2.get("inputs") or inputs
            else:
                plan2 = dict(plan) if isinstance(plan, dict) else {}
                plan2["status"] = "needs_clarification"
                plan2["missing_inputs"] = rr2.get("missing_inputs")
                plan2["next_questions"] = rr2.get("next_questions")
                plan2["choices"] = rr2.get("choices")
                plan2["inputs"] = rr2.get("inputs") or inputs
                plan2["created_at"] = datetime.utcnow().isoformat() + "Z"
                plan2["input_rationales"] = dict(resolver_rationales)
                plan2["pending_approvals"] = list(resolver_approvals)
                plan2["evidence_map"] = dict(resolver_evidence_map)

                st["plan"] = plan2
                update_project(STATE_DIR, project_id, st)
                return {"status": "needs_clarification", "plan": plan2}

        elif pr.get("status") == "needs_clarification":
            q = pr.get("question") or {}
            plan2 = dict(plan) if isinstance(plan, dict) else {}
            plan2["status"] = "needs_clarification"
            plan2["missing_inputs"] = rr.get("missing_inputs")
            plan2["next_questions"] = q.get("next_questions") or rr.get("next_questions") or []
            plan2["choices"] = q.get("choices") or rr.get("choices") or {}
            plan2["inputs"] = inputs
            plan2["created_at"] = datetime.utcnow().isoformat() + "Z"
            plan2["input_rationales"] = dict(resolver_rationales)
            plan2["pending_approvals"] = list(resolver_approvals)
            plan2["evidence_map"] = dict(resolver_evidence_map)

            st["plan"] = plan2
            update_project(STATE_DIR, project_id, st)
            return {"status": "needs_clarification", "plan": plan2}

        else:
            # probe loop도 못 풀었으면 resolver 결과로 질문 반환
            plan2 = dict(plan) if isinstance(plan, dict) else {}
            plan2["status"] = "needs_clarification"
            plan2["missing_inputs"] = rr.get("missing_inputs")
            plan2["next_questions"] = rr.get("next_questions")
            plan2["choices"] = rr.get("choices")
            plan2["inputs"] = inputs
            plan2["created_at"] = datetime.utcnow().isoformat() + "Z"
            plan2["input_rationales"] = dict(resolver_rationales)
            plan2["pending_approvals"] = list(resolver_approvals)
            plan2["evidence_map"] = dict(resolver_evidence_map)

            st["plan"] = plan2
            update_project(STATE_DIR, project_id, st)
            return {"status": "needs_clarification", "plan": plan2}

    # resolver ready
    inputs = rr.get("inputs") or inputs

    # ✅ plan에 확정된 inputs + resolution metadata 반영
    plan2 = dict(plan) if isinstance(plan, dict) else {}
    plan2["inputs"] = dict(inputs)
    plan2["input_rationales"] = dict(resolver_rationales)
    plan2["pending_approvals"] = list(resolver_approvals)
    plan2["evidence_map"] = dict(resolver_evidence_map)
    st["plan"] = plan2
    update_project(STATE_DIR, project_id, st)
    plan = plan2

    append_audit(AUDIT_DIR, {
        "type": "RUN_AUTO_START",
        "project_id": project_id,
        "playbook_id": selected_playbook_id,
        "target_id": target_id,
        "inputs_keys": sorted(list(inputs.keys())),
    })

    # -------- run playbook --------
    result = playbook_runner.run_playbook(
        playbook=pb,
        subagent_url=subagent_url,
        inputs=inputs,
        timeout_s=60,
        project_id=project_id,
        audit_dir=AUDIT_DIR,
        target_id=target_id,
        resolve_subagent_url_fn=resolve_subagent_url,
    )

    # -------- validate fail -> LLM fix loop(1회) + retry --------
    if isinstance(result, dict) and isinstance(result.get("validate"), dict) and result["validate"].get("pass") is False:
        fx = probe_loop.probe_fix_and_retry(
            audit_dir=AUDIT_DIR,
            project_id=project_id,
            request_text=_get_request_text(),
            target_id=target_id,
            subagent_url=subagent_url,
            last_result=result,
            max_iters=1,
        )

        if fx.get("status") == "needs_clarification":
            plan2 = dict(plan) if isinstance(plan, dict) else {}
            q = fx.get("question") or {}
            plan2["status"] = "needs_clarification"
            plan2["next_questions"] = q.get("next_questions") or ["추가 확인이 필요합니다."]
            plan2["choices"] = q.get("choices") or {}
            plan2["inputs"] = inputs
            plan2["created_at"] = datetime.utcnow().isoformat() + "Z"
            plan2["input_rationales"] = dict(resolver_rationales)
            plan2["pending_approvals"] = list(resolver_approvals)
            plan2["evidence_map"] = dict(resolver_evidence_map)

            st["plan"] = plan2
            update_project(STATE_DIR, project_id, st)

            # 실패 결과도 저장(재현/증빙)
            state_store.append_playbook_run(STATE_DIR, project_id, {
                "playbook_id": selected_playbook_id,
                "target_id": target_id,
                "inputs": inputs,
                "result": result,
                "probe_fix": fx,
            })

            # 실행 상태/메타 반영
            plan2 = dict(st.get("plan") or plan or {})
            plan2["status"] = "executed"
            plan2["inputs"] = dict(inputs)
            plan2["input_rationales"] = dict(resolver_rationales)
            plan2["pending_approvals"] = list(resolver_approvals)
            plan2["evidence_map"] = dict(resolver_evidence_map)

            # needs_clarification 잔재 제거
            plan2.pop("missing_inputs", None)
            plan2.pop("choices", None)
            plan2.pop("next_questions", None)

            # 선택 결과 고정
            plan2["selected_playbook_id"] = selected_playbook_id
            plan2["selected_target_ids"] = [target_id]
            plan2["updated_at"] = datetime.utcnow().isoformat() + "Z"

            st["plan"] = plan2
            update_project(STATE_DIR, project_id, st)

            append_audit(AUDIT_DIR, {
                "type": "RUN_AUTO_DONE",
                "project_id": project_id,
                "playbook_id": selected_playbook_id,
                "target_id": target_id,
                "ok": False,
            })

            return {"status": "needs_clarification", "plan": plan2, "inputs": inputs, "result": result, "probe_fix": fx}

        # 1회 재시도
        result = playbook_runner.run_playbook(
            playbook=pb,
            subagent_url=subagent_url,
            inputs=inputs,
            timeout_s=60,
            project_id=project_id,
            audit_dir=AUDIT_DIR,
            target_id=target_id,
            resolve_subagent_url_fn=resolve_subagent_url,
        )

    # -------- persist playbook run (ALWAYS) --------
    state_store.append_playbook_run(STATE_DIR, project_id, {
        "playbook_id": selected_playbook_id,
        "target_id": target_id,
        "inputs": inputs,
        "result": result,
    })

    # --- plan clean-up / reflect resolved inputs after execution ---
    try:
        st2 = load_json(project_path(STATE_DIR, project_id), {}) or st
        plan2 = dict((st2.get("plan") or plan or {}) if isinstance((st2.get("plan") or plan), dict) else {})

        # executed 상태 반영
        plan2["status"] = "executed"
        plan2["inputs"] = dict(inputs)
        plan2["input_rationales"] = dict(resolver_rationales)
        plan2["pending_approvals"] = list(resolver_approvals)
        plan2["evidence_map"] = dict(resolver_evidence_map)

        # 이전 needs_clarification 잔재 제거
        plan2["missing_inputs"] = []
        plan2["choices"] = {}
        plan2["next_questions"] = []

        plan2["updated_at"] = datetime.utcnow().isoformat() + "Z"

        st2["plan"] = plan2
        update_project(STATE_DIR, project_id, st2)
        st = st2
        plan = plan2
    except Exception as e:
        append_audit(AUDIT_DIR, {"type": "PLAN_CLEANUP_FAIL", "project_id": project_id, "error": str(e)})

    append_audit(AUDIT_DIR, {
        "type": "RUN_AUTO_DONE",
        "project_id": project_id,
        "playbook_id": selected_playbook_id,
        "target_id": target_id,
        "ok": bool((result.get("validate") or {}).get("pass", True)) if isinstance(result, dict) else True,
    })

    # plan에도 마지막 inputs 저장(다음 호출에서 이어받기)
    plan2 = dict(plan) if isinstance(plan, dict) else {}
    plan2["inputs"] = dict(inputs)
    plan2["input_rationales"] = dict(resolver_rationales)
    plan2["pending_approvals"] = list(resolver_approvals)
    plan2["evidence_map"] = dict(resolver_evidence_map)
    plan2["created_at"] = datetime.utcnow().isoformat() + "Z"
    st["plan"] = plan2
    update_project(STATE_DIR, project_id, st)
    plan = plan2

    return {"status": "executed", "plan": plan2, "inputs": inputs, "result": result}