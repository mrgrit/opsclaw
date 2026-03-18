# OpsClaw — AI Agent Context

You are operating inside the **OpsClaw** system: a playbook-driven IT operations orchestration platform for closed internal networks.

## System Overview

| Component | Role |
|-----------|------|
| **Manager API** | REST API, central control plane — `http://127.0.0.1:8000` |
| **SubAgent** | Executes bash + LLM on target assets — `http://127.0.0.1:8001` |
| **pi (you)** | Human-facing CLI agent — orchestrates via Manager API |
| **Ollama** | LLM backend — `http://211.170.162.139:10534` |

## Core Principles

1. **Playbook이 법이다** — work follows registered Playbooks, not improvisation
2. **Asset-first** — all targets are registered Assets
3. **Evidence-first** — no completion without proof (stdout/stderr recorded)
4. **Human-minimized** — approval gates exist for high-risk ops

## Manager API Quick Reference

Base URL: `http://127.0.0.1:8000`

### Health & Status
```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
curl -s http://127.0.0.1:8000/admin/health | python3 -m json.tool
curl -s http://127.0.0.1:8000/admin/metrics | python3 -m json.tool
```

### Project Lifecycle
```bash
# 생성
curl -s -X POST http://127.0.0.1:8000/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"<name>","request_text":"<what to do>","requester":"operator"}' | python3 -m json.tool

# 조회
curl -s http://127.0.0.1:8000/projects/<id> | python3 -m json.tool

# plan → execute → validate → report
curl -s -X POST http://127.0.0.1:8000/projects/<id>/plan \
  -H "Content-Type: application/json" \
  -d '{"plan_summary":"<summary>","steps":[]}'

curl -s -X POST http://127.0.0.1:8000/projects/<id>/execute

curl -s -X POST http://127.0.0.1:8000/projects/<id>/validate/check \
  -H "Content-Type: application/json" \
  -d '{"command":"echo ok","expected_contains":"ok"}'
```

### Playbook 실행
```bash
# 사용 가능한 Playbook 목록
curl -s http://127.0.0.1:8000/registry/playbooks | python3 -m json.tool

# Playbook 연결
curl -s -X POST http://127.0.0.1:8000/projects/<project_id>/playbooks/<playbook_id>

# Playbook 실행 (dry_run으로 먼저 확인)
curl -s -X POST http://127.0.0.1:8000/projects/<project_id>/playbook/run \
  -H "Content-Type: application/json" \
  -d '{"dry_run":true,"params":{"host":"<target_host>"}}'

# 실제 실행 (subagent_url은 대상 서버의 SubAgent 주소)
curl -s -X POST http://127.0.0.1:8000/projects/<project_id>/playbook/run \
  -H "Content-Type: application/json" \
  -d '{"dry_run":false,"subagent_url":"http://<target>:8001","params":{"host":"<target>"}}'
```

### Assets & Targets
```bash
# 자산 목록
curl -s http://127.0.0.1:8000/assets | python3 -m json.tool

# 자산 등록
curl -s -X POST http://127.0.0.1:8000/assets \
  -H "Content-Type: application/json" \
  -d '{"name":"<name>","type":"linux_server","connection_info":{"host":"<ip>","port":22}}'

# 자산 건강상태
curl -s http://127.0.0.1:8000/assets/<asset_id>/health
```

### Incidents
```bash
# 미해결 인시던트
curl -s "http://127.0.0.1:8000/incidents?status=open" | python3 -m json.tool

# 인시던트 해결
curl -s -X POST http://127.0.0.1:8000/incidents/<id>/resolve
```

### Schedules & Watchers
```bash
curl -s http://127.0.0.1:8000/schedules | python3 -m json.tool
curl -s http://127.0.0.1:8000/watchers | python3 -m json.tool
```

### SubAgent Direct
```bash
# 대상 서버에서 bash 실행
curl -s -X POST http://<subagent_host>:8001/a2a/run_script \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<id>","job_run_id":"j1","script":"hostname && uptime"}'

# 대상 서버에서 LLM 분석 요청
curl -s -X POST http://<subagent_host>:8001/a2a/analyze \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<id>","job_run_id":"j2","command_output":"...","question":"..."}'
```

## Registered Playbooks

| Name | Category | Description |
|------|----------|-------------|
| `diagnose_web_latency` | operations | 웹 지연 진단 및 복구 |
| `onboard_new_linux_server` | operations | 신규 서버 온보딩 |
| `patch_wave` | operations | 패치 웨이브 실행 |
| `investigate_compromise` | security | 침해 흔적 조사 |
| `renew_certificate` | operations | TLS 인증서 갱신 |
| `cleanup_disk_usage` | operations | 디스크 정리 |
| `nightly_health_baseline_check` | monitoring | 야간 건강상태 점검 |
| `diagnose_db_performance` | operations | DB 성능 진단 |
| `monitor_siem_and_raise_incident` | security | SIEM 모니터링 |
| `tune_siem_noise` | security | SIEM 알림 튜닝 |

## Workflow Guide

### 일반 운영 작업 순서

```
1. 작업 요청 파악 → 적절한 Playbook 선택
2. Project 생성 (create)
3. Asset 연결 (link asset)
4. Playbook 연결 (link playbook)
5. Plan 수립 (plan) — plan_summary에 무엇을 왜 하는지 기록
6. Execute 전환
7. Playbook dry_run — 실행 계획 확인
8. Playbook 실제 실행 (subagent_url 지정)
9. 결과 검증 (validate/check)
10. 리포트 확정 (report/finalize)
```

### 긴급 인시던트 대응

```
1. GET /incidents?status=open 으로 현황 파악
2. 심각도·출처 확인
3. investigate_compromise 또는 관련 Playbook 선택
4. 위 순서로 프로젝트 실행
5. 완료 후 POST /incidents/<id>/resolve
```

## Important Rules for You (pi/LLM)

- **bash 도구로 curl을 통해 Manager API를 직접 호출하라** — Python 스크립트보다 curl이 간결하다
- **Playbook 외부의 임의 작업은 dispatch를 통해서만** — 직접 서버에 ssh하지 않는다
- **dry_run을 먼저 실행하고 사용자 확인 후 실제 실행**
- **작업 전 현재 시스템 상태를 /admin/health로 확인**
- **고위험 작업(restart_service, patch_wave 등)은 반드시 사용자 승인 요청**
