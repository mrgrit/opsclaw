# NEXT-30

## 작업 이름
M2 문서 정리 및 대표 README 갱신 + 통합 smoke 고정

## 수정 파일 목록
- README.md
- tools/dev/m2_integrated_smoke.py
- docs/verification/REVIEW-29.md
- docs/verification/NEXT-30.md
- docs/m2/oldclaw-m2-completion-report.md
- docs/verification/WORK-30.md

## README 갱신 요구사항
- 앞부분을 시스템 소개 / 시스템 컨셉 / 개발 계획 개요 / 현재 구현 상태 (M2 기준) 로 재구성 (앞서 제공된 내용 그대로 적용).
- 과장 없이 현재 구현된 기능만 기술하고, 아직 구현되지 않은 항목은 계획 범위로 표기.

## 통합 smoke 요구사항
- `tools/dev/m2_integrated_smoke.py` 파일을 추가하여 전체 M2 경로(assets, lifecycle, evidence, asset 연결, close) 를 한 번에 검증.
- 스크립트는 위에서 정의한 출력 형식과 성공 기준을 만족해야 함.

## M2 완료보고서 정합화 요구사항
- `docs/m2/oldclaw-m2-completion-report.md` 를 현재 구현 범위와 대표 API/검증 항목에 맞게 업데이트.
- README와 내용이 일관되게 유지되도록 섹션을 맞춤.

## WORK-30 작성 규칙
- 실제 브랜치, HEAD 커밋 해시, 작업 시각(UTC) 등을 **실제 값**으로 기록.
- 수정 파일 목록, 실행 명령, pip install·compileall·통합 smoke 결과, 핵심 관찰점, 미해결 사항(3개 이내) 포함.
- 셸 치환 문자열을 그대로 쓰지 말고 실제 값으로 대체.

## 실제 값 기록 강제
- 모든 문서에 커밋 해시와 UTC 시각을 실제 값으로 삽입.

## main 브랜치 고정
- 모든 작업은 `main` 브랜치에서 수행하고, 커밋·푸시 후 `main`에 머지.

## 명령 1개씩 실행 규칙
- `git checkout main`, `git pull origin main`, `export DATABASE_URL=…`, `python3 -m pip install -r requirements.txt`, `python3 -m compileall apps packages tools`, `PYTHONPATH=. python3 tools/dev/m2_integrated_smoke.py`, `git status --short` 순서대로 각각 별도 명령 실행.
