# OpsClaw Pre-M7 Gap Resolution Completion Report

## 1. 목적

M6까지 완료 후 설계서(00-2.master_plan.md)와 현재 구현을 대조하여 발견한 4개의 핵심 architectural gap을 M7 진입 전에 해소했다.

---

## 2. 해소한 Gap 목록

### Work A: LangGraph 기반 상태기계 (`packages/graph_runtime/__init__.py`)

**이전 상태:** `graph_runtime`이 stage 전이 helper 함수 수준에 불과했으며, 실제 LangGraph StateGraph가 없었다. project lifecycle은 외부 API 호출로 수동 진행해야 했다.

**변경 내용:**
- `ProjectGraphState` (TypedDict): project_id, current_stage, status, replan_reason, approval_required, approval_cleared, error, stop_reason, database_url
- LangGraph 노드 함수: `_node_plan`, `_node_select_assets`, `_node_resolve_targets`, `_node_approval_gate`, `_node_execute`, `_node_validate`, `_node_report`, `_node_close`
- 조건부 엣지: approval_gate → execute (cleared) OR → END (blocked), replan 루프
- `build_project_graph()`: StateGraph 컴파일
- `run_project_graph()`: 자율 실행 — plan부터 close까지 또는 blocked까지

**완료 조건:**
- 저위험 project: 자율 실행으로 close까지 진행
- 고위험 project (review 없음): approval_blocked에서 멈춤
- 고위험 project (review approved): execute 통과

---

### Work B: select_assets / resolve_targets 스테이지 (`packages/project_service/__init__.py`)

**이전 상태:** 설계서에 명시된 `select_assets`, `resolve_targets` 스테이지가 lifecycle에 없었으며 수동 링크만 가능했다.

**변경 내용:**

**`packages/graph_runtime/__init__.py`:**
- `VALID_TRANSITIONS`: dict[str, set[str]] 방식으로 전환 (이전: 단일 next 매핑)
- `plan → {select_assets, execute}` — execute는 bypass 경로 (기존 호환성 유지)
- `select_assets → {resolve_targets, execute}`
- `resolve_targets → {execute}`

**`packages/project_service/__init__.py`:**
- `select_assets_for_project()`: 이미 링크된 asset 사용, 없으면 healthy/unknown asset 자동 선택 (최대 3개), stage → select_assets
- `resolve_targets_for_project()`: 각 linked asset에 `resolve_target_from_asset()` 호출, target → project_targets 연결, 실패는 기록하되 중단 안 함, stage → resolve_targets

**Manager API:**
- `POST /projects/{id}/select_assets`
- `POST /projects/{id}/resolve_targets`

---

### Work C: Approval Gate (`packages/approval_engine/__init__.py`)

**이전 상태:** `packages/approval_engine/__init__.py`가 빈 파일. 고위험 작업 실행 전 승인 검증이 없었다.

**변경 내용:**
- `APPROVAL_REQUIRED_FOR = frozenset({"high", "critical"})` — 이 위험 수준은 approved master_review 필요
- `check_requires_approval()`: project.risk_level이 APPROVAL_REQUIRED_FOR에 해당하는지 확인
- `require_approval_cleared()`: 필요한 경우 master_reviews에서 approved 기록 확인, 없으면 `ApprovalNotClearedError`
- `get_approval_status()`: requires_approval, cleared, latest_review 요약 반환
- `project_service.execute_project_record()`: 전이 확인 후 `require_approval_cleared()` 호출

**Manager API:**
- `GET /projects/{id}/approval`

**설계 원칙 준수:** Human-minimized, not Human-eliminated — 저/중위험은 자동 진행, 고/치명은 반드시 사람 검수 필요.

---

### Work D: Policy Engine (`packages/policy_engine/__init__.py`)

**이전 상태:** `packages/policy_engine/__init__.py`가 빈 파일. policy_tags, policy_hint 등 schema 필드는 있었으나 실제 정책 적용이 없었다.

**변경 내용:**
- `DEFAULT_POLICIES`: prod / staging / lab / default 환경별 규칙 테이블 (코드 기반, 향후 DB 마이그레이션 가능)
  - `prod`: high/critical 승인 필요, one_shot만 허용
  - `staging`: critical 승인 필요, one_shot/batch 허용
  - `lab`: 승인 불필요, 전 모드 허용
  - `default`: critical만 승인 필요
- `get_policy(env)`: env별 정책 반환
- `check_policy(project_id, stage)`: project의 risk_level + 링크된 asset의 env를 기반으로 위반 여부 확인
- `enforce_policy(project_id, stage)`: `PolicyViolation` 발생

---

## 3. 테스트 결과

```
Pre-M7 Smoke: 30/30 passed, 0 failed
M5 Integrated Smoke: 11/11 passed
M6 Integrated Smoke: 14/14 passed
```

**검증 범위 (pre_m7_smoke.py 30개 항목):**

| 구역 | 항목 수 | 내용 |
|---|---|---|
| A. LangGraph | 5 | 컴파일, 저위험 자율실행, 고위험 blocked |
| B. select_assets/resolve_targets | 5 | 스테이지 전이, 결과 구조 |
| C. Approval Engine | 9 | 저/고위험 approval status, execute 차단/통과 |
| D. Policy Engine | 5 | get_policy, check_policy, enforce_policy |
| E. Regression | 6 | lifecycle, evidence gate, registry |

---

## 4. 아직 남은 것 (향후 마일스톤)

- **Policy Engine DB화**: 현재 코드 기반 규칙 → DB 테이블로 마이그레이션
- **Dual-approval for critical**: prod + critical = 두 명 승인 (현재 단일 승인으로 처리)
- **Policy enforcement at other stages**: 현재 execute 단계만 검사
- **Blob store**: stdout/stderr 여전히 inline:// 포맷으로 DB 저장 (M8 이전에 처리 권장)
- **LangGraph replan 루프 이력 관리**: 무한 replan 방지 카운터 (현재 미구현)
