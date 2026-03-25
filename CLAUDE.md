# OpsClaw — Claude Code 오케스트레이션 가이드 (Mode B)

> **AI 에이전트 필독**: 작업 시작 전 `docs/agent-system-prompt.md`를 읽어라.
> 역할 분담, 실행 방법 선택 기준, 안전 규칙이 모두 포함되어 있다.

OpsClaw는 IT 운영/보안 자동화 control-plane 플랫폼이다.
Claude Code가 External Master로서 Manager API를 직접 호출하여 작업을 오케스트레이션할 수 있다.

## 역할 분담 (한 줄 요약)

| 주체 | 역할 |
|------|------|
| **Claude Code (당신)** | 계획 수립, API 호출, 결과 해석, 완료보고 |
| **Manager API :8000** | 상태 관리, evidence 기록, 실행 control-plane |
| **SubAgent :8002** | 실제 명령 실행 — **직접 호출 금지, Manager 통해서만** |

## 인프라 구성

| 서버 | IP | 역할 | SubAgent |
|------|----|------|----------|
| opsclaw | 192.168.208.142 | control plane (Manager API) | http://localhost:8002 |
| secu | 192.168.208.150 | nftables + Suricata IPS | http://192.168.208.150:8002 (내부: http://10.20.30.1:8002) |
| web | 192.168.208.151 | BunkerWeb WAF + JuiceShop | http://192.168.208.151:8002 (내부: http://10.20.30.80:8002) |
| siem | 192.168.208.152 | Wazuh 4.11.2 | http://192.168.208.152:8002 (내부: http://10.20.30.100:8002) |
| dgx-spark | 192.168.0.105 | GPU compute + Ollama LLM | http://192.168.0.105:8002 |

## 서비스 주소

| 서비스 | URL | 역할 |
|--------|-----|------|
| Manager API | http://localhost:8000 | 주 진입점 (프로젝트/Playbook/실행) |
| Master Service | http://localhost:8001 | Native LLM 계획 수립 (Mode A) |
| SubAgent Runtime | http://localhost:8002 | 명령 실행 |

## 핵심 작업 흐름

> **M28 인증 필수**: 모든 API 호출에 `-H "X-API-Key: $OPSCLAW_API_KEY"` 포함
> `export OPSCLAW_API_KEY=opsclaw-api-key-2026` (또는 `.env`에서 로딩)

```bash
# 1. 프로젝트 생성 (master_mode=external → Claude Code가 오케스트레이션)
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"my-task","request_text":"작업 내용","master_mode":"external"}'

# 2. Stage 전환
curl -X POST http://localhost:8000/projects/{id}/plan -H "X-API-Key: $OPSCLAW_API_KEY"
curl -X POST http://localhost:8000/projects/{id}/execute -H "X-API-Key: $OPSCLAW_API_KEY"

# 3a. execute-plan (tasks 배열 직접 실행, task별 subagent_url 지정 가능)
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"tasks":[{"order":1,"instruction_prompt":"echo test","risk_level":"low","subagent_url":"http://192.168.208.150:8002"}],"subagent_url":"http://localhost:8002"}'

# 3b. dispatch (단일 명령)
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"command":"hostname","subagent_url":"http://localhost:8002"}'

# 4. 결과 확인
curl -H "X-API-Key: $OPSCLAW_API_KEY" http://localhost:8000/projects/{id}/evidence/summary

# 5. 완료보고서
curl -X POST http://localhost:8000/projects/{id}/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"summary":"완료","outcome":"success","work_details":["..."]}'
```

## 등록된 Tool/Skill

- **Tools**: `run_command`, `fetch_log`, `query_metric`, `read_file`, `write_file`, `restart_service`
- **Skills**: `probe_linux_host`, `check_tls_cert`, `collect_web_latency_facts`, `monitor_disk_growth`, `summarize_incident_timeline`, `analyze_wazuh_alert_burst`

상세: `docs/api/external-master-guide.md`

## PoW & 보상

`execute-plan`으로 Task를 실행하면 **자동으로** PoW 블록과 보상이 생성된다. 별도 호출 불필요.

```bash
# PoW 블록 조회
curl "http://localhost:8000/pow/blocks?agent_id=http://192.168.208.150:8002"

# 체인 무결성 검증 (M27 패치: orphans 필드 추가)
curl "http://localhost:8000/pow/verify?agent_id=http://192.168.208.150:8002"
# 정상: {"valid":true,"blocks":N,"orphans":0,"tampered":[]}

# 보상 랭킹
curl http://localhost:8000/pow/leaderboard

# 프로젝트 작업 Replay
curl http://localhost:8000/projects/{id}/replay
```

## 강화학습 (RL)

task_reward 데이터로 Q-learning 정책을 학습하여 최적 risk_level을 추천한다.

```bash
# 학습 실행
curl -X POST http://localhost:8000/rl/train

# 추천 조회
curl "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=low"

# 정책 상태
curl http://localhost:8000/rl/policy
```

## 중요 규칙

- **M28 인증**: 모든 API 호출에 `-H "X-API-Key: $OPSCLAW_API_KEY"` 필수 (상세: `docs/manual/agent/09-api-auth.md`)
- `execute-plan` 호출 전 반드시 `/plan` → `/execute` stage 전환 필요
- `risk_level=critical` 태스크는 dry_run 자동 강제 → 사용자 확인 후 실행
- SubAgent URL이 없으면 adhoc dispatch 불가 (local 실행은 `http://localhost:8002`)
- Playbook step params는 `params` 키로 전달 (e.g. `{"command": "apt-get install nginx"}`)
- SubAgent에 직접 POST 금지 — 반드시 Manager API 통해서만 호출
- 파괴적 명령(rm -rf, DROP TABLE 등)은 사용자 명시적 승인 후에만 실행
- **agent_id는 서버별로 고유해야 함** — 같은 agent_id를 여러 환경에서 공유하면 PoW 체인 손상

## SubAgent 배포

`apps/subagent-runtime/` 또는 `packages/pi_adapter/` 변경 시 다른 서버에 배포 필요.

```bash
# 전체 배포 (secu/web/siem)
./scripts/deploy_subagent.sh

# 특정 서버만
./scripts/deploy_subagent.sh secu

# git pull 이후 표준 플로우
git pull origin main
# 새 migration이 있으면 적용
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -f migrations/0013_pow_ts_raw.sql
# Manager API 재시작
kill $(pgrep -f "manager-api") && sleep 2 && set -a && source .env && set +a && \
  export PYTHONPATH=/home/opsclaw/opsclaw && \
  nohup .venv/bin/python3.11 -m uvicorn apps.manager-api.src.main:app \
    --host 0.0.0.0 --port 8000 --log-level warning > /tmp/manager.log 2>&1 &
# SubAgent 배포 (subagent-runtime 또는 pi_adapter 변경 시만)
./scripts/deploy_subagent.sh
```

상세: `docs/manual/agent/08-subagent-deploy.md`

## 상세 문서

- **시스템 프롬프트 (에이전트용)**: `docs/agent-system-prompt.md`
- **API 전체 가이드**: `docs/api/external-master-guide.md`
- **에이전트 운용 매뉴얼**: `docs/manual/agent/05-ai-driven-mode.md`
- **sudo 가이드**: `docs/manual/agent/06-sudo-guide.md`
- **PoW 다중 환경 가이드**: `docs/manual/agent/07-pow-multi-env.md`
- **SubAgent 배포 가이드**: `docs/manual/agent/08-subagent-deploy.md`
- **API 인증 가이드**: `docs/manual/agent/09-api-auth.md`

## 알려진 버그 / 패치 이력

| 마일스톤 | 내용 |
|----------|------|
| M21 | B-01~B-05 버그 5건 수정 (2026-03-24) |
| M27 | PoW 체인 무결성 패치: ts_raw, linked-list 재구성, advisory lock (2026-03-25) |
| M28 | Manager API X-API-Key 인증 미들웨어 추가 (BUG-001, 2026-03-25) |

- **M27 수정**: `execute-plan` body에 `"confirmed": true` 추가 시 critical 태스크 실제 실행 (B-05 유지)
- **M27 신규**: `verify` 응답에 `orphans` 필드 추가 (분기 블록 수, 메인 체인 무결성과 무관)
- **M27 migration**: `0013_pow_ts_raw.sql` — 기존 블록 backfill 포함, 반드시 적용 필요
- 세부 내용: `docs/roadmap.md`, `docs/manual/agent/07-pow-multi-env.md`

## 개발 명령

```bash
# PostgreSQL 기동
echo "1" | sudo -S docker compose -f docker/postgres-compose.yaml up -d

# 서비스 기동
./dev.sh all           # 전체
./dev.sh manager       # manager-api만

# 마이그레이션 적용 (최신 파일 확인 후 적용)
ls migrations/*.sql | sort
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -f migrations/XXXX_name.sql

# Web UI 빌드
cd apps/web-ui && npm run build
```
