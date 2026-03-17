"""Graph Runtime — LangGraph-based project lifecycle state machine.

Stage flow (full path):
  intake → plan → select_assets → resolve_targets → [approval_gate] → execute
         → validate → report → close

Bypass: plan → execute (skips select_assets/resolve_targets for simple projects)
Replan: execute/validate/report → plan
"""
from __future__ import annotations

import os
from typing import Any, Literal, TypedDict

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)

# ── Stage Definitions ─────────────────────────────────────────────────────────

DEFAULT_MANAGER_STAGES = [
    "intake",
    "plan",
    "select_assets",
    "resolve_targets",
    "execute",
    "validate",
    "report",
    "close",
]

# Each stage maps to its allowed next stages (set-based for flexibility)
VALID_TRANSITIONS: dict[str, set[str]] = {
    "intake": {"plan"},
    "plan": {"select_assets", "execute"},       # execute = bypass for simple projects
    "select_assets": {"resolve_targets", "execute"},  # execute = bypass
    "resolve_targets": {"execute"},
    "execute": {"validate"},
    "validate": {"report"},
    "report": {"close"},
    "close": set(),
}

# Stages from which replan (→ plan) is permitted
REPLAN_FROM_STAGES: set[str] = {"execute", "validate", "report"}


# ── Exceptions ────────────────────────────────────────────────────────────────

class GraphRuntimeError(Exception):
    pass


# ── Transition Helpers ────────────────────────────────────────────────────────

def get_next_stage(stage: str) -> str | None:
    """Return the primary (preferred) next stage, or None if terminal."""
    allowed = VALID_TRANSITIONS.get(stage)
    if allowed is None:
        raise GraphRuntimeError(f"Unknown stage: {stage}")
    if not allowed:
        return None
    # Prefer the forward-linear path
    preference_order = DEFAULT_MANAGER_STAGES
    for s in preference_order:
        if s in allowed:
            return s
    return next(iter(allowed))


def require_transition(current_stage: str, next_stage: str) -> None:
    """Raise GraphRuntimeError if the transition is not in VALID_TRANSITIONS."""
    allowed = VALID_TRANSITIONS.get(current_stage)
    if allowed is None:
        raise GraphRuntimeError(f"Unknown stage: {current_stage}")
    if next_stage not in allowed:
        raise GraphRuntimeError(
            f"Invalid stage transition: {current_stage} → {next_stage} "
            f"(allowed: {sorted(allowed)})"
        )


def build_minimal_project_graph() -> dict[str, object]:
    return {
        "stages": list(DEFAULT_MANAGER_STAGES),
        "transitions": {k: sorted(v) for k, v in VALID_TRANSITIONS.items()},
    }


def require_replan_allowed(current_stage: str) -> None:
    if current_stage not in REPLAN_FROM_STAGES:
        raise GraphRuntimeError(
            f"Replan not allowed from stage '{current_stage}'. "
            f"Allowed from: {sorted(REPLAN_FROM_STAGES)}"
        )


# ── LangGraph State Machine ───────────────────────────────────────────────────

class ProjectGraphState(TypedDict):
    project_id: str
    current_stage: str
    status: str
    replan_reason: str | None
    approval_required: bool
    approval_cleared: bool
    error: str | None
    stop_reason: str | None   # "approval_blocked" | "error" | None (complete)
    database_url: str | None


def _db(state: ProjectGraphState) -> str | None:
    return state.get("database_url")


def _node_plan(state: ProjectGraphState) -> ProjectGraphState:
    from packages.project_service import (
        ProjectStageError, ProjectNotFoundError, plan_project_record
    )
    try:
        project = plan_project_record(state["project_id"], database_url=_db(state))
        return {**state, "current_stage": project["current_stage"], "error": None}
    except (ProjectStageError, ProjectNotFoundError) as exc:
        return {**state, "error": str(exc), "stop_reason": "error"}


def _node_select_assets(state: ProjectGraphState) -> ProjectGraphState:
    from packages.project_service import (
        ProjectStageError, ProjectNotFoundError, select_assets_for_project
    )
    try:
        result = select_assets_for_project(state["project_id"], database_url=_db(state))
        return {**state, "current_stage": result["project"]["current_stage"], "error": None}
    except (ProjectStageError, ProjectNotFoundError) as exc:
        return {**state, "error": str(exc), "stop_reason": "error"}


def _node_resolve_targets(state: ProjectGraphState) -> ProjectGraphState:
    from packages.project_service import (
        ProjectStageError, ProjectNotFoundError, resolve_targets_for_project
    )
    try:
        result = resolve_targets_for_project(state["project_id"], database_url=_db(state))
        return {**state, "current_stage": result["project"]["current_stage"], "error": None}
    except (ProjectStageError, ProjectNotFoundError) as exc:
        return {**state, "error": str(exc), "stop_reason": "error"}


def _node_approval_gate(state: ProjectGraphState) -> ProjectGraphState:
    from packages.approval_engine import get_approval_status, ApprovalError
    try:
        status = get_approval_status(state["project_id"], database_url=_db(state))
        return {
            **state,
            "approval_required": status["requires_approval"],
            "approval_cleared": status["cleared"],
            "error": None,
        }
    except ApprovalError as exc:
        return {**state, "error": str(exc), "stop_reason": "error"}


def _node_execute(state: ProjectGraphState) -> ProjectGraphState:
    from packages.project_service import (
        ProjectStageError, ProjectNotFoundError, execute_project_record
    )
    try:
        result = execute_project_record(state["project_id"], database_url=_db(state))
        project = result["project"]
        return {
            **state,
            "current_stage": project["current_stage"],
            "replan_reason": None,
            "error": None,
        }
    except (ProjectStageError, ProjectNotFoundError) as exc:
        return {**state, "error": str(exc), "stop_reason": "error"}


def _node_validate(state: ProjectGraphState) -> ProjectGraphState:
    from packages.project_service import (
        ProjectStageError, ProjectNotFoundError, validate_project_record
    )
    try:
        result = validate_project_record(state["project_id"], database_url=_db(state))
        project = result["project"]
        return {**state, "current_stage": project["current_stage"], "error": None}
    except (ProjectStageError, ProjectNotFoundError) as exc:
        return {**state, "error": str(exc), "stop_reason": "error"}


def _node_report(state: ProjectGraphState) -> ProjectGraphState:
    from packages.project_service import (
        ProjectStageError, ProjectNotFoundError, finalize_report_stage_record
    )
    try:
        result = finalize_report_stage_record(state["project_id"], database_url=_db(state))
        project = result["project"]
        return {**state, "current_stage": project["current_stage"], "error": None}
    except (ProjectStageError, ProjectNotFoundError) as exc:
        return {**state, "error": str(exc), "stop_reason": "error"}


def _node_close(state: ProjectGraphState) -> ProjectGraphState:
    from packages.project_service import (
        ProjectStageError, ProjectNotFoundError, close_project
    )
    try:
        project = close_project(state["project_id"], database_url=_db(state))
        return {**state, "current_stage": project["current_stage"], "error": None}
    except (ProjectStageError, ProjectNotFoundError) as exc:
        return {**state, "error": str(exc), "stop_reason": "error"}


# ── Edge Conditions ───────────────────────────────────────────────────────────

def _route_after_approval_gate(
    state: ProjectGraphState,
) -> Literal["execute", "__end__"]:
    if state.get("stop_reason"):
        return "__end__"
    if state.get("approval_required") and not state.get("approval_cleared"):
        # Block: set stop_reason before ending
        return "__end__"
    return "execute"


def _route_after_execute(
    state: ProjectGraphState,
) -> Literal["validate", "plan", "__end__"]:
    if state.get("stop_reason"):
        return "__end__"
    if state.get("replan_reason"):
        return "plan"
    return "validate"


def _route_after_validate(
    state: ProjectGraphState,
) -> Literal["report", "plan", "__end__"]:
    if state.get("stop_reason"):
        return "__end__"
    if state.get("replan_reason"):
        return "plan"
    return "report"


def _route_after_report(
    state: ProjectGraphState,
) -> Literal["close", "plan", "__end__"]:
    if state.get("stop_reason"):
        return "__end__"
    if state.get("replan_reason"):
        return "plan"
    return "close"


def _route_on_error(
    state: ProjectGraphState,
) -> Literal["__end__"]:
    return "__end__"


# ── Graph Builder ─────────────────────────────────────────────────────────────

def build_project_graph():
    """Build and compile the LangGraph project lifecycle StateGraph."""
    from langgraph.graph import StateGraph, END

    g = StateGraph(ProjectGraphState)

    # Nodes
    g.add_node("plan", _node_plan)
    g.add_node("select_assets", _node_select_assets)
    g.add_node("resolve_targets", _node_resolve_targets)
    g.add_node("approval_gate", _node_approval_gate)
    g.add_node("execute", _node_execute)
    g.add_node("validate", _node_validate)
    g.add_node("report", _node_report)
    g.add_node("close", _node_close)

    # Entry point
    g.set_entry_point("plan")

    # Linear edges (no branching needed)
    g.add_edge("plan", "select_assets")
    g.add_edge("select_assets", "resolve_targets")
    g.add_edge("resolve_targets", "approval_gate")
    g.add_edge("close", END)

    # Conditional edges
    g.add_conditional_edges(
        "approval_gate",
        _route_after_approval_gate,
        {"execute": "execute", "__end__": END},
    )
    g.add_conditional_edges(
        "execute",
        _route_after_execute,
        {"validate": "validate", "plan": "plan", "__end__": END},
    )
    g.add_conditional_edges(
        "validate",
        _route_after_validate,
        {"report": "report", "plan": "plan", "__end__": END},
    )
    g.add_conditional_edges(
        "report",
        _route_after_report,
        {"close": "close", "plan": "plan", "__end__": END},
    )

    return g.compile()


def run_project_graph(
    project_id: str,
    database_url: str | None = None,
    replan_reason: str | None = None,
) -> ProjectGraphState:
    """Run the project lifecycle graph autonomously until blocked or complete.

    The graph starts from plan and proceeds through select_assets → resolve_targets
    → approval_gate → execute → validate → report → close.

    Returns the final state. Inspect state["stop_reason"] and state["error"] to
    determine why execution stopped.
    """
    from packages.project_service import get_project_record, ProjectNotFoundError

    try:
        project = get_project_record(project_id, database_url=database_url)
    except ProjectNotFoundError as exc:
        return ProjectGraphState(
            project_id=project_id,
            current_stage="unknown",
            status="error",
            replan_reason=None,
            approval_required=False,
            approval_cleared=False,
            error=str(exc),
            stop_reason="error",
            database_url=database_url,
        )

    initial_state: ProjectGraphState = {
        "project_id": project_id,
        "current_stage": project["current_stage"],
        "status": project["status"],
        "replan_reason": replan_reason,
        "approval_required": False,
        "approval_cleared": False,
        "error": None,
        "stop_reason": None,
        "database_url": database_url,
    }

    graph = build_project_graph()
    final_state = graph.invoke(initial_state)

    # If approval was required but not cleared, annotate stop_reason
    if (
        final_state.get("approval_required")
        and not final_state.get("approval_cleared")
        and not final_state.get("stop_reason")
    ):
        final_state = {**final_state, "stop_reason": "approval_blocked"}

    return final_state
