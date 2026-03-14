# OldClaw SubAgent Runtime
# Provides health, capability enumeration, and A2A script execution entry points.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import sys

app = FastAPI(title="OldClaw SubAgent Runtime", version="0.1.0")

@app.get("/health")
async def health_check():
    return {"status": "subagent ok"}

# ---------- Capability DTO ----------
class Capability(BaseModel):
    name: str
    description: str

# ---------- Capabilities endpoint ----------
@app.get("/capabilities")
async def list_capabilities():
    # Stub list – in real runtime this would be dynamic
    return [
        Capability(name="run_command", description="Execute shell commands"),
        Capability(name="read_file", description="Read local files"),
    ]

# ---------- A2A script execution (mock) ----------
@app.post("/run")
async def run_script(command: str, timeout: int = 60):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Command timed out")
