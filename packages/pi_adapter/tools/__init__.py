# packages/pi_adapter/tools/__init__.py
"""Tool Bridge definitions.

Each concrete tool class should implement `execute(**kwargs)` and return a
standard result dict compatible with OldClaw evidence schema.
"""

class BaseTool:
    def __init__(self, runtime):
        self.runtime = runtime

    def execute(self, **kwargs):
        raise NotImplementedError("Tool execution not implemented for M0")
