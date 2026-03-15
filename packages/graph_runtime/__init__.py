DEFAULT_MANAGER_STAGES = [
    "intake",
    "plan",
    "execute",
    "validate",
    "report",
    "close",
]

DEFAULT_STAGE_TRANSITIONS = {
    "intake": "plan",
    "plan": "execute",
    "execute": "validate",
    "validate": "report",
    "report": "close",
    "close": None,
}


def get_next_stage(stage: str) -> str | None:
    if stage not in DEFAULT_STAGE_TRANSITIONS:
        raise KeyError(f"Unknown stage: {stage}")
    return DEFAULT_STAGE_TRANSITIONS[stage]


def build_minimal_project_graph() -> dict[str, object]:
    return {
        "stages": list(DEFAULT_MANAGER_STAGES),
        "transitions": dict(DEFAULT_STAGE_TRANSITIONS),
    }
