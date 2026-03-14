# OldClaw M0 DB Schema Overview

## Core Tables (Asset‑first)
| Table | Purpose |
|-------|---------|
| **assets** | 관리 대상 자산 정의. `metadata` JSONB 로 확장 가능 |
| **asset_endpoints** | 자산이 제공하는 접근점 (SSH, HTTP, etc.) |
| **targets** | 실행 시점에 파생되는 endpoint 정보 (임시 객체) |
| **projects** | 사용자가 요청한 작업 단위, 상태·단계 포함 |
| **project_assets** | 프로젝트 ↔ 자산 매핑 (scope) |
| **job_runs** | 세부 실행 단위, skill/playbook/asset 지정 |
| **evidence** | 모든 실행 결과 증빙. stdout/stderr/blob reference 포함 |
| **validation_runs** | 검증 로직 실행 결과 및 link to evidence |
| **master_reviews** | Master 의 최종 검수·승인 기록 |
| **reports** | 최종/중간 보고서 (blob reference) |

## Registry Tables (Tool → Skill → Playbook)
| Table | Description |
|-------|-------------|
| **tools** | 원자 기능 정의 (run_command 등) |
| **skills** | 재사용 가능한 capability, tool 조합 및 validation 힌트 |
| **skill_tools** | Skill ↔ Tool 매핑 |
| **playbooks** | 절차 정의, step 순서와 타입 지정 |
| **playbook_steps** | Playbook 내부 단계 (skill, validation, report 등) |
| **playbook_bindings** | 정책·자산·환경 등과 연계 |

## Supporting Tables
- **approvals**, **policies**, **policy_bindings** – 정책·승인 흐름
- **messages**, **audit_logs** – 운영 로그 & A2A 메시징
- **task_memories**, **experiences**, **retrieval_documents** – 4‑layer history 전략
- **schedules**, **watch_jobs**, **incidents** – batch / continuous 지원

### Schema Definition Files
- `migrations/0001_init_core.sql` – 핵심 테이블 DDL
- `migrations/0002_registry.sql` – registry 전용 테이블 DDL
- `migrations/0003_history_and_experience.sql` – history/experience DDL
- `migrations/0004_scheduler_and_watch.sql` – 배치/연속 작업 DDL

> **Note**: All tables include `created_at`, `updated_at` timestamps and use `jsonb` for flexible extensibility, satisfying the **asset‑first** & **evidence‑first** principles.
