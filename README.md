# OpsClaw

## 1. 시스템 소개

시스템 소개

OpsClaw는 pi runtime 기반 정보시스템 운영·보안 작업 오케스트레이션 플랫폼이다.
Pi(https://github.com/badlogic/pi-mono/)는 OpenClaw의 코어에 SDK를 결합하여 하네스를 구현할 수 있도록 만든 오픈소스 런타임이며, OpsClaw는 이를 기반으로 서버, 네트워크, 보안, 클라우드 구축 및 운영 업무를 체계적으로 통제하고 수행하도록 설계되었다.

OpsClaw의 핵심은 사용자의 자연어 요청을 단순히 곧바로 내부망 작업으로 흘려보내는 것이 아니다.
대신 요청을 먼저 프로젝트 단위로 접수하고, 이를 관리 가능한 작업 체계로 구조화한 뒤, plan → execute → validate → report → close의 단계별 상태 전이를 통해 작업을 통제한다. 즉, 요청을 즉시 실행하는 자동화 도구가 아니라, 작업의 목적·대상·절차·검수 결과를 모두 관리 가능한 형태로 다루는 운영 플랫폼에 가깝다.

OpsClaw는 일반적인 에이전트 프로그램과도 구조적으로 다르다. 작업 대상 시스템을 먼저 Asset으로 등록하고, 대상 환경에 Subagent를 설치한 뒤, Playbook 기반으로 작업을 수행한다. 이 방식은 작업 대상을 명확히 식별하고, 사전에 정의된 절차와 검증 가능한 실행 흐름 안에서 작업을 수행하게 하므로, 장기간 유지에 따른 높은 신뢰성과 재현성, 엄격한 작업 증명 체계를 확보할 수 있다. 그 결과 OpsClaw는 사람의 숙련도에 의존하던 운영·보안 작업을 보다 일관되고 감사 가능한 방식으로 수행하도록 만든다.

특히 OpsClaw는 모든 결과를 evidence/report 중심으로 남기는 것을 중요하게 본다. 작업 과정에서 생성된 명령 실행 기록, 수집 결과, 오류, 조치 내역, 검수 결과를 단순 로그가 아니라 증빙 가능한 산출물로 저장함으로써, 나중에 누가 무엇을 왜 수행했는지 추적할 수 있도록 한다. 이를 통해 감사(Audit), 책임추적성(Accountability), 사후 검토, 재현 가능한 운영 절차 수립이 가능해진다.

또한 모든 작업 이력과 프롬프트, 상태 변화, 결과물은 데이터베이스에 축적되며, 작업이 완료된 이후에는 작업 과정, 시행착오, 이슈, 결과 검수 내용을 종합하여 RAG 기반의 Experience Layer로 발전한다. 이 Experience Layer는 이후 유사한 작업이 들어왔을 때 참고 가능한 운영 지식으로 활용되며, 에이전트가 과거의 성공 사례와 실패 사례를 기반으로 더 일관되고 정교한 방식으로 작업을 수행하도록 돕는다.

OpsClaw의 또 다른 중요한 축은 블록체인 기반 보상 체계이다. 여기서 블록체인은 단순 기록 수단이 아니라, 작업 수행에 대한 대가 지급 기능을 담당한다. 즉, 작업의 수행 결과와 검수 내용, 증빙 자료를 바탕으로 정당한 보상이 연결되도록 설계함으로써, 플랫폼 내부에서 작업 품질과 책임 있는 수행을 유도하는 역할을 한다. 향후에는 여기에 강화학습(RL) 을 결합하여, 에이전트가 보상 극대화 전략을 스스로 학습하고 더 나은 실행 방식을 선택하도록 발전시킬 수 있다. 이는 단순 자동화를 넘어, 시간이 지날수록 품질이 개선되는 자기강화형 운영 구조를 지향한다.

OpsClaw는 Claude Code를 통해 실행하고 작업을 지시할 수 있다. 사용자가 다소 거칠거나 불완전하게 작성한 요청을 입력하더라도, 상위 에이전트가 이를 해석해 명확한 계획과 실행 가능한 작업 지시로 정제하고, 적절한 프로젝트 및 실행 단계로 편입시켜 작업을 진행할 수 있다. 또한 내부망 전용 운영을 고려할 경우 상위 모델만 교체하는 방식으로 폐쇄망 구조에 맞게 조정할 수 있으며, Manager Agent와 Sub Agent에는 gpt-oss:120b, qwen3:32b, gpt-oss:20b, qwen3:8b 등 GPU 자원에 맞는 다양한 모델을 적용할 수 있도록 설계하고 있다.

결국 OpsClaw는 자연어 기반 요청을 신뢰할 수 있는 운영 작업으로 바꾸기 위해, 프로젝트 단위 접수, 단계별 상태 관리, Asset/Subagent/Playbook 기반 실행, evidence/report 중심 기록, 보상과 학습을 통한 품질 개선을 하나의 플랫폼 안에 통합한 시스템이다.
이는 단순히 “에이전트가 대신 일한다”는 수준을 넘어, 작업이 어떻게 계획되고, 어떻게 실행되었으며, 무엇으로 검증되었고, 어떤 결과가 남았는지를 끝까지 설명할 수 있는 구조를 지향한다. 그리고 이러한 축적이 반복될수록, OpsClaw는 최종적으로 사람이 세부 절차를 직접 통제하지 않아도 스스로 운영을 수행하는 자율 시스템(Self System) 에 가까워지게 된다.

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
| M14 | Agent Role Clarity & Workflow — Master/Manager/SubAgent 역할 명확화, 완료보고서 자동 생성 | ✅ 완료 |
| M15 | Platform Modes — master_mode(native/external), External Master 가이드, Mode B 통합 테스트 | ✅ 완료 |
| M16 | Web UI/Dashboard — React+Vite SPA, Projects/Playbooks/Replay/PoW/Settings | ✅ 완료 |
| M17 | Pi Freeze Bug Fix — pi 멈춤 현상 근본 원인 분석 및 패치 | ✅ 완료 |
| M18 | Proof of Work & Blockchain Reward — 작업증명, 블록체인 보상, Audit DB, 작업 Replay | ✅ 완료 |
| M19 | Skill/Tool/Experience 실동작 검증 — 실질적 기능 검증 및 보완 구현 | ✅ 완료 |
| M20 | User & Agent Manual — 사용자/에이전트용 운용 매뉴얼 완성 | ✅ 완료 |

---

## 4. 빠른 시작 (신규 시스템)

Linux + Claude Code가 설치된 환경에서 OpsClaw를 구동하는 가장 빠른 방법이다.

### 사전 조건 (수동)

```bash
# Docker 설치 (없으면)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# 로그아웃 후 재로그인

# Python 3.11 설치 (없으면)
sudo apt install -y python3.11 python3.11-venv

# 저장소 클론
git clone https://github.com/mrgrit/opsclaw.git
cd opsclaw
```

### Claude Code에 지시

`opsclaw/` 디렉토리에서 `claude`를 실행한 뒤 아래 한 줄 입력:

```
CLAUDE.md를 읽고 이 시스템에 OpsClaw를 처음부터 구동해줘.
Python venv 생성, 의존성 설치, PostgreSQL 기동, 마이그레이션 적용,
서비스 실행, health check까지 완료해줘.
```

Claude Code가 `CLAUDE.md`를 읽고 venv → DB → 마이그레이션 → 서비스 기동 → health check까지 자동 처리한다.

### Web UI 빌드 (선택)

`dist/`는 gitignore 대상이므로 clone 후 별도 빌드가 필요하다:

```
apps/web-ui/ 에서 npm install && npm run build 실행해줘
```

빌드 완료 후 `http://localhost:8000/app/` 에서 Web UI 접근 가능.

> 상세 설치 가이드: `docs/manual/user/01-installation.md`

---

## 5. 현재 구현 상태 (M20 기준)

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

**Agent Role & Workflow (M14)**
- Master 지시 프롬프트 생성 엔진 (`POST /master/generate-instruction`)
- Manager execute-plan 엔드포인트 (`POST /projects/{id}/execute-plan`)
- Playbook 완료보고서 자동 생성 (`POST /projects/{id}/completion-report`)
- 완료보고서 RAG 참조 연동 (동일 요청 반복 시 과거 보고서 자동 참조)

**Platform Modes (M15)**
- `projects.master_mode` 컬럼 추가 (native | external)
- External Master 가이드 (`docs/api/external-master-guide.md`)
- Claude Code 오케스트레이션 가이드 (`CLAUDE.md`)
- AI 에이전트 시스템 프롬프트 (`docs/agent-system-prompt.md`)
- Mode B 통합 테스트 16/16 PASS

**Pi Freeze Fix (M17)**
- chunk timeout 세분화 (connect 10s / read 30s / write 10s)
- Ollama keep_alive "10m" 적용
- httpx connection pool (max_connections=5)
- 부하 테스트 6/6 성공

**Skill/Tool/Experience 검증 (M19)**
- Tool/Skill/Playbook 실행 경로 end-to-end 검증
- skill_tools 연결 테이블 12개 행 적재
- Experience 생성 → FTS 검색 → 참조 흐름 정상 동작
- 통합 smoke 테스트 30/30 PASS

**Web UI/Dashboard (M16)**
- React + Vite SPA (`apps/web-ui/`)
- 페이지: Projects, Playbooks, Replay, PoW Blocks, Settings
- Manager API 연동 (proxy via FastAPI `/app/` static serving)
- `npm run build` → `dist/` → Manager API `/app/` 경로로 서빙

**Proof of Work & Blockchain Reward (M18)**
- PoW 블록 생성: SHA-256 nonce 채굴, target difficulty 제어
  - `sha256(prev_hash + evidence_hash + ts + nonce)`가 difficulty개 leading zero hex 만족할 때까지 nonce 반복
  - 기본 difficulty=4 (환경변수 `OPSCLAW_POW_DIFFICULTY`로 조정 가능)
- 작업 완료 시 reward 블록 자동 생성 (execute-plan 연동)
- RL 보상 신호: base_score(성공/실패) + speed_bonus + risk_penalty → reward_ledger 누적
- Blockchain Audit DB: `proof_of_work` 테이블, chain 무결성 검증 (위변조/난이도 미충족 감지)
- Replay API: 과거 프로젝트 실행 흐름 재현 (`/projects/{id}/replay`)
- RL 연결 기반: PoW reward → 강화학습 보상 신호 설계 기반 마련

**User & Agent Manual (M20)**
- 사용자 매뉴얼: `docs/manual/user/` (설치~트러블슈팅 7개 파일)
- 에이전트 매뉴얼: `docs/manual/agent/` (SubAgent 설치~A2A 프로토콜 5개 파일)
- AI 에이전트 시스템 프롬프트: `docs/agent-system-prompt.md`

### 아직 남아 있는 것

- CI 파이프라인 확대
- 인프라 구축 재개 (web/siem enp4s0 케이블 확인 후): Docker+JuiceShop+BunkerWeb(web), Wazuh(siem), Suricata IPS(secu)
- RL 에이전트 학습 루프 연결 (M18 PoW reward → 강화학습 실제 연동)

---

## 6. 저장소 구조 개요

```
apps/
  manager-api/src/main.py      # FastAPI Manager control-plane API (:8000)
  master-service/src/main.py   # Master review/replan/escalate API (:8001)
  subagent-runtime/src/main.py # SubAgent A2A 실행 런타임 (:8002)

packages/
  project_service/             # project lifecycle, evidence, dispatch, execute-plan
  asset_registry/              # asset CRUD, target resolve, onboard
  evidence_service/            # evidence 조회/요약/gate
  validation_service/          # validation check, run, status
  master_review/               # review CRUD, instruction prompt 생성
  registry_service/            # tool/skill/playbook CRUD, composition, explain
  graph_runtime/               # 상태 전이, replan 허용 범위
  a2a_protocol/                # A2AClient, A2ARunRequest/Result
  bootstrap_service/           # SSH bootstrap
  pi_adapter/                  # pi runtime 연동 계층 (Ollama httpx streaming)
  completion_report_service/   # 완료보고서 생성/조회/RAG 참조

migrations/                    # PostgreSQL 스키마 (0001~0008)
seed/playbooks/                # 10개 playbook YAML 정의
tools/dev/                     # 개발용 smoke / seed 스크립트
scripts/                       # 통합 테스트 스크립트
deploy/bootstrap/              # install.sh (원격 SubAgent 설치)
docs/
  api/                         # external-master-guide.md
  manual/user/                 # 사용자 매뉴얼 (01~07)
  manual/agent/                # 에이전트 매뉴얼 (01~05)
  agent-system-prompt.md       # AI 에이전트 주입용 시스템 프롬프트
  mX/                          # 마일스톤별 완료보고서
CLAUDE.md                      # Claude Code 오케스트레이션 가이드
```

---

## 7. 실행 및 검증

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

## 8. Proof of Work & 보상 체계

OpsClaw에서 **"채굴"이란 에이전트가 작업을 수행하는 행위 자체**다.
별도의 채굴 명령은 없으며, `execute-plan`으로 Task를 실행하면 자동으로 PoW 블록이 생성되고 보상이 지급된다.

### 핵심 개념

| 개념 | OpsClaw에서의 의미 |
|------|------------------|
| **채굴(Mining)** | SubAgent가 Task를 실행하는 것. 작업 완료 = 블록 1개 생성 |
| **블록(Block)** | "이 에이전트가 이 작업을 실제로 수행했다"는 위변조 불가능한 증명 |
| **Nonce** | block_hash가 difficulty개의 leading zero를 만족할 때까지 반복 탐색한 값 |
| **Difficulty** | 채굴 난이도. 기본 4 (해시가 `0000...`으로 시작해야 함) |
| **보상(Reward)** | 작업 성공/실패, 속도, 위험도에 따라 자동 계산되는 RL 신호 |
| **Ledger** | 에이전트별 누적 잔액. 보상의 총합 |

### 작업 흐름

```
사용자가 작업 지시
    ↓
execute-plan → SubAgent가 Task 실행 (echo, apt install, 등)
    ↓
Task 완료 (exit_code, stdout, stderr 수집)
    ↓
generate_proof() 자동 호출
    ├─ evidence_hash = sha256(stdout + stderr + exit_code)
    ├─ nonce 채굴: sha256(prev_hash + evidence_hash + ts + nonce)가
    │             "0000"(difficulty=4)으로 시작하는 값 탐색
    ├─ PoW 블록 INSERT (proof_of_work 테이블)
    ├─ 보상 계산 → task_reward 기록
    └─ reward_ledger UPSERT (누적 잔액 갱신)
    ↓
블록체인에 기록 완료 → 위변조 불가능한 작업 증명 + 보상 확정
```

### 보상 계산 규칙

| 항목 | 조건 | 값 |
|------|------|-----|
| **base_score** | 성공 (exit_code=0) | +1.0 |
| | 실패 (exit_code≠0) | -1.0 |
| **speed_bonus** | 성공 && <5초 | +0.3 |
| | 성공 && <30초 | +0.15 |
| | 성공 && <60초 | +0.05 |
| **risk_penalty** | 실패 && risk=high | -0.1 |
| | 실패 && risk=critical | -0.2 |
| **quality_bonus** | (향후 human feedback 연결) | 0.0 |
| **total_reward** | 위 항목의 합계 | reward_ledger에 누적 |

### 블록체인 무결성 검증

```bash
# 에이전트의 전체 블록 체인 검증
curl "http://localhost:8000/pow/verify?agent_id=http://localhost:8002"

# 결과: {"valid": true, "blocks": 11, "tampered": []}
```

검증 항목:
- **block_hash 재계산**: 저장된 해시와 재계산 결과 일치 여부
- **difficulty 충족**: block_hash가 difficulty개의 leading zero로 시작하는지
- **prev_hash 체인 연결**: 이전 블록의 block_hash와 현재 블록의 prev_hash 일치 여부

위변조 감지 시: `tampered` 배열에 `block_hash_mismatch`, `difficulty_not_met`, `chain_broken` 중 하나의 reason과 함께 기록.

### PoW API 엔드포인트

```bash
# PoW 블록 조회
GET /pow/blocks?agent_id=<url>&limit=50

# 단건 블록 조회
GET /pow/blocks/{pow_id}

# 체인 무결성 검증
GET /pow/verify?agent_id=<url>

# 보상 랭킹 (상위 에이전트)
GET /pow/leaderboard?limit=10

# 에이전트 잔액 + 최근 보상 이력
GET /rewards/agents?agent_id=<url>

# 프로젝트별 PoW 블록
GET /projects/{id}/pow

# 프로젝트 작업 Replay (타임라인)
GET /projects/{id}/replay
```

### 설정

| 환경변수 | 기본값 | 설명 |
|---------|--------|------|
| `OPSCLAW_POW_DIFFICULTY` | 4 | leading zero hex 개수 (4 ≈ 65K회 시행, ~0.03초) |
| `OPSCLAW_POW_MAX_NONCE` | 10,000,000 | 무한루프 방지 안전장치 |

### 향후 발전 방향

현재 PoW reward는 RL(강화학습) 보상 신호로 설계되어 있다.
향후 `task_reward` 데이터를 기반으로 에이전트의 policy network를 학습시켜,
더 나은 `instruction_prompt` 선택, 적절한 `risk_level` 판단 등 자기강화형 운영을 실현할 계획이다.

---

## 9. 작업 운영 규칙

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

## 10. 주의

README는 현재 구현 상태를 반영하는 대표 문서다.
없는 기능을 완성된 것처럼 적지 않는다.
M0~M20 전 마일스톤이 완료된 상태이며, "아직 남아 있는 것" 항목만 미구현이다.

---

## 11. 향후 개선 방향 (M14~M20)

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

## 12. 개발 우선순위 요약

| 우선순위 | 마일스톤 | 이유 |
|---------|---------|------|
| 1순위 | M17 (Pi Freeze) | 현재 실운영 가장 큰 장애 요인 |
| 2순위 | M14 (Agent Workflow) | 핵심 기능 완성도, 나머지 모든 마일스톤의 기반 |
| 3순위 | M19 (Skill/Tool 검증) | 이미 구현된 기능 실동작 확인, 기술 부채 해소 |
| 4순위 | M15 (Platform Modes) | 외부 AI 연동 실용성 향상 |
| 5순위 | M16 (Web UI) | 사용성 대폭 향상, 非개발자 접근성 |
| 6순위 | M18 (Blockchain PoW) | 혁신적이나 구현 복잡도 높음 |
| 7순위 | M20 (Manual) | M14~M19 완료 후 작성이 의미 있음 |
