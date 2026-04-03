#!/usr/bin/env bash
# deploy-central.sh — 중앙서버 배포
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[central] Stopping..."
fuser -k 7000/tcp 2>/dev/null || true
sleep 1

echo "[central] Building UI..."
cd apps/central-ui && npm install --silent && npm run build && cd ../..

echo "[central] Starting central-server on :7000..."
set -a && source .env && set +a
export PYTHONPATH="$(pwd)" CENTRAL_API_KEY="${CENTRAL_API_KEY:-central-api-key-2026}"
nohup .venv/bin/python3.11 -m uvicorn apps.central-server.src.main:app \
  --host 0.0.0.0 --port 7000 --log-level warning > /tmp/central.log 2>&1 &

sleep 2
curl -s http://localhost:7000/health && echo " [OK]"
