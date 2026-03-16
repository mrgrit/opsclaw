# NEXT-25

## 작업 이름
M2 코드 주입 1차 / 최소 DB 기반 project lifecycle 구현

## 목적
M2의 첫 단계로, PostgreSQL이 준비된 현재 환경에서 최소한의 project lifecycle 경로를 실제 동작시키는 코드를 주입한다.

## 이번 단계의 구현 범위
- `packages/project_service` 구현
- `packages/graph_runtime` 최소 상태 정의
- `apps/manager-api/src/main.py`의 `/projects` 라우터 구현
- `docs/m2/opsclaw-m2-plan.md` 작성
- `docs/m2/opsclaw-m2-completion-report.md` 작성
- `tools/dev/project_service_smoke.py` 작성
- `tools/dev/manager_projects_http_smoke.py` 작성

## 이번 단계의 성공 기준
- POST `/projects` 로 project 생성 성공
- GET `/projects/{id}` 로 조회 성공
- POST `/projects/{id}/execute` 로 상태/단계 업데이트 및 job_run 생성 성공
- GET `/projects/{id}/report` 로 최소 보고서 조회 성공
- smoke test 2종 성공
