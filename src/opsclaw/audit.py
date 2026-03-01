from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AuditLogger:
    """Append-only audit logger for orchestration decisions and actions."""

    def __init__(self, log_path: str = ".opsclaw/audit/audit.log") -> None:
        self.path = Path(log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        *,
        actor: str,
        role: str,
        action: str,
        decision: str,
        task_id: str,
        prompt: str | None = None,
        policy_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "actor": actor,
            "role": role,
            "action": action,
            "decision": decision,
            "task_id": task_id,
            "policy_id": policy_id or "opsclaw-default-policy",
            "prompt_hash": self._prompt_hash(prompt) if prompt is not None else "",
            "details": details or {},
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    @staticmethod
    def _prompt_hash(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
