from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Decision


PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "bearer": re.compile(r"Authorization:\s*Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
    "private_key": re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"),
    "ipv4_internal": re.compile(r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})\b"),
}

DEFAULT_BLOCK_TERMS = {"confidential", "internal-use-only"}


@dataclass(slots=True)
class GateResult:
    decision: Decision
    findings: list[str]
    transformed_prompt: str


class MasterGate:
    """PII/secret/confidential pre-flight gate for external master calls."""

    def __init__(self, block_terms: set[str] | None = None) -> None:
        self.block_terms = block_terms or DEFAULT_BLOCK_TERMS

    def evaluate(self, prompt: str) -> GateResult:
        findings: list[str] = []
        transformed = prompt

        for name, pattern in PATTERNS.items():
            if pattern.search(prompt):
                findings.append(name)

        lowered = prompt.lower()
        sensitive_terms = [term for term in self.block_terms if term in lowered]
        if sensitive_terms:
            findings.extend(f"dictionary:{term}" for term in sensitive_terms)

        if "private_key" in findings or sensitive_terms:
            return GateResult(
                decision=Decision.BLOCK,
                findings=sorted(findings),
                transformed_prompt="",
            )

        if findings:
            transformed = self._transform(prompt)
            return GateResult(
                decision=Decision.TRANSFORM,
                findings=sorted(findings),
                transformed_prompt=transformed,
            )

        return GateResult(decision=Decision.ALLOW, findings=[], transformed_prompt=prompt)

    def _transform(self, prompt: str) -> str:
        masked = PATTERNS["email"].sub("[REDACTED_EMAIL]", prompt)
        masked = PATTERNS["bearer"].sub("Authorization: Bearer [REDACTED_TOKEN]", masked)
        masked = PATTERNS["ipv4_internal"].sub("INTERNAL_IP", masked)
        return masked
