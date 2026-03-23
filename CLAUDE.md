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

## PoW & 보상

`execute-plan`으로 Task를 실행하면 **자동으로** PoW 블록과 보상이 생성된다. 별도 호출 불필요.

```bash
# PoW 블록 조회
curl "http://localhost:8000/pow/blocks?agent_id=http://localhost:8002"

# 체인 무결성 검증
curl "http://localhost:8000/pow/verify?agent_id=http://localhost:8002"

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

- `execute-plan` 호출 전 반드시 `/plan` → `/execute` stage 전환 필요
- `risk_level=critical` 태스크는 dry_run 자동 강제 → 사용자 확인 후 실행
- SubAgent URL이 없으면 adhoc dispatch 불가 (local 실행은 `http://localhost:8002`)
- Playbook step params는 `params` 키로 전달 (e.g. `{"command": "apt-get install nginx"}`)
- SubAgent에 직접 POST 금지 — 반드시 Manager API 통해서만 호출
- 파괴적 명령(rm -rf, DROP TABLE 등)은 사용자 명시적 승인 후에만 실행

## 상세 문서

- **시스템 프롬프트 (에이전트용)**: `docs/agent-system-prompt.md`
- **API 전체 가이드**: `docs/api/external-master-guide.md`
- **에이전트 운용 매뉴얼**: `docs/manual/agent/05-ai-driven-mode.md`

## 알려진 버그

M21 버그 5건 모두 수정 완료 (2026-03-24).

- B-05 수정 사항: `execute-plan` body에 `"confirmed": true` 추가 시 critical 태스크 실제 실행
- B-04 수정 사항: `execute-plan` 응답 stdout 4096자, PoW hash는 full stdout 기반
- 세부 내용: `docs/roadmap.md` M21 섹션

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
