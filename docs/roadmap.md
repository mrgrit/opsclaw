# OpsClaw Future Roadmap — M14~M20

**작성일:** 2026-03-21
**현재 상태:** M13 완료 기준
**목적:** M14 이후 개선 방향, 마일스톤별 세부 수행 계획 및 TODO List

---

## 개요

M13까지 OpsClaw의 기반 인프라와 운영 안정화를 완료했다. M14부터는 다음 7개 방향으로 플랫폼을 발전시킨다.

| 마일스톤 | 핵심 주제 | 우선순위 |
|---------|---------|---------|
| M14 | Agent Role Clarity & Workflow | 2순위 |
| M15 | Platform Modes (직접구동 vs AI-Driven) | 4순위 |
| M16 | Web UI/Dashboard | 5순위 |
| M17 | Pi Freeze Bug Fix | **1순위** |
| M18 | Proof of Work & Blockchain Reward | 6순위 |
| M19 | Skill/Tool/Experience 실동작 검증 | 3순위 |
| M20 | User & Agent Manual | 7순위 |

---

## M17 — Pi Freeze Bug Fix (1순위)

**목표:** 실운영에서 반복 발생하는 pi 멈춤 현상 근본 원인 분석 및 패치

### 배경

M13에서 pi wake-up 재시도(최대 2회) 및 timeout 300초 연장으로 임시 대응했으나, 근본 원인은 미해결이다. 장시간 부하 환경에서 pi가 응답 없이 멈추는 현상이 지속되고 있다.

### 조사 대상

```
packages/pi_adapter/runtime/client.py   # httpx 스트리밍 응답 처리
packages/pi_adapter/runtime/executor.py # 실행 루프, timeout 관리
```

### TODO List

- [x] **WORK-53** 재현 시나리오 및 부하 테스트 스크립트 작성
  - `scripts/m17_load_test.py` (동시 N개 × R회, API/직접 모드)

- [x] **WORK-54** pi_adapter 응답 수신 로직 분석
  - httpx 스트리밍: [DONE] 처리, 빈 chunk skip, ReadTimeout → 부분응답 성공 처리 확인

- [x] **WORK-55** timeout 세분화 패치
  - `_CHUNK_READ_TIMEOUT`: 60s → 30s (청크 간격)
  - httpx `Timeout(connect=10, read=30, write=10, pool=5)` 적용

- [x] **WORK-56** Ollama keep-alive + httpx 커넥션 풀
  - `keep_alive: "10m"` — GPU 메모리 모델 유지
  - `httpx.Limits(max_connections=5, max_keepalive_connections=3)`

- [x] **WORK-57** 패치 후 부하 테스트 (2026-03-22)
  - 동시 3개 × 2회 = 6/6 성공, timeout 0, freeze 미발생

### 완료 기준

- [x] pi freeze 재현 시나리오에서 패치 후 정상 동작 (6/6 성공)
- [x] chunk 간격 timeout 발생 시 명확한 에러 메시지 반환 (무한 대기 없음)
- [x] 테스트 결과 문서화 (`docs/m17/opsclaw-m17-completion-report.md`)

---

## M14 — Agent Role Clarity & Workflow (2순위)

**목표:** Master → Manager → SubAgent 계층의 역할을 코드 수준에서 명확히 분리하고, Playbook 단위 작업 완료 → 검수 → 보고서 생성 → 다음 작업 참조 전체 흐름을 end-to-end 구현 및 검증

### 핵심 흐름 설계

```
1. 사용자 요구사항 입력
       ↓
2. Master: 요구사항 분석 → 전체 작업 계획 수립 → Playbook 단위로 분해
          → 각 Playbook별 지시 프롬프트 생성
       ↓
3. Manager: Playbook 지시 수신 → 실행 계획 수립
          → 순서: [도구 설치] → [코드 작성] → [설정 변경] → [검증]
          → 각 단계를 SubAgent에게 dispatch
       ↓
4. SubAgent: 명령 실행 → stdout/stderr/exit_code 반환 → evidence 기록
       ↓
5. Manager: 결과 수신 → 성공 시 다음 단계 / 실패 시 오류 처리 또는 replan
       ↓
6. Playbook 완료 시 → Master 검수 요청
       ↓
7. Master: 작업 검수 (evidence 기반)
          → 승인: Manager가 완료보고서 자동 생성
          → 반려: replan 지시
       ↓
8. 완료보고서 DB 저장 → 다음 유사 Playbook 생성 시 RAG 참조
```

### TODO List

- [x] **WORK-58** Master 지시 프롬프트 생성 엔진 구현
  - `apps/master-service/src/main.py` (`POST /projects/{id}/master-plan`)
  - 입력: 자연어 요구사항
  - 출력: Playbook 목록 + 각 Playbook별 지시 프롬프트 (JSON)
  - Ollama LLM 호출로 계획 수립

- [x] **WORK-59** Manager 작업 실행 루프 정형화
  - `apps/manager-api/src/main.py` (`POST /projects/{id}/execute-plan`)
  - tasks[] 순서 실행, playbook_hint → Playbook 실행, 없으면 adhoc dispatch
  - critical 태스크 dry_run 강제, 결과 evidence 자동 기록

- [x] **WORK-60** Playbook 완료보고서 자동 생성 API
  - `POST /projects/{id}/completion-report` 구현
  - 보고서 내용: summary, outcome, work_details[], issues[], next_steps[]
  - DB 테이블: `completion_reports` (migration: 0007_completion_reports.sql)

- [x] **WORK-61** 완료보고서 RAG 참조 연동
  - `retrieval_service.search_documents()` 로 유사 완료보고서 검색
  - Master 지시 프롬프트에 참조 보고서 context 자동 삽입
  - `GET /completion-reports?q={keyword}` API

- [x] **WORK-62** end-to-end 시나리오 테스트 (2026-03-22)
  - 테스트 시나리오: "신규 Ubuntu 서버에 Nginx 설치 및 보안 설정"
  - Master 계획(6태스크) → execute-plan(4태스크 ok) → 완료보고서 DB 저장 검증
  - 동일 요청 2회: `past_reports_referenced=1` 확인

### 완료 기준

- [x] Master → Manager → SubAgent 전체 흐름 코드로 추적 가능
- [x] Playbook 완료보고서 자동 생성 및 DB 저장 동작 확인
- [x] 동일 작업 재요청 시 이전 완료보고서 참조 동작 확인

---

## M19 — Skill/Tool/Experience 실동작 검증 (3순위)

**목표:** DB에 등록된 Skill, Tool, Experience가 실제 코드 실행 경로에서 올바르게 동작하는지 검증하고 미동작 부분 보완

### 개념 정리

> OpsClaw의 Tool/Skill은 Claude Code의 skill과 다르다.
> - **Tool**: 실행 가능한 shell 명령/스크립트 단위 (e.g., `nmap -sV`, `apt-get install`)
> - **Skill**: Tool 조합으로 특정 목적을 달성하는 절차 단위 (e.g., "포트 스캔 + 취약점 분석")
> - **Experience**: 과거 작업 결과에서 추출한 패턴/교훈 (성공/실패 사례 요약)

### TODO List

- [x] **WORK-63** Tool 실행 경로 검증 (2026-03-22)
  - `resolve_playbook()` metadata 누락 버그 수정
  - 6개 seed tool 스크립트 생성 + subagent dispatch 3/3 성공

- [x] **WORK-64** Skill composition engine 검증 (2026-03-22)
  - `skill_tools` 테이블 12개 링크 삽입
  - Playbook(skill step) 실행 → subagent dispatch 2/2 성공

- [x] **WORK-65** Experience 생성 → 검색 → 참조 흐름 테스트 (2026-03-22)
  - `build_task_memory` + `promote_to_experience` + retrieval 인덱싱 정상 동작
  - `get_context_for_project()` → experiences 5개 context 주입 확인

- [x] **WORK-66** 미구현/미연결 부분 보완 (2026-03-22)
  - `resolve_playbook()` metadata 필드 추가
  - `skill_tools` 링크 데이터 삽입

- [x] **WORK-67** 통합 smoke 테스트 스크립트 작성 (2026-03-22)
  - `scripts/m19_skill_smoke.py` — 30개 항목 30/30 PASS

### 완료 기준

- [x] 6개 seed tool 실제 실행 성공
- [x] Playbook composition engine end-to-end 성공
- [x] Experience 검색 결과가 신규 프로젝트 context에 반영 확인

---

## M15 — Platform Modes (4순위)

**목표:** OpsClaw를 구동하는 방식에 따라 두 가지 모드를 명시적으로 지원

### 모드 정의

| 모드 | 설명 | Master 역할 |
|------|------|------------|
| **Mode A: Native** | 사용자가 Web UI/API로 직접 요청 | OpsClaw 내장 LLM |
| **Mode B: AI-Driven** | Claude Code/Codex 등 외부 AI가 오케스트레이션 | 외부 AI |

### Mode B 동작 원리

```
사용자 → Claude Code에게 "~해줘" (자연어)
       → Claude Code: OpsClaw Manager API 직접 호출
         POST /projects, POST /projects/{id}/dispatch, ...
       → OpsClaw: 실행 control-plane 역할 (인증, evidence, 상태전이)
       → Claude Code: 결과 확인 후 다음 API 호출
```

### TODO List

- [x] **WORK-68** Manager API `master_mode` 컨텍스트 필드 추가
  - 프로젝트 생성 시 `master_mode: "native" | "external"` 필드
  - native 모드: OpsClaw 내장 LLM으로 계획 수립
  - external 모드: LLM 계획 없이 API 호출 그대로 실행

- [x] **WORK-69** External Master용 OpenAPI spec 정리
  - 주요 API endpoint에 LLM-friendly 설명 추가 (한국어)
  - `docs/api/external-master-guide.md` 작성

- [x] **WORK-70** Claude Code용 오케스트레이션 가이드 작성
  - `CLAUDE.md` 업데이트: OpsClaw API 호출 방법
  - 예시 프롬프트 작성: "신규 서버 온보딩", "패키지 설치", "보안 점검"

- [x] **WORK-71** Mode B 통합 테스트
  - Claude Code가 Manager API를 직접 호출하여 작업 완료하는 시나리오 검증
  - 결과: 16/16 PASS (2026-03-22)

### 완료 기준

- [x] Mode A (Native): Web UI에서 작업 요청 → LLM 계획 → 실행 동작
- [x] Mode B (AI-Driven): Claude Code가 API 직접 호출로 작업 완료

---

## M16 — Web UI/Dashboard (5순위)

**목표:** API 전용인 OpsClaw에 웹 기반 운용 UI 추가

### 화면 구성

| 화면 | 주요 기능 |
|------|---------|
| 대시보드 | 에이전트 상태, 진행 중 프로젝트, 최근 알림 |
| 프로젝트 | 목록, 생성, 상태 추적, evidence 조회 |
| 에이전트 | SubAgent 등록/편집/삭제, 상태 모니터링, bootstrap 실행 |
| Playbook | 목록, 생성/편집, 실행 이력 |
| 설정 | 알림 채널(Slack/Email/Webhook), RBAC 사용자/역할 |
| 작업 Replay | 프로젝트 단위 작업 단계별 Replay 뷰어 |

### 기술 스택

- Frontend: React + Vite + TypeScript
- Backend: 기존 FastAPI Manager API 활용 (CORS 추가)
- 실시간: WebSocket (`/ws/projects/{id}/status`)
- 배포: FastAPI static 서빙 또는 Nginx

### TODO List

- [ ] **WORK-72** 프론트엔드 프로젝트 초기화
  - `apps/web-ui/` 디렉토리 생성
  - React + Vite + TypeScript 설정
  - Manager API 클라이언트 자동 생성 (openapi-typescript-codegen)

- [ ] **WORK-73** 대시보드 & 에이전트 화면
  - SubAgent 상태 카드 (온라인/오프라인, 마지막 heartbeat)
  - 진행 중 프로젝트 목록

- [ ] **WORK-74** 프로젝트 관리 화면
  - 프로젝트 CRUD + 상태 전이 버튼
  - evidence 목록 및 상세 조회

- [ ] **WORK-75** Playbook 관리 화면
  - Playbook CRUD
  - Step 편집 UI

- [ ] **WORK-76** 설정 화면
  - 알림 채널 등록 (Slack/Email/Webhook)
  - RBAC 사용자/역할 관리

- [ ] **WORK-77** 작업 Replay 뷰어
  - 프로젝트 실행 단계 타임라인
  - 각 단계 evidence 상세 (command, stdout, stderr)

- [ ] **WORK-78** WebSocket 실시간 업데이트
  - Manager API에 `/ws/projects/{id}/status` 엔드포인트 추가
  - 프로젝트 상태 변경 시 Web UI 실시간 반영

### 완료 기준

- [ ] 에이전트 등록 → 프로젝트 생성 → dispatch → evidence 확인 전 과정 Web UI에서 가능
- [ ] Slack/Email 알림 채널 Web UI에서 설정 가능
- [ ] 작업 Replay 뷰어에서 단계별 evidence 확인 가능

---

## M18 — Proof of Work & Blockchain Reward (6순위)

**목표:** 에이전트 작업에 대한 블록체인 기반 증명과 보상 체계 도입

### 개념

- 각 SubAgent가 수행한 작업(evidence)을 해시로 블록체인에 기록 → 위변조 불가 작업증명
- 작업량/품질 기반 보상 토큰 지급
- 작업 전체 내역 DB 저장 → Audit 강화, 책임 추적성
- 웹 UI에서 작업 Replay 및 작업증명 조회

### 작업증명 데이터 구조

```json
{
  "pow_id": "uuid",
  "agent_id": "subagent-secu-01",
  "project_id": "uuid",
  "playbook_id": "uuid",
  "evidence_hash": "sha256(evidence_content)",
  "timestamp": "2026-03-21T10:00:00Z",
  "block_hash": "sha256(prev_hash + evidence_hash + timestamp)",
  "reward_tokens": 10,
  "signature": "agent_private_key_sign(block_hash)"
}
```

### TODO List

- [ ] **WORK-79** 작업증명 DB 설계 및 마이그레이션
  - `proof_of_work` 테이블 추가
  - `reward_ledger` 테이블 추가 (에이전트별 토큰 잔액)
  - `migrations/0007_proof_of_work.sql` 작성

- [ ] **WORK-80** 작업증명 서비스 구현
  - `packages/pow_service/__init__.py`
  - `generate_proof(evidence)` — evidence → hash → block 생성
  - `verify_proof(pow_id)` — 블록 체인 검증
  - `get_agent_rewards(agent_id)` — 에이전트 보상 조회

- [ ] **WORK-81** 블록체인 연동 검토 및 구현
  - Option A: 자체 경량 Merkle Chain (외부 의존성 없음, 내부망 적합)
  - Option B: Hyperledger Fabric 연동
  - 결정 후 구현

- [ ] **WORK-82** 보상 토큰 회계 서비스
  - 작업 완료 시 자동 보상 계산 (기본 10 + 품질 보너스)
  - 품질 기준: validation all_passed(+5), 재시도 없음(+3), 시간 내 완료(+2)
  - `GET /agents/{id}/rewards` API

- [ ] **WORK-83** 작업 Replay API
  - `GET /projects/{id}/replay` — 단계별 실행 타임라인 반환
  - 각 단계: timestamp, command, stdout, stderr, exit_code, evidence_hash

- [ ] **WORK-84** 웹 UI 블록체인 뷰어
  - 에이전트별 작업증명 목록
  - 블록 체인 시각화
  - 보상 토큰 잔액 표시

### 완료 기준

- [ ] SubAgent 작업 완료 시 자동 작업증명 생성 및 DB 저장
- [ ] 블록 해시 검증으로 위변조 탐지 동작 확인
- [ ] 에이전트 보상 토큰 자동 지급 및 잔액 조회 동작
- [ ] 작업 Replay API에서 전체 단계 타임라인 반환

---

## M20 — User & Agent Manual (7순위)

**목표:** 사용자와 에이전트 운영자를 위한 완성된 매뉴얼 작성

### 사용자 매뉴얼 목차

```
docs/manual/user/
  01-installation.md          # OpsClaw 설치 및 초기 설정
  02-quick-start.md           # 5분 퀵스타트 가이드
  03-project-workflow.md      # 프로젝트 생성 → 실행 → 완료 흐름
  04-playbook-guide.md        # Playbook 작성 및 관리
  05-notification-setup.md   # Slack/Email/Webhook 알림 설정
  06-web-ui-guide.md          # 웹 UI 사용 가이드
  07-troubleshooting.md       # FAQ 및 트러블슈팅
```

### 에이전트 운용 매뉴얼 목차

```
docs/manual/agent/
  01-subagent-install.md      # SubAgent 신규 시스템 설치 (install.sh)
  02-agent-prompts.md         # Master/Manager/SubAgent 프롬프트 작성 가이드
  03-custom-skill-tool.md     # 커스텀 Skill/Tool/Playbook 추가 방법
  04-a2a-protocol.md          # A2A 프로토콜 연동 가이드
  05-ai-driven-mode.md        # Claude Code로 OpsClaw 오케스트레이션 가이드
```

### TODO List

- [ ] **WORK-85** 사용자 매뉴얼 작성 (7개 파일)
- [ ] **WORK-86** 에이전트 운용 매뉴얼 작성 (5개 파일)
- [ ] **WORK-87** README.md 최종 정리 (M14~M19 완료 반영)

### 완료 기준

- [ ] OpsClaw를 처음 접하는 운영자가 매뉴얼만으로 설치 및 첫 작업 실행 가능
- [ ] 에이전트 운영자가 매뉴얼만으로 SubAgent 설치 및 커스텀 Playbook 추가 가능

---

## 전체 TODO 요약

### M17 (Pi Freeze) — 완료 2026-03-22
- [x] WORK-53: 재현 환경 구성 및 시나리오 작성
- [x] WORK-54: pi_adapter 응답 수신 로직 분석
- [x] WORK-55: timeout 세분화 패치
- [x] WORK-56: Ollama 연결 재사용 설정
- [x] WORK-57: 패치 후 부하 테스트

### M14 (Agent Workflow) — 완료 2026-03-22
- [x] WORK-58: Master 지시 프롬프트 생성 엔진
- [x] WORK-59: Manager 작업 실행 루프 정형화
- [x] WORK-60: Playbook 완료보고서 자동 생성 API
- [x] WORK-61: 완료보고서 RAG 참조 연동
- [x] WORK-62: end-to-end 시나리오 테스트

### M19 (Skill/Tool/Experience 검증) — 완료 2026-03-22
- [x] WORK-63: Tool 실행 경로 검증
- [x] WORK-64: Skill composition engine 검증
- [x] WORK-65: Experience 생성 → 검색 → 참조 흐름 테스트
- [x] WORK-66: 미구현/미연결 부분 보완
- [x] WORK-67: 통합 smoke 테스트 스크립트

### M15 (Platform Modes)
- [x] WORK-68: master_mode 컨텍스트 필드 추가
- [x] WORK-69: External Master용 API 가이드
- [x] WORK-70: Claude Code용 오케스트레이션 가이드 (CLAUDE.md)
- [x] WORK-71: Mode B 통합 테스트 (16/16 PASS)

### M16 (Web UI)
- [ ] WORK-72: 프론트엔드 프로젝트 초기화
- [ ] WORK-73: 대시보드 & 에이전트 화면
- [ ] WORK-74: 프로젝트 관리 화면
- [ ] WORK-75: Playbook 관리 화면
- [ ] WORK-76: 설정 화면
- [ ] WORK-77: 작업 Replay 뷰어
- [ ] WORK-78: WebSocket 실시간 업데이트

### M18 (Blockchain PoW)
- [ ] WORK-79: 작업증명 DB 설계 및 마이그레이션
- [ ] WORK-80: 작업증명 서비스 구현
- [ ] WORK-81: 블록체인 연동 구현
- [ ] WORK-82: 보상 토큰 회계 서비스
- [ ] WORK-83: 작업 Replay API
- [ ] WORK-84: 웹 UI 블록체인 뷰어

### M20 (Manual)
- [ ] WORK-85: 사용자 매뉴얼 (7개 파일)
- [ ] WORK-86: 에이전트 운용 매뉴얼 (5개 파일)
- [ ] WORK-87: README.md 최종 정리

---

*문서 갱신: M17~M20 각 마일스톤 완료 시 해당 completion-report 작성 후 이 파일 업데이트*
