from fastapi import FastAPI

from storage.audit_store import append_audit

app = FastAPI(title="OpsClaw Core (Rebuild)")

@app.get("/health")
def health():
    return {"ok": True, "service": "opsclaw-core", "version": "core-rebuild-v0"}

@app.post("/audit/test")
def audit_test():
    append_audit({"type": "AUDIT_TEST", "msg": "hello from core"})
    return {"ok": True}