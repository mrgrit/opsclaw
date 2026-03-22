# 프로젝트 관리 가이드

## 프로젝트 상태 전이

```
intake → plan → execute → validate → report → close
                    ↑__________________________|
                         replan (필요 시)
```

| 상태 | 설명 |
|------|------|
| `intake` | 프로젝트 접수 |
| `plan` | 작업 계획 수립 중 |
| `execute` | 명령 실행 중 |
| `validate` | 결과 검증 중 |
| `report` | 보고서 작성 중 |
| `close` | 완료 (evidence 필수) |

---

## 프로젝트 API

### 생성

```bash
POST /projects
{
  "name": "작업명",
  "request_text": "자연어 요청 내용",
  "master_mode": "external",   # external | native
  "mode": "one_shot",          # one_shot | batch | continuous
  "priority": "normal",        # low | normal | high | critical
  "risk_level": "low"          # low | medium | high | critical
}
```

### 조회

```bash
GET /projects              # 전체 목록
GET /projects/{id}         # 단건 조회
GET /projects?stage=plan   # 상태 필터 (미구현 시 클라이언트 필터)
```

### Stage 전환

```bash
POST /projects/{id}/plan      # intake → plan
POST /projects/{id}/execute   # plan → execute
POST /projects/{id}/validate  # execute → validate
POST /projects/{id}/report    # validate → report
POST /projects/{id}/close     # report → close (evidence 필수)
POST /projects/{id}/replan    # 현재 → plan (이유 필수)
  body: {"reason": "재계획 사유"}
```

---

## Evidence (실행 증거)

모든 작업 실행 결과는 evidence로 자동 기록된다.

```bash
# evidence 목록
GET /projects/{id}/evidence

# evidence 요약
GET /projects/{id}/evidence/summary
# → {"total": 5, "success_count": 5, "failure_count": 0, "success_rate": 1.0}
```

evidence 항목 구조:
```json
{
  "id": "ev_...",
  "project_id": "prj_...",
  "command": "실행된 명령",
  "stdout": "표준 출력",
  "stderr": "표준 에러",
  "exit_code": 0,
  "created_at": "2026-03-22T..."
}
```

---

## 실행 방법

### execute-plan — 다단계 작업

```bash
POST /projects/{id}/execute-plan
{
  "tasks": [
    {"order": 1, "title": "작업명", "instruction_prompt": "명령어", "risk_level": "low"}
  ],
  "subagent_url": "http://subagent-host:8002",
  "dry_run": false
}
```

`risk_level` 별 동작:
- `low / medium / high`: 즉시 실행
- `critical`: `dry_run=true` 자동 강제 → 결과 확인 후 `dry_run=false`로 재실행

### dispatch — 단일 명령

```bash
POST /projects/{id}/dispatch
{"command": "systemctl status nginx", "subagent_url": "http://...:8002"}
```

---

## 완료보고서

```bash
POST /projects/{id}/completion-report
{
  "summary": "한 줄 요약",
  "outcome": "success",         # success | partial | failed
  "work_details": ["완료 항목"],
  "issues": ["발생 이슈"],
  "next_steps": ["후속 권장"]
}

# 조회
GET /projects/{id}/report
```

---

## Approval Gate

`risk_level=high` 또는 `critical` 프로젝트는 실행 전 승인 필요:

```bash
# 승인 상태 확인
GET /projects/{id}/approval

# 승인 처리 (Master Review)
POST /master/reviews
{"project_id": "{id}", "decision": "approve", "comment": "승인"}
```

---

## replan (재계획)

실행 중 문제 발생 시 plan 단계로 되돌림:

```bash
POST /projects/{id}/replan
{"reason": "패키지 설치 실패 — 대안 방법 재계획 필요"}
```
