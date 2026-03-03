import os, json, time
from typing import Any, Dict

def ensure_dirs(*paths: str):
    for p in paths:
        os.makedirs(p, exist_ok=True)

def now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")

def load_json(path: str, default: Any):
    try:
        if not os.path.exists(path):
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # corrupted/empty file → reset to default
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return default

def save_json(path: str, data: Any):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def project_path(state_dir: str, project_id: str) -> str:
    return os.path.join(state_dir, f"{project_id}.json")

def init_project(state_dir: str, project_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    p = project_path(state_dir, project_id)
    st = {
        "project_id": project_id,
        "project_type": payload.get("project_type", "generic"),
        "targets": payload.get("targets", []),
        "milestones": payload.get("milestones", ["M1"]),
        "todos": [],
        "runs": [],
        "tests": [],
        "errors": [],
        "master_calls": [],
        "timestamps": {"started": now_ts(), "updated": now_ts(), "completed": None},
    }
    save_json(p, st)
    return st

def update_project(state_dir: str, project_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    p = project_path(state_dir, project_id)
    st = load_json(p, {})
    st.update(patch)
    st.setdefault("timestamps", {})
    st["timestamps"]["updated"] = now_ts()
    save_json(p, st)
    return st

def append_run(state_dir: str, project_id: str, run_obj: Dict[str, Any]) -> Dict[str, Any]:
    p = project_path(state_dir, project_id)
    st = load_json(p, {})
    st.setdefault("runs", [])
    st["runs"].append(run_obj)
    st.setdefault("timestamps", {})
    st["timestamps"]["updated"] = now_ts()
    save_json(p, st)
    return st