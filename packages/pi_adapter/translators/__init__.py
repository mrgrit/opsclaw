# packages/pi_adapter/translators/__init__.py
"""Translation layer between OldClaw types and pi runtime types.

Functions here convert OldClaw request/response structures to the format
expected by the pi SDK and vice‑versa.
"""

def to_pi_message(oldclaw_obj: dict) -> dict:
    """Translate an OldClaw dict to a pi SDK message payload.
    """
    # Placeholder implementation – in M0 we simply forward the dict.
    return oldclaw_obj

def from_pi_message(pi_msg: dict) -> dict:
    """Translate a pi SDK response back to OldClaw format.
    """
    return pi_msg
