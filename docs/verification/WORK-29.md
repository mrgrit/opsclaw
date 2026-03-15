# WORK-29

## 1. 작업 정보
- 작업 이름: M2 코드 주입 5차 / asset 목록·project 연결·project asset 조회 최소 경로 구현
- 현재 브랜치: main
- 현재 HEAD 커밋: fb39f79b7768dc548f794a00ee770164c5f02eb0
- 작업 시각: 2026-03-15T07:20:36Z

## 2. 이번 작업에서 수정한 파일
- packages/project_service/__init__.py
- apps/manager-api/src/main.py
- tools/dev/project_asset_smoke.py
- tools/dev/manager_projects_asset_http_smoke.py
- docs/verification/REVIEW-28.md
- docs/verification/NEXT-29.md
- docs/m2/oldclaw-m2-completion-report.md
- docs/verification/WORK-29.md

## 3. 실행한 명령 목록
- git checkout main
- git pull origin main
- export DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw'
- python3 -m pip install -r requirements.txt
- python3 -m compileall apps packages tools
- PYTHONPATH=. python3 tools/dev/project_asset_smoke.py
- PYTHONPATH=. python3 tools/dev/manager_projects_asset_http_smoke.py
- git status --short

## 4. pip install 결과
- stdout: (omitted for brevity, all packages already satisfied)
- stderr: *(none)*
- exit code: 0

## 5. compileall 결과
- stdout: (listing of compiled modules, compilation succeeded without errors)
- stderr: *(none)*
- exit code: 0

## 6. project_asset_smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/project_asset_smoke.py`
- stdout:
```
ASSET_COUNT: 1
PROJECT_ID: prj_25a2b9311d3e
LINKED_ASSET_ID: ast_dummy
PROJECT_ASSET_COUNT: 1
SUMMARY_ASSET_COUNT: 1
```
- stderr: *(none)*
- exit code: 0

## 7. manager_projects_asset_http_smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/manager_projects_asset_http_smoke.py`
- stdout:
```
HTTP_ASSET_COUNT: 1
HTTP_PROJECT_ID: prj_9d52d8e88320
HTTP_LINKED_ASSET_ID: ast_dummy
HTTP_PROJECT_ASSET_COUNT: 1
```
- stderr: *(none)*
- exit code: 0

## 8. 핵심 관찰점
- `/assets` 조회 성공, 1건 반환 (dummy asset 자동 삽입)
- `POST /projects/{id}/assets/{asset_id}` 로 프로젝트와 asset 연결 성공
- `/projects/{id}/assets` 조회 성공, 연결된 asset 1건 반환
- project summary (`get_project_report_evidence_summary`) 에 asset 목록 포함 확인
- 기존 lifecycle (plan/execute/validate/report/close)와 asset 연동 정상 동작

## 9. 미해결 사항
- graph_runtime 전체 오케스트레이션 로직 구현 필요
- asset/playbook 라우터 세부 구현 및 정책/승인 연동 계획 수립
- CI/CD 파이프라인에 전체 lifecycle 및 asset 테스트 자동화 통합
