from fastapi import FastAPI, HTTPException

from storage.audit_store import append_audit
from schemas.projects import CreateProjectReq
from storage.projects_store import create_project, get_project

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