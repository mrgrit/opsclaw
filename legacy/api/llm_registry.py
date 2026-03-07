import os
from typing import Any, Dict, List, Optional

from state_store import load_json, save_json, ensure_dirs

STATE_DIR = os.getenv("STATE_DIR", "/data/state")
ensure_dirs(STATE_DIR, os.getenv("ARTIFACT_DIR", "/data/artifacts"), os.getenv("EVIDENCE_DIR", "/data/evidence"), os.getenv("AUDIT_DIR", "/data/audit"))

CONNS_FILE = os.path.join(STATE_DIR, "_llm_conns.json")
ROLES_FILE = os.path.join(STATE_DIR, "_llm_roles.json")


def _load_conns() -> List[Dict[str, Any]]:
    data = load_json(CONNS_FILE, [])
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"]
    return []


def _save_conns(items: List[Dict[str, Any]]) -> None:
    save_json(CONNS_FILE, items)


def list_llm_conns() -> List[Dict[str, Any]]:
    return _load_conns()


def get_llm_conn(conn_id: str) -> Optional[Dict[str, Any]]:
    for x in _load_conns():
        if (x.get("id") or "").strip() == (conn_id or "").strip():
            return x
    return None


def upsert_llm_conn(obj: Dict[str, Any]) -> Dict[str, Any]:
    items = _load_conns()
    cid = (obj.get("id") or "").strip()
    if not cid:
        raise ValueError("llm connection id is empty")

    out = dict(obj)
    out["id"] = cid
    out["name"] = (out.get("name") or cid).strip()
    out["provider"] = (out.get("provider") or "").strip()
    out["base_url"] = (out.get("base_url") or "").strip()
    out["api_key"] = (out.get("api_key") or "").strip()
    out["model"] = (out.get("model") or "").strip()
    out["timeout_s"] = int(out.get("timeout_s") or 60)
    out["headers"] = out.get("headers") or {}

    replaced = False
    new_items: List[Dict[str, Any]] = []
    for x in items:
        if (x.get("id") or "").strip() == cid:
            new_items.append(out)
            replaced = True
        else:
            new_items.append(x)
    if not replaced:
        new_items.append(out)

    _save_conns(new_items)
    return out


def delete_llm_conn(conn_id: str) -> bool:
    items = _load_conns()
    cid = (conn_id or "").strip()
    new_items = [x for x in items if (x.get("id") or "").strip() != cid]
    if len(new_items) == len(items):
        return False
    _save_conns(new_items)
    return True


def get_llm_roles() -> Dict[str, Any]:
    data = load_json(ROLES_FILE, {})
    if not isinstance(data, dict):
        data = {}
    return {
        "master_conn_id": data.get("master_conn_id"),
        "manager_conn_id": data.get("manager_conn_id"),
        "subagent_default_conn_id": data.get("subagent_default_conn_id"),
    }


def set_llm_roles(obj: Dict[str, Any]) -> Dict[str, Any]:
    roles = get_llm_roles()
    roles["master_conn_id"] = obj.get("master_conn_id")
    roles["manager_conn_id"] = obj.get("manager_conn_id")
    roles["subagent_default_conn_id"] = obj.get("subagent_default_conn_id")
    save_json(ROLES_FILE, roles)
    return roles


def resolve_llm_conn_for_role(role: str, target_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    # target override (optional)
    if target_id:
        try:
            from targets_store import get_target
            t = get_target(target_id)
            if t and t.get("llm_conn_id"):
                return get_llm_conn(t["llm_conn_id"])
        except Exception:
            pass

    roles = get_llm_roles()
    key = None
    if role == "master":
        key = "master_conn_id"
    elif role == "manager":
        key = "manager_conn_id"
    elif role == "subagent":
        key = "subagent_default_conn_id"

    conn_id = roles.get(key) if key else None
    if conn_id:
        return get_llm_conn(conn_id)
    return None