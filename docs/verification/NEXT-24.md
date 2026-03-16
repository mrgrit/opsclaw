# NEXT-24

## 작업 이름
M2 코드 주입 준비 / project_service · graph_runtime · manager-api 현행 본문 고정

## 목적
다음 단계에서 M2 1차 코드를 직접 주입하기 전에,
아래 핵심 파일들의 현재 본문과 디렉터리 상태를 검수 채널에 고정 저장한다.

## 다음 단계에서 교체 또는 신규 작성 예정인 핵심 파일
- apps/manager-api/src/main.py
- packages/project_service/__init__.py
- packages/graph_runtime/__init__.py
- requirements.txt
- docs/m2/opsclaw-m2-plan.md
- docs/m2/opsclaw-m2-completion-report.md
- tools/dev/project_service_smoke.py
- tools/dev/manager_projects_http_smoke.py

## 다음 단계의 구현 목표
- DB 연결 설정 추가
- 최소 project service 구현
- manager-api `/projects` 라우터의 DB 저장/조회 경로 구현
- 최소 execute stage update 구현
- 최소 report 조회 경로 구현
- smoke test 2종 추가
- 실제 HTTP 검증 수행

## 이번 단계에서 해야 할 일
- 위 파일들의 현재 본문을 WORK-24에 저장
- 관련 디렉터리 트리를 저장
- 현재 requirements.txt 내용 저장
- 현재 manager-api 본문 저장
- project_service, graph_runtime 패키지 상태 저장
