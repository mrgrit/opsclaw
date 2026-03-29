# 튜토리얼: nftables 방화벽 설정 -- 처음부터 끝까지

## 학습 목표

이 튜토리얼을 완료하면 다음을 할 수 있다.

- OpsClaw로 방화벽 현황을 점검한다
- nftables 규칙을 추가/삭제한다
- execute-plan으로 다단계 방화벽 설정을 자동화한다
- Evidence와 PoW 블록으로 변경 이력을 추적한다
- CLI와 API 두 가지 방법으로 같은 작업을 수행한다

**소요 시간:** 약 30분
**난이도:** 초급~중급
**대상 서버:** v-secu (192.168.0.108)

---

## 사전 준비

### 환경 확인

```bash
# OpsClaw Manager가 실행 중인지 확인
curl -s http://localhost:8000/health
# → {"status": "ok", "service": "manager-api"}

# SubAgent가 실행 중인지 확인
curl -s http://192.168.0.108:8002/health
# → {"status": "ok", "service": "subagent-runtime"}

# API Key 설정
export OPSCLAW_API_KEY=opsclaw-api-key-2026
```

---

## 단계 1: 프로젝트 생성

모든 OpsClaw 작업은 프로젝트로 시작한다. 프로젝트는 작업의 컨테이너이며,
모든 Evidence가 이 프로젝트에 연결된다.

### API 방식

```bash
# 프로젝트 생성
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "firewall-setup-tutorial",
    "request_text": "v-secu 서버 nftables 방화벽 설정 튜토리얼",
    "master_mode": "external"
  }'

# 응답에서 project_id를 확인한다
# {"status": "ok", "project": {"id": "proj_xxxxx", ...}}

# 환경변수에 저장
PID="proj_xxxxx"  # 실제 응답값으로 교체
```

### CLI 방식

```bash
# CLI로 같은 작업
opsclaw run "v-secu 방화벽 점검" --target v-secu --manual
# CLI는 프로젝트 생성 + stage 전환 + dispatch를 자동으로 수행한다
```

---

## 단계 2: Stage 전환

프로젝트는 `intake → plan → execute` 순서로 stage를 전환해야
실행(dispatch/execute-plan)이 가능하다.

```bash
# plan stage로 전환
curl -s -X POST http://localhost:8000/projects/$PID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY"
# → {"status": "ok", "project": {"current_stage": "plan", ...}}

# execute stage로 전환
curl -s -X POST http://localhost:8000/projects/$PID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY"
# → {"status": "ok", "result": {"current_stage": "execute", ...}}
```

---

## 단계 3: 현재 방화벽 규칙 확인

먼저 현재 nftables 규칙을 확인한다.

### API: dispatch 사용

```bash
curl -s -X POST http://localhost:8000/projects/$PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "nft list ruleset",
    "subagent_url": "http://192.168.0.108:8002"
  }'
```

**응답 예시:**

```json
{
  "status": "ok",
  "result": {
    "exit_code": 0,
    "stdout": "table inet filter {\n  chain input {\n    type filter hook input priority 0; policy accept;\n  }\n  chain forward {\n    ...\n  }\n  chain output {\n    ...\n  }\n}",
    "stderr": "",
    "evidence_id": "ev_xxxxx",
    "llm_converted": false
  }
}
```

이 결과는 자동으로 Evidence로 기록되었다. `evidence_id`로 나중에 조회할 수 있다.

### API: execute-plan 사용 (다중 명령)

```bash
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "nftables 규칙 확인",
        "instruction_prompt": "nft list ruleset",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 2,
        "title": "열린 포트 확인",
        "instruction_prompt": "ss -tlnp | grep LISTEN",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 3,
        "title": "nftables 설정 파일 확인",
        "instruction_prompt": "cat /etc/nftables.conf",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      }
    ]
  }'
```

**응답 예시:**

```json
{
  "status": "ok",
  "project_id": "proj_xxxxx",
  "tasks_total": 3,
  "tasks_ok": 3,
  "tasks_failed": 0,
  "overall": "success",
  "task_results": [
    {"order": 1, "title": "nftables 규칙 확인", "status": "ok", "duration_s": 1.234},
    {"order": 2, "title": "열린 포트 확인", "status": "ok", "duration_s": 0.876},
    {"order": 3, "title": "nftables 설정 파일 확인", "status": "ok", "duration_s": 0.543}
  ]
}
```

---

## 단계 4: 방화벽 규칙 추가

### 4.1 기본 규칙 설정 (SSH + HTTP만 허용)

```bash
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "현재 규칙 백업",
        "instruction_prompt": "nft list ruleset > /tmp/nftables-backup-$(date +%Y%m%d%H%M%S).conf && echo \"Backup saved\"",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 2,
        "title": "SSH 허용 규칙 추가",
        "instruction_prompt": "nft add rule inet filter input tcp dport 22 ct state new,established accept",
        "risk_level": "medium",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 3,
        "title": "HTTP/HTTPS 허용 규칙 추가",
        "instruction_prompt": "nft add rule inet filter input tcp dport { 80, 443 } ct state new,established accept",
        "risk_level": "medium",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 4,
        "title": "ICMP 허용 (ping)",
        "instruction_prompt": "nft add rule inet filter input icmp type echo-request accept",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 5,
        "title": "loopback 허용",
        "instruction_prompt": "nft add rule inet filter input iif lo accept",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 6,
        "title": "established/related 허용",
        "instruction_prompt": "nft add rule inet filter input ct state established,related accept",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 7,
        "title": "변경 후 규칙 확인",
        "instruction_prompt": "nft list chain inet filter input",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      }
    ]
  }'
```

### 4.2 특정 IP 차단 (risk_level: high)

```bash
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 8,
        "title": "악성 IP 차단",
        "instruction_prompt": "nft insert rule inet filter input ip saddr 203.0.113.50 counter drop",
        "risk_level": "high",
        "subagent_url": "http://192.168.0.108:8002"
      },
      {
        "order": 9,
        "title": "차단 확인",
        "instruction_prompt": "nft list chain inet filter input | grep 203.0.113.50",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      }
    ]
  }'
```

> sudo가 포함된 명령은 자동으로 `risk_level`이 `high`로 상향된다.
> `risk_level: critical` 명령은 `confirmed: true`가 없으면 dry_run으로 실행된다.

---

## 단계 5: Evidence 확인

모든 실행 결과는 Evidence로 기록되어 있다.

### Evidence 요약

```bash
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PID/evidence/summary
```

**응답 예시:**

```json
{
  "status": "ok",
  "project_id": "proj_xxxxx",
  "total": 9,
  "success": 9,
  "failed": 0,
  "commands": [
    "nft list ruleset",
    "ss -tlnp | grep LISTEN",
    "cat /etc/nftables.conf",
    "nft list ruleset > /tmp/nftables-backup...",
    "nft add rule inet filter input tcp dport 22...",
    "..."
  ]
}
```

### 상세 Evidence 목록

```bash
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PID/evidence
```

---

## 단계 6: PoW 블록 확인

execute-plan 실행 시 자동으로 PoW 블록이 생성되었다.

```bash
# 프로젝트의 PoW 블록 조회
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PID/pow
```

**응답 예시:**

```json
{
  "status": "ok",
  "total": 9,
  "blocks": [
    {
      "id": "pow_xxxxx",
      "agent_id": "http://192.168.0.108:8002",
      "task_title": "nftables 규칙 확인",
      "block_hash": "a1b2c3d4...",
      "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
      "ts": "2026-03-30T10:00:00.123456+00:00"
    },
    ...
  ]
}
```

### 체인 무결성 검증

```bash
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  "http://localhost:8000/pow/verify?agent_id=http://192.168.0.108:8002"

# 정상 응답
# {"status": "ok", "result": {"valid": true, "blocks": 9, "orphans": 0, "tampered": []}}
```

---

## 단계 7: Replay 확인

프로젝트의 전체 작업 과정을 타임라인으로 재생한다.

```bash
curl -s -H "X-API-Key: $OPSCLAW_API_KEY" \
  http://localhost:8000/projects/$PID/replay
```

---

## 단계 8: 완료보고서 생성

### 수동 보고서

```bash
curl -s -X POST http://localhost:8000/projects/$PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "v-secu nftables 방화벽 기본 설정 완료",
    "outcome": "success",
    "work_details": [
      "SSH(22), HTTP(80), HTTPS(443) 허용 규칙 추가",
      "ICMP echo-request 허용",
      "loopback 및 established/related 트래픽 허용",
      "악성 IP 203.0.113.50 차단"
    ],
    "next_steps": [
      "default policy를 drop으로 변경 검토",
      "규칙을 /etc/nftables.conf에 영구 저장"
    ]
  }'
```

### 자동 보고서

```bash
# Evidence를 자동 집계하여 보고서 생성
curl -s -X POST http://localhost:8000/projects/$PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"auto": true}'
```

---

## 단계 9: 경험 축적

이번 작업의 결과를 장기 메모리로 저장한다.

```bash
# Task Memory 생성 + Experience 자동 승격
curl -s -X POST "http://localhost:8000/projects/$PID/memory/build?promote=true" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

다음에 유사한 방화벽 작업을 수행할 때, Master의 master-plan이 이 경험을 RAG로 참조한다.

---

## 단계 10: 프로젝트 종료

```bash
curl -s -X POST http://localhost:8000/projects/$PID/close \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

---

## 전체 흐름 요약

```
1. 프로젝트 생성      POST /projects
2. Stage 전환        POST /projects/{id}/plan → /execute
3. 현황 확인         POST /projects/{id}/dispatch (nft list ruleset)
4. 규칙 추가         POST /projects/{id}/execute-plan (tasks 배열)
5. Evidence 확인     GET /projects/{id}/evidence/summary
6. PoW 블록 확인     GET /projects/{id}/pow
7. Replay           GET /projects/{id}/replay
8. 완료보고서        POST /projects/{id}/completion-report
9. 경험 축적         POST /projects/{id}/memory/build?promote=true
10. 종료            POST /projects/{id}/close
```

---

## CLI로 전체 과정 (간편 버전)

```bash
# 1. 방화벽 점검 (자동 프로젝트 생성 + native 모드 실행)
opsclaw run "v-secu의 nftables 방화벽 규칙을 확인하고 SSH/HTTP만 허용하도록 설정해줘" --target v-secu

# 2. 프로젝트 목록에서 ID 확인
opsclaw list

# 3. 상태 확인
opsclaw status <project_id>

# 4. Replay
opsclaw replay <project_id>
```

---

## 주의사항

- **백업 필수**: 규칙 변경 전에 항상 현재 규칙을 백업한다
- **risk_level 확인**: 방화벽 변경은 최소 `medium`, 정책 변경은 `high` 이상
- **default policy drop**: 기본 정책을 drop으로 변경할 때는 `risk_level: critical`로 설정하고 `confirmed: true` 필수
- **영구 저장**: nft 명령으로 추가한 규칙은 재부팅 시 사라진다. `/etc/nftables.conf`에 저장해야 영구 적용된다
