from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import TaskResult


class JsonStateStore:
    """File-based state store for task results."""

    def __init__(self, root_dir: str = ".opsclaw/state") -> None:
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, result: TaskResult) -> Path:
        output_path = self.root / f"{result.task_id}.json"
        output_path.write_text(
            json.dumps(asdict(result), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return output_path
