# OpsClaw M5 Completion Report

## 1. M5 목표

- Evidence gate 강화: close 전 evidence 필수, 내용 추출 지원
- Validation service: 명령 실행 → 기대값 검증 → evidence/validation_run 기록
- Master review workflow: approve / reject / needs_replan
- Master service API: review, replan, escalate, status 엔드포인트 실제 구현

---

## 2. 실제 반영한 것

### packages/evidence_service/__init__.py (신규)

- `get_evidence_content()`: `inline://stdout/{id}:{content}` 형식에서 내용 추출
- `get_evidence_summary()`: total / success_count / failure_count / success_rate 통계
- `require_evidence_for_close()`: evidence 0건이면 `EvidenceRequiredError` 발생
- `EvidenceRequiredError` — `close_project()`에서 catch → `ProjectStageError`로 변환

### packages/validation_service/__init__.py (신규)

- `run_validation_check()`: 명령 로컬 실행 또는 A2A 전송 → `expected_contains` / `expected_exit_code` 검증 → evidence + `validation_runs` 레코드 생성
- `create_validation_run()`, `get_validation_runs()`, `get_validation_status()`
- validation_status: `"all_passed"` / `"has_failures"` / `"inconclusive"` / `"no_runs"`

### packages/master_review/__init__.py (신규)

- `create_master_review()`: `master_reviews` 테이블에 reviewer / status / comment 기록
- `get_latest_master_review()`, `get_all_master_reviews()`
- 상태 값: `approved` / `rejected` / `needs_replan`

### packages/graph_runtime/__init__.py (수정)

- `REPLAN_FROM_STAGES = {"execute", "validate", "report"}` 정의
- `require_replan_allowed()`: 해당 단계 외에서 replan 시도 시 `GraphRuntimeError`

### apps/master-service/src/main.py (전면 재작성)

501 stub → 실제 구현:

| 메서드 | 경로 | 기능 |
|---|---|---|
| POST | /projects/{id}/review | review 기록, `auto_replan=true` 시 자동 replan |
| GET | /projects/{id}/review | 최신 review 조회 |
| GET | /projects/{id}/reviews | 전체 review 목록 |
| POST | /projects/{id}/replan | 강제 plan 전이 |
| POST | /projects/{id}/escalate | rejected review 기록 |
| GET | /projects/{id}/status | project 상태 + 최신 review 요약 |

### Manager API (수정)

- `POST /projects/{id}/validate/check`: validation_service 연동
- `GET /projects/{id}/validations`: validation 목록 + 상태
- `GET /projects/{id}/evidence/summary`: evidence 통계
- `POST /projects/{id}/replan`: replan 엔드포인트

---

## 3. 테스트 결과

| 스크립트 | 결과 |
|---|---|
| `tools/dev/m5_integrated_smoke.py` | 11/11 통과 |

검증 범위: project lifecycle → evidence 생성 → validation check → evidence summary → evidence gate (close 블로킹) → close 성공 → master review → replan → re-close

---

## 4. 한계 및 다음 단계로 넘기는 것

- validation_service의 A2A 경로는 subagent_url이 실제로 접근 가능할 때만 동작
- master_review는 human approval 흉내; 실제 승인 UI/알림은 미구현
- escalation은 rejected review 기록에 그침; 실제 에스컬레이션 채널 연동 없음
