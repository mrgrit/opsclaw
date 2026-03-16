# Repository & Service Structure (M0 Reference)

```
opsclaw/
├─ apps/
│   ├─ manager-api/      # FastAPI entrypoint, REST façade
│   ├─ master-service/   # Review / Re‑plan / Escalation service
│   ├─ subagent-runtime/ # Lightweight HTTP API for health, capabilities, A2A run
│   ├─ scheduler-worker/ # Background poller for `schedules`
│   └─ watch-worker/     # Background processor for `watch_jobs`
├─ docs/m0/               # M0 설계 문서 (본 디렉터리)
├─ migrations/            # Flyway‑like SQL 마이그레이션 (초기 스키마)
├─ packages/
│   └─ pi_adapter/        # pi runtime 과의 어댑터 계층 (runtime, tools, sessions …)
├─ schemas/                # JSON‑Schema 기반 API 계약 및 Registry 스키마
├─ seed/                   # 초기 registry 데이터 (Tool, Skill, Playbook, Policy)
├─ tests/                  # 테스트 스위트 (현재 placeholder)
└─ README.md
```

## 서비스 간 의존 방향
- **Manager API** → `packages/core`, `packages/pi_adapter` (ToolBridge 사용) → DB (via core services) – 외부 요청을 받아 내부 서비스와 데이터베이스를 연결합니다.
- **Master Service** → `packages/policy_engine` (향후) → DB – 검토·리플랜·에스컬레이션 로직은 DB 상태만을 조회·수정합니다.
- **SubAgent Runtime** → `packages/pi_adapter/runtime` (세션 관리) → pi runtime (외부) – **읽기 전용**으로, 실제 명령 실행은 SubAgent 자체가 아닌 pi 를 통해 수행됩니다.
- **Scheduler / Watch Workers** → DB (읽기) → `packages/core` (JobRun / WatchJob 생성) → `apps/manager-api` (엔드포인트 트리거) – 백그라운드 잡을 생성하고, Manager API 가 이를 감시합니다.

### 의존성 규칙
1. **수직 의존** – 하위 서비스는 상위 서비스에 직접 의존하지 않으며, 모두 공통 `core` 패키지를 통해 데이터 교환합니다.
2. **외부 경계** – `pi_adapter` 는 **외부** pi 엔진에만 의존하고, OpsClaw 내부 로직에 절대 침투하지 않으며, 인터페이스만 노출합니다.
3. **독립 배포** – 각 서비스는 독립적인 Docker 이미지/시스템 서비스로 배포될 수 있도록 설계되었습니다.

---
*임의 적용*: 일부 디렉터리 구조는 추후 M1 단계에서 세부 패키지로 재구성될 수 있습니다.*
