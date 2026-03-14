# OldClaw M0 Design Baseline (Reference Implementation)

## 1. 목표
- **OldClaw**는 **pi runtime** 위에 구축되는 **Control‑Plane Orchestration Platform**이다.
- 핵심 원칙: **Asset‑first**, **Evidence‑first**, **Tool < Skill < Playbook** 계층화.
- 서비스는 **Manager API**, **Master Service**, **SubAgent Runtime**, **Scheduler Worker**, **Watch Worker** 로 명확히 분리한다.

## 2. 핵심 설계 결정 (M0 고정)
| 영역 | 결정 사항 | 이유 |
|------|------------|------|
| 데이터 모델 | `assets`, `projects`, `job_runs`, `evidence` 등 핵심 테이블을 **UUID PK**, `created_at/updated_at` 타임스탬프 기본 제공 | 일관된 식별자와 추적 가능성 보장 |
| Tool/Skill/Playbook 경계 | Tool은 **저수준 시스템 호출**만 수행; Skill은 Tool 조합 + 검증; Playbook은 Skill 순차 실행 및 정책 바인딩 | 책임 분리, 검증 가능, 정책 적용 용이 |
| Service 책임 | Manager → 외부 API 제공, Project/Asset CRUD 및 Playbook 트리거<br>Master → Review, Re‑plan, Escalation 로직<br>SubAgent → Health, Capability 열람, A2A 스크립트 실행<br>Scheduler → `schedules` 기반 JobRun 생성<br>Watch → `watch_jobs` 모니터링 및 이벤트 처리 | 책임 명확화, 독립 배포 가능 |
| 모델 프로파일 | `packages/pi_adapter/model_profiles` 에 `manager`, `master`, `subagent` 각각의 모델·temperature 정의 | 향후 M1에서 모델 교체 용이 |

## 3. M1 로 넘기는 항목 (보강 후 이관)
- 정책 엔진 상세 구현 (policy_engine 패키지)
- 고도화된 검증/리포팅 파이프라인
- 실제 pi SDK 연동 및 세션 관리
- 복합 인덱스 및 성능 튜닝

---
## Detailed Design Rationale

### Asset‑First Principle
The platform treats assets as the primary source of truth. All other entities (targets, projects, job runs) reference an asset via foreign keys. This guarantees that any operation can be traced back to a concrete infrastructure object, simplifying audit and compliance.

### Evidence‑First Principle
Every actionable step (Tool execution, Skill run, Playbook) creates an **Evidence** record. Evidence is immutable and linked to the originating `JobRun`. Down‑stream validators and reports consume only evidence, never raw logs, ensuring reproducibility.

### Tool → Skill → Playbook Flow
- **Tool**: atomic operation, no side‑effects beyond its explicit output.
- **Skill**: orchestrates one or more Tools, performs input validation, and produces structured evidence.
- **Playbook**: defines a directed acyclic graph of Skills, controls flow (conditions, retries) and binds policies (e.g., SLA, risk limits).

### Separation of Concerns
- **Manager API**: external façade, request validation, routing, and orchestration triggers.
- **Master Service**: business logic for review, re‑planning, escalation; operates on persisted state only.
- **SubAgent Runtime**: lightweight execution environment exposing capabilities via HTTP; communicates with Manager via A2A messages.
- **Scheduler / Watch Workers**: background daemons that translate temporal or event‑driven triggers into `JobRun` entries.

### Extensibility
New Tools, Skills, or Playbooks are added by inserting rows into the registry tables and adding corresponding JSON schema files under `schemas/registry`. No code change is required for the core platform.

---
*임의 적용*: 일부 정책‑바인딩 상세는 M1 에서 정의될 예정입니다.*
