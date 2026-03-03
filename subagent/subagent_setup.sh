#!/usr/bin/env bash
set -euo pipefail

# =========================================================
# OpsClaw SubAgent one-shot bootstrap (Ubuntu 22.04)
# - Install Docker + compose plugin
# - Allow port 55123 (ufw if enabled)
# - Clone/Pull repo
# - Build & Run subagent container
# =========================================================

REPO_URL="${REPO_URL:-https://github.com/mrgrit/opsclaw}"
REPO_DIR="${REPO_DIR:-$HOME/opsclaw}"

SUBAGENT_PORT="${SUBAGENT_PORT:-55123}"
IMAGE_NAME="${IMAGE_NAME:-opsclaw-subagent}"
CONTAINER_NAME="${CONTAINER_NAME:-opsclaw-subagent}"

log() { echo -e "\n\033[1;36m[opsclaw]\033[0m $*"; }
warn(){ echo -e "\033[1;33m[warn]\033[0m $*"; }

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    warn "This script needs root for package install. Re-running with sudo..."
    exec sudo -E bash "$0" "$@"
  fi
}

install_base_packages() {
  log "Installing base packages..."
  apt-get update -y
  apt-get install -y \
    ca-certificates \
    curl \
    git \
    gnupg \
    lsb-release \
    ufw
}

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    log "Docker already installed: $(docker --version)"
  else
    log "Installing Docker (official repo)..."

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    UBUNTU_CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME}")"
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      ${UBUNTU_CODENAME} stable" \
      > /etc/apt/sources.list.d/docker.list

    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
  fi

  log "Docker OK: $(docker --version)"
  log "Compose plugin OK: $(docker compose version)"
}

setup_user_group() {
  # add invoking user (SUDO_USER) to docker group for convenience
  local u="${SUDO_USER:-}"
  if [[ -n "${u}" ]]; then
    if getent group docker >/dev/null 2>&1; then
      log "Adding user '${u}' to docker group (if not already)..."
      usermod -aG docker "${u}" || true
      warn "You may need to re-login for docker group to take effect."
    fi
  fi
}

open_firewall_port() {
  if command -v ufw >/dev/null 2>&1; then
    local status
    status="$(ufw status | head -n 1 || true)"
    if echo "${status}" | grep -qi "Status: active"; then
      log "UFW is active. Allowing ${SUBAGENT_PORT}/tcp..."
      ufw allow "${SUBAGENT_PORT}/tcp" || true
      ufw reload || true
    else
      log "UFW not active. Skipping firewall rule."
    fi
  fi
}

clone_or_update_repo() {
  log "Cloning/updating repo into: ${REPO_DIR}"
  if [[ -d "${REPO_DIR}/.git" ]]; then
    git -C "${REPO_DIR}" fetch --all --prune
    git -C "${REPO_DIR}" pull --ff-only || true
  else
    git clone "${REPO_URL}" "${REPO_DIR}"
  fi
}

build_subagent_image() {
  log "Building subagent image: ${IMAGE_NAME}"
  docker build -t "${IMAGE_NAME}" "${REPO_DIR}/subagent"
}

run_subagent_container() {
  log "Stopping old container if exists: ${CONTAINER_NAME}"
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true

  log "Running subagent container on port ${SUBAGENT_PORT}..."
  docker run -d \
    --name "${CONTAINER_NAME}" \
    --restart unless-stopped \
    -p "${SUBAGENT_PORT}:55123" \
    "${IMAGE_NAME}"

  log "Container status:"
  docker ps --filter "name=${CONTAINER_NAME}"
}

health_check() {
  log "Health check (local): http://localhost:${SUBAGENT_PORT}/health"
  # curl should exist from base packages
  curl -fsS "http://localhost:${SUBAGENT_PORT}/health" || {
    warn "Health check failed. Showing logs:"
    docker logs --tail=200 "${CONTAINER_NAME}" || true
    exit 1
  }
  echo
  log "OK ✅ SubAgent is up."
}

main() {
  require_root "$@"
  install_base_packages
  install_docker
  setup_user_group
  open_firewall_port
  clone_or_update_repo
  build_subagent_image
  run_subagent_container
  health_check

  log "Next: from OpsClaw manager server, set target base_url to this server:"
  echo "  http://$(hostname -I | awk '{print $1}'):${SUBAGENT_PORT}"
}

main "$@"