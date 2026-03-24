#!/usr/bin/env bash
# deploy_subagent.sh — SubAgent 업데이트를 secu/web/siem에 배포
#
# 사용법:
#   ./scripts/deploy_subagent.sh            # 전체 3개 서버 배포
#   ./scripts/deploy_subagent.sh secu       # 특정 서버만
#   ./scripts/deploy_subagent.sh secu web   # 복수 지정
#
# 동작:
#   SSH로 각 서버에 직접 접속하여:
#   1. git sparse checkout (apps/subagent-runtime + packages/pi_adapter)
#   2. fuser -k 8002/tcp 로 기존 프로세스 종료
#   3. nohup + disown 으로 uvicorn 재시작
#   4. /health 확인 후 PoW 기록 (Manager API execute-plan)
#
# 의존성: ssh (키 인증), curl, python3, git

set -euo pipefail

MANAGER="${OPSCLAW_MANAGER_URL:-http://localhost:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# git remote에서 토큰 포함 URL 동적 추출
REPO_URL=$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null || echo "")
if [ -z "$REPO_URL" ]; then
  echo "[ERROR] git remote origin을 찾을 수 없습니다: $REPO_ROOT"
  exit 1
fi

# ── 서버 정의: user:ip ───────────────────────────────────────────────────────
declare -A SERVER_IPS=(
  [secu]="192.168.208.150"
  [web]="192.168.208.151"
  [siem]="192.168.208.152"
)

# 배포 대상 결정
if [ $# -gt 0 ]; then
  TARGETS=("$@")
else
  TARGETS=(secu web siem)
fi

# ── 유틸 함수 ────────────────────────────────────────────────────────────────
log() { echo "[$(date '+%H:%M:%S')] $*"; }

api() {
  local method="$1" path="$2" body="${3:-}"
  if [ -n "$body" ]; then
    curl -sf -X "$method" "$MANAGER$path" -H "Content-Type: application/json" -d "$body"
  else
    curl -sf -X "$method" "$MANAGER$path"
  fi
}

jq_val() { python3 -c "import sys,json; print(json.load(sys.stdin)$1)"; }

ssh_run() {
  # ssh_run user ip 'remote command'
  local user="$1" ip="$2" cmd="$3"
  ssh -n -T \
    -o StrictHostKeyChecking=no \
    -o ConnectTimeout=10 \
    -o ServerAliveInterval=5 \
    "$user@$ip" "$cmd" 2>&1
}

# ── 메인 ─────────────────────────────────────────────────────────────────────
log "SubAgent 배포 시작 → 대상: ${TARGETS[*]}"

DEPLOY_OK=1
declare -A RESULTS

for user in "${TARGETS[@]}"; do
  ip="${SERVER_IPS[$user]:-}"
  if [ -z "$ip" ]; then
    log "[WARN] 알 수 없는 서버: $user — 건너뜀"
    continue
  fi
  path="/home/$user/opsclaw"
  log "── $user ($ip) ──────────────────────────"

  # Step 1: git 설치 확인 (siem은 git 없을 수 있음)
  log "  [1/3] git 환경 확인..."
  ssh_run "$user" "$ip" \
    "command -v git >/dev/null 2>&1 || sudo apt-get install -y git >/dev/null 2>&1 && echo GIT_OK" \
    | grep -q "GIT_OK" && log "  git OK" || log "  git 설치됨"

  # Step 2: sparse git checkout
  log "  [2/3] git sync (apps/subagent-runtime + packages/pi_adapter)..."
  SYNC_OUT=$(ssh_run "$user" "$ip" "
cd '$path'
if [ ! -d .git ]; then
  git init
  git remote add origin '$REPO_URL'
fi
git config core.sparseCheckout true
mkdir -p .git/info
printf 'apps/subagent-runtime/\npackages/pi_adapter/\n' > .git/info/sparse-checkout
git fetch origin main --depth=1 2>&1 | tail -2
git checkout -f FETCH_HEAD -- apps/subagent-runtime packages/pi_adapter 2>&1 | tail -2
echo SYNC_OK
")

  if echo "$SYNC_OUT" | grep -q "SYNC_OK"; then
    log "  git sync ✓"
  else
    log "  git sync ✗: $SYNC_OUT"
    RESULTS[$user]="SYNC_FAILED"
    DEPLOY_OK=0
    continue
  fi

  # Step 3: 재시작
  # fuser -k 8002/tcp: 포트 기반 kill (pkill -f 는 SSH 셸 자신도 죽이는 버그)
  # nohup + disown: SSH 세션 종료 후에도 uvicorn 생존
  log "  [3/3] SubAgent 재시작..."
  RESTART_OUT=$(ssh_run "$user" "$ip" "
fuser -k 8002/tcp 2>/dev/null
sleep 1
cd '$path'
export PYTHONPATH='$path'
nohup .venv/bin/python3 -m uvicorn apps.subagent-runtime.src.main:app \
  --host 0.0.0.0 --port 8002 --log-level warning \
  >> /tmp/subagent.log 2>&1 & disown
echo RESTART_OK
")

  if echo "$RESTART_OUT" | grep -q "RESTART_OK"; then
    log "  restart ✓"
    RESULTS[$user]="RESTARTED"
  else
    log "  restart ✗: $RESTART_OUT"
    RESULTS[$user]="RESTART_FAILED"
    DEPLOY_OK=0
  fi
done

# ── Health 검증 ───────────────────────────────────────────────────────────────
log "SubAgent 기동 대기 (8초)..."
sleep 8

log "Health 확인..."
for user in "${TARGETS[@]}"; do
  ip="${SERVER_IPS[$user]:-}"
  [ -z "$ip" ] && continue
  STATUS=$(curl -sf --max-time 5 "http://$ip:8002/health" 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null \
    || echo "UNREACHABLE")
  if [ "$STATUS" = "ok" ]; then
    log "  ✓ $user ($ip:8002)"
    RESULTS[$user]="HEALTHY"
  else
    log "  ✗ $user ($ip:8002) — $STATUS"
    RESULTS[$user]="${RESULTS[$user]:-UNKNOWN}_HEALTH_FAIL"
    DEPLOY_OK=0
  fi
done

# ── PoW 기록 (건강한 서버에만 execute-plan 실행) ───────────────────────────────
HEALTHY_TARGETS=()
for user in "${TARGETS[@]}"; do
  [ "${RESULTS[$user]:-}" = "HEALTHY" ] && HEALTHY_TARGETS+=("$user")
done

if [ ${#HEALTHY_TARGETS[@]} -gt 0 ]; then
  log "PoW 증거 기록..."
  PROJECT=$(api POST /projects '{
    "name": "deploy-subagent-evidence",
    "request_text": "subagent 배포 완료 증거 기록",
    "master_mode": "external"
  }')
  EPID=$(echo "$PROJECT" | jq_val "['project']['id']")
  api POST "/projects/$EPID/plan" > /dev/null
  api POST "/projects/$EPID/execute" > /dev/null 2>&1 || true

  TASKS="["
  ORDER=1
  FIRST=1
  for user in "${HEALTHY_TARGETS[@]}"; do
    ip="${SERVER_IPS[$user]}"
    subagent="http://$ip:8002"
    [ $FIRST -eq 0 ] && TASKS+=","
    TASKS+="{\"order\":$ORDER,\"title\":\"$user: verify\",\"instruction_prompt\":\"curl -s http://localhost:8002/health\",\"risk_level\":\"low\",\"subagent_url\":\"$subagent\"}"
    ORDER=$((ORDER+1))
    FIRST=0
  done
  TASKS+="]"

  api POST "/projects/$EPID/execute-plan" \
    "{\"tasks\":$TASKS,\"subagent_url\":\"http://localhost:8002\"}" > /dev/null 2>&1 || true

  SERVERS_STR=$(IFS=,; echo "${HEALTHY_TARGETS[*]}")
  OUTCOME=$([ $DEPLOY_OK -eq 1 ] && echo "success" || echo "partial_failure")
  api POST "/projects/$EPID/completion-report" \
    "{\"summary\":\"SubAgent 배포 완료 ($SERVERS_STR)\",\"outcome\":\"$OUTCOME\",\
\"work_details\":[\"sparse git pull: apps/subagent-runtime + packages/pi_adapter\",\
\"fuser port kill + nohup disown restart\",\"health verified\"]}" > /dev/null

  log "PoW 기록 완료 (project: $EPID)"
fi

# ── 결과 요약 ─────────────────────────────────────────────────────────────────
echo ""
log "=== 배포 결과 ==="
for user in "${TARGETS[@]}"; do
  log "  $user: ${RESULTS[$user]:-SKIPPED}"
done

if [ $DEPLOY_OK -eq 1 ]; then
  log "배포 성공 ✓"
  exit 0
else
  log "일부 서버 실패 ✗ (로그: ssh user@host 'cat /tmp/subagent.log | tail -20')"
  exit 1
fi
