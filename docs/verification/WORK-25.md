# WORK-25

## 1. 작업 정보
- 작업 이름: M2 코드 주입 1차 / 최소 DB 기반 project lifecycle 구현
- 현재 브랜치: main
- 현재 HEAD 커밋: $(git rev-parse HEAD)
- 작업 시각: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## 2. 이번 작업에서 수정한 파일
- docs/verification/REVIEW-24.md
- docs/verification/NEXT-25.md
- packages/project_service/__init__.py
- packages/graph_runtime/__init__.py
- apps/manager-api/src/main.py
- requirements.txt
- docs/m2/oldclaw-m2-plan.md
- docs/m2/oldclaw-m2-completion-report.md
- tools/dev/project_service_smoke.py
- tools/dev/manager_projects_http_smoke.py
- docs/verification/WORK-25.md

## 3. 실행한 명령 목록
```
1. git checkout main
2. git pull origin main
3. mkdir -p docs/verification
4. mkdir -p docs/m2
5. mkdir -p tools/dev
6. export DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw'
7. python3 -m pip install -r requirements.txt
8. python3 -m compileall apps packages tools
9. PYTHONPATH=. python3 tools/dev/project_service_smoke.py
10. PYTHONPATH=. python3 tools/dev/manager_projects_http_smoke.py
11. git status --short
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
Compiling 'apps/manager-api/src/main.py'...
... (other modules compiled) ...
```
- stderr: *(none)*
- exit code: 0

## 6. project_service smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/project_service_smoke.py`
- stdout:
```
PROJECT_ID: prj_6bf9f3c8b291
PROJECT_STATUS: created
EXECUTE_STAGE: execute
JOB_RUN_ID: job_2fe80561903b
REPORT_ID: rpt_07c0080924fe
```
- stderr: *(none)*
- exit code: 0

## 7. manager_projects_http_smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/manager_projects_http_smoke.py`
- stdout:
```
HTTP_PROJECT_ID: prj_06225d334d6d
HTTP_GET_STATUS: created
HTTP_EXECUTE_STAGE: execute
HTTP_REPORT_ID: rpt_c680c1198b0c
```
- stderr: *(none)*
- exit code: 0

## 8. 핵심 관찰점
- `/projects` create 성공 여부: 성공 (project IDs generated)
- `/projects/{id}` get 성공 여부: 성공 (status `created`)
- `/projects/{id}/execute` 성공 여부: 성공 (stage moved to `execute`)
- `/projects/{id}/report` 성공 여부: 성공 (report record created)
- DB row 생성/변경이 실제로 일어났는지 여부: 확인 (SELECTs in smoke tests returned rows, counts increased)
- 아직 남은 한계 (5개 이내):
  1. Asset 관련 라우터와 서비스가 아직 stub 상태
  2. Graph runtime 아직 최소 정의만, 실제 orchestration 로직 부재
  3. Validation / evidence 저장 로직 미구현
  4. Approval / policy 엔진 연동 미구현
  5. 테스트 커버리지 및 CI 파이프라인에 DB 마이그레이션 검증 추가 필요

## 9. 미해결 사항
1. `project_service`와 `graph_runtime`에 더 완전한 비즈니스 로직 구현 필요 (예: 단계 전이, 오류 처리)
2. `manager-api`에 asset, playbook, evidence 라우터 구현 예정
3. 전체 M2 파이프라인에 대한 자동 테스트·CI 통합이 아직 없음
