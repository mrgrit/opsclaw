from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str


class SubAgentExecutor:
    """Minimal local subagent runtime for Sprint A."""

    def __init__(self, timeout_seconds: int = 30) -> None:
        self.timeout_seconds = timeout_seconds

    def run_script(self, script: str) -> ExecutionResult:
        completed = subprocess.run(
            ["bash", "-lc", script],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        return ExecutionResult(
            exit_code=completed.returncode,
            stdout=completed.stdout.strip(),
            stderr=completed.stderr.strip(),
        )
