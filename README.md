# OpsClaw

OpsClaw는 **pi runtime 기반 정보시스템 운영/보안 작업 오케스트레이션 플랫폼**이다.
Claude Code로 OpsClaw를 실행시키고 작업을 시킬 수 있다. 
User가 대충 쓴 작업요청도 Mater Agent인 Claude Code가 명석하게 계획을 짜고 작업을 성공시킬 수 있는 프롬프트로 작업을 시킨다.
내부망 전용으로 활요하고자 한다면 Claude Code만 오픈모델로 바꾸면 된다. 
현재 완전히 폐쇄망 작업을 고려하여 Manager Agent, Sub Agent는 gpt-oss:120b, qwen3:32b, gtp-oss:20b, qwen3:8b 등 GPU에 맞는 모델을 사용할 수 있다. 

프로젝트의 핵심 목적은 자연어 요청을 내부망 운영 작업으로 바로 흘려보내는 것이 아니라,
그 요청을 **프로젝트 단위로 접수하고**, **단계별 상태 전이(plan → execute → validate → report → close)** 로 관리하며,
결과를 **evidence/report 중심으로 기록 가능한 형태**로 남기는 것이다.

---

## 1. 시스템 소개

OpsClaw는 다음 상황을 해결하기 위해 설계되었다.

- 내부망 또는 통제된 환경에서 운영/보안 작업을 구조화해서 수행하고 싶다.
- 자연어 요청을 바로 실행하지 않고, 프로젝트/단계/증빙 단위로 관리하고 싶다.
- 실행 결과를 stdout/stderr 감상이 아니라 evidence/report 로 남기고 싶다.
- 신규 업무를 코어 수정이 아니라 asset / skill / playbook 추가 중심으로 수용하고 싶다.
- 장기적으로 approval, policy, history‑aware retrieval, continuous watch 모드까지 확장하고 싶다.
- 반복/정기적인 정보시스템 작업은 Playbook 기반으로 LLM이 함부로 창의적인 작업을 통제한다.

OpsClaw는 이 목표를 위해 다음 철학을 따른다.

- **pi는 실행 런타임 엔진**
- **OpsClaw는 control‑plane**
- **asset‑first**: 모든 실행은 자산에서 시작
- **evidence‑first**: close 전에 반드시 evidence 존재
- **history‑aware, context‑light**
- **구조 우선**
- **신규 업무는 코어 수정이 아니라 skill / playbook 추가로 수용**

---

## 2. 시스템 컨셉

OpsClaw의 기본 구조는 아래와 같다.

- **Master**: 고수준 판단, 정책, 승인, 향후 경험/지식 축적과 연결될 상위 오케스트레이션 계층
- **Manager**: 프로젝트 lifecycle, 상태 전이, API, registry 접근을 담당하는 중심 control‑plane
- **SubAgent / Runtime**: 실제 환경에서 명령을 수행하는 실행 계층 (A2A HTTP 경로)
- **pi runtime**: 실제 작업 실행을 담당하는 런타임 엔진

---

## 3. 개발 계획 개요

| 마일스톤 | 내용 | 상태 |
|---|---|---|
| M0 | 설계 고정 — repo 구조, 문서/스키마/registry 기본 틀 | ✅ 완료 |
| M1 | pi Runtime Adapter — pi CLI wrapper, Ollama 연동 | ✅ 완료 |
| M2 | Manager Core — PostgreSQL project lifecycle, evidence/report, asset 최소 경로 | ✅ 완료 |
| M3 | A2A 실행 경로 — SubAgent run_script, Bootstrap installer, evidence gate, replan | ✅ 완료 |
| M4 | Asset Registry CRUD — create/get/update/delete/list, onboard, target resolve | ✅ 완료 |
| M5 | Evidence gate 강화, Validation service, Master review workflow | ✅ 완료 |
| M6 | Skill/Playbook Registry CRUD, Seed loader, 10 playbooks, Composition engine, Explain mode | ✅ 완료 |
| Pre-M7 | LangGraph 상태기계, select_assets/resolve_targets 스테이지, Approval Gate, Policy Engine | ✅ 완료 |
| M7 | Batch/Continuous Execution — scheduler, watch runner | ✅ 완료 |
| M8 | History/Experience/Retrieval — 4-layer memory, task_memory, experience promotion, FTS retrieval | ✅ 완료 |
| M9 | RBAC, Audit, Monitoring, Reporting, Backup | ✅ 완료 |
| M10 | Notification & Alerting — webhook/rule-based event routing | ✅ 완료 |
| M11 | Integration Fixes — pi adapter, ToolBridge, A2A LLM 호출 수정, subagent 실 배포 | ✅ 완료 |
| M12 | Real-System Operation Test — secu/web/siem 연결, nftables 설정, 실운영 문제 발굴 | ✅ 완료 |
| M13 | Operational Hardening — Bootstrap, Playbook API, dispatch LLM 변환, pi wake-up 자동화 | ✅ 완료 |
| M14 | Agent Role Clarity & Workflow — Master/Manager/SubAgent 역할 명확화, 완료보고서 자동 생성 | 🔲 예정 |
| M15 | Platform Modes — 직접구동/Claude Code/Codex 모드 최적화, Master 역할 분리 | 🔲 예정 |
| M16 | Web UI/Dashboard — 설정·에이전트 등록·메신저 연동 웹 UI | 🔲 예정 |
| M17 | Pi Freeze Bug Fix — pi 멈춤 현상 근본 원인 분석 및 패치 | 🔲 예정 |
| M18 | Proof of Work & Blockchain Reward — 작업증명, 블록체인 보상, Audit DB, 작업 Replay | 🔲 예정 |
| M19 | Skill/Tool/Experience 실동작 검증 — 실질적 기능 검증 및 보완 구현 | 🔲 예정 |
| M20 | User & Agent Manual — 사용자/에이전트용 운용 매뉴얼 완성 | 🔲 예정 |

---

## 4. 현재 구현 상태 (M13 기준)

### 구현 완료

**Project Lifecycle**
- PostgreSQL 기반 project create/get
- plan → execute → validate → report → close 상태 전이
- replan: execute/validate/report → plan 전이 (이유 기록)
- evidence gate: close 전 evidence 필수

**Evidence & Validation**
- minimal evidence 생성 (command / stdout / stderr / exit_code)
- project evidence 조회 및 요약 (total / success_count / failure_count / success_rate)
- validation check: 명령 실행 → expected_contains / expected_exit_code 검증 → evidence + validation_run 기록
- validation status: all_passed / has_failures / inconclusive / no_runs

**Asset Registry**
- asset CRUD (create / get / update / delete / list)
- asset 온보딩 워크플로우 (identity check → create → bootstrap → target resolve)
- target 자동 도출 (subagent ping → targets 테이블 upsert)
- bootstrap: SSH → `install.sh` → systemd 서비스 등록

**A2A Execution**
- Manager → SubAgent HTTP dispatch (`POST /a2a/run_script`)
- SubAgent: subprocess 실제 실행, timeout 처리
- `A2AClient`: run_script() wraps HTTP call

**Master Review**
- approve / reject / needs_replan 기록
- auto_replan 옵션
- escalate (rejected review 기록)

**LangGraph 상태기계**
- `build_project_graph()` — StateGraph 컴파일
- `run_project_graph()` — 자율 실행 (plan → select_assets → resolve_targets → approval_gate → execute → validate → report → close)
- select_assets / resolve_targets 정식 스테이지 추가 (bypass 경로로 기존 호환성 유지)

**Approval Gate**
- `check_requires_approval()` — risk_level high/critical은 approved master_review 필요
- `require_approval_cleared()` — execute 전 자동 검증
- `GET /projects/{id}/approval` — 승인 상태 조회

**Policy Engine**
- env별 정책 테이블 (prod / staging / lab / default)
- `check_policy()`, `enforce_policy()` — 정책 위반 시 PolicyViolation

**Registry (Tool / Skill / Playbook)**
- Tool CRUD with upsert (ON CONFLICT DO UPDATE)
- Skill CRUD with required_tools / optional_tools
- Playbook CRUD with steps, execution_mode, risk_level, dry_run_supported
- Seed loader: YAML → DB upsert (6 tools, 6 skills, 10 playbooks)
- Composition engine: playbook → step → skill → tool 전체 트리 resolve
- Explain mode: 마크다운 사람 가독 설명

**Batch/Continuous Execution (M7)**
- schedule CRUD + croniter cron next-run 계산
- get_due_schedules / execute_due_schedule 배치 사이클
- watch_job / watch_event / incident CRUD
- run_watch_check: subprocess 실행 → 연속 실패 threshold → incident 자동 생성
- Scheduler Worker + Watch Worker 폴링 루프
- `/schedules`, `/watchers`, `/incidents` API 라우터

**History/Experience/Retrieval (M8)**
- history_service: ingest_event / ingest_stage_event / get_project_history / get_asset_history
- experience_service: build_task_memory / promote_to_experience / create_experience / list_experiences
- retrieval_service: index_document / search_documents (FTS + ILIKE fallback) / reindex_project / get_context_for_project
- Manager API: `/projects/{id}/history`, `/experience`, `/projects/{id}/context`

**RBAC / Audit / Monitoring / Reporting / Backup (M9)**
- RBAC: roles + actor_roles 테이블, 4개 기본 역할 (admin/operator/viewer/auditor)
- rbac_service: create_role / assign_role / get_actor_permissions / check_permission (`*` wildcard 지원)
- audit_service: log_audit_event / query_audit_logs / export_audit_json / export_audit_csv
- monitoring_service: get_system_health (healthy/degraded) / get_operational_metrics
- reporting_service: generate_project_report / export_evidence_pack / export_evidence_pack_json
- backup_service: create_backup (pg_dump) / list_backups / get_backup_info
- Manager API: `/admin/*` (12개 엔드포인트), `/reports/*` (3개 엔드포인트)

**Notification & Alerting (M10)**
- notification_service: create_channel / create_rule / fire_event / list_notification_logs
- 채널 타입: webhook (HTTP POST), log (stdout), email (smtplib STARTTLS/SSL), Slack (Bot Token + chat.postMessage)
- Rule-based 라우팅: event_type 매칭 + wildcard `*` + filter_conditions 지원
- Integration hooks: watch_service.create_incident() → `incident.created`, scheduler_service.execute_due_schedule() → `schedule.failed`
- Manager API: `/notifications/*` (12개 엔드포인트), API v0.10.0-m10

**Integration Fixes & Real Deployment (M11)**
- pi_adapter: subprocess 제거, httpx로 Ollama 직접 호출 (`http://192.168.0.105:11434/v1`)
- ToolBridge.run_tool: subprocess 실행 구현, exit_code 127/124 처리
- A2A invoke_llm / analyze 500 에러 수정
- Email/Slack 알림 실 구현 (OldClaw 봇, #bot-cc 채널)
- secu/web/siem 3개 시스템에 subagent-runtime 수동 배포 완료 (systemd, port 8002)

**Real-System Operation Test (M12)**
- opsclaw → secu/web/siem subagent 연결 검증
- secu: nftables 설치/설정 완료 (내부망 게이트웨이 10.20.30.1, NAT, forward 룰)
- runtime/invoke LLM 호출 → GPU 서버 정상 동작 확인
- a2a/run_script 직접 dispatch 정상 동작 확인
- 실운영 테스트 통해 M13 개발 대상 7개 문제 발굴

**Operational Hardening (M13)**
- Playbook CRUD API: `POST /playbooks`, `PUT /playbooks/{id}`, `DELETE /playbooks/{id}`, `POST /playbooks/{id}/steps`
- Bootstrap 재작성: `deploy/bootstrap/install.sh` — git clone 기반 실제 subagent-runtime 설치, health check 자동 수행, `/var/log/opsclaw-bootstrap.log` 기록
- Bootstrap SSH 인증: sshpass 제거 → paramiko 기반 패스워드/키 인증 (`POST /assets/{id}/bootstrap` body에 `ssh_pass` 지원)
- dispatch LLM 변환: `mode` 필드 (auto/shell/adhoc). auto 모드에서 한글/자연어 자동 감지 → LLM으로 bash script 변환 후 실행
- pi wake-up 자동화: timeout/빈응답 시 최대 2회 재시도, `wake up!` 자동 전송
- pi 기본 timeout: 120초 → 300초 (환경변수 `OPSCLAW_PI_DEFAULT_TIMEOUT_S` 으로 조절)
- asset history 자동 기록: dispatch 완료 시 `history_service.ingest_event()` 자동 호출, `GET /assets/{id}/history` 조회 가능
- asset `expected_subagent_port` 기본값: 8001 → 8002

### 아직 남아 있는 것

- CI 파이프라인 확대
- 인프라 구축 재개 (web/siem enp4s0 케이블 확인 후): Docker+JuiceShop+BunkerWeb(web), Wazuh(siem), Suricata IPS(secu)

---

## 5. 저장소 구조 개요

```
apps/
  manager-api/src/main.py   # FastAPI Manager control-plane API
  master-service/src/main.py # Master review/replan/escalate API
  subagent-runtime/src/main.py # SubAgent A2A 실행 런타임

packages/
  project_service/           # project lifecycle, evidence, dispatch
  asset_registry/            # asset CRUD, target resolve, onboard
  evidence_service/          # evidence 조회/요약/gate
  validation_service/        # validation check, run, status
  master_review/             # review CRUD
  registry_service/          # tool/skill/playbook CRUD, composition, explain
  graph_runtime/             # 상태 전이, replan 허용 범위
  a2a_protocol/              # A2AClient, A2ARunRequest/Result
  bootstrap_service/         # SSH bootstrap
  pi_adapter/                # pi runtime 연동 계층

migrations/                  # PostgreSQL 스키마 (4개 마이그레이션)
seed/playbooks/              # 10개 playbook YAML 정의
tools/dev/                   # 개발용 smoke / seed 스크립트
deploy/bootstrap/            # install.sh (원격 SubAgent 설치)
docs/                        # 마일스톤별 계획/완료 보고서
```

---

## 6. 실행 및 검증

### 전체 컴파일 확인

```bash
python3 -m compileall apps packages tools
```

### M6 통합 smoke

```bash
PYTHONPATH=. python3 tools/dev/m6_integrated_smoke.py
```

### M5 통합 smoke (evidence gate, validation, master review)

```bash
PYTHONPATH=. python3 tools/dev/m5_integrated_smoke.py
```

### Seed loader

```bash
PYTHONPATH=. python3 tools/dev/seed_loader.py           # 실제 적재
PYTHONPATH=. python3 tools/dev/seed_loader.py --dry-run # 확인만
```

---

## 7. 작업 운영 규칙

이 저장소의 작업은 아래 규칙을 따른다.

- main 브랜치만 사용
- 코어 설계와 코드 본문은 사람이 정의
- 에이전트는 반영 / 실행 / 테스트 / 결과 보고 담당
- 검수 없는 완료 주장 금지
- 검수/지시/작업결과는 문서로 남김

문서 체계:

- `docs/mX/opsclaw-mX-completion-report.md` — 마일스톤 완료 보고서
- `docs/verification/WORK-XX.md` — 개별 작업 상세 기록

---

## 8. 주의

README는 현재 구현 상태를 반영하는 대표 문서다.
없는 기능을 완성된 것처럼 적지 않는다.
M14 이후는 **계획 범위**이지 현재 완료 기능이 아니다.

---

## 9. 향후 개선 방향 (M14~M20)

세부 수행 계획: [`docs/roadmap.md`](docs/roadmap.md)

### M14 — Agent Role Clarity & Workflow

에이전트 계층의 역할과 책임을 코드 수준에서 명확히 분리하고 end-to-end 검증한다.

**핵심 흐름:**
```
사용자 요구사항
  → Master: 요구사항 이해 → 전체 계획 수립 → Playbook 단위 분해 → 지시 프롬프트 생성
  → Manager: Playbook 순서에 따라 도구 설치/코드 작성/설정 등 작업 계획 수행
  → SubAgent: 각 시스템에서 명령 실행 → 결과 Manager에게 반환
  → Manager: 결과 확인 → 다음 작업 전달 또는 오류 처리
  → Master: Playbook 단위 작업 검수 → 완료보고서(메타데이터, 작업내역, 이슈, 다음작업 참고사항) 생성
  → 다음 유사 Playbook 생성 시 완료보고서 참조하여 동일 방식 적용
```

**주요 TODO:**
- Master 지시 프롬프트 생성 엔진 구현
- Manager 작업 계획 실행 루프 정형화 (tool install → code → config → validate)
- Playbook 완료보고서 자동 생성 (`POST /projects/{id}/completion-report`)
- 완료보고서 DB 저장 및 다음 Playbook 생성 시 RAG 참조 연동
- end-to-end 시나리오 테스트 (신규 시스템 온보딩 ~ 작업 완료 ~ 보고서)

---

### M15 — Platform Modes

OpsClaw를 구동하는 방식에 따라 Master 역할이 달라진다. 두 모드를 명시적으로 지원한다.

**Mode A — 직접구동 (Native Master):**
- 사용자가 Web UI 또는 API로 작업 요청
- OpsClaw 내장 Master Agent(LLM)가 계획 수립 및 Manager 지시

**Mode B — AI-Driven (External Master):**
- Claude Code, Codex, Claude Co-work 등 외부 AI가 Master 역할 수행
- 사용자가 대략적인 요청을 외부 AI에게 전달
- 외부 AI가 OpsClaw Manager API를 직접 호출하여 작업 오케스트레이션
- OpsClaw는 실행 control-plane 역할에 집중

**주요 TODO:**
- Manager API에 `master_mode` 컨텍스트 필드 추가 (native / external)
- External Master용 OpenAPI spec 정리 및 LLM-friendly 설명 추가
- Claude Code용 CLAUDE.md 오케스트레이션 가이드 작성
- Mode B용 system prompt 템플릿 제공

---

### M16 — Web UI/Dashboard

현재 API 전용인 OpsClaw에 웹 기반 UI를 추가한다.

**주요 기능:**
- 에이전트(SubAgent) 등록/상태 모니터링
- 프로젝트 생성, 상태 추적, evidence 조회
- Playbook 목록/생성/편집
- 알림 채널(Slack/Email/Webhook) 설정
- RBAC 사용자/역할 관리
- 작업 실행 이력 및 Replay 뷰어
- 실시간 SubAgent 상태 대시보드

**기술 스택 후보:** React + Vite / FastAPI 정적 서빙, WebSocket 실시간 업데이트

---

### M17 — Pi Freeze Bug Fix

실운영에서 반복적으로 발생하는 pi 멈춤 현상의 근본 원인을 코드에서 찾아 패치한다.

**조사 대상:**
- `packages/pi_adapter/runtime/client.py` — httpx 스트리밍 응답 처리 로직
- Ollama API 응답 지연/빈 청크 처리
- 동시 요청 시 GPU 메모리 포화로 인한 응답 중단
- 스트림 종료 신호 누락 시 무한 대기

**주요 TODO:**
- pi_adapter 응답 수신 로직 분석 및 재현 시나리오 작성
- 스트림 chunk 타임아웃 세분화 (연결/첫응답/청크간격 분리)
- Ollama keep-alive 및 연결 재사용 설정 검토
- 패치 후 장시간 부하 테스트

---

### M18 — Proof of Work & Blockchain Reward

에이전트가 수행한 작업에 대한 증명과 보상 체계를 도입한다.

**개념:**
- 각 SubAgent의 작업 수행 결과(evidence)를 블록체인에 기록 → 위변조 불가 작업증명
- 작업량/품질 기반 보상 토큰 지급 (on-chain 또는 내부 포인트)
- 작업 전체 내역 DB 저장: Audit 강화 및 책임 추적성
- 웹 UI에서 작업 중계/Replay 기능

**주요 TODO:**
- 작업증명 데이터 구조 설계 (task_id, agent_id, evidence_hash, timestamp, signature)
- 경량 블록체인 또는 분산 원장 연동 검토 (Hyperledger Fabric / 자체 Merkle chain)
- `proof_of_work` 테이블 및 마이그레이션 추가
- 보상 토큰 회계 서비스 구현
- 작업 Replay API: `GET /projects/{id}/replay`
- 웹 UI Replay 뷰어

---

### M19 — Skill/Tool/Experience 실동작 검증

현재 DB에 등록된 Skill, Tool, Experience 레코드가 실제 코드에서 올바르게 동작하는지 검증하고 미동작 부분을 보완한다.

> ※ OpsClaw의 Skill/Tool은 Claude의 skill과 다르다: OpsClaw의 Tool은 실행 가능한 shell 명령/스크립트 단위이고, Skill은 Tool 조합으로 특정 목적을 달성하는 절차 단위이다. Experience는 과거 작업 결과에서 추출한 패턴/교훈이다.

**주요 TODO:**
- `registry_service` composition engine end-to-end 실행 테스트
- Skill 실행 시 required_tools 실제 tool 실행 여부 검증
- Experience 생성 → 검색 → Playbook 생성 참조 전체 흐름 테스트
- 미구현/미연결 부분 보완 구현
- `GET /skills/{id}/execute` dry-run 모드 구현

---

### M20 — User & Agent Manual

**사용자 매뉴얼:**
- OpsClaw 설치 및 초기 설정 가이드
- 작업 요청 방법 (Web UI / API / Claude Code를 통한 방법)
- Playbook 작성 가이드
- 알림/연동 설정 가이드
- 트러블슈팅 FAQ

**에이전트 운용 매뉴얼:**
- SubAgent 신규 시스템 설치 가이드 (install.sh)
- Master/Manager/SubAgent 프롬프트 작성 가이드
- 커스텀 Skill/Tool/Playbook 추가 방법
- A2A 프로토콜 연동 가이드

---

## 10. 개발 우선순위 요약

| 우선순위 | 마일스톤 | 이유 |
|---------|---------|------|
| 1순위 | M17 (Pi Freeze) | 현재 실운영 가장 큰 장애 요인 |
| 2순위 | M14 (Agent Workflow) | 핵심 기능 완성도, 나머지 모든 마일스톤의 기반 |
| 3순위 | M19 (Skill/Tool 검증) | 이미 구현된 기능 실동작 확인, 기술 부채 해소 |
| 4순위 | M15 (Platform Modes) | 외부 AI 연동 실용성 향상 |
| 5순위 | M16 (Web UI) | 사용성 대폭 향상, 非개발자 접근성 |
| 6순위 | M18 (Blockchain PoW) | 혁신적이나 구현 복잡도 높음 |
| 7순위 | M20 (Manual) | M14~M19 완료 후 작성이 의미 있음 |
