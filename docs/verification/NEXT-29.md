# NEXT-29

## 작업 이름
M2 코드 주입 5차 / asset 목록·project 연결·project asset 조회 최소 경로 구현

## 목적
M2 4차에서 구현한 report/evidence/close 흐름에 이어 asset-first 최소 경로를 열어 프로젝트와 자산을 연결하고 조회한다.

## 수정 파일 목록
- packages/project_service/__init__.py
- apps/manager-api/src/main.py
- tools/dev/project_asset_smoke.py
- tools/dev/manager_projects_asset_http_smoke.py
- docs/verification/REVIEW-28.md
- docs/verification/NEXT-29.md
- docs/m2/oldclaw-m2-completion-report.md
- docs/verification/WORK-29.md

## 구현 요구사항
- `packages/project_service`에 asset 목록 조회, project‑asset 연결, project‑asset 조회 함수 추가
- `apps/manager-api/src/main.py`에 `GET /assets`, `POST /projects/{project_id}/assets/{asset_id}`, `GET /projects/{project_id}/assets` 엔드포인트 추가
- smoke test 2종(`project_asset_smoke.py`, `manager_projects_asset_http_smoke.py`) 작성 및 검증

## 테스트 요구사항
- `tools/dev/project_asset_smoke.py`가 asset 목록, 프로젝트 생성, asset 연결, 연결 조회, summary 확인을 수행하고 stdout에 지정된 항목을 출력
- `tools/dev/manager_projects_asset_http_smoke.py`가 HTTP 레벨에서 동일 흐름을 검증하고 stdout에 지정된 항목을 출력

## WORK-29 작성 규칙
- 현재 브랜치, HEAD 커밋, 작업 시각(UTC) 등을 실제 값으로 기록
- 수정 파일 목록, 실행 명령, pip install·compileall·각 smoke 테스트 결과를 상세히 기록
- 핵심 관찰점과 미해결 사항(3개 이내) 포함

## 실행 순서 (반드시 1개씩)
1. `git checkout main`
2. `git pull origin main`
3. 필요한 파일 수정
4. `export DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw'`
5. `python3 -m pip install -r requirements.txt`
6. `python3 -m compileall apps packages tools`
7. project asset smoke 실행
8. manager‑api asset HTTP smoke 실행
9. `git status --short`
10. 결과를 `docs/verification/WORK-29.md`에 정리
