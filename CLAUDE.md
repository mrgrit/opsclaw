# OpsClaw — Claude Code 오케스트레이션 가이드 (Mode B)

OpsClaw는 IT 운영/보안 자동화 control-plane 플랫폼이다.
Claude Code가 External Master로서 Manager API를 직접 호출하여 작업을 오케스트레이션할 수 있다.

## 서비스 주소

| 서비스 | URL | 역할 |
|--------|-----|------|
| Manager API | http://localhost:8000 | 주 진입점 (프로젝트/Playbook/실행) |
| Master Service | http://localhost:8001 | Native LLM 계획 수립 (Mode A) |
| SubAgent Runtime | http://localhost:8002 | 명령 실행 |

## 핵심 작업 흐름

```bash
# 1. 프로젝트 생성 (master_mode=external → Claude Code가 오케스트레이션)
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"my-task","request_text":"작업 내용","master_mode":"external"}'

# 2. Stage 전환
curl -X POST http://localhost:8000/projects/{id}/plan
curl -X POST http://localhost:8000/projects/{id}/execute

# 3a. execute-plan (tasks 배열 직접 실행)
curl -X POST http://localhost:8000/projects/{id}/execute-plan \
  -d '{"tasks":[{"order":1,"instruction_prompt":"echo test","risk_level":"low"}],"subagent_url":"http://localhost:8002"}'

# 3b. dispatch (단일 명령)
curl -X POST http://localhost:8000/projects/{id}/dispatch \
  -d '{"command":"hostname","subagent_url":"http://localhost:8002"}'

# 4. 결과 확인
curl http://localhost:8000/projects/{id}/evidence/summary

# 5. 완료보고서
curl -X POST http://localhost:8000/projects/{id}/completion-report \
  -d '{"summary":"완료","outcome":"success","work_details":["..."]}'
```

## 등록된 Tool/Skill

- **Tools**: `run_command`, `fetch_log`, `query_metric`, `read_file`, `write_file`, `restart_service`
- **Skills**: `probe_linux_host`, `check_tls_cert`, `collect_web_latency_facts`, `monitor_disk_growth`, `summarize_incident_timeline`, `analyze_wazuh_alert_burst`

상세: `docs/api/external-master-guide.md`

## 중요 규칙

- `execute-plan` 호출 전 반드시 `/plan` → `/execute` stage 전환 필요
- `risk_level=critical` 태스크는 dry_run 자동 강제
- SubAgent URL이 없으면 adhoc dispatch 불가 (local 실행은 `http://localhost:8002`)
- Playbook step params는 `params` 키로 전달 (e.g. `{"command": "apt-get install nginx"}`)

## 개발 명령

```bash
# PostgreSQL 기동
echo "1" | sudo -S docker compose -f docker/postgres-compose.yaml up -d

# 서비스 기동
./dev.sh all           # 전체
./dev.sh manager       # manager-api만

# 마이그레이션 적용
PGPASSWORD=opsclaw psql -h 127.0.0.1 -U opsclaw -d opsclaw -f migrations/000X_*.sql
```
