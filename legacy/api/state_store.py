import os, json, time
from typing import Any, Dict
from datetime import datetime

def ensure_dirs(*paths: str):
    for p in paths:
        os.makedirs(p, exist_ok=True)

def now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")

def _now_iso():
    # 기존에 now_iso()가 있으면 그걸 쓰고, 없으면 이걸 씀
    return datetime.utcnow().isoformat() + "Z"

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

def append_playbook_run(state_dir: str, project_id: str, entry: dict):
    """
    프로젝트 state JSON에 playbook_runs[]로 실행 기록을 append
    - load_project 같은 함수는 이 코드베이스에 없으므로 사용 금지
    - 기존 패턴: load_json(project_path(...)) -> update_project(...)
    """
    st = load_json(project_path(state_dir, project_id), {})
    st.setdefault("playbook_runs", [])

    e = dict(entry)
    e.setdefault("created_at", _now_iso())
    st["playbook_runs"].append(e)

    update_project(state_dir, project_id, st)
    return e