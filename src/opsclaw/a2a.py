from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    RUN_SCRIPT = "RUN_SCRIPT"
    RUN_TEST = "RUN_TEST"
    STATUS_UPDATE = "STATUS_UPDATE"
    UPLOAD_EVIDENCE = "UPLOAD_EVIDENCE"


@dataclass(slots=True)
class A2AMessage:
    message_type: MessageType
    task_id: str
    payload: dict[str, Any] = field(default_factory=dict)


def build_run_script_message(task_id: str, script: str, timeout_seconds: int) -> A2AMessage:
    return A2AMessage(
        message_type=MessageType.RUN_SCRIPT,
        task_id=task_id,
        payload={"script": script, "timeout_seconds": timeout_seconds},
    )


def build_status_update_message(task_id: str, status: str, detail: str) -> A2AMessage:
    return A2AMessage(
        message_type=MessageType.STATUS_UPDATE,
        task_id=task_id,
        payload={"status": status, "detail": detail},
    )
