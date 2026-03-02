from __future__ import annotations
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

class WFState(TypedDict, total=False):
    project_id: str
    request_text: str
    timeout_s: int

    plan: str
    commands: List[str]

    dispatch_runs: List[Dict[str, Any]]
    validate: Dict[str, Any]

    diagnosis: Dict[str, Any]
    fix_commands: List[str]
    fix_runs: List[Dict[str, Any]]
    retry_count: int
    max_retries: int

    step_log: List[Dict[str, Any]]
    decision_branch: str
    error: str

def build_graph(dispatch_fn):
    """
    dispatch_fn(cmd: str, timeout_s: int) -> dict
      returns: {exit_code, stdout, stderr, evidence_refs, run_id}
    """

    def intake(state: WFState) -> WFState:
        state.setdefault("step_log", [])
        state.setdefault("retry_count", 0)
        state.setdefault("max_retries", 2)
        state.setdefault("timeout_s", 60)
        state["step_log"].append({"node": "Intake", "ok": True})
        return state

    def plan(state: WFState) -> WFState:
        req = (state.get("request_text") or "").strip()
        state["plan"] = (
            "M1: Gather basic system facts\n"
            "M2: Collect service/network snapshot\n"
            "M3: Validate outputs (exit_code)\n"
            f"User request: {req}"
        )
        state["step_log"].append({"node": "Plan", "ok": True})
        return state

    def generate_artifacts(state: WFState) -> WFState:
        state["commands"] = ["uname -a", "uptime", "df -h", "ss -lntp"]
        state["step_log"].append({"node": "GenerateArtifacts", "ok": True, "commands": state["commands"]})
        return state

    def dispatch(state: WFState) -> WFState:
        runs: List[Dict[str, Any]] = []
        for i, cmd in enumerate(state.get("commands") or [], start=1):
            r = dispatch_fn(cmd, int(state.get("timeout_s") or 60))
            runs.append({
                "step": i,
                "command": cmd,
                "exit_code": r.get("exit_code"),
                "stdout": (r.get("stdout") or "")[:200000],
                "stderr": (r.get("stderr") or "")[:200000],
                "evidence_refs": r.get("evidence_refs") or [],
                "run_id": r.get("run_id"),
            })
        state["dispatch_runs"] = runs
        state["step_log"].append({"node": "Dispatch", "ok": True, "steps": len(runs), "retry": state.get("retry_count", 0)})
        return state

    def collect(state: WFState) -> WFState:
        state["step_log"].append({"node": "Collect", "ok": True, "runs": len(state.get("dispatch_runs") or [])})
        return state

    def validate(state: WFState) -> WFState:
        runs = state.get("dispatch_runs") or []
        failed = [r for r in runs if r.get("exit_code") != 0]
        state["validate"] = {
            "pass": len(failed) == 0,
            "failed_steps": [{"step": r["step"], "command": r["command"], "exit_code": r.get("exit_code"), "stderr": r.get("stderr","")} for r in failed],
        }
        state["step_log"].append({"node": "Validate", "ok": state["validate"]["pass"], "failed": len(failed)})
        return state

    def diagnose(state: WFState) -> WFState:
        failed = (state.get("validate") or {}).get("failed_steps") or []
        kind = "unknown"
        missing_cmds: List[str] = []
        for f in failed:
            ec = f.get("exit_code")
            cmd = (f.get("command") or "").strip()
            err = (f.get("stderr") or "").lower()
            if ec == 127 or "not found" in err:
                kind = "missing_tools"
                missing_cmds.append(cmd.split()[0] if cmd else "")
        diagnosis = {"kind": kind, "missing_cmds": sorted(list(set([c for c in missing_cmds if c])))}
        state["diagnosis"] = diagnosis
        state["step_log"].append({"node": "Diagnose", "ok": True, "diagnosis": diagnosis})
        return state

    def decide(state: WFState) -> WFState:
        if (state.get("validate") or {}).get("pass") is True:
            state["decision_branch"] = "done"
            state["fix_commands"] = []
            state["step_log"].append({"node": "Decide", "ok": True, "branch": "done"})
            return state

        diag = state.get("diagnosis") or {}
        fix_cmds: List[str] = []
        if diag.get("kind") == "missing_tools":
            pkg_map = {"uptime": "procps", "ss": "iproute2"}
            pkgs = []
            for c in diag.get("missing_cmds") or []:
                if c in pkg_map:
                    pkgs.append(pkg_map[c])
            pkgs = sorted(list(set(pkgs)))
            if pkgs and int(state.get("retry_count") or 0) < int(state.get("max_retries") or 2):
                fix_cmds = ["apt-get update", "DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends " + " ".join(pkgs)]
                state["decision_branch"] = "fix"
            else:
                state["decision_branch"] = "stop"
        else:
            state["decision_branch"] = "stop"

        state["fix_commands"] = fix_cmds
        state["step_log"].append({"node": "Decide", "ok": True, "branch": state["decision_branch"], "fix_commands": fix_cmds})
        return state

    def fix(state: WFState) -> WFState:
        fix_cmds = state.get("fix_commands") or []
        results: List[Dict[str, Any]] = []
        for cmd in fix_cmds:
            r = dispatch_fn(cmd, int(state.get("timeout_s") or 60))
            results.append({
                "command": cmd,
                "exit_code": r.get("exit_code"),
                "stdout": (r.get("stdout") or "")[:200000],
                "stderr": (r.get("stderr") or "")[:200000],
                "evidence_refs": r.get("evidence_refs") or [],
                "run_id": r.get("run_id"),
            })
        state.setdefault("fix_runs", [])
        state["fix_runs"].append({"attempt": int(state.get("retry_count") or 0) + 1, "results": results})
        state["retry_count"] = int(state.get("retry_count") or 0) + 1
        state["step_log"].append({"node": "Fix", "ok": True, "attempt": state["retry_count"]})
        return state

    def stop(state: WFState) -> WFState:
        state["error"] = "Stopped: cannot auto-fix or max retries reached"
        state["step_log"].append({"node": "Stop", "ok": False, "reason": state["error"]})
        return state

    g = StateGraph(WFState)
    g.add_node("Intake", intake)
    g.add_node("Plan", plan)
    g.add_node("GenerateArtifacts", generate_artifacts)
    g.add_node("Dispatch", dispatch)
    g.add_node("Collect", collect)
    g.add_node("Validate", validate)
    g.add_node("Diagnose", diagnose)
    g.add_node("Decide", decide)
    g.add_node("Fix", fix)
    g.add_node("Stop", stop)

    g.set_entry_point("Intake")
    g.add_edge("Intake", "Plan")
    g.add_edge("Plan", "GenerateArtifacts")
    g.add_edge("GenerateArtifacts", "Dispatch")
    g.add_edge("Dispatch", "Collect")
    g.add_edge("Collect", "Validate")
    g.add_edge("Validate", "Diagnose")
    g.add_edge("Diagnose", "Decide")

    def route(state: WFState) -> str:
        return state.get("decision_branch", "stop")

    g.add_conditional_edges("Decide", route, {"done": END, "fix": "Fix", "stop": "Stop"})
    g.add_edge("Fix", "Dispatch")
    g.add_edge("Stop", END)

    return g.compile()
