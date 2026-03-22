# OpsClaw M15 완료보고서: Platform Modes

**날짜:** 2026-03-22
**마일스톤:** M15 — Platform Modes
**상태:** ✅ 완료

---

## 개요

OpsClaw에 두 가지 오케스트레이션 모드(Mode A: Native, Mode B: External)를 도입했다.
외부 AI(Claude Code 등)가 Manager API를 직접 호출하여 작업을 완료하는 Mode B 경로를 완전히 구현하고 검증했다.

---

## 완료 항목

### WORK-68: `master_mode` DB 컬럼 및 API 추가

- `migrations/0008_master_mode.sql`: `projects.master_mode` 컬럼 추가 (`native|external`, DEFAULT `native`)
- `packages/project_service/__init__.py`: `create_project_record()` 에 `master_mode` 파라미터 추가
- `apps/manager-api/src/main.py`: `ProjectCreateRequest` 에 `master_mode` 필드 추가, DB 저장 연동

### WORK-69: External Master 가이드 문서

- `docs/api/external-master-guide.md`: 외부 AI용 API 흐름 가이드 (Mode B 전용)
  - 7단계 순서: 프로젝트 생성 → Playbook → Stage 전환 → 실행 → Evidence → 완료보고서 → 종료
  - 등록된 Tool/Skill 목록 및 params 명세
  - 시나리오 예시 3개 (서버 온보딩, 패키지 설치, 보안 점검)

### WORK-70: CLAUDE.md 작성

- `CLAUDE.md`: Claude Code 오케스트레이션 가이드
  - 서비스 주소, 핵심 워크플로우 bash 예시, Tool/Skill 목록, 운영 규칙

### WORK-71: Mode B 통합 테스트

- `scripts/m15_mode_b_test.py`: 9구간 16항목 통합 테스트
- **결과: 16/16 PASS**

---

## 테스트 결과

```
[1] 프로젝트 생성 (master_mode=external)   ✅✅
[2] Playbook + Steps 3개 등록               ✅✅
[3] Playbook → Project 연결                 ✅
[4] Stage 전환: intake → plan → execute     ✅✅
[5] dry_run 검증                            ✅✅
[6] 실제 실행 (3/3 steps ok, 0.6s)          ✅✅✅✅
[7] Evidence 3건 기록 확인                  ✅
[8] Completion Report 생성                  ✅
[9] master_mode=external DB 저장 확인       ✅

결과: 16/16 통과, 0건 실패 ✅ PASS
```

---

## 아키텍처 정리

| 모드 | `master_mode` | 오케스트레이터 | 진입점 |
|------|--------------|--------------|--------|
| Mode A: Native | `native` | master-service (내장 LLM) | Web UI / master-service:8001 |
| Mode B: External | `external` | 외부 AI (Claude Code 등) | manager-api:8000 직접 호출 |
