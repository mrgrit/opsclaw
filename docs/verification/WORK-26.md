# WORK-26

## 1. 작업 정보
- 작업 이름: M2 코드 주입 2차 / graph_runtime 최소 상태 전이 및 plan·validate 경로 구현
- 현재 브랜치: main
- 현재 HEAD 커밋: 1134bed8ba139ef9f0afc04c71b9917a54ecf412
- 작업 시각: 2026-03-15T04:09:13Z

## 2. 이번 작업에서 수정한 파일
- docs/verification/REVIEW-25.md
- docs/verification/NEXT-26.md
- packages/project_service/__init__.py
- packages/graph_runtime/__init__.py
- apps/manager-api/src/main.py
- docs/m2/opsclaw-m2-completion-report.md
- tools/dev/graph_runtime_smoke.py
- tools/dev/manager_projects_lifecycle_http_smoke.py
- docs/verification/WORK-26.md

## 3. 실행한 명령 목록
```
1. git checkout main
2. git pull origin main
3. mkdir -p docs/verification
4. mkdir -p docs/m2
5. mkdir -p tools/dev
6. export DATABASE_URL='postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw'
7. python3 -m pip install -r requirements.txt
8. python3 -m compileall apps packages tools
9. PYTHONPATH=. python3 tools/dev/project_service_smoke.py
10. PYTHONPATH=. python3 tools/dev/graph_runtime_smoke.py
11. PYTHONPATH=. python3 tools/dev/manager_projects_lifecycle_http_smoke.py
12. git status --short
```

## 4. pip install 결과
- stdout:
```
Defaulting to user installation because normal site-packages is not writeable
Requirement already satisfied: fastapi==0.116.1 ...
Collecting psycopg2-binary==2.9.10
Downloading psycopg2_binary-2.9.10-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.0 MB)
Collecting httpx==0.28.1
Downloading httpx-0.28.1-py3-none-any.whl (73 kB)
Downloading httpcore-1.0.9-py3-none-any.whl (78 kB)
Successfully installed httpcore-1.0.9 httpx-0.28.1 psycopg2-binary-2.9.10
```
- stderr: *(none)*
- exit code: 0

## 5. compileall 결과
- stdout:
```
Listing 'apps'...
Listing 'apps/manager-api'...
Listing 'apps/manager-api/src'...
... (other modules compiled) ...
```
- stderr: *(none)*
- exit code: 0

## 6. project_service smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/project_service_smoke.py`
- stdout:
```
PROJECT_ID: prj_e0c182514a7e
PROJECT_STATUS: created
PLAN_STAGE: plan
EXECUTE_STAGE: execute
VALIDATE_STAGE: validate
REPORT_ID: rpt_83c0cf6ad33e
```
- stderr: *(none)*
- exit code: 0

## 7. graph_runtime smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/graph_runtime_smoke.py`
- stdout:
```
STAGES: intake,plan,execute,validate,report,close
NEXT_INTAKE: plan
NEXT_PLAN: execute
NEXT_EXECUTE: validate
NEXT_VALIDATE: report
```
- stderr: *(none)*
- exit code: 0

## 8. manager_projects_lifecycle_http_smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/manager_projects_lifecycle_http_smoke.py`
- stdout:
```
HTTP_PROJECT_ID: prj_faf3c2fe5c0b
HTTP_PLAN_STAGE: plan
HTTP_EXECUTE_STAGE: execute
HTTP_VALIDATE_STAGE: validate
HTTP_REPORT_ID: rpt_24b21607129e
```
- stderr: *(none)*
- exit code: 0

## 9. 핵심 관찰점
- `/projects/{id}/plan` 성공 여부: 성공
- `/projects/{id}/execute` 성공 여부: 성공
- `/projects/{id}/validate` 성공 여부: 성공
- `/projects/{id}/report` 성공 여부: 성공
- 상태 전이가 실제 DB와 HTTP 경로에서 반영됐는지 여부: 확인 (DB rows show correct stages and reports)
- 아직 남은 한계 (5개 이내):
  1. Asset, playbook, evidence 라우터는 아직 stub 상태
  2. 전체 graph runtime 및 오케스트레이션 로직 부재
  3. Approval / policy 엔진 연동 미구현
  4. 테스트 커버리지 및 CI 파이프라인 통합 필요
  5. report stage 전이를 위한 별도 endpoint 아직 없음

## 10. 미해결 사항
1. `graph_runtime`에 full orchestration graph 구현 필요
2. `manager-api`에 asset, playbook, evidence 라우터 구현 예정
3. CI 파이프라인에 전체 lifecycle 자동 테스트 추가 필요
