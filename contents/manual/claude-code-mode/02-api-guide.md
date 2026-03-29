# Manager API 전체 가이드

> **문서 버전**: 1.0 | **최종 수정**: 2026-03-30
> **서비스 포트**: 8000
> **인증**: `X-API-Key: opsclaw-api-key-2026`

---

## 개요

Manager API는 OpsClaw의 주 진입점이다. 프로젝트 라이프사이클 관리, 명령 실행,
Evidence 기록, PoW 블록체인, 강화학습(RL), Playbook, Schedule, Watcher, Notification 등
모든 기능이 이 API를 통해 제공된다.

---

## 인증

모든 요청에 `X-API-Key` 헤더가 필수이다.

```bash
export OPSCLAW_API_KEY="opsclaw-api-key-2026"

# 모든 curl 호출 예시의 공통 헤더
-H "X-API-Key: $OPSCLAW_API_KEY"
-H "Content-Type: application/json"
```

인증 실패 시:
```json
{"detail": "Missing or invalid API key"}
```

---

## 1. 프로젝트 (Project)

### POST /projects — 프로젝트 생성

```bash
curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "name": "보안-점검-2026-03-30",
    "request_text": "v-secu 서버의 방화벽 규칙과 IDS 상태를 점검",
    "master_mode": "external"
  }'
```

요청 필드:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | string | 필수 | 프로젝트 이름 |
| `request_text` | string | 권장 | 자연어 요구사항 |
| `master_mode` | string | 필수 | `native` 또는 `external` |

응답:
```json
{
  "status": "ok",
  "project": {
    "id": "prj_a1b2c3d4e5f6",
    "name": "보안-점검-2026-03-30",
    "request_text": "v-secu 서버의 방화벽 규칙과 IDS 상태를 점검",
    "current_stage": "init",
    "master_mode": "external",
    "created_at": "2026-03-30T10:00:00Z"
  }
}
```

### GET /projects — 프로젝트 목록

```bash
curl -s http://localhost:8000/projects \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### GET /projects/{id} — 프로젝트 상세

```bash
curl -s http://localhost:8000/projects/$PID \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

---

## 2. Stage 전환

프로젝트 실행 전 반드시 Stage를 순서대로 전환해야 한다.

### POST /projects/{id}/plan — 계획 단계 진입

```bash
curl -s -X POST http://localhost:8000/projects/$PID/plan \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### POST /projects/{id}/execute — 실행 단계 진입

```bash
curl -s -X POST http://localhost:8000/projects/$PID/execute \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### POST /projects/{id}/close — 프로젝트 종료

```bash
curl -s -X POST http://localhost:8000/projects/$PID/close \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

Stage 순서 위반 시:
```json
{"detail": {"message": "stage must be plan before execute"}}
```

---

## 3. 작업 실행

### POST /projects/{id}/execute-plan — 다단계 작업 실행

```bash
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "시스템 정보 수집",
        "instruction_prompt": "hostname && uptime && uname -a",
        "risk_level": "low"
      },
      {
        "order": 2,
        "title": "디스크 확인",
        "instruction_prompt": "df -h",
        "risk_level": "low"
      },
      {
        "order": 3,
        "title": "메모리 확인",
        "instruction_prompt": "free -m",
        "risk_level": "low",
        "subagent_url": "http://192.168.0.108:8002"
      }
    ],
    "subagent_url": "http://localhost:8002",
    "dry_run": false,
    "parallel": true
  }'
```

요청 필드:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `tasks` | array | 필수 | 실행할 태스크 목록 |
| `tasks[].order` | int | 필수 | 실행 순서 |
| `tasks[].title` | string | 권장 | 태스크 제목 |
| `tasks[].instruction_prompt` | string | 필수 | 실행할 명령 또는 지시 |
| `tasks[].risk_level` | string | 권장 | `low`, `medium`, `high`, `critical` |
| `tasks[].subagent_url` | string | 선택 | task별 SubAgent URL (상위 설정 오버라이드) |
| `subagent_url` | string | 필수 | 기본 SubAgent URL |
| `dry_run` | bool | 선택 | true면 실행하지 않고 계획만 확인 |
| `parallel` | bool | 선택 | true면 병렬 실행 (기본: true) |
| `confirmed` | bool | 선택 | critical 태스크 실행 확인 (M27) |

응답:
```json
{
  "status": "ok",
  "tasks_total": 3,
  "tasks_ok": 3,
  "tasks_failed": 0,
  "overall": "success",
  "task_results": [
    {
      "order": 1,
      "title": "시스템 정보 수집",
      "status": "ok",
      "duration_s": 1.15,
      "evidence_id": "ev_abc123",
      "pow_id": "pow_xyz789",
      "detail": {
        "stdout": "opsclaw\n 10:30:45 up 5 days...",
        "stderr": "",
        "exit_code": 0
      }
    }
  ]
}
```

overall 값:

| 값 | 설명 |
|----|------|
| `success` | 모든 태스크 성공 |
| `partial` | 일부 태스크 실패 |
| `failed` | 전체 실패 |

### POST /projects/{id}/dispatch — 단일 명령 실행

```bash
curl -s -X POST http://localhost:8000/projects/$PID/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "command": "systemctl status nginx",
    "subagent_url": "http://localhost:8002"
  }'
```

요청 필드:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `command` | string | 필수 | 실행할 shell 명령 |
| `subagent_url` | string | 필수 | SubAgent URL |
| `mode` | string | 선택 | 실행 모드 (기본: auto) |

응답:
```json
{
  "status": "ok",
  "result": {
    "stdout": "nginx.service - A high performance web server...",
    "stderr": "",
    "exit_code": 0,
    "evidence_id": "ev_def456"
  }
}
```

---

## 4. Evidence (증거)

### GET /projects/{id}/evidence — Evidence 목록

```bash
curl -s http://localhost:8000/projects/$PID/evidence \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

응답:
```json
{
  "status": "ok",
  "evidence": [
    {
      "id": "ev_abc123",
      "project_id": "prj_a1b2c3d4e5f6",
      "task_title": "시스템 정보 수집",
      "stdout": "opsclaw\n 10:30:45 up 5 days...",
      "stderr": "",
      "exit_code": 0,
      "duration_s": 1.15,
      "created_at": "2026-03-30T10:30:45Z"
    }
  ]
}
```

### GET /projects/{id}/evidence/summary — Evidence 요약

```bash
curl -s http://localhost:8000/projects/$PID/evidence/summary \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

응답:
```json
{
  "status": "ok",
  "total_evidence": 3,
  "success_count": 3,
  "failure_count": 0,
  "success_rate": "100%",
  "total_duration_s": 3.15
}
```

---

## 5. Proof-of-Work (PoW)

### GET /pow/blocks — PoW 블록 조회

```bash
# 특정 에이전트의 블록
curl -s "http://localhost:8000/pow/blocks?agent_id=http://localhost:8002&limit=10" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

응답:
```json
{
  "status": "ok",
  "total": 5,
  "blocks": [
    {
      "id": "pow_88210bdf570b",
      "agent_id": "http://localhost:8002",
      "project_id": "prj_a1b2c3d4e5f6",
      "task_order": 1,
      "task_title": "시스템 정보 수집",
      "evidence_hash": "c530...",
      "prev_hash": "0000...",
      "block_hash": "000052f7...",
      "nonce": 36166,
      "difficulty": 4,
      "ts": "2026-03-30T10:30:46Z"
    }
  ]
}
```

### GET /pow/blocks/{pow_id} — 단건 블록 조회

```bash
curl -s http://localhost:8000/pow/blocks/pow_88210bdf570b \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### GET /pow/verify — 체인 무결성 검증

```bash
curl -s "http://localhost:8000/pow/verify?agent_id=http://localhost:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

응답:
```json
{
  "status": "ok",
  "result": {
    "agent_id": "http://localhost:8002",
    "valid": true,
    "blocks": 11,
    "orphans": 0,
    "tampered": []
  }
}
```

위변조 감지 시 `tampered` 배열에 사유 포함:
- `block_hash_mismatch` — 블록 해시 불일치
- `difficulty_not_met` — 난이도 조건 미충족
- `chain_broken` — 이전 블록 연결 끊김

### GET /pow/leaderboard — 보상 랭킹

```bash
curl -s "http://localhost:8000/pow/leaderboard?limit=10" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### GET /projects/{id}/pow — 프로젝트별 PoW 블록

```bash
curl -s http://localhost:8000/projects/$PID/pow \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### GET /projects/{id}/replay — 프로젝트 실행 타임라인

```bash
curl -s http://localhost:8000/projects/$PID/replay \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

응답:
```json
{
  "project_id": "prj_a1b2c3d4e5f6",
  "steps_total": 3,
  "steps_success": 3,
  "total_reward": 3.9,
  "timeline": [
    {
      "task_order": 1,
      "task_title": "시스템 정보 수집",
      "exit_code": 0,
      "duration_s": 1.15,
      "total_reward": 1.3,
      "block_hash": "000052f7..."
    }
  ]
}
```

---

## 6. 보상 (Reward)

### GET /rewards/agents — 에이전트 잔액 + 보상 이력

```bash
curl -s "http://localhost:8000/rewards/agents?agent_id=http://localhost:8002" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

보상은 `execute-plan` 실행 시 자동 지급된다. 별도의 채굴 API 호출은 필요 없다.

보상 계산:
- 성공(exit_code=0): 기본 보상 + 속도 보너스
- 실패: 감소된 보상 또는 0

---

## 7. 강화학습 (RL)

### POST /rl/train — 학습 실행

```bash
curl -s -X POST "http://localhost:8000/rl/train?alpha=0.1&gamma=0.95&epsilon=0.15&limit=500" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

파라미터:

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `alpha` | 0.1 | 학습률 |
| `gamma` | 0.95 | 할인율 |
| `epsilon` | 0.15 | 탐색 확률 |
| `limit` | 500 | 학습에 사용할 최대 에피소드 수 |

응답:
```json
{
  "status": "ok",
  "episodes_used": 12,
  "updates": 12,
  "train_count": 2
}
```

### GET /rl/recommend — 추천 조회

```bash
curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=low&task_order=1" \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

응답:
```json
{
  "status": "ok",
  "recommended_risk_level": "low",
  "q_values": {"low": 0.74, "medium": 0.0, "high": 0.0, "critical": 0.0},
  "confidence": "trained"
}
```

confidence 값:
- `trained` — 학습된 정책 기반 추천
- `default` — 학습 데이터 부족, 기본값 반환

### GET /rl/policy — 정책 상태 조회

```bash
curl -s http://localhost:8000/rl/policy \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

응답:
```json
{
  "status": "ok",
  "num_states": 48,
  "num_actions": 4,
  "nonzero_entries": 2,
  "coverage_pct": 1.0,
  "episodes_trained": 12,
  "train_count": 2
}
```

---

## 8. 완료보고서 (Completion Report)

### POST /projects/{id}/completion-report — 보고서 제출

```bash
curl -s -X POST http://localhost:8000/projects/$PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "summary": "v-secu 서버 보안 점검 완료",
    "outcome": "success",
    "work_details": [
      "nftables 방화벽 규칙 확인 - 정상",
      "Suricata IDS 상태 확인 - 정상 동작 중",
      "오픈 포트 감사 - 불필요한 포트 없음"
    ],
    "issues": [],
    "next_steps": ["TLS 인증서 갱신 예정 (만료 30일 전)"]
  }'
```

요청 필드:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `summary` | string | 필수 | 한 줄 요약 |
| `outcome` | string | 필수 | `success`, `partial`, `failed` |
| `work_details` | array | 필수 | 완료된 작업 항목 목록 |
| `issues` | array | 선택 | 발견된 이슈 (없으면 빈 배열) |
| `next_steps` | array | 선택 | 후속 권장사항 (없으면 빈 배열) |

### GET /projects/{id}/report — 보고서 조회

```bash
curl -s http://localhost:8000/projects/$PID/report \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

---

## 9. Playbook

### POST /playbooks — Playbook 생성

```bash
curl -s -X POST http://localhost:8000/playbooks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name": "server-health-check", "version": "1.0"}'
```

### POST /playbooks/{id}/steps — Step 추가

```bash
# Tool 타입 (shell 명령)
curl -s -X POST http://localhost:8000/playbooks/$PBID/steps \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "step_order": 1,
    "step_type": "tool",
    "name": "run_command",
    "ref_id": "run_command",
    "params": {"command": "hostname && uptime && df -h"}
  }'

# Skill 타입 (절차)
curl -s -X POST http://localhost:8000/playbooks/$PBID/steps \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "step_order": 2,
    "step_type": "skill",
    "name": "probe_linux_host",
    "ref_id": "probe_linux_host"
  }'
```

### GET /playbooks — Playbook 목록

```bash
curl -s http://localhost:8000/playbooks \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### POST /projects/{id}/playbooks/{playbook_id} — Playbook 연결

```bash
curl -s -X POST http://localhost:8000/projects/$PID/playbooks/$PBID \
  -H "X-API-Key: $OPSCLAW_API_KEY"
```

### POST /projects/{id}/playbook/run — Playbook 실행

```bash
curl -s -X POST http://localhost:8000/projects/$PID/playbook/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "dry_run": false,
    "subagent_url": "http://localhost:8002"
  }'
```

---

## 10. PoW 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OPSCLAW_POW_DIFFICULTY` | `4` | leading zero hex 개수 (4 = 약 65,536회 시행) |
| `OPSCLAW_POW_MAX_NONCE` | `10,000,000` | 무한루프 방지 상한 |

난이도 수준:
- 3: 약 4,096회 (빠름)
- 4: 약 65,536회 (기본, 약 1~2초)
- 5: 약 1,048,576회 (느림)

---

## 전체 워크플로우 예시

### 예시 1: 서버 온보딩

```bash
# 환경변수
export OPSCLAW_API_KEY="opsclaw-api-key-2026"
TARGET="http://192.168.0.108:8002"

# 1. 프로젝트 생성
PID=$(curl -s -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"name":"server-onboard","request_text":"v-secu 온보딩","master_mode":"external"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['project']['id'])")

# 2. Stage 전환
curl -s -X POST http://localhost:8000/projects/$PID/plan -H "X-API-Key: $OPSCLAW_API_KEY"
curl -s -X POST http://localhost:8000/projects/$PID/execute -H "X-API-Key: $OPSCLAW_API_KEY"

# 3. 작업 실행
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d "{
    \"tasks\": [
      {\"order\":1, \"title\":\"시스템 정보\", \"instruction_prompt\":\"hostname && uname -a && uptime\", \"risk_level\":\"low\"},
      {\"order\":2, \"title\":\"디스크/메모리\", \"instruction_prompt\":\"df -h && free -m\", \"risk_level\":\"low\"},
      {\"order\":3, \"title\":\"네트워크\", \"instruction_prompt\":\"ip addr show && ss -tlnp\", \"risk_level\":\"low\"},
      {\"order\":4, \"title\":\"패키지 업데이트\", \"instruction_prompt\":\"apt-get update -y\", \"risk_level\":\"medium\"}
    ],
    \"subagent_url\": \"$TARGET\"
  }"

# 4. 결과 확인
curl -s http://localhost:8000/projects/$PID/evidence/summary -H "X-API-Key: $OPSCLAW_API_KEY"

# 5. PoW 검증
curl -s "http://localhost:8000/pow/verify?agent_id=$TARGET" -H "X-API-Key: $OPSCLAW_API_KEY"

# 6. 완료보고서
curl -s -X POST http://localhost:8000/projects/$PID/completion-report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{"summary":"v-secu 온보딩 완료","outcome":"success","work_details":["시스템 정보 수집","디스크/메모리 확인","네트워크 상태 확인","패키지 업데이트 완료"]}'

echo "프로젝트 ID: $PID"
```

### 예시 2: 보안 점검

```bash
# 다중 서버를 대상으로 보안 점검
curl -s -X POST http://localhost:8000/projects/$PID/execute-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $OPSCLAW_API_KEY" \
  -d '{
    "tasks": [
      {
        "order": 1,
        "title": "방화벽 규칙 감사",
        "instruction_prompt": "nft list ruleset",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.150:8002"
      },
      {
        "order": 2,
        "title": "TLS 인증서 확인",
        "instruction_prompt": "openssl s_client -connect localhost:443 < /dev/null 2>/dev/null | openssl x509 -noout -dates -subject",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.151:8002"
      },
      {
        "order": 3,
        "title": "Wazuh 알림 수집",
        "instruction_prompt": "cat /var/ossec/logs/alerts/alerts.json | tail -10",
        "risk_level": "low",
        "subagent_url": "http://192.168.208.152:8002"
      }
    ],
    "subagent_url": "http://localhost:8002"
  }'
```

---

## RL 활용 워크플로우

강화학습을 활용하여 최적 risk_level을 자동 추천받는 흐름:

```bash
# 1. 충분한 작업을 실행하여 데이터 축적 (execute-plan 반복)
# ... (여러 프로젝트 실행)

# 2. 학습 실행
curl -s -X POST http://localhost:8000/rl/train -H "X-API-Key: $OPSCLAW_API_KEY"

# 3. 추천 조회
curl -s "http://localhost:8000/rl/recommend?agent_id=http://localhost:8002&risk_level=low" \
  -H "X-API-Key: $OPSCLAW_API_KEY"

# 4. 추천된 risk_level을 execute-plan에 반영
```

---

## 에러 코드 정리

| 상태 코드 | 원인 | 대응 |
|-----------|------|------|
| 400 | Stage 전환 순서 위반, 필수 필드 누락 | 요청 확인 |
| 401 | API Key 누락/오류 | X-API-Key 헤더 확인 |
| 404 | 프로젝트/리소스 없음 | ID 확인 |
| 502 | SubAgent 연결 실패 | SubAgent /health 확인 |

---

## 다음 단계

- **Claude Code 모드 개요**: [01-overview.md](01-overview.md)
- **Native 모드**: [../native-mode/01-overview.md](../native-mode/01-overview.md)
- **CLI 가이드**: [../native-mode/02-cli-guide.md](../native-mode/02-cli-guide.md)
