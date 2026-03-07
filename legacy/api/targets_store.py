import os
from typing import Any, Dict, List, Optional

from state_store import ensure_dirs, load_json, save_json

STATE_DIR = os.getenv("STATE_DIR", "/data/state")
TARGETS_PATH = os.path.join(STATE_DIR, "_targets.json")

ensure_dirs(STATE_DIR)

def _load_targets() -> Dict[str, Any]:
    return load_json(TARGETS_PATH, {"items": []})

def _save_targets(obj: Dict[str, Any]) -> None:
    save_json(TARGETS_PATH, obj)

def list_targets() -> List[Dict[str, Any]]:
    obj = _load_targets()
    items = obj.get("items") or []
    # ensure stable shape
    out = []
    for t in items:
        if not isinstance(t, dict):
            continue
        out.append({
            "id": t.get("id"),
            "base_url": (t.get("base_url") or "").rstrip("/"),
            "name": t.get("name") or t.get("id"),
            "tags": t.get("tags") or [],
            "notes": t.get("notes") or "",
        })
    return out

def get_target(target_id: str) -> Optional[Dict[str, Any]]:
    tid = (target_id or "").strip()
    if not tid:
        return None
    for t in list_targets():
        if t.get("id") == tid:
            return t
    return None

def upsert_target(t: Dict[str, Any]) -> Dict[str, Any]:
    items = list_targets()

    tid = (t.get("id") or "").strip()
    if not tid:
        raise ValueError("target.id required")

    url = (t.get("base_url") or "").strip().rstrip("/")
    if not url:
        raise ValueError("target.base_url required (e.g. http://192.168.24.176:55123)")

    obj = {
        "id": tid,
        "base_url": url,
        "name": (t.get("name") or tid).strip(),
        "tags": t.get("tags") or [],
        "notes": t.get("notes") or "",
    }

    replaced = False
    for i in range(len(items)):
        if items[i].get("id") == tid:
            items[i] = obj
            replaced = True
            break
    if not replaced:
        items.append(obj)

    _save_targets({"items": items})
    return obj

def delete_target(target_id: str) -> bool:
    tid = (target_id or "").strip()
    if not tid:
        return False
    items = list_targets()
    new_items = [t for t in items if t.get("id") != tid]
    if len(new_items) == len(items):
        return False
    _save_targets({"items": new_items})
    return True
