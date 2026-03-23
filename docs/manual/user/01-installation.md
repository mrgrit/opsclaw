# OpsClaw 설치 가이드

## 방법 A — Claude Code 자동 설치 (권장)

Linux + Claude Code만 있는 신규 시스템에서 가장 빠른 방법이다.

### 사전 조건 (수동)

Claude Code가 sudo 없이 처리할 수 없는 항목은 직접 설치해야 한다.

```bash
# 1. Docker 설치 (없으면)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# → 로그아웃 후 재로그인 (docker 그룹 반영)

# 2. Python 3.11 설치 (없으면)
sudo apt install -y python3.11 python3.11-venv

# 3. 저장소 클론
git clone https://github.com/mrgrit/opsclaw.git
cd opsclaw
```

### Claude Code 실행 및 지시

```bash
claude   # opsclaw/ 디렉토리에서 실행
```

Claude Code 프롬프트에 아래 한 줄 입력:

```
CLAUDE.md를 읽고 이 시스템에 OpsClaw를 처음부터 구동해줘.
Python venv 생성, 의존성 설치, PostgreSQL 기동, 마이그레이션 적용,
서비스 실행, health check까지 완료해줘.
```

Claude Code가 자동으로 처리하는 항목:
1. `.venv` 생성 및 pip 의존성 설치
2. `.env.example` → `.env` 복사
3. `docker compose -f docker/postgres-compose.yaml up -d`
4. 마이그레이션 0001~0009 순서 적용
5. `./dev.sh all` 로 3개 서비스 기동
6. `/health` 엔드포인트 확인

### Web UI 빌드 (선택)

`dist/`는 gitignore 대상이므로 clone 후 별도 빌드 필요:

```
apps/web-ui/ 에서 npm install && npm run build 실행해줘
```

빌드 완료 후 `http://localhost:8000/app/` 에서 Web UI 접근 가능.

### 주의사항

| 항목 | 내용 |
|------|------|
| Ollama (LLM) | `.env`의 `OPSCLAW_PI_BASE_URL`을 GPU 서버 주소로 수정 필요 |
| sudo 비밀번호 | docker compose 실행 시 필요 — Claude Code가 요청하면 입력 |
| 방화벽 | 8000/8001/8002 포트 열려 있어야 함 |

---

## 방법 B — 수동 설치

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

마이그레이션 목록 (`0001` ~ `0009`):
- 0001: 기본 스키마 (projects, assets, evidence, ...)
- 0002~0007: 기능별 테이블 추가
- 0008: `projects.master_mode` 컬럼 (M15)
- 0009: `proof_of_work`, `reward_ledger` 테이블 (M18)
- 0010: PoW `nonce`, `difficulty` 컬럼 추가 (M18 nonce 채굴)

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
