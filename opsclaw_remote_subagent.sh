#!/usr/bin/env bash
set -euo pipefail

# =============================
# OpsClaw Remote SubAgent Bootstrap (2 nodes)
# - run this on MANAGER host
# - requires: ssh key already works (no password for SSH)
# - sudo on remote may ask password (TTY); script uses -t so you can type once per node
# =============================

# ---- EDIT THESE ----
NODE1_USER="work1"
NODE1_IP="192.168.208.143"
NODE1_ID="node-1"

NODE2_USER="work2"
NODE2_IP="192.168.208.144"
NODE2_ID="node-2"

SUBAGENT_PORT="55123"
REPO_URL="https://github.com/mrgrit/opsclaw.git"
REMOTE_DIR="~/opsclaw"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"

# =============================

ssh_run() {
  local user="$1" ip="$2" cmd="$3"
  ssh -t -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=no "$user@$ip" "$cmd"
}

remote_bootstrap_cmd() {
  local agent_id="$1"
  cat <<'EOS'
set -euo pipefail

echo "[1/7] whoami / hostname"
whoami; hostname

echo "[2/7] ensure packages (git, curl) + docker"
# git/curl
if ! command -v git >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y git
fi
if ! command -v curl >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y curl ca-certificates
fi

# docker + compose plugin
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y docker.io
  sudo systemctl enable --now docker || true
fi
if ! docker compose version >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y docker-compose-plugin
fi

echo "[3/7] clone/update repo"
# expand ~ correctly
REMOTE_DIR_EXPANDED="$(eval echo "${REMOTE_DIR}")"
if [ ! -d "$REMOTE_DIR_EXPANDED/.git" ]; then
  rm -rf "$REMOTE_DIR_EXPANDED"
  git clone "'"$REPO_URL"'" "$REMOTE_DIR_EXPANDED"
else
  cd "$REMOTE_DIR_EXPANDED"
  git fetch --all -p
  git reset --hard origin/HEAD || true
  # if origin/HEAD not set, fallback
  git reset --hard origin/main || true
  git reset --hard origin/master || true
fi

cd "$REMOTE_DIR_EXPANDED"

echo "[4/7] patch docker-compose for AGENT_ID env (if hardcoded)"
# If docker-compose has "AGENT_ID: local-agent-1" replace to env form
if grep -qE '^\s*AGENT_ID:\s*local-agent-1\s*$' docker-compose.yml; then
  sed -i 's/^\(\s*AGENT_ID:\s*\)local-agent-1\s*$/\1${AGENT_ID:-local-agent-1}/' docker-compose.yml
fi

echo "[5/7] write .env for subagent"
# Keep minimal env used by subagent/compose
cat > .env <<EOF
SUBAGENT_PORT='"$SUBAGENT_PORT"'
AGENT_ID='"$AGENT_ID"'
EOF

echo "[6/7] stop any existing service on port $SUBAGENT_PORT and start subagent"
# Best effort: kill old container(s) that bind 55123
if command -v docker >/dev/null 2>&1; then
  # stop any container exposing the port
  docker ps --format '{{.ID}} {{.Ports}} {{.Names}}' | grep -E ":${SUBAGENT_PORT}->" | awk '{print $1}' | xargs -r docker stop || true
fi

# Bring up subagent only
docker compose up -d --build subagent

echo "[7/7] health check"
sleep 1
curl -sS "http://127.0.0.1:${SUBAGENT_PORT}/health" || true
echo
EOS
}

echo "=== BOOTSTRAP node-1 ($NODE1_USER@$NODE1_IP) ==="
ssh_run "$NODE1_USER" "$NODE1_IP" "$(AGENT_ID="$NODE1_ID" REPO_URL="$REPO_URL" REMOTE_DIR="$REMOTE_DIR" SUBAGENT_PORT="$SUBAGENT_PORT" bash -lc "$(remote_bootstrap_cmd "$NODE1_ID")")"

echo "=== BOOTSTRAP node-2 ($NODE2_USER@$NODE2_IP) ==="
ssh_run "$NODE2_USER" "$NODE2_IP" "$(AGENT_ID="$NODE2_ID" REPO_URL="$REPO_URL" REMOTE_DIR="$REMOTE_DIR" SUBAGENT_PORT="$SUBAGENT_PORT" bash -lc "$(remote_bootstrap_cmd "$NODE2_ID")")"

echo "=== VERIFY FROM MANAGER ==="
echo "- node-1:"
curl -sS "http://$NODE1_IP:$SUBAGENT_PORT/health"; echo
echo "- node-2:"
curl -sS "http://$NODE2_IP:$SUBAGENT_PORT/health"; echo