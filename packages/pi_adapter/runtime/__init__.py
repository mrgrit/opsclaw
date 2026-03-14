# packages/pi_adapter/runtime/__init__.py
"""Runtime utilities for interacting with the pi engine.

In a full implementation this would wrap the pi SDK client, handle model loading,
session lifecycle, and provide low‑level invoke APIs.
"""

class RuntimeError(NotImplementedError):
    pass

class PiRuntime:
    def __init__(self, model_profile: str):
        self.model_profile = model_profile
        # TODO: Load model configuration, establish connection
        raise RuntimeError("PiRuntime not implemented in M0")
