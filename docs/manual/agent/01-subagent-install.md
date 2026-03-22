# SubAgent 설치 가이드

SubAgent Runtime은 실제 명령을 실행하는 계층이다.
작업 대상 서버마다 설치해야 한다.

---

## 방법 A — Manager API Bootstrap (권장)

OpsClaw에 Asset을 등록한 후 API로 원격 설치한다.

### 1. Asset 등록

```bash
curl -X POST http://localhost:8000/assets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-server-01",
    "asset_type": "server",
    "hostname": "192.168.0.10",
    "description": "웹 서버"
  }'
```

응답에서 `asset.id` 저장.

### 2. Bootstrap 실행

```bash
curl -X POST http://localhost:8000/assets/{asset_id}/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "ssh_host": "192.168.0.10",
    "ssh_user": "root",
    "ssh_pass": "password",
    "ssh_port": 22
  }'
```

SSH 키 인증 사용 시:
```bash
{
  "ssh_host": "192.168.0.10",
  "ssh_user": "root",
  "ssh_key_path": "/home/opsclaw/.ssh/id_rsa"
}
```

Bootstrap이 자동으로:
1. `deploy/bootstrap/install.sh` 전송 및 실행
2. Python venv 생성 및 의존성 설치
3. `opsclaw-subagent` systemd 서비스 등록
4. Health check 확인

---

## 방법 B — 수동 설치

```bash
# 대상 서버에서 실행
git clone https://github.com/mrgrit/opsclaw.git /opt/opsclaw
cd /opt/opsclaw

python3.11 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn httpx psycopg2-binary

cp .env.example .env
# .env 편집: DATABASE_URL, OLLAMA_BASE_URL 설정
```

### systemd 서비스 등록

```bash
cat > /etc/systemd/system/opsclaw-subagent.service << 'EOF'
[Unit]
Description=OpsClaw SubAgent Runtime
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/opsclaw
Environment=PYTHONPATH=/opt/opsclaw
ExecStart=/opt/opsclaw/.venv/bin/uvicorn "apps.subagent-runtime.src.main:app" \
    --host 0.0.0.0 --port 8002
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now opsclaw-subagent
```

---

## 방법 C — install.sh 직접 실행

```bash
scp deploy/bootstrap/install.sh root@192.168.0.10:/tmp/
ssh root@192.168.0.10 "bash /tmp/install.sh"
```

로그 확인:
```bash
ssh root@192.168.0.10 "tail -f /var/log/opsclaw-bootstrap.log"
```

---

## 설치 후 확인

```bash
# 대상 서버에서
curl http://localhost:8002/health
# → {"status":"ok","service":"subagent-runtime"}

# Manager에서 원격 확인
curl http://192.168.0.10:8002/health
```

---

## SubAgent 포트 변경

기본 포트는 8002다. 변경 시:

```bash
# .env 수정
SUBAGENT_PORT=9002

# 또는 systemd 서비스 수정
ExecStart=... --port 9002
```

Asset의 `expected_subagent_port` 필드도 업데이트:
```bash
curl -X PUT http://localhost:8000/assets/{asset_id} \
  -d '{"expected_subagent_port": 9002}'
```

---

## 다중 SubAgent 운영

여러 서버에 SubAgent를 설치하면 `subagent_url`로 구분해서 dispatch한다:

```bash
# web-server로 dispatch
POST /projects/{id}/dispatch
{"command": "nginx -v", "subagent_url": "http://192.168.0.10:8002"}

# db-server로 dispatch
POST /projects/{id}/dispatch
{"command": "mysql --version", "subagent_url": "http://192.168.0.20:8002"}
```
