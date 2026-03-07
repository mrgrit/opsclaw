from fastapi import FastAPI

app = FastAPI(title="OpsClaw Core (Rebuild)")

@app.get("/health")
def health():
    return {"ok": True, "service": "opsclaw-core", "version": "core-rebuild-v0"}