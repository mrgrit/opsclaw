from typing import Any, Dict, List, Optional


ResolutionResult = Dict[str, Any]


def resolved_result(
    *,
    fact_key: str,
    value: Any,
    rationale: Optional[List[str]] = None,
    evidence_refs: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> ResolutionResult:
    return {
        "status": "resolved",
        "fact_key": fact_key,
        "value": value,
        "choices": [],
        "question": None,
        "approval": None,
        "rationale": rationale or [],
        "evidence_refs": evidence_refs or [],
        "meta": meta or {},
    }


def clarification_result(
    *,
    fact_key: str,
    question: str,
    choices: Optional[List[Any]] = None,
    rationale: Optional[List[str]] = None,
    evidence_refs: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> ResolutionResult:
    return {
        "status": "needs_clarification",
        "fact_key": fact_key,
        "value": None,
        "choices": choices or [],
        "question": question,
        "approval": None,
        "rationale": rationale or [],
        "evidence_refs": evidence_refs or [],
        "meta": meta or {},
    }


def approval_result(
    *,
    fact_key: str,
    action_summary: str,
    risk: str = "high",
    rationale: Optional[List[str]] = None,
    evidence_refs: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> ResolutionResult:
    return {
        "status": "needs_approval",
        "fact_key": fact_key,
        "value": None,
        "choices": [],
        "question": None,
        "approval": {
            "action_summary": action_summary,
            "risk": risk,
        },
        "rationale": rationale or [],
        "evidence_refs": evidence_refs or [],
        "meta": meta or {},
    }


def insufficient_result(
    *,
    fact_key: str,
    rationale: Optional[List[str]] = None,
    evidence_refs: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> ResolutionResult:
    return {
        "status": "insufficient_evidence",
        "fact_key": fact_key,
        "value": None,
        "choices": [],
        "question": None,
        "approval": None,
        "rationale": rationale or [],
        "evidence_refs": evidence_refs or [],
        "meta": meta or {},
    }