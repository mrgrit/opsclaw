import re
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Any, Literal

Decision = Literal["ALLOW", "TRANSFORM", "BLOCK"]

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
PHONE_RE = re.compile(r"\b(01[016789])[-.\s]?\d{3,4}[-.\s]?\d{4}\b")
JWT_RE = re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b")
BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-+/=]{10,}\b")
APIKEY_RE = re.compile(r"(?i)\b(api[_-]?key|token|secret)\b\s*[:=]\s*['\"]?[A-Za-z0-9._\-+/=]{8,}['\"]?")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")

IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
HOST_RE = re.compile(r"\b[a-zA-Z0-9][a-zA-Z0-9\-]{0,62}(?:\.[a-zA-Z0-9\-]{1,63})+\b")

@dataclass
class GateResult:
    decision: Decision
    transformed_prompt: str
    findings: List[str]
    redactions: List[str]
    required_action: str
    prompt_hash: str

def _mask_map(text: str, pattern: re.Pattern, token: str, redactions: List[str], findings: List[str], finding_label: str) -> str:
    def repl(m):
        redactions.append(f"{finding_label}: {m.group(0)[:40]}...")
        return token
    if pattern.search(text):
        findings.append(finding_label)
        return pattern.sub(repl, text)
    return text

def mastergate_scan(draft_prompt: str, context_snippets: str, policy_profile: str = "enterprise-default") -> GateResult:
    raw = f"[PROMPT]\n{draft_prompt}\n\n[CONTEXT]\n{context_snippets}"
    findings: List[str] = []
    redactions: List[str] = []
    transformed = raw

    # Secrets are BLOCK (strong rule)
    if PRIVATE_KEY_RE.search(transformed):
        prompt_hash = hashlib.sha256(raw.encode()).hexdigest()
        return GateResult(
            decision="BLOCK",
            transformed_prompt="",
            findings=["PRIVATE_KEY"],
            redactions=["PRIVATE_KEY detected"],
            required_action="Remove private key material. Use local-only analysis or provide redacted snippets.",
            prompt_hash=prompt_hash,
        )

    transformed = _mask_map(transformed, BEARER_RE, "[REDACTED_BEARER]", redactions, findings, "BEARER_TOKEN")
    transformed = _mask_map(transformed, JWT_RE, "[REDACTED_JWT]", redactions, findings, "JWT")
    transformed = _mask_map(transformed, APIKEY_RE, "[REDACTED_SECRET]", redactions, findings, "APIKEY_OR_SECRET")

    # PII -> TRANSFORM
    transformed = _mask_map(transformed, EMAIL_RE, "[REDACTED_EMAIL]", redactions, findings, "EMAIL")
    transformed = _mask_map(transformed, PHONE_RE, "[REDACTED_PHONE]", redactions, findings, "PHONE")

    # Internal assets -> TRANSFORM (기본 정책)
    # (너의 정책 파일로 세밀화 가능. MVP는 단순 마스킹)
    if IPV4_RE.search(transformed):
        findings.append("INTERNAL_IP_POSSIBLE")
        transformed = IPV4_RE.sub("INTERNAL_IP_X", transformed)
        redactions.append("IP masked")

    # hostnames도 마스킹(필요 시)
    if HOST_RE.search(transformed):
        findings.append("HOSTNAME_POSSIBLE")
        transformed = HOST_RE.sub("HOST_X", transformed)
        redactions.append("Hostname masked")

    decision: Decision = "ALLOW"
    required_action = ""

    # secrets(토큰류)는 TRANSFORM 후 ALLOW (MVP)
    if any(x in findings for x in ["BEARER_TOKEN", "JWT", "APIKEY_OR_SECRET", "EMAIL", "PHONE", "INTERNAL_IP_POSSIBLE", "HOSTNAME_POSSIBLE"]):
        decision = "TRANSFORM"

    prompt_hash = hashlib.sha256(transformed.encode()).hexdigest()
    return GateResult(
        decision=decision,
        transformed_prompt=transformed,
        findings=sorted(list(set(findings))),
        redactions=redactions[:50],
        required_action=required_action,
        prompt_hash=prompt_hash,
    )