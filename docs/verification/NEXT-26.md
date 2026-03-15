# NEXT-26

## 작업 이름
M2 코드 주입 2차 / graph_runtime 최소 상태 전이 및 plan·validate 경로 구현

## 목적
M2 1차에서 만든 최소 DB-backed lifecycle을 한 단계 확장하여,
`plan -> execute -> validate -> report` 흐름의 최소 상태 전이 경로를 실제 DB와 HTTP 라우터에 반영한다.

## 이번 단계의 구현 범위
- `packages/graph_runtime` 최소 상태 전이 함수 구현
- `packages/project_service`의 plan/validate/report 보강
- `apps/manager-api/src/main.py`에 `/projects/{id}/plan`, `/projects/{id}/validate` 추가
- graph runtime smoke test 추가
- lifecycle HTTP smoke test 추가
- M2 completion report 갱신

## 이번 단계의 성공 기준
- POST `/projects` 성공
- POST `/projects/{id}/plan` 성공
- POST `/projects/{id}/execute` 성공
- POST `/projects/{id}/validate` 성공
- GET `/projects/{id}/report` 성공
- graph runtime smoke 성공
- lifecycle HTTP smoke 성공
