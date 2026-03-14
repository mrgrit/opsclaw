# packages/pi_adapter/contracts/__init__.py
"""Contract definitions for data exchanged with pi runtime.

These define the JSON schema for tool invocation requests and responses.
"""

TOOL_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {"type": "string"},
        "args": {"type": "object"},
    },
    "required": ["tool", "args"]
}

TOOL_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "result": {},
        "status": {"type": "string"}
    },
    "required": ["result"]
}
