# packages/pi_adapter/runtime/client.py
"""Runtime client for the pi engine.

In the M0 version this class provides the public interface that higher‑level
components (ToolBridge, sessions, etc.) would call. The actual SDK integration
is omitted and a ``NotImplementedError`` is raised to make the missing
implementation explicit.
"""

class PiRuntime:
    def __init__(self, model_profile: str):
        self.model_profile = model_profile
        # TODO: Initialize real pi SDK client based on the given model profile
        raise NotImplementedError("PiRuntime client not implemented in M0 – SDK integration pending")

