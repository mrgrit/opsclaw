# packages/pi_adapter/sessions/__init__.py
"""Session management for pi runtime.

`PiSession` encapsulates a model‑specific chat session.
"""

class PiSession:
    def __init__(self, model_name: str):
        self.model_name = model_name
        # Placeholder – actual SDK integration pending
        raise NotImplementedError("PiSession not available in M0")
