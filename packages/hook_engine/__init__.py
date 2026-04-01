"""
OpsClaw Hook Engine — 라이프사이클 이벤트 기반 확장 시스템.

Claude Code의 14-event Hook 패턴을 참고하여 구현.
작업 전후에 webhook/script/llm Hook을 실행하고,
pre_* Hook은 실행을 차단(block)할 수 있다.
"""

from packages.hook_engine.events import HOOK_EVENTS, HookEvent
from packages.hook_engine.models import HookDefinition, HookResponse
from packages.hook_engine.executor import fire_event
from packages.hook_engine.registry import (
    register_hook,
    unregister_hook,
    list_hooks,
    get_hooks_for_event,
)

__all__ = [
    "HOOK_EVENTS",
    "HookEvent",
    "HookDefinition",
    "HookResponse",
    "fire_event",
    "register_hook",
    "unregister_hook",
    "list_hooks",
    "get_hooks_for_event",
]
