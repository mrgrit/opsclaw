# OpsClaw 설치 가이드

## 요구사항

| 항목 | 최소 사양 |
|------|---------|
| OS | Ubuntu 20.04+ / Debian 11+ |
| Python | 3.11+ |
| PostgreSQL | 15+ (Docker 권장) |
| GPU (선택) | NVIDIA — Ollama 모델 실행용 |
| RAM | 8GB+ (LLM 없이 4GB 가능) |

---

## 1. 저장소 클론

```bash
git clone https://github.com/mrgrit/opsclaw.git
cd opsclaw
```

---

## 2. Python 가상환경 설치

```bash
python3.11 -m venv .venv
source .venv/bin/activate

pip install fastapi pydantic uvicorn requests psycopg2-binary httpx \
            sqlalchemy langgraph croniter paramiko sshpass
```

---

## 3. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 주요 항목:

```env
DATABASE_URL=postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw
OLLAMA_BASE_URL=http://192.168.0.105:11434/v1   # GPU 서버 주소
SLACK_BOT_TOKEN=xoxb-...                         # Slack 알림 사용 시
```

---

## 4. PostgreSQL 기동

```bash
# Docker 사용 (권장)
sudo docker compose -f docker/postgres-compose.yaml up -d

# 확인
sudo docker ps | grep postgres
```

---

## 5. DB 마이그레이션

```bash
for f in migrations/00*.sql; do
  PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -f "$f"
done
```

마이그레이션 목록 (`0001` ~ `0008`):
- 0001: 기본 스키마 (projects, assets, evidence, ...)
- 0002~0007: 기능별 테이블 추가
- 0008: `projects.master_mode` 컬럼 (M15)

---

## 6. Seed 데이터 로드

```bash
# Tool/Skill/Playbook 기본 데이터 적재
PYTHONPATH=. .venv/bin/python3 tools/dev/seed_loader.py
```

---

## 7. 서비스 기동

```bash
# 전체 기동 (manager-api + master-service + subagent-runtime)
./dev.sh all

# 개별 기동
./dev.sh manager    # manager-api :8000
./dev.sh master     # master-service :8001
./dev.sh subagent   # subagent-runtime :8002
```

---

## 8. 동작 확인

```bash
curl http://localhost:8000/health   # {"status":"ok","service":"manager-api"}
curl http://localhost:8002/health   # {"status":"ok","service":"subagent-runtime"}
```

---

## SubAgent 원격 설치

대상 서버에 SubAgent를 설치하려면:

```bash
# Manager API를 통한 bootstrap
curl -X POST http://localhost:8000/assets/{asset_id}/bootstrap \
  -d '{"ssh_host":"192.168.0.10","ssh_user":"root","ssh_pass":"password"}'
```

또는 수동 설치:

```bash
scp deploy/bootstrap/install.sh root@192.168.0.10:/tmp/
ssh root@192.168.0.10 "bash /tmp/install.sh"
```
