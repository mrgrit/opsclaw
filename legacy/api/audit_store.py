import os, json, time
from typing import Dict, Any

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")

def append_audit(audit_dir: str, event: Dict[str, Any]) -> None:
    ensure_dir(audit_dir)
    event = dict(event)
    event.setdefault("ts", now_ts())
    path = os.path.join(audit_dir, "audit.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
