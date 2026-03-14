# OldClaw M0 Design Baseline

## 목표
- **OldClaw**는 **pi runtime** 위에 구축되는 **Control‑Plane Orchestration Platform**이다.
- Asset‑first, Evidence‑first 원칙을 고수하며, **Tool → Skill → Playbook** 의 3‑계층 흐름을 강제한다.
- 서비스는 **Manager API, Master Service, SubAgent Runtime, Scheduler Worker, Watch Worker** 로 구분한다.

## 핵심 설계 결정 (M0 고정)
| 영역 | 결정 내용 | 이유 |
|------|-----------|------|
| 데이터 모델 | `assets`, `projects`, `job_runs` 등 핵심 테이블을 PK=UUID, `created_at/updated_at` 기본 제공 | 일관된 식별자와 시간 추적 보장 |
| 서비스 경계 | Manager‑API: 외부 API 제공<br>Master‑Service: 검토·리플랜·Escalation 로직<br>SubAgent‑Runtime: A2A 실행 엔진, Capability 조회<br>Scheduler‑Worker / Watch‑Worker: 백그라운드 잡 스케줄링 및 모니터링 | 책임 분리, 확장성 확보 |
| Registry | `tools`, `skills`, `playbooks` 를 별도 스키마로 관리, versioned ID (`<name>:<ver>`) 사용 | 재사용·버전 관리 용이 |
| 플로우 | **Tool** 은 원시 명령/시스템 콜, **Skill** 은 Tool 조합 + 검증, **Playbook** 은 Skill 순차 실행 정의 | 단계적 검증, 정책 적용 가능 |

## 다음 마일스톤 (M1) 에 위임된 항목
- 복잡한 정책 엔진 구현
- 고도화된 검증/리포팅 로직
- 실제 pi runtime 연동 (모델 프로파일, 세션 관리)

---
*본 문서는 M0 단계에서 확정된 설계 사항을 기록합니다. 이후 변경 시 "임의 적용"으로 명시합니다.*
