# packages/pi_adapter/model_profiles/__init__.py
"""Model profile definitions.

A profile declares which model, temperature, and system prompt to use for a
given OldClaw role (manager, master, subagent, etc.).
"""

MODEL_PROFILES = {
    "manager": {"model": "gpt-4o-mini", "temperature": 0.2},
    "master": {"model": "gpt-4o", "temperature": 0.1},
    "subagent": {"model": "gpt-4o-mini", "temperature": 0.3},
}

# In M0 these are static; M1 may load from config or DB.
