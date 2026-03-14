# master-service placeholder

from fastapi import FastAPI

app = FastAPI(title="OldClaw Master Service")

@app.get("/health")
async def health_check():
    return {"status": "master ok"}
