#!/usr/bin/env bash
set -euo pipefail

SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
SUBAGENT_PORT="${SUBAGENT_PORT:-55123}"
REPO_URL="${REPO_URL:-https://github.com/mrgrit/opsclaw.git}"
REMOTE_DIR="${REMOTE_DIR:-/home}"

NODES=(
  "node-1 work1 192.168.208.143"
  "node-2 work2 192.168.208.144"
)

ssh_t() {
  local user="$1" ip="$2"
  shift 2
  ssh -t -i "$SSH_KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=no "$user@$ip" "$@"
}

remote_script='
set -euo pipefail

AGENT_ID="$1"
SUBAGENT_PORT="$2"
REPO_URL="$3"
REMOTE_BASE="$4"

echo "[whoami] $(whoami) @ $(hostname)"
echo "[agent_id] $AGENT_ID"

# packages
if ! command -v git >/dev/null 2>&1; then sudo apt-get update -y; sudo apt-get install -y git; fi
if ! command -v curl >/dev/null 2>&1; then sudo apt-get update -y; sudo apt-get install -y curl ca-certificates; fi

# docker + compose
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y docker.io
  sudo systemctl enable --now docker || true
fi
if ! docker compose version >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y docker-compose-plugin
fi

# repo
cd "$REMOTE_BASE"
if [ ! -d opsclaw/.git ]; then
  rm -rf opsclaw
  git clone "$REPO_URL" opsclaw
else
  cd opsclaw
  git fetch --all -p
  git reset --hard origin/main || true
  git reset --hard origin/master || true
fi

cd "$REMOTE_BASE/opsclaw"

# make AGENT_ID env-driven (only if hardcoded)
if grep -qE "^[[:space:]]*AGENT_ID:[[:space:]]*local-agent-1[[:space:]]*$" docker-compose.yml; then
  sudo sed -i "s/^[[:space:]]*AGENT_ID:[[:space:]]*local-agent-1[[:space:]]*$/      AGENT_ID: \${AGENT_ID:-local-agent-1}/" docker-compose.yml
fi

# write .env
cat > .env <<EOF
SUBAGENT_PORT=$SUBAGENT_PORT
AGENT_ID=$AGENT_ID
EOF

# stop any container binding the port
docker ps --format "{{.ID}} {{.Ports}}" | grep -E ":${SUBAGENT_PORT}->" | awk "{print \$1}" | xargs -r docker stop || true

# run subagent
docker compose up -d --build subagent

# health
sleep 1
curl -sS "http://127.0.0.1:${SUBAGENT_PORT}/health" || true
echo
'

for row in "${NODES[@]}"; do
  set -- $row
  nid="$1"; user="$2"; ip="$3"
  echo "=== $nid ($user@$ip) ==="
  ssh_t "$user" "$ip" "bash -s -- '$nid' '$SUBAGENT_PORT' '$REPO_URL' '$REMOTE_DIR' " <<'EOF'
'"$remote_script"'
EOF
done

echo "=== VERIFY FROM MANAGER ==="
for row in "${NODES[@]}"; do
  set -- $row
  nid="$1"; ip="$3"
  echo "- $nid: $(curl -sS "http://$ip:$SUBAGENT_PORT/health" || true)"
done
