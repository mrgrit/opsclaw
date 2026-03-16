#!/usr/bin/env bash
# OpsClaw SubAgent Bootstrap Installer
# Usage: bash -s < install.sh
# Env:   OPSCLAW_SUBAGENT_PORT  (default: 8001)
#        OPSCLAW_INSTALL_DIR    (default: /opt/opsclaw)
set -euo pipefail

SUBAGENT_PORT="${OPSCLAW_SUBAGENT_PORT:-8001}"
INSTALL_DIR="${OPSCLAW_INSTALL_DIR:-/opt/opsclaw}"
SERVICE_NAME="opsclaw-subagent"
PYTHON="python3"
PIP="pip3"

log()  { echo "[opsclaw-bootstrap] $*"; }
die()  { echo "[opsclaw-bootstrap] ERROR: $*" >&2; exit 1; }

# ── 1. Python 3.11+ 확인 ──────────────────────────────────────────────────────
log "Checking Python..."
PYVER=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0.0")
PYMAJ=$(echo "$PYVER" | cut -d. -f1)
PYMIN=$(echo "$PYVER" | cut -d. -f2)

if [ "$PYMAJ" -lt 3 ] || { [ "$PYMAJ" -eq 3 ] && [ "$PYMIN" -lt 11 ]; }; then
    log "Python $PYVER found, need 3.11+. Installing..."
    if command -v apt-get &>/dev/null; then
        apt-get update -qq
        apt-get install -y -qq python3.11 python3.11-venv python3-pip
        PYTHON=python3.11
        PIP="python3.11 -m pip"
    elif command -v dnf &>/dev/null; then
        dnf install -y python3.11 python3.11-pip
        PYTHON=python3.11
        PIP="python3.11 -m pip"
    else
        die "Cannot install Python 3.11+. Please install manually and re-run."
    fi
fi
log "Using: $($PYTHON --version)"

# ── 2. pip 패키지 설치 ────────────────────────────────────────────────────────
log "Installing Python packages..."
$PIP install --quiet --upgrade fastapi "uvicorn[standard]" httpx psycopg2-binary pydantic

# ── 3. 설치 디렉토리 생성 ─────────────────────────────────────────────────────
log "Creating install dir: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# ── 4. SubAgent 엔트리포인트 작성 ─────────────────────────────────────────────
log "Writing subagent_main.py..."
cat > "$INSTALL_DIR/subagent_main.py" << 'PYEOF'
import subprocess
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, FastAPI


@dataclass
class RunScriptRequest:
    project_id: str
    job_run_id: str
    script: str
    timeout_s: int = 120


@dataclass
class A2ARunResponse:
    status: str
    detail: dict


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "opsclaw-subagent"}

    return router


def create_capabilities_router() -> APIRouter:
    router = APIRouter(tags=["capabilities"])

    @router.get("/capabilities")
    def capabilities() -> dict:
        return {
            "service": "opsclaw-subagent",
            "capabilities": ["health", "capabilities", "run_script"],
        }

    return router


def create_a2a_router() -> APIRouter:
    router = APIRouter(prefix="/a2a", tags=["a2a"])

    @router.post("/run_script")
    def run_script(payload: RunScriptRequest) -> A2ARunResponse:
        try:
            result = subprocess.run(
                payload.script,
                shell=True,
                capture_output=True,
                text=True,
                timeout=payload.timeout_s,
            )
            return A2ARunResponse(
                status="ok" if result.returncode == 0 else "error",
                detail={
                    "project_id": payload.project_id,
                    "job_run_id": payload.job_run_id,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                },
            )
        except subprocess.TimeoutExpired:
            return A2ARunResponse(
                status="timeout",
                detail={
                    "project_id": payload.project_id,
                    "job_run_id": payload.job_run_id,
                    "stdout": "",
                    "stderr": f"Script timed out after {payload.timeout_s}s",
                    "exit_code": -1,
                },
            )

    return router


app = FastAPI(title="OpsClaw SubAgent", version="0.3.0-m3")
app.include_router(create_health_router())
app.include_router(create_capabilities_router())
app.include_router(create_a2a_router())
PYEOF

# ── 5. systemd 서비스 파일 작성 ───────────────────────────────────────────────
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
log "Writing systemd service: $SERVICE_FILE"
cat > "$SERVICE_FILE" << SVCEOF
[Unit]
Description=OpsClaw SubAgent Runtime
After=network.target

[Service]
ExecStart=$PYTHON -m uvicorn subagent_main:app --host 0.0.0.0 --port $SUBAGENT_PORT
WorkingDirectory=$INSTALL_DIR
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

# ── 6. 서비스 활성화 및 시작 ──────────────────────────────────────────────────
log "Enabling and starting $SERVICE_NAME..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

log "Bootstrap complete."
log "SubAgent running on port $SUBAGENT_PORT at $INSTALL_DIR"
log "Check: systemctl status $SERVICE_NAME"
