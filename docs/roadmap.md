# OpsClaw Future Roadmap — M14~M24

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

- [x] **WORK-72** 프론트엔드 프로젝트 초기화
  - `apps/web-ui/` 디렉토리 생성
  - React + Vite + TypeScript 설정
  - Manager API 클라이언트 (fetch 기반 직접 구현)

- [x] **WORK-73** 대시보드 & 에이전트 화면
  - 서비스 상태, 활성 프로젝트, 에이전트 수 카드
  - 최근 프로젝트 목록, 에이전트 보상 랭킹

- [x] **WORK-74** 프로젝트 관리 화면
  - 프로젝트 CRUD + 상태 전이 버튼
  - evidence 목록 및 상세 조회

- [x] **WORK-75** Playbook 관리 화면
  - Playbook CRUD
  - Step 조회 및 실행 UI

- [x] **WORK-76** 설정 화면
  - 알림 채널 등록 (Slack/Email/Webhook)
  - 알림 규칙 관리

- [x] **WORK-77** 작업 Replay 뷰어
  - 프로젝트 실행 단계 타임라인
  - PoW 체인 무결성 검증

- [x] **WORK-78** WebSocket 실시간 업데이트
  - Manager API에 `/ws/projects/{id}` 엔드포인트 추가
  - 프로젝트 상태 변경 시 Web UI 실시간 반영

### 완료 기준

- [x] 에이전트 등록 → 프로젝트 생성 → dispatch → evidence 확인 전 과정 Web UI에서 가능
- [x] Slack/Email 알림 채널 Web UI에서 설정 가능
- [x] 작업 Replay 뷰어에서 단계별 evidence 확인 가능

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

- [x] **WORK-79** 작업증명 DB 설계 및 마이그레이션
  - `proof_of_work` 테이블 추가
  - `reward_ledger` 테이블 추가 (에이전트별 토큰 잔액)
  - `migrations/0007_proof_of_work.sql` 작성

- [x] **WORK-80** 작업증명 서비스 구현
  - `packages/pow_service/__init__.py`
  - `generate_proof(evidence)` — evidence → hash → block 생성
  - `verify_proof(pow_id)` — 블록 체인 검증
  - `get_agent_rewards(agent_id)` — 에이전트 보상 조회

- [x] **WORK-81** 블록체인 연동 검토 및 구현
  - Option A 선택: 자체 경량 Merkle Chain (외부 의존성 없음, 내부망 적합)

- [x] **WORK-82** 보상 토큰 회계 서비스
  - 작업 완료 시 자동 보상 계산 (기본 10 + 품질 보너스)
  - 품질 기준: validation all_passed(+5), 재시도 없음(+3), 시간 내 완료(+2)
  - `GET /agents/{id}/rewards` API

- [x] **WORK-83** 작업 Replay API
  - `GET /projects/{id}/replay` — 단계별 실행 타임라인 반환
  - 각 단계: timestamp, command, stdout, stderr, exit_code, evidence_hash

- [x] **WORK-84** 웹 UI 블록체인 뷰어
  - 에이전트별 작업증명 목록 (PoW Blocks 페이지)
  - 블록 해시 + prev_hash 체인 표시
  - 보상 토큰 잔액 표시

### 완료 기준

- [x] SubAgent 작업 완료 시 자동 작업증명 생성 및 DB 저장
- [x] 블록 해시 검증으로 위변조 탐지 동작 확인
- [x] 에이전트 보상 토큰 자동 지급 및 잔액 조회 동작
- [x] 작업 Replay API에서 전체 단계 타임라인 반환

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

- [x] **WORK-85** 사용자 매뉴얼 작성 (7개 파일)
- [x] **WORK-86** 에이전트 운용 매뉴얼 작성 (5개 파일)
- [x] **WORK-87** README.md 최종 정리 (M14~M19 완료 반영)

### 완료 기준

- [x] OpsClaw를 처음 접하는 운영자가 매뉴얼만으로 설치 및 첫 작업 실행 가능
- [x] 에이전트 운영자가 매뉴얼만으로 SubAgent 설치 및 커스텀 Playbook 추가 가능

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
- [x] WORK-72: 프론트엔드 프로젝트 초기화
- [x] WORK-73: 대시보드 & 에이전트 화면
- [x] WORK-74: 프로젝트 관리 화면
- [x] WORK-75: Playbook 관리 화면
- [x] WORK-76: 설정 화면
- [x] WORK-77: 작업 Replay 뷰어
- [x] WORK-78: WebSocket 실시간 업데이트

### M18 (Blockchain PoW)
- [x] WORK-79: 작업증명 DB 설계 및 마이그레이션
- [x] WORK-80: 작업증명 서비스 구현
- [x] WORK-81: 블록체인 연동 구현
- [x] WORK-82: 보상 토큰 회계 서비스
- [x] WORK-83: 작업 Replay API
- [x] WORK-84: 웹 UI 블록체인 뷰어

### M20 (Manual)
- [x] WORK-85: 사용자 매뉴얼 (7개 파일)
- [x] WORK-86: 에이전트 운용 매뉴얼 (5개 파일)
- [x] WORK-87: README.md 최종 정리

---

*문서 갱신: M17~M20 각 마일스톤 완료 시 해당 completion-report 작성 후 이 파일 업데이트*

---

# OpsClaw Roadmap — M21~M24

**작성일:** 2026-03-24
**현재 상태:** M20 완료 기준
**출처:** future_opsclaw.md (버그 B-01~B-05, 아키텍처 개선 A-01~A-08)

---

## 개요

M21~M24는 실운영 및 RL 시나리오 테스트에서 발굴된 버그와 아키텍처 개선 사항을 다룬다.

| 마일스톤 | 핵심 주제 | 포함 항목 | 우선순위 |
|---------|---------|---------|---------|
| M21 | Bug Fix Sprint | B-01~B-05 | **1순위** (즉시) |
| M25 | Web UI 정상화 | GET /projects, key alias, evidence 정규화, Agents 페이지 | 즉시 |
| M22 | Playbook Engine v2 | A-01, A-02, A-03, A-06 | ✅ 완료 |
| M23 | Async & Multi-Agent | A-04, A-05 | ✅ 완료 |
| M24 | Advanced RL & Experience | A-07, A-08 | 4순위 |

---

## M21 — Bug Fix Sprint (1순위, 즉시)

**목표:** 실운영 중 발견된 버그 5건 수정

### 버그 목록

| ID | 증상 | 영향 |
|----|------|------|
| B-01 | Playbook `/run` 실행 시 PoW 블록 미생성 | 감사 추적 불완전 |
| B-02 | `verify_chain()` 오검출 — nonce 포함 블록에서 False 반환 | 체인 무결성 검증 불가 |
| B-03 | `metadata` vs `params` 키 혼용 — SubAgent 파라미터 전달 오류 | Playbook 실행 실패 |
| B-04 | stdout 절단 — 큰 출력(>4KB)에서 evidence 불완전 | 감사 추적 불완전 |
| B-05 | `risk_level=critical` 항상 dry_run 강제 — 명시적 confirmed=true 무시 | 운영 작업 불가 |

### 세부 작업 (TODO List)

- [ ] **WORK-88** B-01: Playbook run PoW 연동
  - `apps/manager-api/src/main.py` — `/playbooks/{id}/run` 엔드포인트에 `generate_proof()` 호출 추가
  - 기존 `execute-plan`과 동일한 증명 생성 패턴 적용
  - 대상 파일: `apps/manager-api/src/main.py`, `packages/pow_service/__init__.py`

- [ ] **WORK-89** B-02: verify_chain 오검출 수정
  - `packages/pow_service/__init__.py` — difficulty>0 블록 해시 계산에 nonce 포함 확인
  - `verify_chain()` 레거시 블록(difficulty=0)과 신규 블록(difficulty>0) 분기 처리 검증
  - 통합 테스트: 레거시 체인 + 신규 채굴 블록 혼합 시나리오

- [ ] **WORK-90** B-03: metadata/params 키 표준화
  - Playbook step 실행 시 `metadata` 필드와 `params` 필드 혼용 지점 전수 조사
  - `packages/playbook_engine/__init__.py` 또는 관련 파일 표준화 (params로 통일)
  - 기존 Playbook 데이터 마이그레이션 스크립트 작성

- [ ] **WORK-91** B-04: stdout 절단 수정
  - `packages/subagent_runtime/__init__.py` 또는 ToolBridge — 출력 버퍼 크기 제한 해제
  - evidence 저장 시 텍스트 크기 제한 확인 (PostgreSQL TEXT 컬럼 제한 없음)
  - 테스트: `seq 10000` 출력(>4KB) 명령 evidence 전체 저장 확인

- [ ] **WORK-92** B-05: critical dry_run 강제 조건 완화
  - `apps/manager-api/src/main.py` — `execute-plan` 로직에서 `confirmed=true` 파라미터 처리 추가
  - critical 태스크: `confirmed` 없으면 dry_run, `confirmed=true`이면 실제 실행
  - API 스펙: `execute-plan` body에 `confirmed: bool = False` 필드 추가

### 완료 기준

- [x] Playbook run 실행 후 `GET /pow/blocks?agent_id=...` 에서 블록 확인
- [x] `GET /pow/verify` 에서 신규 채굴 블록 포함 체인 `valid=true` 반환 (19/19 blocks)
- [x] params 표준화 후 기존 Playbook seed 데이터 정상 실행
- [x] stdout 4KB 이상 명령 응답 4096자 이내 전달, PoW는 full stdout 기반
- [x] `confirmed=true` critical 태스크 실제 실행 확인

---

## M22 — Playbook Engine v2 (2순위)

**목표:** Playbook 실행 엔진 일반화 및 운영 편의 기능 추가

### 개선 항목

| ID | 내용 |
|----|------|
| A-01 | 스텝별 params override — Playbook step에서 base params 덮어쓰기 |
| A-02 | execute-plan/Playbook 통합 — 동일 실행 엔진 사용 |
| A-03 | sudo 실행 가이드 — elevated privilege 안전 규칙 및 가이드 |
| A-06 | Playbook 버전 관리 — 버전 스냅샷, 히스토리, 롤백 |

### 세부 작업 (TODO List)

- [ ] **WORK-93** A-01: 스텝별 params override
  - Playbook step 실행 시 `step.params`가 있으면 base_params와 merge (step 우선)
  - `packages/playbook_engine/__init__.py` — `resolve_step_params()` 함수 추가
  - 테스트: 동일 Playbook, 스텝별 다른 params로 실행

- [ ] **WORK-94** A-02: execute-plan/Playbook 통합 실행 엔진
  - `execute-plan` tasks[]와 Playbook steps[]를 동일 `_run_task()` 함수로 처리
  - `POST /projects/{id}/execute-plan` — `playbook_id` 파라미터로 Playbook 직접 실행 지원
  - 중복 코드 제거 및 결과 일관성 확보

- [ ] **WORK-95** A-03: sudo 가이드 문서화 및 안전 규칙 구현
  - `docs/manual/agent/06-sudo-guide.md` 작성: sudoers 설정, 최소 권한 원칙
  - Manager API: sudo 명령 포함 task → `risk_level` 자동 상향 조정 로직
  - CLAUDE.md 및 agent-system-prompt.md에 sudo 주의사항 추가

- [ ] **WORK-96** A-06: Playbook 버전 관리
  - DB: `playbook_versions` 테이블 (playbook_id, version, snapshot_json, created_at)
  - API: `POST /playbooks/{id}/snapshot` — 현재 상태 버전 저장
  - API: `GET /playbooks/{id}/versions` — 버전 목록 조회
  - API: `POST /playbooks/{id}/rollback?version=N` — 특정 버전으로 롤백
  - 마이그레이션: `migrations/0011_playbook_versions.sql`

### 완료 기준

- [ ] 동일 Playbook을 스텝별 다른 params로 실행 성공
- [ ] execute-plan body에 `playbook_id` 지정 시 Playbook 단계 실행
- [ ] Playbook 스냅샷 저장 → 수정 → 롤백 흐름 확인
- [ ] sudo 가이드 문서 완성

---

## M23 — Async & Multi-Agent (3순위)

**목표:** 장기 실행 작업 비동기화 및 다중 에이전트 병렬 실행 지원

### 개선 항목

| ID | 내용 |
|----|------|
| A-04 | 비동기 장기 태스크 — background task queue, polling endpoint |
| A-05 | 멀티에이전트 병렬 실행 — 여러 SubAgent에 동시 dispatch |

### 세부 작업 (TODO List)

- [ ] **WORK-97** A-04: 비동기 태스크 큐
  - `tasks` 테이블에 `async_job_id`, `job_status` 컬럼 추가
  - `POST /projects/{id}/execute-plan` — `async=true` 파라미터 시 background 실행
  - `GET /projects/{id}/tasks/{task_id}/status` — 태스크 상태 polling endpoint
  - FastAPI `BackgroundTasks` 또는 `asyncio.create_task` 활용
  - 마이그레이션: `migrations/0012_async_tasks.sql`

- [ ] **WORK-98** A-05: 멀티에이전트 병렬 dispatch
  - `execute-plan` tasks[]에 `subagent_url` 필드 추가 (태스크별 다른 에이전트 지정)
  - `asyncio.gather()` 로 복수 SubAgent 동시 dispatch
  - 결과 집계 및 partial failure 처리 (일부 성공 시 evidence 개별 저장)
  - API: `POST /projects/{id}/execute-plan/parallel` — 병렬 실행 전용 엔드포인트

### 완료 기준

- [ ] `async=true` 태스크 → 즉시 job_id 반환 → polling으로 완료 확인
- [ ] 2개 SubAgent에 동시 dispatch → 각 evidence 독립 저장 확인
- [ ] partial failure (한 에이전트 실패) 시 성공 에이전트 evidence 유지

---

## M24 — Advanced RL & Experience (4순위)

**목표:** Q-learning 정책 품질 향상 및 경험 자동 축적 시스템 강화

### 개선 항목

| ID | 내용 |
|----|------|
| A-07 | 자동 경험 승급 — task_memory → experiences 자동 프로모션 |
| A-08 | RL Q-table 커버리지 향상 — exploration 전략, 상태 공간 확장 |

### 세부 작업 (TODO List)

- [ ] **WORK-99** A-07: 자동 경험 승급 정책
  - `packages/rl_service/__init__.py` — 학습 후 고보상 에피소드 자동 experience 저장
  - 조건: reward > threshold (기본 0.8) + 동일 state에서 N회 이상 반복 성공
  - `packages/experience_service/__init__.py` — `auto_promote_from_rl(episodes)` 함수
  - Scheduler worker에 주기적 자동 승급 태스크 등록 (daily)

- [ ] **WORK-100** A-08: RL Q-table 커버리지 향상
  - `packages/rl_service/__init__.py` — ε-greedy → UCB1 (Upper Confidence Bound) 탐색 전략으로 교체
  - 미방문 state 우선 탐색 (exploration bonus)
  - 상태 공간 확장: `asset_type` 차원 추가 (linux/windows/network) → 48→192 states
  - `GET /rl/policy` 응답에 `unvisited_states_count`, `exploration_rate` 필드 추가
  - 마이그레이션 불필요 (Q-table JSON 재생성)

### 완료 기준

- [ ] 고보상 에피소드 → experience DB 자동 저장 확인
- [ ] UCB1 탐색으로 미방문 state coverage > 80% 달성
- [ ] `GET /rl/policy` — `coverage_pct > 80` 및 `unvisited_states_count < 40` 확인

---

## 전체 TODO 요약 (M21~M24)

### M25 (Web UI 정상화) — 완료 2026-03-24
- [x] WORK-101: GET /projects 엔드포인트 + list_projects() 추가
- [x] WORK-102: evidence 필드 정규화 (body_ref→command, stdout_ref→stdout)
- [x] WORK-103: 응답 key alias (playbooks/channels/rules)
- [x] WORK-104: POST /playbook/run 글로벌 엔드포인트
- [x] WORK-105: Projects.tsx ev.risk_level 제거
- [x] WORK-106: Agents 페이지 신규 (leaderboard 테이블)
- [x] WORK-107: 빌드 (npm run build)

### M21 (Bug Fix Sprint) — 완료 2026-03-24
- [x] WORK-88: B-01 Playbook run PoW 연동
- [x] WORK-89: B-02 verify_chain 오검출 수정
- [x] WORK-90: B-03 metadata/params 키 표준화
- [x] WORK-91: B-04 stdout 절단 수정 (300 → 4096자, full stdout for PoW hash)
- [x] WORK-92: B-05 critical confirmed 파라미터 처리

### M22 (Playbook Engine v2) — 완료 2026-03-24
- [x] WORK-93: A-01 스텝별 params override (step.metadata.params > request.params)
- [x] WORK-94: A-02 execute-plan에 playbook_id 직접 지원
- [x] WORK-95: A-03 sudo 감지 + risk_level 자동 high 상향 + 가이드 문서
- [x] WORK-96: A-06 Playbook 버전 관리 (snapshot/versions/rollback API)

### M23 (Async & Multi-Agent) — 완료 2026-03-24
- [x] WORK-97: A-04 비동기 태스크 큐 (async_mode=true, polling endpoint, async_jobs 테이블)
- [x] WORK-98: A-05 멀티에이전트 병렬 dispatch (parallel=true, task별 subagent_url, ThreadPoolExecutor)

### M24 (Advanced RL & Experience) — 목표: 2026-06 이내
- [ ] WORK-99: A-07 자동 경험 승급
- [ ] WORK-100: A-08 RL Q-table 커버리지 향상

---

*문서 갱신: M21~M24 각 마일스톤 완료 시 해당 completion-report 작성 후 이 파일 업데이트*
