# 트러블슈팅 FAQ

## 서비스 기동 문제

### Q: `./dev.sh manager` 실행 시 포트 충돌

```bash
# 기존 프로세스 확인 및 종료
lsof -i :8000
pkill -f "manager-api"

# 재기동
./dev.sh manager
```

### Q: DB 연결 실패 (`connection refused`)

```bash
# PostgreSQL 컨테이너 상태 확인
sudo docker ps | grep postgres

# 재기동
sudo docker compose -f docker/postgres-compose.yaml up -d

# 연결 테스트
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -c "SELECT 1"
```

### Q: `ModuleNotFoundError` 발생

```bash
# 가상환경 활성화 확인
source .venv/bin/activate
which python3   # .venv/bin/python3 이어야 함

# PYTHONPATH 설정 확인
export PYTHONPATH=/home/opsclaw/opsclaw
```

---

## API 호출 문제

### Q: `400 stage must be plan`

execute-plan 호출 전 stage 전환이 필요하다:

```bash
curl -X POST http://localhost:8000/projects/$ID/plan
curl -X POST http://localhost:8000/projects/$ID/execute
# 이제 execute-plan 가능
```

### Q: `400 evidence required to close`

close 전 반드시 evidence가 1건 이상 있어야 한다:

```bash
# evidence 확인
curl http://localhost:8000/projects/$ID/evidence

# evidence가 없으면 dispatch 1회 실행 후 close
curl -X POST http://localhost:8000/projects/$ID/dispatch \
  -d '{"command":"echo done","subagent_url":"http://localhost:8002"}'
```

### Q: `completion-report` 필드 오류

필수 필드: `summary`, `outcome`, `work_details`(배열), `issues`(배열), `next_steps`(배열):

```bash
# 올바른 형식
curl -X POST http://localhost:8000/projects/$ID/completion-report \
  -d '{
    "summary": "요약",
    "outcome": "success",
    "work_details": ["항목1"],
    "issues": [],
    "next_steps": []
  }'
```

---

## Web UI 문제

### Q: `http://localhost:8000/app/` → 404

dist가 없거나 Manager API가 dist 없이 기동된 경우:

```bash
# 1. Web UI 빌드
cd apps/web-ui && npm install && npm run build && cd ../..

# 2. Manager API 재시작 (dist가 있어야 /app/ 경로가 등록됨)
pkill -f "manager-api"
./dev.sh manager
```

### Q: `/` 접속 시 `/ui`로 리다이렉트 (구 버전 동작)

Manager API가 코드 변경 전 상태로 실행 중인 경우:

```bash
pkill -f "manager-api"
./dev.sh manager
```

---

## SubAgent 실행 문제

### Q: SubAgent 연결 불가

```bash
# SubAgent 상태 확인
curl http://localhost:8002/health

# SubAgent 재기동
./dev.sh subagent

# 원격 SubAgent일 경우 방화벽 확인
ssh root@target "systemctl status opsclaw-subagent"
```

### Q: step status: failed

evidence에서 stderr 확인:

```bash
curl http://localhost:8000/projects/$ID/evidence | python3 -m json.tool
# items[n].stderr 내용 확인
```

일반적인 원인:
- 명령어 오타 → `instruction_prompt` 수정
- 권한 부족 → `sudo` 추가 또는 권한 확인
- 패키지 미설치 → 선행 설치 step 추가

### Q: Playbook step에서 "no command specified"

step 등록 시 `params` 필드 누락:

```bash
# 올바른 형식
curl -X POST http://localhost:8000/playbooks/$PB_ID/steps \
  -d '{
    "step_order": 1,
    "step_type": "tool",
    "name": "run_command",
    "ref_id": "run_command",
    "params": {"command": "echo test"}
  }'
```

---

## Ollama / LLM 문제

### Q: pi_adapter timeout

```bash
# Ollama 서버 상태 확인
curl http://192.168.0.105:11434/api/tags

# .env에서 Ollama URL 확인
grep OLLAMA .env
```

timeout은 `OPSCLAW_PI_DEFAULT_TIMEOUT_S` 환경변수로 조절 (기본 300초):

```bash
export OPSCLAW_PI_DEFAULT_TIMEOUT_S=600
```

### Q: Ollama 모델 응답 없음 (freeze)

```bash
# 모델이 GPU 메모리에 로드되어 있는지 확인
curl http://192.168.0.105:11434/api/ps

# keep_alive 설정 (pi_adapter에 적용됨)
# packages/pi_adapter/runtime/client.py: keep_alive="10m"
```

---

## 로그 확인

```bash
# manager-api 로그 (터미널 실행 시 stdout)
./dev.sh manager 2>&1 | tee /tmp/manager.log

# SubAgent 로그 (systemd로 실행 시)
journalctl -u opsclaw-subagent -f

# Bootstrap 로그 (원격 서버)
ssh root@target "tail -f /var/log/opsclaw-bootstrap.log"
```

---

## 데이터 초기화 (개발/테스트)

```bash
# 특정 프로젝트 데이터만 삭제
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw \
  -c "DELETE FROM projects WHERE name LIKE 'test-%'"

# Seed 데이터 재적재
PYTHONPATH=. .venv/bin/python3 tools/dev/seed_loader.py
```
