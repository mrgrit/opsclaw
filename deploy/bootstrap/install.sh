#!/usr/bin/env bash
# OpsClaw SubAgent Bootstrap Installer
# Usage:
#   직접 실행  : sudo bash install.sh
#   원격 실행  : ssh user@host 'sudo bash -s' < install.sh
#   환경변수   : OPSCLAW_SUBAGENT_PORT (default: 8002)
#               OPSCLAW_INSTALL_DIR   (default: /opt/opsclaw)
#               OPSCLAW_REPO_URL      (default: https://github.com/mrgrit/opsclaw.git)
set -euo pipefail

SUBAGENT_PORT="${OPSCLAW_SUBAGENT_PORT:-8002}"
INSTALL_DIR="${OPSCLAW_INSTALL_DIR:-/opt/opsclaw}"
REPO_URL="${OPSCLAW_REPO_URL:-https://github.com/mrgrit/opsclaw.git}"
SERVICE_NAME="opsclaw-subagent"
LOG_FILE="/var/log/opsclaw-bootstrap.log"

log()  { echo "[opsclaw-bootstrap] $*" | tee -a "$LOG_FILE"; }
die()  { echo "[opsclaw-bootstrap] ERROR: $*" | tee -a "$LOG_FILE" >&2; exit 1; }

log "=========================================="
log "OpsClaw SubAgent Bootstrap Start"
log "Port: $SUBAGENT_PORT  InstallDir: $INSTALL_DIR"
log "=========================================="

# ── 0. root 확인 ───────────────────────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    die "Must run as root (use sudo)"
fi

# ── 1. 의존 패키지 설치 ────────────────────────────────────────────────────────
log "Installing system dependencies..."
if command -v apt-get &>/dev/null; then
    apt-get update -qq
    apt-get install -y -qq python3.11 python3.11-venv python3-pip git curl
elif command -v dnf &>/dev/null; then
    dnf install -y python3.11 python3.11-pip git curl
else
    die "Unsupported package manager. Install Python 3.11, git, curl manually."
fi

# ── 2. Python 버전 확인 ────────────────────────────────────────────────────────
PYTHON="python3.11"
command -v "$PYTHON" &>/dev/null || PYTHON="python3"
PYVER=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
log "Python: $($PYTHON --version)  ($PYVER)"

PYMAJ=$(echo "$PYVER" | cut -d. -f1)
PYMIN=$(echo "$PYVER" | cut -d. -f2)
if [ "$PYMAJ" -lt 3 ] || { [ "$PYMAJ" -eq 3 ] && [ "$PYMIN" -lt 11 ]; }; then
    die "Python 3.11+ required, got $PYVER"
fi

# ── 3. opsclaw 저장소 클론 또는 업데이트 ─────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
    log "Updating existing repo at $INSTALL_DIR..."
    git -C "$INSTALL_DIR" pull --ff-only
else
    log "Cloning opsclaw repo to $INSTALL_DIR..."
    rm -rf "$INSTALL_DIR"
    git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
fi

# ── 4. Python venv 생성 및 의존성 설치 ────────────────────────────────────────
log "Creating Python venv..."
$PYTHON -m venv "$INSTALL_DIR/.venv"
VENV_PIP="$INSTALL_DIR/.venv/bin/pip"

log "Installing Python packages..."
$VENV_PIP install --quiet --upgrade pip
$VENV_PIP install --quiet \
    fastapi "uvicorn[standard]" httpx psycopg2-binary pydantic \
    sqlalchemy langgraph croniter requests

# ── 5. .env 파일 설정 ─────────────────────────────────────────────────────────
if [ ! -f "$INSTALL_DIR/.env" ]; then
    if [ -f "$INSTALL_DIR/.env.example" ]; then
        cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
        log "Created .env from .env.example (review and update as needed)"
    fi
fi

# ── 6. systemd 서비스 파일 작성 ────────────────────────────────────────────────
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
log "Writing systemd service: $SERVICE_FILE"
cat > "$SERVICE_FILE" << SVCEOF
[Unit]
Description=OpsClaw SubAgent Runtime
After=network.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/.venv/bin/uvicorn apps.subagent-runtime.src.main:app --host 0.0.0.0 --port $SUBAGENT_PORT
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
EnvironmentFile=-$INSTALL_DIR/.env
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=opsclaw-subagent

[Install]
WantedBy=multi-user.target
SVCEOF

# ── 7. 서비스 활성화 및 시작 ───────────────────────────────────────────────────
log "Enabling and starting $SERVICE_NAME..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

# ── 8. health check ────────────────────────────────────────────────────────────
log "Waiting for subagent to start..."
sleep 5
HTTP_CODE="000"
for i in 1 2 3 4 5; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${SUBAGENT_PORT}/health" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        log "Health check OK (http://localhost:${SUBAGENT_PORT}/health)"
        break
    fi
    log "Waiting... ($i/5, http_code=$HTTP_CODE)"
    sleep 3
done

if [ "$HTTP_CODE" != "200" ]; then
    log "WARNING: Health check failed. Check: journalctl -u $SERVICE_NAME -n 50"
else
    log "=========================================="
    log "Bootstrap COMPLETE"
    log "SubAgent: http://$(hostname -I | awk '{print $1}'):${SUBAGENT_PORT}/health"
    log "Service:  systemctl status $SERVICE_NAME"
    log "Logs:     journalctl -u $SERVICE_NAME -f"
    log "=========================================="
fi
