# OpsClaw M1 Next TODO

## 목표
M1 단계에서는 **M0에서 고정된 설계·스키마** 를 기반으로 실제 실행 로직, 정책/검증 엔진, 그리고 pi runtime 연동을 구현한다. 모든 구현은 **Tool < Skill < Playbook** 흐름을 유지하면서, 정책과 검증을 자동화하고, 고성능 백그라운드 워커를 완전하게 동작시키는 것을 목표로 한다.

## 주요 작업 리스트 (세부 항목)
1. **Policy Engine** 구현
   - 정책 DSL 파싱·컴파일러 개발
   - 런타임 시 `policy_engine.evaluate(policy, context)` API 제공
   - `policy_engine` 패키지에 검증 로직, 라우터와 연동하는 미들웨어 추가
2. **pi Runtime 연동**
   - `packages/pi_adapter/runtime/client.py` 에 실제 pi SDK 클라이언트 초기화 구현
   - `model_profiles` 로부터 모델·temperature·system_prompt 로드 로직 구현
   - `sessions` 에서 사용자/에이전트 별 세션 관리 (생성·폐기·재시도)
   - `tools` 디렉터리에서 각 Tool 에 대한 구체적인 `execute` 메서드 구현 (예: `RunCommandTool` 실제 subprocess 호출 또는 pi SDK 명령 실행)
3. **서비스 비즈니스 로직**
   - **Master Service**: Review, Re‑plan, Escalation 엔드포인트에 DB 기반 로직 및 정책 적용 구현
   - **Scheduler Worker**: `load_schedules`, `process_schedule` 를 완전 구현하고, `JobRun` 생성 트랜잭션 처리
   - **Watch Worker**: `load_watch_jobs`, `process_watch_job` 구현, `Incident` 생성 및 알림 파이프라인 연결
4. **인덱스·성능 튜닝**
   - 주요 쿼리 (Project 조회, JobRun 상태 업데이트, Evidence 검색) 프로파일링
   - 복합 인덱스, 파티셔닝, 커버링 인덱스 추가
   - `audit_logs` 와 `messages` 에 TTL (PostgreSQL `pg_cron` 혹은 애플리케이션 레벨) 적용
5. **테스트 커버리지**
   - Unit 테스트 : 각 Registry 스키마, Service 핸들러, pi_adapter 인터페이스
   - Integration 테스트 : 전체 흐름 (Project → Playbook → Skill → Tool → Evidence) 검증
   - CI 파이프라인에 `pytest`, `coverage`, `flake8` 등 통합
6. **문서 정리**
   - `docs/m1/` 디렉터리 생성, 설계 상세, API 버전 관리 정책, 배포 가이드 작성
   - 기존 M0 문서와 차이점, 마이그레이션 가이드 명시

## 넘어갈 항목 (M0에서 미완성)
- **정책 정의·바인딩**: 정책 DSL, 정책‑Tool/Skill 매핑, 실행 시점 적용
- **고도화된 검증·리포팅**: Validation Service, Reporting Service, 자동화된 리포트 생성
- **모델 프로파일·세션**: 다중 모델 지원, 세션 재사용, 토큰 관리
- **복합 인덱스·성능 최적화**: 실제 워크로드 기반 인덱스 설계 및 테스트

---
*임의 적용*: 작업 순서는 프로젝트 리소스 상황에 따라 조정될 수 있습니다.*
