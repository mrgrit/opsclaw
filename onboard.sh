set -e

: "${ADMIN_USER:?ADMIN_USER is required}"
: "${PUBKEY:?PUBKEY is required}"

echo "[info] admin_user=$ADMIN_USER"

# sudo 확인
command -v sudo >/dev/null 2>&1 || { echo "sudo not found" >&2; exit 2; }

# 유저 생성 (없으면 생성)
if id "$ADMIN_USER" >/dev/null 2>&1; then
  echo "[ok] user exists: $ADMIN_USER"
else
  sudo useradd -m -s /bin/bash "$ADMIN_USER" 2>/dev/null || sudo adduser --disabled-password --gecos "" "$ADMIN_USER"
  echo "[ok] user created: $ADMIN_USER"
fi

# SSH 키 등록
sudo mkdir -p "/home/$ADMIN_USER/.ssh"
sudo chmod 700 "/home/$ADMIN_USER/.ssh"
echo "$PUBKEY" | sudo tee -a "/home/$ADMIN_USER/.ssh/authorized_keys" >/dev/null
sudo chmod 600 "/home/$ADMIN_USER/.ssh/authorized_keys"
sudo chown -R "$ADMIN_USER:$ADMIN_USER" "/home/$ADMIN_USER/.ssh"
echo "[ok] ssh key installed"

# 패키지 설치 (curl/jq)
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y curl ca-certificates jq
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y curl ca-certificates jq
elif command -v yum >/dev/null 2>&1; then
  sudo yum install -y curl ca-certificates jq
else
  echo "no supported pkg manager" >&2
  exit 3
fi
echo "[ok] packages installed"

# 검증
id "$ADMIN_USER"
test -f "/home/$ADMIN_USER/.ssh/authorized_keys"
command -v curl >/dev/null
command -v jq >/dev/null
echo "[done] onboarding"
