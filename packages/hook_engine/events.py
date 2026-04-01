"""Hook 이벤트 정의 — OpsClaw 라이프사이클의 10개 이벤트 포인트."""

from typing import Literal


HookEvent = Literal[
    "project_created",      # 프로젝트 생성 직후
    "stage_changed",        # 프로젝트 상태 전이 시 (plan→execute 등)
    "pre_dispatch",         # 명령 dispatch 직전 (차단 가능)
    "post_dispatch",        # 명령 dispatch 직후 (결과 포함)
    "pre_playbook_step",    # Playbook 스텝 실행 직전 (차단 가능)
    "post_playbook_step",   # Playbook 스텝 실행 직후 (결과 포함)
    "evidence_recorded",    # evidence DB 기록 직후
    "incident_created",     # 인시던트 생성 시
    "mission_step",         # 자율 미션 각 스텝 완료 시
    "daemon_alert",         # 감시 데몬 이상 감지 시
]

HOOK_EVENTS: list[str] = list(HookEvent.__args__)  # type: ignore[attr-defined]

# pre_* 이벤트만 실행을 차단(block)할 수 있음
BLOCKING_EVENTS: set[str] = {"pre_dispatch", "pre_playbook_step"}
