# OldClaw M0 Repository & Service Structure

## Repository Layout
```
apps/
  manager-api/      # FastAPI 기반 외부 API 엔드포인트
  master-service/   # 검토·리플랜·Escalation 비즈니스 로직
  scheduler-worker/ # 백그라운드 스케줄러 워커
  subagent-runtime/ # A2A 실행 엔진, Capability 제공
  watch-worker/     # 모니터링/Watch 엔진

docs/m0/            # M0 설계 문서 (이 문서)

migrations/         # Flyway‑like SQL 마이그레이션 파일들
schemas/            # JSON Schema 기반 API 계약
seed/               # 초기 데이터 (tools, skills, playbooks, policies)
packages/           # 공유 라이브러리 및 서비스 별 패키지
  pi_adapter/       # pi runtime 과의 어댑터 계층 (경계 정의)
```

## 서비스 책임
- **Manager API**: HTTP/REST 인터페이스 제공, 인증·권한 검사, 프로젝트/에셋 CRUD, Playbook 실행 트리거.
- **Master Service**: 프로젝트 검토, 재계획, 에스컬레이션, 정책 적용 로직.
- **SubAgent Runtime**: 실제 명령 실행, Tool Bridge 제공, A2A 메시징 수신·전송.
- **Scheduler Worker**: `schedules` 테이블 기반 주기적인 JobRun 생성, 재시도 로직.
- **Watch Worker**: `watch_jobs` 와 `watch_events` 를 활용해 상태 변화를 감시하고 알림.

## 패키지 의존 방향
```
manager-api  -->  core, pi_adapter, shared
master-service --> core, policy_engine, shared
subagent-runtime --> pi_adapter, a2a_protocol, shared
scheduler-service --> core, shared
watch-service --> core, shared
```
*하위 패키지는 상위 패키지(예: `core`)에만 직접 의존하고, 서로 순환 의존을 피한다.*

---
*임의 적용*: 일부 패키지 의존도는 차후 M1 단계에서 조정될 수 있습니다.*
