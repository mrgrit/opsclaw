# OpsClaw

OpsClaw는 **pi runtime 기반 정보시스템 운영/보안 작업 오케스트레이션 플랫폼**이다.
pi를 단순히 호출하는 보조 도구가 아니라, **pi를 실행 런타임으로 사용하고 OpsClaw가 control‑plane을 담당하는 구조**를 목표로 한다.

프로젝트의 핵심 목적은 자연어 요청을 내부망 운영 작업으로 바로 흘려보내는 것이 아니라,
그 요청을 **프로젝트 단위로 접수하고**, **단계별 상태 전이(plan → execute → validate → report → close)** 로 관리하며,
결과를 **evidence/report 중심으로 기록 가능한 형태**로 남기는 것이다.

---

## 1. 시스템 소개

OpsClaw는 다음 상황을 해결하기 위해 설계되었다.

- 내부망 또는 통제된 환경에서 운영/보안 작업을 구조화해서 수행하고 싶다.
- 자연어 요청을 바로 실행하지 않고, 프로젝트/단계/증빙 단위로 관리하고 싶다.
- 실행 결과를 stdout/stderr 감상이 아니라 evidence/report 로 남기고 싶다.
- 신규 업무를 코어 수정이 아니라 asset / skill / playbook 추가 중심으로 수용하고 싶다.
- 장기적으로 approval, policy, history‑aware retrieval, continuous watch 모드까지 확장하고 싶다.

OpsClaw는 이 목표를 위해 다음 철학을 따른다.

- **pi는 실행 런타임 엔진**
- **OpsClaw는 control‑plane**
- **asset‑first**: 모든 실행은 자산에서 시작
- **evidence‑first**: close 전에 반드시 evidence 존재
- **history‑aware, context‑light**
- **구조 우선**
- **신규 업무는 코어 수정이 아니라 skill / playbook 추가로 수용**

---

## 2. 시스템 컨셉

OpsClaw의 기본 구조는 아래와 같다.

- **Master**: 고수준 판단, 정책, 승인, 향후 경험/지식 축적과 연결될 상위 오케스트레이션 계층
- **Manager**: 프로젝트 lifecycle, 상태 전이, API, registry 접근을 담당하는 중심 control‑plane
- **SubAgent / Runtime**: 실제 환경에서 명령을 수행하는 실행 계층 (A2A HTTP 경로)
- **pi runtime**: 실제 작업 실행을 담당하는 런타임 엔진

---

## 3. 개발 계획 개요

| 마일스톤 | 내용 | 상태 |
|---|---|---|
| M0 | 설계 고정 — repo 구조, 문서/스키마/registry 기본 틀 | ✅ 완료 |
| M1 | pi Runtime Adapter — pi CLI wrapper, Ollama 연동 | ✅ 완료 |
| M2 | Manager Core — PostgreSQL project lifecycle, evidence/report, asset 최소 경로 | ✅ 완료 |
| M3 | A2A 실행 경로 — SubAgent run_script, Bootstrap installer, evidence gate, replan | ✅ 완료 |
| M4 | Asset Registry CRUD — create/get/update/delete/list, onboard, target resolve | ✅ 완료 |
| M5 | Evidence gate 강화, Validation service, Master review workflow | ✅ 완료 |
| M6 | Skill/Playbook Registry CRUD, Seed loader, 10 playbooks, Composition engine, Explain mode | ✅ 완료 |
| Pre-M7 | LangGraph 상태기계, select_assets/resolve_targets 스테이지, Approval Gate, Policy Engine | ✅ 완료 |
| M7 | Batch/Continuous Execution — scheduler, watch runner | ✅ 완료 |
| M8 | History/Experience/Retrieval — 4-layer memory, task_memory, experience promotion, FTS retrieval | ✅ 완료 |
| M9 | RBAC, Audit, Monitoring, Reporting, Backup | ✅ 완료 |

---

## 4. 현재 구현 상태 (M9 기준)

### 구현 완료

**Project Lifecycle**
- PostgreSQL 기반 project create/get
- plan → execute → validate → report → close 상태 전이
- replan: execute/validate/report → plan 전이 (이유 기록)
- evidence gate: close 전 evidence 필수

**Evidence & Validation**
- minimal evidence 생성 (command / stdout / stderr / exit_code)
- project evidence 조회 및 요약 (total / success_count / failure_count / success_rate)
- validation check: 명령 실행 → expected_contains / expected_exit_code 검증 → evidence + validation_run 기록
- validation status: all_passed / has_failures / inconclusive / no_runs

**Asset Registry**
- asset CRUD (create / get / update / delete / list)
- asset 온보딩 워크플로우 (identity check → create → bootstrap → target resolve)
- target 자동 도출 (subagent ping → targets 테이블 upsert)
- bootstrap: SSH → `install.sh` → systemd 서비스 등록

**A2A Execution**
- Manager → SubAgent HTTP dispatch (`POST /a2a/run_script`)
- SubAgent: subprocess 실제 실행, timeout 처리
- `A2AClient`: run_script() wraps HTTP call

**Master Review**
- approve / reject / needs_replan 기록
- auto_replan 옵션
- escalate (rejected review 기록)

**LangGraph 상태기계**
- `build_project_graph()` — StateGraph 컴파일
- `run_project_graph()` — 자율 실행 (plan → select_assets → resolve_targets → approval_gate → execute → validate → report → close)
- select_assets / resolve_targets 정식 스테이지 추가 (bypass 경로로 기존 호환성 유지)

**Approval Gate**
- `check_requires_approval()` — risk_level high/critical은 approved master_review 필요
- `require_approval_cleared()` — execute 전 자동 검증
- `GET /projects/{id}/approval` — 승인 상태 조회

**Policy Engine**
- env별 정책 테이블 (prod / staging / lab / default)
- `check_policy()`, `enforce_policy()` — 정책 위반 시 PolicyViolation

**Registry (Tool / Skill / Playbook)**
- Tool CRUD with upsert (ON CONFLICT DO UPDATE)
- Skill CRUD with required_tools / optional_tools
- Playbook CRUD with steps, execution_mode, risk_level, dry_run_supported
- Seed loader: YAML → DB upsert (6 tools, 6 skills, 10 playbooks)
- Composition engine: playbook → step → skill → tool 전체 트리 resolve
- Explain mode: 마크다운 사람 가독 설명

**Batch/Continuous Execution (M7)**
- schedule CRUD + croniter cron next-run 계산
- get_due_schedules / execute_due_schedule 배치 사이클
- watch_job / watch_event / incident CRUD
- run_watch_check: subprocess 실행 → 연속 실패 threshold → incident 자동 생성
- Scheduler Worker + Watch Worker 폴링 루프
- `/schedules`, `/watchers`, `/incidents` API 라우터

**History/Experience/Retrieval (M8)**
- history_service: ingest_event / ingest_stage_event / get_project_history / get_asset_history
- experience_service: build_task_memory / promote_to_experience / create_experience / list_experiences
- retrieval_service: index_document / search_documents (FTS + ILIKE fallback) / reindex_project / get_context_for_project
- Manager API: `/projects/{id}/history`, `/experience`, `/projects/{id}/context`

**RBAC / Audit / Monitoring / Reporting / Backup (M9)**
- RBAC: roles + actor_roles 테이블, 4개 기본 역할 (admin/operator/viewer/auditor)
- rbac_service: create_role / assign_role / get_actor_permissions / check_permission (`*` wildcard 지원)
- audit_service: log_audit_event / query_audit_logs / export_audit_json / export_audit_csv
- monitoring_service: get_system_health (healthy/degraded) / get_operational_metrics
- reporting_service: generate_project_report / export_evidence_pack / export_evidence_pack_json
- backup_service: create_backup (pg_dump) / list_backups / get_backup_info
- Manager API: `/admin/*` (12개 엔드포인트), `/reports/*` (3개 엔드포인트)

### 아직 남아 있는 것

- CI 파이프라인 확대
- playbook 기반 실제 명령 실행 자동화 (pi runtime 연동)

---

## 5. 저장소 구조 개요

```
apps/
  manager-api/src/main.py   # FastAPI Manager control-plane API
  master-service/src/main.py # Master review/replan/escalate API
  subagent-runtime/src/main.py # SubAgent A2A 실행 런타임

packages/
  project_service/           # project lifecycle, evidence, dispatch
  asset_registry/            # asset CRUD, target resolve, onboard
  evidence_service/          # evidence 조회/요약/gate
  validation_service/        # validation check, run, status
  master_review/             # review CRUD
  registry_service/          # tool/skill/playbook CRUD, composition, explain
  graph_runtime/             # 상태 전이, replan 허용 범위
  a2a_protocol/              # A2AClient, A2ARunRequest/Result
  bootstrap_service/         # SSH bootstrap
  pi_adapter/                # pi runtime 연동 계층

migrations/                  # PostgreSQL 스키마 (4개 마이그레이션)
seed/playbooks/              # 10개 playbook YAML 정의
tools/dev/                   # 개발용 smoke / seed 스크립트
deploy/bootstrap/            # install.sh (원격 SubAgent 설치)
docs/                        # 마일스톤별 계획/완료 보고서
```

---

## 6. 실행 및 검증

### 전체 컴파일 확인

```bash
python3 -m compileall apps packages tools
```

### M6 통합 smoke

```bash
PYTHONPATH=. python3 tools/dev/m6_integrated_smoke.py
```

### M5 통합 smoke (evidence gate, validation, master review)

```bash
PYTHONPATH=. python3 tools/dev/m5_integrated_smoke.py
```

### Seed loader

```bash
PYTHONPATH=. python3 tools/dev/seed_loader.py           # 실제 적재
PYTHONPATH=. python3 tools/dev/seed_loader.py --dry-run # 확인만
```

---

## 7. 작업 운영 규칙

이 저장소의 작업은 아래 규칙을 따른다.

- main 브랜치만 사용
- 코어 설계와 코드 본문은 사람이 정의
- 에이전트는 반영 / 실행 / 테스트 / 결과 보고 담당
- 검수 없는 완료 주장 금지
- 검수/지시/작업결과는 문서로 남김

문서 체계:

- `docs/mX/opsclaw-mX-completion-report.md` — 마일스톤 완료 보고서
- `docs/verification/WORK-XX.md` — 개별 작업 상세 기록

---

## 8. 주의

README는 현재 구현 상태를 반영하는 대표 문서다.
없는 기능을 완성된 것처럼 적지 않는다.
M7(Batch/Continuous Execution) 이후는 **계획 범위**이지 현재 완료 기능이 아니다.
