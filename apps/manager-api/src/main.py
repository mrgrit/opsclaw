# manager-api placeholder

from fastapi import FastAPI

app = FastAPI(title="OldClaw Manager API")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
