"""다층 퍼미션 결정 파이프라인.

결정 소스 우선순위:
1. API Key 범위 (X-API-Key의 허용 명령)
2. RBAC 역할 권한 (rbac_service)
3. Policy Engine 규칙 (policy_engine)
4. Approval Engine (approval_engine)
5. Hook pre_dispatch 결과 (hook_engine)
6. risk_level 기반 자동 판단

어느 소스든 deny를 반환하면 즉시 거부된다.
모든 소스가 allow이면 허용.
ask를 반환하는 소스가 있으면 사용자 확인이 필요하다.
"""

import os
from dataclasses import dataclass, field
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor


_DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


def _conn():
    return psycopg2.connect(_DB_URL)


# ── 결정 모델 ────────────────────────────────────────────────────────────────


@dataclass
class PermissionDecision:
    """퍼미션 결정 결과."""
    behavior: str       # "allow" | "deny" | "ask"
    source: str         # 결정을 내린 소스
    reason: str = ""    # 사유
    details: dict[str, Any] = field(default_factory=dict)


class PermissionDenied(Exception):
    """퍼미션 거부."""
    def __init__(self, decision: PermissionDecision):
        self.decision = decision
        super().__init__(f"Permission denied by {decision.source}: {decision.reason}")


# ── Denial Tracking (Claude Code 패턴) ───────────────────────────────────────

_denial_counts: dict[str, int] = {}
_DENIAL_ESCALATION_THRESHOLD = 3


def _track_denial(actor_id: str, tool_name: str) -> int:
    """연속 거부 횟수 추적. 임계값 초과 시 에스컬레이션."""
    key = f"{actor_id}:{tool_name}"
    _denial_counts[key] = _denial_counts.get(key, 0) + 1
    return _denial_counts[key]


def _reset_denial(actor_id: str, tool_name: str) -> None:
    """허용 시 거부 카운터 리셋."""
    key = f"{actor_id}:{tool_name}"
    _denial_counts.pop(key, None)


# ── 개별 소스 체크 ────────────────────────────────────────────────────────────


def _check_api_key_scope(actor_id: str, action: str) -> PermissionDecision | None:
    """API Key가 특정 범위만 허용하는 경우 체크."""
    # 현재는 단일 키 방식이므로 항상 통과. 향후 키별 scope 지원 시 확장.
    return None


def _check_rbac(actor_id: str, permission: str) -> PermissionDecision | None:
    """RBAC 역할 기반 권한 체크.

    actor에게 역할이 할당되어 있으면 해당 역할의 권한을 체크한다.
    역할이 없으면(미등록 actor) → None 반환 (다음 소스로 위임).
    """
    try:
        from packages.rbac_service import get_actor_permissions
        perms = get_actor_permissions(actor_id)
        if not perms:
            return None  # 역할 미할당 → 다음 소스로 위임 (deny가 아님)
        if "*" in perms or permission in perms:
            return None  # 권한 있음 → 통과
        return PermissionDecision(
            behavior="deny",
            source="rbac",
            reason=f"Actor '{actor_id}' lacks permission '{permission}'",
        )
    except Exception:
        return None  # RBAC 서비스 오류 → 다음 소스로


def _check_policy(env: str, risk_level: str, mode: str) -> PermissionDecision | None:
    """환경/위험도 기반 정책 체크."""
    try:
        from packages.policy_engine import get_policy
        policy = get_policy(env)

        # 실행 모드 체크
        blocked = policy.get("blocked_modes", [])
        if mode in blocked:
            return PermissionDecision(
                behavior="deny",
                source="policy",
                reason=f"Mode '{mode}' is blocked in environment '{env}'",
            )

        allowed = policy.get("allowed_modes", [])
        if allowed and mode not in allowed:
            return PermissionDecision(
                behavior="deny",
                source="policy",
                reason=f"Mode '{mode}' not in allowed modes for '{env}': {allowed}",
            )

        # 위험도 기반 승인 요구
        requires_approval = policy.get("requires_approval", [])
        if risk_level in requires_approval:
            return PermissionDecision(
                behavior="ask",
                source="policy",
                reason=f"Risk level '{risk_level}' requires approval in '{env}'",
            )

        return None
    except Exception:
        return None


def _check_approval(project_id: str | None) -> PermissionDecision | None:
    """프로젝트 승인 상태 체크."""
    if not project_id:
        return None
    try:
        from packages.approval_engine import check_requires_approval, get_approval_status
        if check_requires_approval(project_id):
            status = get_approval_status(project_id)
            if not status.get("approved"):
                return PermissionDecision(
                    behavior="ask",
                    source="approval",
                    reason="Project requires master review approval before execution",
                    details=status,
                )
        return None
    except Exception:
        return None


def _check_risk_auto(risk_level: str, tool_name: str) -> PermissionDecision | None:
    """risk_level + tool 특성 기반 자동 판단."""
    # 읽기 전용 도구는 항상 허용
    try:
        from packages.tool_validator import load_tool_schemas
        schemas = load_tool_schemas()
        schema = schemas.get(tool_name)
        if schema and schema.is_read_only:
            return None  # 즉시 허용
        if schema and schema.is_destructive:
            return PermissionDecision(
                behavior="ask",
                source="risk_auto",
                reason=f"Tool '{tool_name}' is marked as destructive",
            )
    except Exception:
        pass

    if risk_level == "critical":
        return PermissionDecision(
            behavior="ask",
            source="risk_auto",
            reason="Critical risk level requires explicit confirmation",
        )
    return None


# ── 통합 결정 파이프라인 ──────────────────────────────────────────────────────


def check_permission(
    actor_id: str = "system",
    permission: str = "*",
    tool_name: str = "",
    risk_level: str = "medium",
    env: str = "default",
    mode: str = "one_shot",
    project_id: str | None = None,
    params: dict | None = None,
) -> PermissionDecision:
    """다층 퍼미션 체크. 모든 소스를 순서대로 평가.

    Args:
        actor_id: 요청자 (user ID, API key, agent ID)
        permission: RBAC 권한 문자열 (예: "project:execute")
        tool_name: 실행하려는 도구명
        risk_level: 위험도 (low/medium/high/critical)
        env: 환경 (prod/staging/lab/default)
        mode: 실행 모드 (one_shot/batch/continuous)
        project_id: 프로젝트 ID
        params: 추가 파라미터

    Returns:
        PermissionDecision (behavior: allow/deny/ask)
    """
    # 읽기전용 도구는 다른 소스 체크 전에 즉시 허용
    if tool_name:
        try:
            from packages.tool_validator import load_tool_schemas
            schemas = load_tool_schemas()
            schema = schemas.get(tool_name)
            if schema and schema.is_read_only:
                _reset_denial(actor_id, tool_name)
                return PermissionDecision(behavior="allow", source="read_only_tool")
        except Exception:
            pass

    checks = [
        lambda: _check_api_key_scope(actor_id, permission),
        lambda: _check_rbac(actor_id, permission),
        lambda: _check_policy(env, risk_level, mode),
        lambda: _check_approval(project_id),
        lambda: _check_risk_auto(risk_level, tool_name),
    ]

    ask_decisions: list[PermissionDecision] = []

    for check_fn in checks:
        decision = check_fn()
        if decision is None:
            continue
        if decision.behavior == "deny":
            _track_denial(actor_id, tool_name)
            return decision
        if decision.behavior == "ask":
            ask_decisions.append(decision)

    # ask가 있으면 첫 번째 ask 반환
    if ask_decisions:
        count = _track_denial(actor_id, tool_name)
        if count >= _DENIAL_ESCALATION_THRESHOLD:
            return PermissionDecision(
                behavior="deny",
                source="escalation",
                reason=f"Repeated denials ({count}x) for {actor_id}:{tool_name}",
            )
        return ask_decisions[0]

    # 모든 소스 통과
    _reset_denial(actor_id, tool_name)
    return PermissionDecision(behavior="allow", source="all_passed")
