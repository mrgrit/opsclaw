# OpsClaw 설치 가이드

> **문서 버전**: 1.0 | **최종 수정**: 2026-03-30

---

## 사전 요구사항

OpsClaw를 설치하기 전에 다음 소프트웨어가 필요하다.

| 소프트웨어 | 최소 버전 | 용도 | 설치 확인 |
|-----------|-----------|------|-----------|
| Python | 3.11 | 백엔드 런타임 | `python3.11 --version` |
| Docker | 24.0+ | PostgreSQL 컨테이너 | `docker --version` |
| Docker Compose | v2.0+ | 컨테이너 오케스트레이션 | `docker compose version` |
| Git | 2.30+ | 소스코드 관리 | `git --version` |
| curl | 최신 | API 테스트 | `curl --version` |
| psql | 15+ | DB 마이그레이션 (선택) | `psql --version` |

### Python 3.11 설치 (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
```

### Docker 설치

```bash
# Docker 공식 설치 스크립트
curl -fsSL https://get.docker.com | sudo sh

# 현재 사용자를 docker 그룹에 추가 (재로그인 필요)
sudo usermod -aG docker $USER
newgrp docker
```

---

## 1단계: 소스코드 클론

```bash
# GitHub에서 클론
git clone https://github.com/mrgrit/opsclaw.git
cd opsclaw

# 디렉토리 구조 확인
ls -la
# apps/          — 서비스 소스코드 (manager-api, master-service, subagent-runtime, cli)
# packages/      — 공통 패키지 (27개)
# migrations/    — DB 마이그레이션 (13개)
# docker/        — Docker Compose 파일
# scripts/       — 배포/유틸리티 스크립트
# docs/          — 개발 문서
# contents/      — 매뉴얼, 논문, 교육 자료
# .env.example   — 환경변수 템플릿
# dev.sh         — 개발 서버 실행 스크립트
```

---

## 2단계: Python 가상환경 구성

```bash
# 가상환경 생성
python3.11 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치
pip install fastapi pydantic uvicorn requests psycopg2-binary httpx sqlalchemy langgraph croniter
```

> **참고**: `pyproject.toml`의 Poetry 설정에 호환성 문제가 있으므로, pip + venv 방식을 사용한다.

### 설치 확인

```bash
# Python 버전 확인
python --version
# Python 3.11.x

# FastAPI 설치 확인
python -c "import fastapi; print(fastapi.__version__)"
```

---

## 3단계: 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필요시 편집
vi .env
```

주요 환경변수:

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DATABASE_URL` | `postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw` | PostgreSQL 접속 정보 |
| `OPSCLAW_API_KEY` | `opsclaw-api-key-2026` | Manager API 인증 키 |
| `OLLAMA_BASE_URL` | `http://192.168.0.105:11434/v1` | Ollama LLM 서버 주소 |
| `OLLAMA_MODEL` | `gpt-oss:120b` | 사용할 LLM 모델 |
| `OPSCLAW_POW_DIFFICULTY` | `4` | PoW 난이도 (leading zero hex 개수) |
| `OPSCLAW_POW_MAX_NONCE` | `10000000` | PoW 최대 시행 횟수 |

---

## 4단계: PostgreSQL 기동

```bash
# Docker Compose로 PostgreSQL 시작
sudo docker compose -f docker/postgres-compose.yaml up -d

# 컨테이너 상태 확인
docker ps
# NAMES              IMAGE        PORTS
# docker-postgres-1  postgres:15  0.0.0.0:5432->5432/tcp

# 접속 테스트
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c "SELECT 1;"
#  ?column?
# ----------
#         1
```

> **sudo 없이 Docker 실행하기**: `sudo usermod -aG docker $USER` 후 재로그인하면 `sudo` 없이 `docker compose`를 실행할 수 있다.

---

## 5단계: DB 마이그레이션

13개의 마이그레이션 파일을 순서대로 적용한다.

```bash
# 마이그레이션 파일 목록 확인
ls migrations/*.sql | sort
# 0001_init_core.sql
# 0002_registry.sql
# 0003_history_and_experience.sql
# 0004_scheduler_and_watch.sql
# 0005_rbac.sql
# 0006_notifications.sql
# 0007_completion_reports.sql
# 0008_master_mode.sql
# 0009_proof_of_work.sql
# 0010_pow_nonce_difficulty.sql
# 0011_playbook_versions.sql
# 0012_async_tasks.sql
# 0013_pow_ts_raw.sql

# 전체 마이그레이션 적용 (순서대로)
for f in $(ls migrations/*.sql | sort); do
  echo "적용 중: $f"
  PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -f "$f"
done
```

### 개별 마이그레이션 적용

특정 마이그레이션만 적용할 때:

```bash
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw \
  -f migrations/0013_pow_ts_raw.sql
```

### 마이그레이션 적용 확인

```bash
# 주요 테이블 존재 확인
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c "
  SELECT tablename FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY tablename;
"
# 예상 결과: projects, evidence, proof_of_work, task_reward,
#            reward_ledger, playbooks, playbook_steps, ...
```

---

## 6단계: 서비스 기동

### 방법 A — dev.sh 스크립트 (권장)

```bash
# 전체 서비스 기동 (Manager + Master + SubAgent)
./dev.sh all

# 또는 개별 서비스만
./dev.sh manager     # Manager API (:8000)
./dev.sh master      # Master Service (:8001)
./dev.sh subagent    # SubAgent Runtime (:8002)
```

### 방법 B — 수동 기동

```bash
# 환경변수 로딩
set -a && source .env && set +a
export PYTHONPATH=/home/opsclaw/opsclaw

# Manager API 기동
.venv/bin/uvicorn "apps.manager-api.src.main:app" \
  --host 0.0.0.0 --port 8000 --reload &

# Master Service 기동
.venv/bin/uvicorn "apps.master-service.src.main:app" \
  --host 0.0.0.0 --port 8001 --reload &

# SubAgent Runtime 기동
.venv/bin/uvicorn "apps.subagent-runtime.src.main:app" \
  --host 0.0.0.0 --port 8002 --reload &
```

### 방법 C — 백그라운드 프로덕션 기동

```bash
set -a && source .env && set +a
export PYTHONPATH=/home/opsclaw/opsclaw

# Manager API (로그: /tmp/manager.log)
nohup .venv/bin/python3.11 -m uvicorn apps.manager-api.src.main:app \
  --host 0.0.0.0 --port 8000 --log-level warning > /tmp/manager.log 2>&1 &

# Master Service (로그: /tmp/master.log)
nohup .venv/bin/python3.11 -m uvicorn apps.master-service.src.main:app \
  --host 0.0.0.0 --port 8001 --log-level warning > /tmp/master.log 2>&1 &

# SubAgent Runtime (로그: /tmp/subagent.log)
nohup .venv/bin/python3.11 -m uvicorn apps.subagent-runtime.src.main:app \
  --host 0.0.0.0 --port 8002 --log-level warning > /tmp/subagent.log 2>&1 &
```

---

## 7단계: 헬스체크

모든 서비스가 정상 기동되었는지 확인한다.

```bash
# Manager API
curl -s http://localhost:8000/health | python3 -m json.tool
# {"status": "ok", "service": "manager-api"}

# Master Service
curl -s http://localhost:8001/health | python3 -m json.tool
# {"status": "ok", "service": "master-service"}

# SubAgent Runtime
curl -s http://localhost:8002/health | python3 -m json.tool
# {"status": "ok", "service": "subagent-runtime"}
```

### 전체 상태를 한 번에 확인

```bash
for port in 8000 8001 8002; do
  echo -n "Port $port: "
  curl -s --max-time 2 http://localhost:$port/health 2>/dev/null || echo "FAIL"
done
```

---

## 8단계: SubAgent 원격 배포

원격 서버(secu, web, siem)에 SubAgent를 배포한다.

### 사전 조건

- 각 서버에 SSH 키 인증이 설정되어 있어야 한다
- 각 서버에 Python 3.11이 설치되어 있어야 한다
- 각 서버에서 포트 8002가 열려 있어야 한다

### 배포 실행

```bash
# 전체 서버 배포 (secu, web, siem)
./scripts/deploy_subagent.sh

# 특정 서버만 배포
./scripts/deploy_subagent.sh secu

# 복수 서버 지정
./scripts/deploy_subagent.sh secu web
```

### 배포 스크립트 동작

1. SSH로 대상 서버에 접속
2. `git sparse checkout`으로 SubAgent 코드만 가져옴
3. 기존 SubAgent 프로세스를 종료 (`fuser -k 8002/tcp`)
4. `nohup + disown`으로 새 SubAgent를 백그라운드 실행
5. `/health` 엔드포인트로 정상 기동 확인
6. Manager API에 PoW 기록

### 배포 확인

```bash
# 원격 서버 SubAgent 헬스체크
curl -s http://192.168.208.150:8002/health  # secu
curl -s http://192.168.208.151:8002/health  # web
curl -s http://192.168.208.152:8002/health  # siem

# CLI로 전체 서버 상태 확인
python3 apps/cli/opsclaw.py servers
# Alias      URL                                 Status
# -------------------------------------------------------
# local      http://localhost:8002               online
# secu       http://192.168.208.150:8002         online
# v-secu     http://192.168.0.108:8002           online
# ...
```

---

## 문제 해결 (Troubleshooting)

### PostgreSQL 접속 실패

```
psql: error: connection refused
```

**원인**: Docker 컨테이너가 실행 중이지 않음

```bash
# 컨테이너 상태 확인
docker ps -a | grep postgres

# 재시작
sudo docker compose -f docker/postgres-compose.yaml up -d

# 로그 확인
docker logs docker-postgres-1
```

### 모듈 import 에러

```
ModuleNotFoundError: No module named 'packages'
```

**원인**: `PYTHONPATH`가 설정되지 않음

```bash
export PYTHONPATH=/home/opsclaw/opsclaw
```

### 포트 충돌

```
ERROR: [Errno 98] Address already in use
```

**원인**: 이미 같은 포트에서 프로세스가 실행 중

```bash
# 포트를 사용 중인 프로세스 확인
lsof -i :8000
# 또는
fuser 8000/tcp

# 프로세스 종료
kill $(lsof -t -i :8000)
```

### Manager API 기동 후 즉시 종료

```bash
# 로그 확인
cat /tmp/manager.log

# 일반적인 원인:
# 1. .env 파일 없음 → cp .env.example .env
# 2. PostgreSQL 접속 실패 → docker compose up -d
# 3. 마이그레이션 미적용 → 마이그레이션 재실행
```

### API 호출 시 401 Unauthorized

```json
{"detail": "Missing or invalid API key"}
```

**원인**: X-API-Key 헤더가 없거나 잘못됨

```bash
# 올바른 호출 방법
curl -H "X-API-Key: opsclaw-api-key-2026" http://localhost:8000/projects
```

### SubAgent 원격 접속 실패

```
Connection refused: http://192.168.208.150:8002
```

**원인**: 원격 서버에서 SubAgent가 실행 중이지 않거나 방화벽에서 차단

```bash
# 원격 서버에서 직접 확인
ssh secu "curl -s http://localhost:8002/health"

# 방화벽 확인
ssh secu "sudo nft list ruleset | grep 8002"

# SubAgent 재배포
./scripts/deploy_subagent.sh secu
```

### Python 3.11 not found

```bash
# Ubuntu에서 deadsnakes PPA 추가
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

---

## 업데이트 절차

코드가 업데이트된 후 적용하는 표준 절차:

```bash
# 1. 코드 가져오기
git pull origin main

# 2. 새 마이그레이션이 있으면 적용
ls migrations/*.sql | sort
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw \
  -f migrations/0013_pow_ts_raw.sql  # 최신 파일

# 3. Manager API 재시작
kill $(pgrep -f "manager-api") && sleep 2
set -a && source .env && set +a
export PYTHONPATH=/home/opsclaw/opsclaw
nohup .venv/bin/python3.11 -m uvicorn apps.manager-api.src.main:app \
  --host 0.0.0.0 --port 8000 --log-level warning > /tmp/manager.log 2>&1 &

# 4. SubAgent 코드가 변경된 경우에만 원격 배포
./scripts/deploy_subagent.sh
```

---

## 다음 단계

설치가 완료되었으면 [03-quickstart.md](03-quickstart.md)에서 첫 프로젝트를 실행해 본다.
