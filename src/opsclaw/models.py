from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Decision(str, Enum):
    ALLOW = "allow"
    TRANSFORM = "transform"
    BLOCK = "block"


@dataclass(slots=True)
class TaskRequest:
    task_id: str
    objective: str
    constraints: list[str] = field(default_factory=list)
    requires_master: bool = False
    install_dependencies: bool = False


@dataclass(slots=True)
class TaskResult:
    task_id: str
    status: str
    todo: list[str]
    execution_log: list[str]
    validation_passed: bool
    metadata: dict[str, Any] = field(default_factory=dict)
