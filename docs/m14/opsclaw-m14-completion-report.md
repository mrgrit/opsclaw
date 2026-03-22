# OpsClaw M14 완료보고서 — Agent Role Clarity & Workflow

**작성일:** 2026-03-22
**마일스톤:** M14 — Agent Role Clarity & Workflow
**상태:** 완료

---

## 1. 목표 및 완료 기준

**목표:** Master → Manager → SubAgent 계층의 역할을 코드 수준에서 명확히 분리하고,
Playbook 단위 작업 완료 → 검수 → 보고서 생성 → 다음 작업 참조 전체 흐름을 end-to-end 구현 및 검증

**완료 기준:**
- [x] Master → Manager → SubAgent 전체 흐름 코드로 추적 가능
- [x] Playbook 완료보고서 자동 생성 및 DB 저장 동작 확인
- [x] 동일 작업 재요청 시 이전 완료보고서 참조 동작 확인

---

## 2. 구현 내용

### WORK-58 — Master 지시 프롬프트 생성 엔진 (`POST /projects/{id}/master-plan`)

**파일:** `apps/master-service/src/main.py`

- 자연어 요구사항 입력 → Ollama LLM 호출 → Playbook 단위 작업 계획(JSON) 반환
- 기존 Playbook 키워드 매칭 (`similar_playbooks`)
- 과거 완료보고서 RAG 검색 (`past_reports_referenced`)
- 반환 구조: `{summary, tasks[], similar_playbooks[], past_reports_referenced}`

### WORK-59 — Manager 작업 실행 루프 (`POST /projects/{id}/execute-plan`)

**파일:** `apps/manager-api/src/main.py`

- Master plan의 `tasks[]` 배열을 순서대로 실행
- `playbook_hint` 있으면 Playbook 실행, 없으면 adhoc dispatch
- `risk_level=critical` 태스크는 `dry_run` 강제
- 각 태스크 결과를 evidence로 자동 기록
- 반환: `{tasks_total, tasks_ok, tasks_failed, overall, task_results[]}`

### WORK-60 — Playbook 완료보고서 자동 생성 (`POST /projects/{id}/completion-report`)

**파일:** `apps/manager-api/src/main.py`, `packages/completion_report_service/`

- 보고서 내용: summary, outcome, work_details[], issues[], next_steps[]
- DB 테이블: `completion_reports` (migration: `0007_completion_reports.sql`)
- 생성 즉시 retrieval index에 등록 (RAG 참조용)

### WORK-61 — 완료보고서 RAG 참조 연동

**파일:** `apps/master-service/src/main.py`, `apps/manager-api/src/main.py`

- `packages/retrieval_service.search_documents()` 로 유사 완료보고서 검색
- Master 지시 프롬프트에 참조 보고서 context 자동 삽입
- `GET /completion-reports?q={keyword}&limit={n}` 검색 API

### WORK-62 — end-to-end 시나리오 테스트

테스트 시나리오: **"신규 Ubuntu 서버에 Nginx 설치 및 보안 설정"**

---

## 3. e2e 테스트 결과 (2026-03-22)

### 검증 환경
- manager-api: http://localhost:8000
- master-service: http://localhost:8001
- subagent-runtime: http://localhost:8002
- PostgreSQL 15: Docker (localhost:5432)

### 테스트 흐름 및 결과

| # | 단계 | API 호출 | 결과 |
|---|------|---------|------|
| 1 | Project 생성 | `POST /projects` | ✅ `prj_6a6f838b2c08` |
| 2 | Playbook 생성 | `POST /playbooks` + `POST /playbooks/{id}/steps` | ✅ `pb_5d46e0f1c4f4` (3 steps) |
| 3 | Master 계획 수립 | `POST /projects/{id}/master-plan` | ✅ 6개 태스크 생성 (LLM 응답) |
| 4 | Stage 전환 | `POST /plan` → `POST /execute` | ✅ `intake → plan → execute` |
| 5 | Manager 실행 | `POST /projects/{id}/execute-plan` | ✅ tasks_ok=4/4, overall=success |
| 6 | SubAgent dispatch | adhoc → subagent-runtime | ✅ exit_code=0 (4개 태스크) |
| 7 | 완료보고서 생성 | `POST /projects/{id}/completion-report` | ✅ DB 저장 `7d370705-...` |
| 8 | RAG 검색 | `GET /completion-reports?q=nginx` | ✅ 3건 반환 |
| 9 | 2회차 RAG 참조 | `POST /projects/{id2}/master-plan` | ✅ `past_reports_referenced: 1` |

### 핵심 검증 사항

**Master → Manager → SubAgent 흐름:**
```
사용자 요구사항
  → Master /master-plan: 6개 태스크 JSON 계획 생성
  → Manager /execute-plan: 4개 태스크 순서 실행
  → SubAgent /a2a/dispatch: echo 명령 실행 (exit_code=0)
  → /completion-report: 완료보고서 DB 저장
```

**RAG 참조 동작:**
- 1회차 완료보고서 저장 후 `search_documents("nginx")` → 1건 검색됨
- 2회차 동일 요청 시 master-plan `past_reports_referenced=1` 확인

---

## 4. 버그 및 수정 사항

| 항목 | 내용 |
|------|------|
| `execute-plan` 엔드포인트 미등록 | 서버 재기동 전까지 OpenAPI에 미노출 → 재기동으로 해결 |
| `CompletionReportRequest` 필드 불일치 | `requirements`/`work_summary`가 아닌 `summary`/`work_details[]` 사용 |
| Project stage 순서 | `execute-plan` 호출 전 `intake→plan→execute` 단계 전환 필요 |

---

## 5. API 레퍼런스 (신규)

### `POST /projects/{project_id}/master-plan` (master-service:8001)
```json
Request: {"request_text": "자연어 요구사항"}
Response: {
  "summary": "전체 계획 요약",
  "tasks": [{"order":1,"title":"...","instruction_prompt":"...","risk_level":"low"}],
  "similar_playbooks": [],
  "past_reports_referenced": 1
}
```

### `POST /projects/{project_id}/execute-plan` (manager-api:8000)
```json
Request: {
  "tasks": [{"order":1,"title":"...","instruction_prompt":"...","risk_level":"low"}],
  "subagent_url": "http://localhost:8002",
  "dry_run": false
}
Response: {
  "tasks_total": 4, "tasks_ok": 4, "tasks_failed": 0, "overall": "success",
  "task_results": [{"order":1,"status":"ok","method":"adhoc","detail":{"exit_code":0}}]
}
```

### `POST /projects/{project_id}/completion-report` (manager-api:8000)
```json
Request: {
  "summary": "작업 완료 요약",
  "outcome": "success",
  "work_details": ["작업1", "작업2"],
  "issues": [],
  "next_steps": ["다음 권장 사항"]
}
```

### `GET /completion-reports?q={keyword}&limit={n}` (manager-api:8000)
- 완료보고서 전문 검색 (retrieval_service 기반)

---

## 6. 다음 단계

- M15 이후: `similar_playbooks` 벡터 검색 강화 (현재 keyword 매칭만)
- `execute-plan` → Master review 연동 (현재 별도 호출 필요)
- SubAgent 실제 명령 실행 시 evidence 자동 연동
