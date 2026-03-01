from opsclaw.mastergate import MasterGate
from opsclaw.models import Decision


def test_mastergate_transforms_email_and_internal_ip() -> None:
    gate = MasterGate()
    prompt = "문의자 a@corp.local, 서버 10.1.0.80 에서 오류 발생"
    result = gate.evaluate(prompt)

    assert result.decision == Decision.TRANSFORM
    assert "[REDACTED_EMAIL]" in result.transformed_prompt
    assert "INTERNAL_IP" in result.transformed_prompt


def test_mastergate_blocks_private_key() -> None:
    gate = MasterGate()
    prompt = "-----BEGIN PRIVATE KEY-----\nabc"
    result = gate.evaluate(prompt)

    assert result.decision == Decision.BLOCK
    assert result.transformed_prompt == ""
