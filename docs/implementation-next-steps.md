# OpsClaw 구현 다음 단계 실행 가이드

이 문서는 `opsclaw-plan-v1.0.md`가 정의한 요구사항을 실제 구현으로 전환하기 위한 **즉시 실행용 로드맵**이다.

## 1. 지금 바로 할 일 (이번 주)

### 1) MVP-1 범위 고정 (Scope Freeze)

- 아래 기능만 1차 배포 범위로 잠금:
  - Manager + SubAgent 기본 통신
  - Todo/스크립트/테스트 생성
  - 실행 결과 수집/검증
  - Guardrails + Stop Conditions
  - MasterGate (scan → classify → allow/transform/block)
- 범위 밖 항목(RBAC 고도화, 플러그인 마켓, 대규모 UI)은 백로그로 이동.

**산출물**
- `docs/mvp-scope-v1.md` (in/out 목록)
- 이슈 트래커 에픽 3개: `orchestration`, `agent-runtime`, `mastergate`

### 2) 실행 아키텍처 결정 (기술 스택 확정)

- Manager API: FastAPI(REST + WebSocket) 또는 gRPC 중 하나로 확정
- State Store: 시작은 SQLite + JSON Artifact로 단순화
- Queue/비동기: 초기에는 프로세스 내 task runner, 이후 메시지 브로커 전환
- SubAgent 실행기: shell executor + timeout + allowlist/blocklist

**산출물**
- `docs/adr/0001-mvp-architecture.md`
- 컴포넌트 다이어그램(Manager/SubAgent/Store/Policy)

### 3) 데이터 계약(스키마) 먼저 잠금

- A2A 메시지 스키마 정의
  - `RUN_SCRIPT`, `RUN_TEST`, `STATUS_UPDATE`, `UPLOAD_EVIDENCE`
- 표준 결과 포맷 고정
  - exit code, stdout/stderr, changed files, service/network snapshot
- Audit Log 스키마 고정
  - actor, role, decision, policy_id, prompt_hash, timestamp

**산출물**
- `schemas/a2a/*.json`
- `schemas/audit-log.schema.json`

## 2. 2주 구현 스프린트 제안

## Sprint A (주 1): 실행 가능 뼈대

### 목표
- “요청 1건 → 계획/Todo 생성 → SubAgent 명령 실행 → 결과 저장”까지 관통

### 작업
- Manager 워크플로우 최소 노드 구현
  - Intake → Plan → Todo → Dispatch → Collect → Validate → Report
- SubAgent MVP 구현
  - 명령 수신, 실행, 타임아웃, 결과 업로드
- State/Evidence 저장
  - 작업별 폴더 구조 및 메타데이터 JSON
- CLI 또는 간단 UI
  - 작업 시작, 상태 조회, 로그 보기

### 완료 기준 (DoD)
- 샘플 작업 3개가 동일한 출력 구조로 완료
- 실패 작업 1개에서 error 분류 + 재시도 1회 동작

## Sprint B (주 2): 안전장치 + MasterGate

### 목표
- 외부 Master 호출 전 데이터 유출 방지 경로 완성

### 작업
- Guardrails 구현
  - 위험 명령 차단, 민감 경로 승인 필요, 네트워크 호출 정책
- MasterGate 구현
  - regex 1차 스캔
  - dictionary 2차 스캔
  - local LLM 3차 분류(없으면 룰 기반 임시 점수)
  - allow/transform/block 의사결정
- Transform 파이프라인
  - IP/호스트/유저/토큰 마스킹
  - 의미보존 요약 템플릿 적용
- 승인 UI(최소)
  - 전송 프롬프트 미리보기 + 마스킹 diff + 승인/거절

### 완료 기준 (DoD)
- 민감 데이터 포함 샘플 5건 중 5건 모두 `transform` 또는 `block`
- 승인 이력/정책 이력 Audit 로그 저장 확인

## 3. 병렬로 준비할 운영 기본기

- 테스트 자산
  - 정상/오류/민감정보 샘플 입력 세트 구축
- 관측성
  - 최소 메트릭(작업 성공률, 평균 실행시간, 재시도율, block율)
- 롤백 체계
  - 변경 전 백업 + 실패 시 자동 복구 스크립트
- 배포 방식
  - 폐쇄망 번들(의존성 포함) 패키징 초안

## 4. 팀 역할 분담(권장)

- Track 1: Orchestrator 팀
  - LangGraph 노드, 상태전이, 재시도/중지 조건
- Track 2: Agent Runtime 팀
  - SubAgent 실행 안정성, 표준 결과 포맷
- Track 3: Policy/Security 팀
  - Guardrails, MasterGate, Audit/Evidence
- Track 4: UX/Report 팀
  - Todo/승인 UX, 리포트/증빙 다운로드

## 5. 이번 주 킥오프 체크리스트

- [ ] MVP-1 In/Out 승인 완료
- [ ] 아키텍처 ADR 승인 완료
- [ ] A2A/Audit 스키마 리뷰 완료
- [ ] Sprint A 작업 분해 및 담당자 지정
- [ ] 샘플 시나리오 3개(운영/보안/유지보수) 테스트 데이터 준비

## 6. “다음에 무엇을 할지” 한 줄 요약

**먼저 MVP-1 범위를 잠그고, A2A/감사 스키마를 고정한 뒤, 2주 안에 `실행 뼈대(Sprint A) + MasterGate 안전장치(Sprint B)`를 완성하세요.**
