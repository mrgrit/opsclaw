"""
OpsClaw Permission Engine — 다층 퍼미션 통합.

기존 rbac_service, policy_engine, approval_engine를 하나의 결정 파이프라인으로 통합.
Claude Code의 7-source permission model 패턴을 참고.

기존 패키지는 그대로 유지하되, permission_engine이 상위 통합 레이어로 동작한다.
"""

from packages.permission_engine.decision import (
    check_permission,
    PermissionDecision,
    PermissionDenied,
)

__all__ = [
    "check_permission",
    "PermissionDecision",
    "PermissionDenied",
]
