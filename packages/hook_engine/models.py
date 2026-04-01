"""Hook 데이터 모델."""

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class HookDefinition:
    """Hook 등록 정보."""
    event: str                          # HOOK_EVENTS 중 하나
    hook_type: str                      # "webhook" | "script" | "notification"
    target: str                         # URL, script path, 또는 channel_id
    name: str = ""                      # 사람이 읽을 수 있는 이름
    condition: str | None = None        # Python expression 조건 (예: "risk_level == 'critical'")
    timeout_s: int = 15                 # 실행 타임아웃 (초)
    can_block: bool = False             # True면 pre_* 이벤트에서 실행 차단 가능
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"hook_{uuid.uuid4().hex[:12]}")


@dataclass
class HookInput:
    """Hook에 전달되는 이벤트 데이터."""
    event: str
    project_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    # 이벤트별 추가 데이터
    command: str | None = None          # dispatch 이벤트
    risk_level: str | None = None
    exit_code: int | None = None        # post_* 이벤트
    stdout: str | None = None
    stderr: str | None = None
    step_order: int | None = None       # playbook 이벤트
    step_name: str | None = None
    severity: str | None = None         # daemon/incident 이벤트
    agent_id: str | None = None


@dataclass
class HookResponse:
    """Hook 실행 결과."""
    hook_id: str
    hook_name: str
    event: str
    success: bool = True
    continue_: bool = True              # False면 실행 중단 (pre_* 이벤트에서만 유효)
    reason: str = ""                    # 차단/오류 사유
    modified_input: dict | None = None  # 입력 수정 (pre_* 이벤트에서 명령 변경 등)
    response_data: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
