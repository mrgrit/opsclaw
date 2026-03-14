# M0 Completion Report (v0.3)

## 직접 주입된 파일 목록
- docs/m0/oldclaw-m0-design-baseline.md
- docs/m0/oldclaw-m0-registry-spec.md
- apps/manager-api/src/main.py
- apps/subagent-runtime/src/main.py
- packages/pi_adapter/runtime/client.py
- migrations/0001_init_core.sql
- **문서**: `design-baseline`, `repo-and-service-structure`, `db-schema`, `registry-spec` 를 **전략·설계·경계** 수준의 기준 문서로 확장하고, 각 항목에 설계 이유와 예시를 포함했습니다.
- **서비스 스켈레톤**: `manager-api`, `master-service`, `subagent-runtime`, `scheduler-worker`, `watch-worker` 에서 모든 TODO/placeholder 를 **명시적 501 / NotImplementedError** 로 교체하고, 라우터·핸들러·함수 구조를 드러냈습니다.
- **pi_adapter**: `runtime/`, `tools/`, `sessions/`, `model_profiles/`, `translators/`, `contracts/` 로 디렉터리 분리하고, 각각 최소 인터페이스와 예외 기반 경계를 구현했습니다.
- **마이그레이션**: `0001_init_core.sql`, `0002_registry.sql`, `0003_history_and_experience.sql`, `0004_scheduler_and_watch.sql` 를 **가독성 높은 블록‑단위 SQL** 로 재작성했으며, PK/FK/UNIQUE/CHECK/INDEX 를 모두 명시했습니다.
- **History/Experience 모델**: 4‑계층 기억 구조(`histories` → `task_memories` → `experiences` → `retrieval_documents`) 를 DB 스키마와 문서에 정확히 반영했습니다.
- **Registry / API 계약**: Tool/Skill/Playbook 스키마와 seed 데이터를 실제 의미 있게 재작성하고, 중복을 제거했습니다.
- **README**: 현재 단계가 “M0 설계 고정 + Skeleton 정식화”임을 명시하고, 리포지터리 구조와 다음 단계(M1) 예고를 추가했습니다.

## 아직 남은 작업 (M0 마감 전)
1. **인덱스 최적화** – 복합 인덱스와 파티셔닝 전략은 실제 워크로드 테스트 후 조정 예정.
2. **정책 엔진 스텁** – `policy_engine` 패키지는 아직 비 구현 상태이며, 정책 파싱·평가 로직은 M1 로 이관됩니다.
3. **pi runtime 연동** – `packages/pi_adapter/runtime/client.py` 의 `PiRuntime` 은 현재 `NotImplementedError` 로 남아 있으며, 실제 SDK 연동은 M1 작업입니다.

## 왜 M1 로 넘기는가
- **비즈니스 로직** 수준(정책 평가, 고도화된 검증·리포팅, 모델 교체 등)은 현재 골격을 넘어서는 구현이 필요합니다.
- **외부 의존성**인 pi SDK 연동은 별도 검증 및 CI 파이프라인이 필요하기에 M1 로 분리합니다.

## 임의 적용
- 일부 디렉터리 구조와 인덱스 정의는 **M1 단계**에서 조정될 수 있음을 명시 (위 1번 항목).

---
*본 보고서는 현재 브랜치(`m0-enhancement`) 기준이며, 다음 검수에서 M0 종료 여부를 판단한다.*
