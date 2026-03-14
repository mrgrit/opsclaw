# OldClaw M0 DB Schema

## 핵심 테이블 개요
| 테이블 | 주요 컬럼 | 설명 |
|--------|-----------|------|
| **assets** | `id`, `name`, `type`, `platform`, `metadata` | 관리 대상 인프라 자산 정의 |
| **asset_endpoints** | `asset_id`, `endpoint_type`, `value` | 자산이 제공하는 엔드포인트 정보 |
| **targets** | `asset_id`, `base_url`, `health` | 자산에 연계된 접근 대상 (URL 등) |
| **projects** | `id`, `name`, `status`, `current_stage`, `playbook_id` | 오케스트레이션 작업 단위 |
| **project_assets** | `project_id`, `asset_id`, `scope_role` | 프로젝트와 자산 매핑 |
| **job_runs** | `project_id`, `playbook_id`, `skill_id`, `asset_id`, `status` | Playbook·Skill 실행 인스턴스 |
| **evidence** | `project_id`, `job_run_id`, `tool_name`, `command_text`, `stdout_ref` | 실행 결과와 로그 저장 |
| **validation_runs** | `project_id`, `job_run_id`, `validator_name`, `status` | 검증 결과 기록 |
| **master_reviews** | `project_id`, `reviewer_agent_id`, `status` | 검토·승인 기록 |
| **reports** | `project_id`, `report_type`, `body_ref` | 최종 보고서 |
| **messages** | `project_id`, `job_run_id`, `sender`, `content` | 시스템·사용자 메시지 |
| **audit_logs** | `event_type`, `actor`, `target`, `outcome` | 감사 로그 |
| **schedules** | `project_id`, `schedule_type`, `cron_expr`, `next_run` | 주기적 스케줄 정의 |
| **histories** | `project_id`, `event`, `context` | 히스토리 이벤트 |
| **experiences** | `asset_id`, `skill_id`, `outcome` | 경험/학습 데이터 |
| **retrieval_documents** | `source`, `content` | 검색용 문서 저장 |
| **task_memories** | `task_id`, `memory_type`, `payload` | 작업 메모리 (예: LLM 컨텍스트) |
| **incidents** | `project_id`, `severity`, `description`, `status` | 인시던트 기록 |
| **watch_jobs** | `project_id`, `job_type`, `status` | Watch 엔진 잡 |
| **watch_events** | `watch_job_id`, `event_type`, `payload` | Watch 이벤트 |

## 공통 컬럼
- 모든 테이블은 `id`(UUID) 기본키와 `created_at` 타임스탬프를 가짐.
- `updated_at` 은 주요 엔터티(`assets`, `projects`, `job_runs` 등) 에 적용.
- 외래키 제약조건을 통해 데이터 무결성을 보장.

---
*임의 적용*: 일부 상세 인덱스·제약은 M1 단계에서 추가될 수 있습니다.*
