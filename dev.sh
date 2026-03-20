#!/bin/bash
# OpsClaw dev launcher
# Usage: ./dev.sh [manager|master|subagent|all]

set -a
source "$(dirname "$0")/.env"
set +a
export PYTHONPATH="$(dirname "$0")"

VENV=".venv/bin"
SVC=${1:-all}

start_manager() {
  echo "[manager-api] Starting on :8000..."
  $VENV/uvicorn "apps.manager-api.src.main:app" --host 0.0.0.0 --port 8000 --reload &
}

start_master() {
  echo "[master-service] Starting on :8001..."
  $VENV/uvicorn "apps.master-service.src.main:app" --host 0.0.0.0 --port 8001 --reload &
}

start_subagent() {
  echo "[subagent-runtime] Starting on :8002..."
  $VENV/uvicorn "apps.subagent-runtime.src.main:app" --host 0.0.0.0 --port 8002 --reload &
}

case $SVC in
  manager)   start_manager ;;
  master)    start_master ;;
  subagent)  start_subagent ;;
  all)
    start_manager
    start_master
    start_subagent
    wait
    ;;
  *)
    echo "Usage: $0 [manager|master|subagent|all]"
    exit 1
    ;;
esac

wait
