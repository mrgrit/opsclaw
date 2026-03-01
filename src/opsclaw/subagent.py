from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str


class SubAgentExecutor:
    """Minimal local subagent runtime with guardrails."""

    DANGEROUS_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r"\brm\s+-rf\b"),
        re.compile(r"\bmkfs\b"),
        re.compile(r"\bshutdown\b"),
        re.compile(r"\breboot\b"),
    )
    SENSITIVE_PATHS: tuple[str, ...] = ("/etc", "/var/lib")

    def __init__(self, timeout_seconds: int = 30, approval_mode: bool = False) -> None:
        self.timeout_seconds = timeout_seconds
        self.approval_mode = approval_mode

    def run_script(self, script: str) -> ExecutionResult:
        guardrail_error = self._guardrails(script)
        if guardrail_error:
            return ExecutionResult(exit_code=126, stdout="", stderr=guardrail_error)

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

    def _guardrails(self, script: str) -> str | None:
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(script):
                return f"guardrail:block dangerous command pattern `{pattern.pattern}`"

        if not self.approval_mode and any(path in script for path in self.SENSITIVE_PATHS):
            if any(cmd in script for cmd in ("rm ", "mv ", "cp ", "sed ", "tee ", "cat >")):
                return "guardrail:block sensitive path write requires approval mode"

        return None
