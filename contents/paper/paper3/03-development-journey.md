# 3. 개발 여정: 25 마일스톤 (Development Journey)

본 장에서는 OpsClaw의 25 마일스톤 개발 과정을 6개 단계로 구분하여 기술하고, 각 단계의 핵심 설계 결정과 교훈을 분석한다.

## 3.1 설계 기준선 확립 (M0~M2)

M0에서 확정한 것: 역할 분리(Master/Manager/SubAgent), 개념 계층(Tool→Skill→Playbook), 서비스/패키지 경계, DB 스키마, 의존 방향 규칙, 완료 판정 원칙("evidence 없는 완료 주장 금지").

M0 설계 기준 문서는 "개요 메모"가 아니라 **구현자가 코드 작성 시 참조하는 최상위 설계 기준**으로 작성하였다. "구현 중 코드와 이 문서가 충돌하면, 기존 편의보다 이 문서의 구조적 의도를 우선한다"를 명시하였다.

**교훈 L1: 설계 기준 문서를 코드보다 먼저, 코드보다 상위에 고정하라.** M0 문서가 이후 25개 마일스톤에서 설계 방향이 흔들리는 것을 방지하였다. 특히 "역방향 의존 금지"(pi_adapter → 상위 패키지) 규칙은 여러 번의 유혹을 물리치는 데 효과적이었다.

## 3.2 핵심 서비스 구현 (M3~M12)

13개 패키지(project_service, graph_runtime, asset_registry, evidence_service 등)와 5개 서비스(manager-api, master-service, subagent-runtime, scheduler-worker, watch-worker)를 순차적으로 구현하였다.

주요 이슈:
- **pi runtime 연동 경계.** 초기에 pi CLI(pi-coding-agent)를 subprocess로 호출하였으나, ollama provider 미지원으로 500 에러가 발생. httpx로 Ollama를 직접 호출하는 방식으로 전환하여 해결 (M12).
- **LangGraph 상태 머신.** 8단계 라이프사이클을 LangGraph StateGraph로 구현. 조건부 에지(approval gate)와 재계획 루프(replan)의 표현력이 높았으나, 디버깅 시 상태 전이 추적이 어려운 점이 단점.

**교훈 L2: 외부 런타임 의존은 어댑터 경계를 반드시 설정하라.** pi_adapter 패키지가 pi runtime의 변경으로부터 상위 비즈니스 로직을 보호하였다. pi CLI가 ollama를 지원하지 않는 문제도 어댑터 내부에서 httpx 직접 호출로 해결할 수 있었다.

**교훈 L3: 상태 머신은 무효 전이를 코드가 아닌 데이터로 차단하라.** `VALID_TRANSITIONS` 딕셔너리를 데이터로 정의하여, 허용되지 않은 전이를 일관되게 거부하였다. 실험 E에서 5/5 무효 전이 차단을 확인.

## 3.3 모드 분리와 외부 Master (M13~M15)

M13에서 실운영 테스트 중 Playbook 생성 API 부재, Bootstrap SSH 실패, SubAgent 포트 기본값 불일치 등 6건의 이슈를 발견. M15에서 Mode A(Native LLM)와 Mode B(External AI) 분리를 완료.

**교훈 L4: Master 교체 가능성이 아키텍처의 핵심 분기점이다.** Mode B 도입으로 Claude Code가 Manager API를 직접 호출하는 워크플로가 가능해졌다. Manager와 SubAgent가 Master의 정체에 무관하게 동작하도록 설계한 것이 이를 가능하게 했다. "누가 계획하든 실행 계층은 동일하게 동작한다"는 원칙.

## 3.4 해시 체인과 강화학습 (M18, M27)

M18에서 PoW 해시 체인과 보상 시스템을 도입. 각 태스크 실행 시 SHA-256 해시 블록과 보상(base + speed_bonus + risk_penalty)이 자동 생성된다.

**M27 버그 패치 (B-02): 시간대 해시 불일치.** 초기 구현에서 `ORDER BY ts`로 체인 순서를 결정하였으나, psycopg2가 naive datetime을 반환할 때 시간대 차이로 해시가 불일치하는 버그 발견. `ts_raw` 필드(원본 ISO 문자열)를 추가하고, `_build_chain`을 prev_hash 링크 순회(linked-list)로 변경하여 해결. 동시성 제어를 위해 `pg_advisory_xact_lock`도 추가.

**교훈 L5: 타임스탬프에 절대 의존하지 마라.** 해시 계산에 타임스탬프 객체를 사용하면 시간대, 직렬화 포맷, DB 드라이버 동작에 따라 결과가 달라진다. 원본 문자열(`ts_raw`)을 그대로 보존하여 해싱에 사용하는 것이 유일한 안전한 방법이다.

**교훈 L6: 동시성 문제는 "나중에 처리"하면 안 된다.** 병렬 execute-plan에서 동일 agent_id에 대한 동시 PoW 블록 생성이 prev_hash 충돌을 일으켰다. advisory lock으로 직렬화하여 해결했으나, 초기 설계에서 고려했어야 할 사항이다.

## 3.5 버그 수정과 보안 패치 (M21, M28)

**M21: 5건 버그 일괄 수정 (B-01~B-05).**
- B-01: evidence 조회 시 project_id 필터 누락
- B-02: 시간대 해시 불일치 (3.4절에서 상세)
- B-03: Playbook step params 전달 오류
- B-04: async_mode 결과 수집 race condition
- B-05: critical risk_level dry_run 미강제

**M28: API 인증 미들웨어 긴급 추가.** Purple Team 보안 실험(T2)에서 OpsClaw Manager API에 인증이 없어 외부에서 임의 명령 실행(RCE)이 가능함이 발견되었다. X-API-Key 미들웨어를 긴급 추가하여 해결.

**교훈 L7: Control-plane 보안은 보호 대상만큼 중요하다.** 보안 자동화 플랫폼 자체가 공격 벡터가 될 수 있다. Manager API의 인증 부재는 Purple Team 실험에서 Critical 취약점으로 발견되었으며, "우리 시스템은 내부용"이라는 가정이 얼마나 위험한지를 보여주었다.

## 3.6 보안 실험 운용 (M25~)

실환경 4대 서버에서 Red/Blue/Purple Team 16시간 자율 실행. 상세 결과는 별도 논문 [Paper 2]에서 기술.

운영 중 발견된 이슈:
- Wazuh Agent 버전(4.14.4) > Manager 버전 → 등록 거부, 로그 수집 실패
- SubAgent 120초 타임아웃 → 장시간 스캔(nmap 전체 포트) 불가
- SSH 이스케이핑 복잡성 → 복잡한 페이로드는 스크립트 파일 분리 필요

**교훈 L8: 실험 전 인프라 호환성 검증을 체크리스트화하라.** Wazuh Agent/Manager 버전 불일치는 Blue Team 실험의 실시간 탐지 검증을 불가능하게 만들었다. 사전 호환성 체크리스트가 있었다면 방지할 수 있었다.
