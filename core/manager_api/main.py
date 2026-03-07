from fastapi import FastAPI, HTTPException

from storage.audit_store import append_audit
from schemas.projects import CreateProjectReq
from storage.projects_store import create_project, get_project

from schemas.targets import TargetUpsertReq
from storage.targets_store import list_targets, get_target, upsert_target, delete_target


app = FastAPI(title="OpsClaw Core (Rebuild)")

@app.get("/health")
def health():
    return {"ok": True, "service": "opsclaw-core", "version": "core-rebuild-v0"}

@app.post("/audit/test")
def audit_test():
    append_audit({"type": "AUDIT_TEST", "msg": "hello from core"})
    return {"ok": True}

@app.post("/projects")
def create_project_api(req: CreateProjectReq):
    st = create_project(name=req.name, request_text=req.request_text)
    append_audit({"type": "PROJECT_CREATED", "project_id": st["project_id"], "name": st["name"]})
    return {"project_id": st["project_id"], "state": st}

@app.get("/projects/{project_id}")
def get_project_api(project_id: str):
    st = get_project(project_id)
    if not st:
        raise HTTPException(status_code=404, detail="project not found")
    return st

@app.get("/targets")
def list_targets_api():
    return {"items": list_targets()}

@app.get("/targets/{target_id}")
def get_target_api(target_id: str):
    t = get_target(target_id)
    if not t:
        raise HTTPException(status_code=404, detail="target not found")
    return t

@app.post("/targets")
def upsert_target_api(req: TargetUpsertReq):
    t = req.model_dump()
    upsert_target(t)
    append_audit({"type": "TARGET_UPSERT", "target_id": t["id"], "base_url": t["base_url"]})
    return t

@app.delete("/targets/{target_id}")
def delete_target_api(target_id: str):
    ok = delete_target(target_id)
    append_audit({"type": "TARGET_DELETE", "target_id": target_id, "ok": ok})
    return {"ok": ok}