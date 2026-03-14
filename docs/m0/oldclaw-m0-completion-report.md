# OldClaw M0 Completion Report

## 이번 작업 요약 (M0 보강)
- **SQL Migration**: `0003_history_and_experience.sql` 와 `0004_scheduler_and_watch.sql` 에 실제 테이블 정의 추가. `0001_init_core.sql` 에 지원 테이블(`messages`, `audit_logs`, `schedules`) 구현.
- **문서 보강**: `docs/m0/` 내 5개 파일을 전면 재작성하여 설계 결정, 서비스 경계, DB 스키마, Registry 규격, 다음 단계(M1) 작업을 명시.
- **Registry Spec & Seed**: Tool 6개, Skill 6개, Playbook 5개에 대한 메타데이터 및 JSON Schema 파일 추가 (see `schemas/registry/` 및 `seed/` directories).
- **API Schema**: `schemas/api/` 아래 13개 계약 파일을 순수 JSON 형태로 새로 작성.
- **Service 엔트리**: 각 앱(`manager-api`, `master-service`, `subagent-runtime`, `scheduler-worker`, `watch-worker`)에 FastAPI/CLI 골격 구현, 라우트·핸들러 스텁 제공.
- **pi_adapter**: 디렉터리 구조 재구성 (`runtime`, `tools`, `sessions`, `model_profiles`, `translators`, `contracts`) 및 기본 인터페이스 정의, 실제 동작 대신 `NotImplementedError` 를 명시.

## 주요 변경 파일 목록 (상위 경로)
- `migrations/0001_init_core.sql`
- `migrations/0003_history_and_experience.sql`
- `migrations/0004_scheduler_and_watch.sql`
- `docs/m0/*.md` (전체 5개)
- `schemas/registry/tools/*.json`, `schemas/registry/skills/*.json`, `schemas/registry/playbooks/*.json`
- `schemas/api/...` (13 파일)
- `seed/tools/*.yaml`, `seed/skills/*.yaml`, `seed/playbooks/*.yaml`
- `apps/manager-api/src/main.py`, `apps/master-service/src/main.py`, `apps/subagent-runtime/src/main.py`, `apps/scheduler-worker/src/main.py`, `apps/watch-worker/src/main.py`
- `packages/pi_adapter/__init__.py` 및 서브 디렉터리 파일들

## 미해결 사항 (3 이하) 
1. **인덱스 최적화**: 일부 테이블에 복합 인덱스가 정의되지 않았음. M1 단계에서 성능 테스트 후 추가 필요.
2. **정책 엔진 구현**: `policy_engine` 패키지는 아직 스텁 상태이며, 실제 정책 평가 로직은 미구현.
3. **pi runtime 연동**: `pi_adapter` 의 실제 모델 프로파일·세션 관리 구현은 추후 진행 예정.

---
*임의 적용*: 일부 패키지 의존 관계와 상세 인덱스 정의는 M1 로 이월되었습니다.*
