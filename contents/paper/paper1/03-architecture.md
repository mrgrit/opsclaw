# 3. 시스템 아키텍처 (System Architecture)

본 장에서는 OpsClaw의 설계 원칙, 3계층 위임 아키텍처, 프로젝트 라이프사이클 상태 머신, 개념 계층, 서비스 경계를 기술한다.

## 3.1 설계 원칙

OpsClaw의 아키텍처는 다음 세 가지 핵심 원칙에 기반한다.

**원칙 1: 위임 분리 (Delegation Separation).** 계획(planning)과 실행(execution)을 명확히 분리하여, 고비용 추론을 담당하는 Master와 실제 명령을 수행하는 SubAgent가 서로의 영역을 침범하지 않도록 한다. 이를 통해 (1) 감사 시 누가 어떤 판단을 내렸고 무엇이 실행되었는지를 분리 추적할 수 있으며, (2) Master LLM을 교체하더라도 실행 계층에 영향을 주지 않는다.

**원칙 2: 증적 일체화 (Evidence-First).** 모든 태스크 실행은 stdout, stderr, exit_code를 포함하는 증적(evidence)과 SHA-256 해시 체인 블록, 보상(reward)을 원자적으로 생성한다. 증적이 없는 완료 주장은 시스템 수준에서 차단된다. 이는 "evidence 없는 완료 주장 금지"라는 설계 불변식(invariant)으로 강제된다. 기록된 증적과 보상은 에이전트 성과 평가, 비용 정산, 감사 추적에 활용된다.

**원칙 3: 정책 자율 개선 (Self-Improving Policy).** 태스크 실행의 보상(reward)이 Q-learning 정책 엔진에 자동으로 공급되어, 위험도별 최적 실행 전략이 점진적으로 수렴한다. 고보상 태스크는 경험 메모리로 자동 승급(auto-promote)되어 RAG를 통해 향후 의사결정에 활용된다.

## 3.2 3계층 위임 아키텍처

OpsClaw는 Master, Manager, SubAgent의 3계층으로 구성된다. 그림 1은 전체 아키텍처를 도시한다.

```
그림 1. OpsClaw 3계층 위임 아키텍처

┌──────────────────────────────────────────────────────────────┐
│                    Master (LLM)                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐  │
│  │ 계획 수립   │  │ 결과 해석   │  │ 재계획 / 최종 검토     │  │
│  └──────┬─────┘  └──────▲─────┘  └────────────────────────┘  │
│         │               │                                     │
│         │  REST API      │  Evidence + PoW                    │
├─────────┼───────────────┼────────────────────────────────────┤
│         ▼               │       Manager API (:8000)           │
│  ┌──────────────────────┴──────────────────────────────────┐ │
│  │  프로젝트 라이프사이클 │ 상태 머신 │ Playbook 엔진       │ │
│  │  Evidence 수집        │ PoW 생성  │ RL 정책 엔진         │ │
│  │  보상 산출            │ 경험 승급  │ 4-Layer 메모리       │ │
│  └──┬───────────┬───────────┬────────────────────────────┘  │
│     │           │           │                                │
│     ▼           ▼           ▼                                │
│  ┌────────┐ ┌────────┐ ┌────────┐                           │
│  │SubAgent│ │SubAgent│ │SubAgent│  SubAgent Runtime (:8002)  │
│  │ secu   │ │ web    │ │ siem   │                            │
│  │ :8002  │ │ :8002  │ │ :8002  │                            │
│  └────────┘ └────────┘ └────────┘                            │
│   nftables    BunkerWeb   Wazuh                              │
│   Suricata    JuiceShop   4.11.2                             │
└──────────────────────────────────────────────────────────────┘
```

**Master** (LLM 계층)는 사용자의 자연어 요청을 분석하여 작업 계획을 수립하고, 실행 결과를 해석하며, 필요 시 재계획(replan)을 지시한다. OpsClaw는 두 가지 Master 모드를 지원한다: **Mode A (Native)**는 내장 LLM(master-service, :8001)이 계획을 수립하고, **Mode B (External)**는 외부 AI(Claude Code, Codex 등)가 Manager API를 직접 호출하여 오케스트레이션한다. Mode B에서 Master는 두뇌(brain) 역할만 수행하며, 대상 서버에 직접 접근하지 않는다.

**Manager** (control-plane 계층)는 프로젝트 라이프사이클 전체를 관리하는 중앙 조율자(orchestrator)이다. 프로젝트 상태 전이, evidence 수집 및 저장, PoW 블록 생성, 보상 산출, Playbook 실행 중재, SubAgent로의 태스크 dispatch를 담당한다. Manager는 상태 관리의 단일 진실점(single source of truth)으로 기능하며, 모든 실행 기록이 이 계층을 통해 PostgreSQL에 영구 저장된다.

**SubAgent** (실행 계층)는 대상 서버에서 실제 명령을 수행하는 경량 런타임이다. 각 SubAgent는 독립된 서버에 배포되며, shell 명령 실행, 파일 조작, 서비스 제어, 헬스 체크를 수행한다. SubAgent는 반드시 Manager를 통해서만 호출되며(직접 호출 금지), 실행 결과(stdout, stderr, exit_code)를 Manager에게 반환한다.

이 3계층 구조의 핵심 이점은 **위임 준수(delegation compliance) 감사 가능성**이다. Manager를 경유하지 않는 직접 실행은 구조적으로 차단되며, 모든 태스크의 요청자(Master), 중재자(Manager), 실행자(SubAgent)가 evidence에 기록되어 사후 추적이 가능하다.

## 3.3 프로젝트 라이프사이클 상태 머신

OpsClaw의 모든 작업은 프로젝트(project) 단위로 관리되며, 각 프로젝트는 LangGraph 기반 상태 머신(state machine)에 의해 라이프사이클이 제어된다. 그림 2는 상태 전이 다이어그램을 도시한다.

```
그림 2. 프로젝트 라이프사이클 상태 머신

                ┌──────────────────────────────────────┐
                │           replan (루프)               │
                │                                      │
                ▼                                      │
 ┌────────┐  ┌──────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐
 │created │→ │ plan │→ │select_   │→ │resolve_ │→ │ execute  │→ │validate  │→ │ report  │→ close
 │        │  │      │  │assets    │  │targets  │  │          │  │          │  │         │
 └────────┘  └──────┘  └──────────┘  └─────────┘  └──────────┘  └──────────┘  └─────────┘
                                         │              ▲
                                         │   approval   │
                                         └──── gate ────┘
```

상태 머신의 핵심 특성은 다음과 같다:

**무효 전이 차단.** `VALID_TRANSITIONS` 딕셔너리가 각 상태에서 허용되는 다음 상태만을 정의하며, 허용되지 않은 전이 시도(예: created→execute)는 HTTP 400 에러로 즉시 거부된다. 실험 E에서 5건의 무효 전이 시도가 100% 차단됨을 검증하였다.

**재계획(replan) 루프.** 실행(execute), 검증(validate), 보고(report) 단계에서 문제가 발견되면 계획(plan) 단계로 회귀하여 수정된 계획을 재수립할 수 있다. `REPLAN_FROM_STAGES = {execute, validate, report}`로 정의된 단계에서만 재계획이 허용된다.

**승인 게이트(approval gate).** 정책에 따라 승인이 필요한 프로젝트는 `approval_required` 플래그가 설정되며, 승인이 완료되기 전까지 실행 단계로의 전이가 조건부 에지(conditional edge)에 의해 차단된다.

**바이패스 경로.** 자산 선택(select_assets)과 대상 해석(resolve_targets)이 불필요한 경우, 계획 단계에서 직접 실행 단계로 전이할 수 있다. 이는 Mode B의 execute-plan 워크플로에서 활용된다.

상태 머신의 구현에는 LangGraph의 StateGraph를 사용하며, 각 상태를 노드(node)로, 전이를 에지(edge)로 정의한다. `ProjectGraphState` TypedDict가 현재 단계(`current_stage`), 상태(`status`), 재계획 사유(`replan_reason`), 승인 여부(`approval_required`), 에러(`error`) 등의 상태를 관리한다.

## 3.4 개념 계층: Tool → Skill → Playbook → Project

OpsClaw는 실행 단위를 4단계 추상화 계층으로 구조화한다.

```
그림 3. 개념 계층

Project (라이프사이클 관리 단위)
  └── Playbook (절차: Skill/Tool의 순서화된 묶음)
        ├── Skill (재사용 가능한 능력: Tool 조합)
        │     ├── Tool (원자적 기능: run_command, fetch_log, ...)
        │     └── Tool
        └── Skill
              └── Tool
```

**Tool**은 가장 작은 원자적 기능 단위이다. `run_command`(shell 명령 실행), `fetch_log`(로그 조회), `query_metric`(시스템 메트릭 수집), `read_file`(파일 읽기), `write_file`(파일 쓰기), `restart_service`(서비스 재시작)의 6개 기본 Tool이 등록되어 있다.

**Skill**은 Tool을 조합한 재사용 가능한 능력이다. 예를 들어 `probe_linux_host` Skill은 hostname, uptime, 커널 버전, 디스크, 메모리, 프로세스, 포트 정보를 종합 수집하며, 내부적으로 `run_command` Tool을 여러 번 호출한다. 6개 기본 Skill이 등록되어 있다.

**Playbook**은 Skill과 Tool을 순서화하여 묶은 절차(procedure)이다. Playbook의 각 단계(step)는 `step_type`(tool 또는 skill), `ref_id`, `params`를 지정하며, 동일 Playbook의 반복 실행은 결정론적(deterministic) 결과를 보장한다. `resolve_step_script()` 함수가 파라미터를 바인딩하여 LLM의 비결정론을 제거한다.

**Project**는 라이프사이클 관리의 최상위 단위이다. 하나의 프로젝트는 하나의 작업 단위에 대응하며, 상태 머신에 의해 intake부터 close까지 관리된다. 프로젝트 내의 모든 evidence, PoW 블록, 보상, 경험이 `project_id`로 연결되어 일관된 추적이 가능하다.

이 계층 구조의 **확장 원칙**은 다음과 같다: 신규 업무가 발생하면 코어를 수정하지 않고, (1) 기존 Tool 재사용 → (2) 새 Skill 추가 → (3) 새 Playbook 추가 → (4) Policy binding 추가의 순서로 확장한다.

## 3.5 서비스 경계 및 패키지 구조

OpsClaw는 5개의 독립 서비스와 13개의 핵심 패키지로 구성된다.

### 서비스 경계

| 서비스 | 포트 | 역할 |
|--------|------|------|
| **manager-api** | :8000 | 인간/AI 진입점. 프로젝트, 자산, Playbook, evidence, PoW, RL 전체 API |
| **master-service** | :8001 | Mode A 전용 내장 LLM. 계획 검토, 재계획, 에스컬레이션 |
| **subagent-runtime** | :8002 | 명령 실행, 파일 조작, 헬스/capabilities 제공 |
| **scheduler-worker** | — | 배치 스케줄 처리 (cron 기반 반복 작업) |
| **watch-worker** | — | 연속 감시 처리 (이벤트 기반 트리거) |

### 핵심 패키지

| 패키지 | 역할 |
|--------|------|
| `project_service` | 프로젝트 CRUD, 상태 전이, 완료보고 |
| `graph_runtime` | LangGraph 기반 상태 머신 정의 및 실행 |
| `asset_registry` | 자산 등록, 상태 관리, 대상 해석(resolve) |
| `registry_service` | Tool, Skill, Playbook 레지스트리 |
| `evidence_service` | Evidence 저장, 조회, 요약 |
| `pow_service` | PoW 블록 생성, 체인 검증, 리더보드 |
| `rl_service` | Q-learning 학습, UCB1 추천, 정책 관리 |
| `experience_service` | Task memory 구축, 경험 승급, 자동 승급 |
| `retrieval_service` | 문서 인덱싱, 전문 검색(FTS), RAG 지원 |
| `validation_service` | 실행 결과 검증, 완료 기준 판정 |
| `history_service` | 원시 이력 관리 |
| `pi_adapter` | pi runtime 연동 경계 (하부 실행 계층) |
| `approval_engine` | 정책 기반 승인 게이트 |

### 의존 방향

패키지 간 의존은 엄격한 단방향 계층을 따른다:

```
apps/* → packages/*
packages/graph_runtime → packages/project_service, approval_engine, policy_engine
packages/project_service → packages/asset_registry, registry_service, evidence_service, validation_service
packages/retrieval_service → packages/history_service, experience_service
packages/* → packages/pi_adapter (허용)
packages/pi_adapter → packages/* (금지: 역방향 의존 차단)
```

`pi_adapter`는 하부 연동 계층이지 상위 오케스트레이션 계층이 아니다. 이 의존 방향 규칙에 의해 실행 엔진의 교체가 상위 비즈니스 로직에 영향을 미치지 않는다.

## 3.6 데이터 저장 전략

OpsClaw는 세 가지 저장 계층을 활용한다.

**PostgreSQL 15** (구조화 저장): 프로젝트, 자산, evidence, PoW 블록, 보상, 경험, Playbook, 스케줄, 정책, 감사 로그 등 모든 구조화 데이터를 영구 저장한다. 17개의 핵심 테이블과 13개의 마이그레이션 파일로 스키마가 관리된다.

**Inline Blob** (원본 보관): stdout, stderr, 생성 스크립트, 보고서 등의 원본 데이터는 evidence 레코드 내 `inline://` 참조로 저장된다. 대용량 바이너리 데이터를 위한 외부 Object Store 확장이 설계되어 있으나, 현재 구현에서는 인라인 저장을 사용한다.

**PostgreSQL FTS** (의미 검색): `retrieval_documents` 테이블에 대해 PostgreSQL의 `to_tsvector` / `plainto_tsquery` 기반 전문 검색(Full-Text Search)을 제공한다. FTS로 결과가 없을 경우 ILIKE 폴백 검색을 수행한다. 문서 유형(`document_type`)별 필터링을 지원하며, report, evidence_summary, experience, playbook, asset 유형이 인덱싱된다.

## 3.7 실행 모드: Mode A vs Mode B

OpsClaw는 Master 역할의 수행 주체에 따라 두 가지 실행 모드를 지원한다.

| | Mode A (Native) | Mode B (External) |
|---|---|---|
| Master | 내장 LLM (master-service) | 외부 AI (Claude Code, Codex) |
| `master_mode` | `native` | `external` |
| 계획 수립 | master-service가 LLM으로 계획 생성 | 외부 AI가 직접 tasks 배열 구성 |
| API 호출 | Manager가 내부적으로 호출 | 외부 AI가 REST API 직접 호출 |
| 실행 흐름 | 자동 (상태 머신 주도) | 반자동 (외부 AI 주도, 상태 전이는 Manager) |

Mode B에서 외부 AI는 `POST /projects` (생성) → `POST /plan` → `POST /execute` → `POST /execute-plan` (태스크 배열 전달) → `GET /evidence/summary` → `POST /completion-report`의 순서로 Manager API를 호출한다. Manager는 상태 전이, evidence 기록, PoW 생성, 보상 산출을 자동으로 처리하므로, 외부 AI는 계획 수립과 결과 해석에만 집중할 수 있다.

이 이중 모드 설계는 Master LLM의 교체 가능성(swappability)을 보장한다. Manager와 SubAgent 계층은 Master의 정체에 무관하게 동일한 control-plane 기능을 제공한다.
