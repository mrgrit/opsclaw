# SubAgent 업데이트 배포 가이드

> **대상**: opsclaw control plane에서 secu/web/siem SubAgent를 관리하는 운영자

---

## 배포 범위

SubAgent 서버(secu/web/siem)에는 다음 두 디렉토리만 배포됩니다:

```
apps/subagent-runtime/    ← SubAgent HTTP 서버 (FastAPI)
packages/pi_adapter/      ← 유일한 내부 의존성
```

나머지 packages(pow_service, project_service 등)는 manager-api(opsclaw)에서만 사용하므로
SubAgent 서버에 배포할 필요 없습니다.

---

## 배포 명령

```bash
# 전체 3개 서버 배포
./scripts/deploy_subagent.sh

# 특정 서버만
./scripts/deploy_subagent.sh secu
./scripts/deploy_subagent.sh secu web
```

### 표준 운영 플로우 (git pull 이후)

```bash
# 1. opsclaw control plane 업데이트
git pull origin main
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw \
  -f migrations/$(ls migrations/*.sql | sort | tail -1 | xargs basename)

# 2. Manager API 재시작
kill $(pgrep -f "manager-api") && sleep 2
set -a && source .env && set +a && export PYTHONPATH=/home/opsclaw/opsclaw
nohup .venv/bin/python3.11 -m uvicorn apps.manager-api.src.main:app \
  --host 0.0.0.0 --port 8000 --log-level warning > /tmp/manager.log 2>&1 &

# 3. SubAgent 배포 (apps/subagent-runtime 또는 packages/pi_adapter 변경 시에만)
./scripts/deploy_subagent.sh
```

---

## 동작 원리

```
deploy_subagent.sh
│
├─ [각 서버에 SSH 접속]
│   ├─ git sparse checkout (apps/subagent-runtime + packages/pi_adapter)
│   │   - 최초 실행: git init + remote add
│   │   - 이후: git fetch --depth=1 + checkout -f
│   │
│   └─ SubAgent 재시작
│       - fuser -k 8002/tcp (포트 기반 kill, pkill -f 는 SSH 셸 버그)
│       - nohup uvicorn & disown (SSH 종료 후에도 생존)
│
├─ Health 검증 (http://ip:8002/health × 3)
│
└─ PoW 기록 (Manager API execute-plan → 성공 서버만)
```

### SSH 키 인증

opsclaw의 RSA 키(`/home/opsclaw/.ssh/id_rsa`)가 각 서버의 `authorized_keys`에 등록되어 있어야 합니다.

```bash
# 키 등록 확인
ssh -n -T -o StrictHostKeyChecking=no secu@192.168.208.150 'echo OK'
ssh -n -T -o StrictHostKeyChecking=no web@192.168.208.151 'echo OK'
ssh -n -T -o StrictHostKeyChecking=no siem@192.168.208.152 'echo OK'
```

---

## SubAgent 배포가 필요한 경우 vs 불필요한 경우

| 변경 파일 | SubAgent 배포 필요 |
|-----------|:-----------------:|
| `apps/subagent-runtime/` | ✅ |
| `packages/pi_adapter/` | ✅ |
| `apps/manager-api/` | ❌ (control plane만 재시작) |
| `packages/pow_service/` | ❌ |
| `packages/project_service/` | ❌ |
| `packages/rl_service/` | ❌ |
| `migrations/` | ❌ (opsclaw DB만 적용) |
| `apps/web-ui/` | ❌ (`npm run build` 후 Manager API가 자동 서빙) |

---

## 서버 구성

| 서버 | IP | SSH 유저 | SubAgent 포트 | opsclaw 경로 |
|------|----|---------|--------------|-------------|
| secu | 192.168.208.150 | secu | 8002 | /home/secu/opsclaw |
| web | 192.168.208.151 | web | 8002 | /home/web/opsclaw |
| siem | 192.168.208.152 | siem | 8002 | /home/siem/opsclaw |

서버 추가 시 `deploy_subagent.sh`의 `SERVER_IPS` 맵에 추가합니다.

---

## 트러블슈팅

### 배포 실패 시 로그 확인

```bash
ssh secu@192.168.208.150 'cat /tmp/subagent.log | tail -30'
ssh web@192.168.208.151  'cat /tmp/subagent.log | tail -30'
ssh siem@192.168.208.152 'cat /tmp/subagent.log | tail -30'
```

### 특정 서버만 수동 재시작

```bash
ssh secu@192.168.208.150 'fuser -k 8002/tcp 2>/dev/null; sleep 1; cd /home/secu/opsclaw && export PYTHONPATH=/home/secu/opsclaw && nohup .venv/bin/python3 -m uvicorn apps.subagent-runtime.src.main:app --host 0.0.0.0 --port 8002 --log-level warning >> /tmp/subagent.log 2>&1 & disown; echo DONE'
```

### Health 직접 확인

```bash
for ip in 192.168.208.150 192.168.208.151 192.168.208.152; do
  echo -n "$ip: "; curl -sf http://$ip:8002/health 2>/dev/null || echo "DOWN"
done
```
