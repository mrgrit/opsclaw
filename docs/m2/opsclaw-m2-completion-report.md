# OpsClaw M2 Completion Report

## 1. 이번 단계에서 실제 반영한 것

- `packages/project_service/__init__.py`
  - PostgreSQL 기반 project create/get/plan/execute/validate/report finalize/evidence 최소 로직 구현
  - **evidence 리스트 조회 함수**, **close 전이 함수**, **report/evidence/project 요약 함수** 추가
  - **asset 리스트 조회 함수**, **project‑asset 연결 함수**, **project‑asset 조회 함수** 추가
- `packages/graph_runtime/__init__.py`
  - 최소 stage / transition / transition validation 정의
- `apps/manager-api/src/main.py`
  - `/projects` 라우터에 `plan`, `validate`, `report/finalize`, `evidence/minimal` 경로 추가
  - **`GET /projects/{project_id}/evidence`**, **`POST /projects/{project_id}/close`**, **`GET /assets`**, **`POST /projects/{project_id}/assets/{asset_id}`**, **`GET /projects/{project_id}/assets`** 경로 추가
- `requirements.txt`
  - `psycopg2-binary`, `httpx` 포함
- `docs/m2/opsclaw-m2-plan.md`
  - M2 1차 계획문서 작성
- `tools/dev/project_service_smoke.py`
  - project 서비스 직접 smoke test 추가
- `tools/dev/manager_projects_http_smoke.py`
  - manager API HTTP smoke test 추가
- `tools/dev/graph_runtime_smoke.py`
  - graph runtime smoke test 추가
- `tools/dev/manager_projects_lifecycle_http_smoke.py`
  - lifecycle HTTP smoke test 추가
- `tools/dev/project_report_evidence_smoke.py`
  - report/evidence 최소 경로 및 close 전이 검증 추가
- `tools/dev/manager_projects_report_http_smoke.py`
  - report/evidence 조회 및 close 전이 검증 추가
- `tools/dev/m2_integrated_smoke.py`
  - M2 전체 경로(assets, lifecycle, evidence, asset 연결, close) 한 번에 검증하는 통합 smoke 추가
- `README.md`
  - 현재 M2 구현 상태를 반영하도록 전면 갱신

## 2. 이번 단계에서 고정된 사실

- M2 4차는 전체 orchestration graph 완성이 아니라 `report → evidence 조회 → close` 흐름을 구현한다.
- manager API `/projects` 라우터는 create/get/plan/execute/validate/report/finalize/evidence/minimal/evidence 조회/close 경로를 제공한다.
- 추가로 **자산 최소 경로**가 구현되어 `/assets` 조회, 프로젝트와 자산 연결, 연결된 자산 조회가 가능하다.
- 통합 검증 스크립트 `tools/dev/m2_integrated_smoke.py` 가 전체 M2 흐름을 한 번에 검증한다.

## 3. 한계

- full LangGraph runtime은 아직 없다.
- approval / policy 엔진 연동은 아직 없다.
- asset selection / target resolve / playbook routing은 아직 stub 상태다.
- evidence는 minimal row insert 수준이며 검증/패키징은 아직 없다.

## 4. 다음 단계로 넘기는 것

- approval gate 골격
- validation hook 확장
- evidence/history/service 연계 강화
- graph runtime 확장
- CI 파이프라인 확대
