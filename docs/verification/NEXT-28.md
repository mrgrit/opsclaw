# NEXT-28

## 작업 이름
M2 코드 주입 4차 / report·evidence 조회 경로 및 close 최소 전이 구현

## 목적
M2 3차에서 만든 lifecycle을 한 단계 확장하여, `report` 단계 이후에 evidence 목록 조회와 프로젝트 close 전이를 실제 DB와 HTTP 라우터에 반영한다.

## 이번 단계의 구현 범위
- `packages/project_service/__init__.py`에 evidence 리스트 조회 함수, close 전이 함수, report/evidence/project 요약 함수 추가
- `apps/manager-api/src/main.py`에 `GET /projects/{project_id}/evidence` 와 `POST /projects/{project_id}/close` 엔드포인트 추가
- smoke test 2종 (project service 레벨, manager-api HTTP) 갱신 및 실행
- 관련 문서(`REVIEW-27.md`, `NEXT-28.md`, `opsclaw-m2-completion-report.md`, `WORK-28.md`) 업데이트

## 이번 단계의 성공 기준
- `POST /projects` 성공
- `POST /projects/{id}/plan` 성공
- `POST /projects/{id}/execute` 성공
- `POST /projects/{id}/validate` 성공
- `POST /projects/{id}/report/finalize` 성공
- `POST /projects/{id}/evidence/minimal` 성공
- `GET /projects/{id}/evidence` 성공 (항목 1개 이상 반환)
- `POST /projects/{id}/close` 성공, `current_stage = close`, `status = completed`
- project service smoke exit code 0, evidence count ≥1, close 전이 확인
- manager‑api HTTP smoke exit code 0, evidence count ≥1, close 전이 확인

## WORK-28 작성 규칙
- 실제 브랜치, HEAD 커밋, 작업 시각(UTC) 등을 **실제 값**으로 기록
- 수정 파일 목록에 실제 수정한 파일만 열거
- 실행한 명령을 순서대로 기재
- `pip install`, `compileall`, 각 smoke 테스트 결과를 상세히 기록
- 핵심 관찰점과 미해결 사항(3개 이내) 포함

## 실행 순서 (반드시 1개씩)
1. `git checkout main`
2. `git pull origin main`
3. 필요한 파일 수정
4. `export DATABASE_URL='postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw'`
5. `python3 -m pip install -r requirements.txt`
6. `python3 -m compileall apps packages tools`
7. project service smoke 실행
8. manager‑api HTTP smoke 실행
9. `git status --short`
10. 결과를 `docs/verification/WORK-28.md`에 정리
