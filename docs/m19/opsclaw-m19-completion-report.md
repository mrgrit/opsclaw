# OpsClaw M19 완료보고서 — Skill/Tool/Experience 실동작 검증

**작성일:** 2026-03-22
**마일스톤:** M19 — Skill/Tool/Experience 실동작 검증 (3순위)
**상태:** 완료

---

## 1. 목표 및 완료 기준

**목표:** DB에 등록된 Skill, Tool, Experience가 실제 코드 실행 경로에서 올바르게 동작하는지 검증하고 미동작 부분 보완

| 완료 기준 | 결과 |
|---------|------|
| 6개 seed tool 실제 실행 성공 | ✅ |
| Playbook composition engine end-to-end 성공 | ✅ |
| Experience 검색 결과가 신규 프로젝트 context에 반영 확인 | ✅ |

---

## 2. 개념 정리

| 개념 | 설명 |
|------|------|
| **Tool** | 실행 가능한 shell 명령/스크립트 단위 (`run_command`, `fetch_log` 등) |
| **Skill** | Tool 조합으로 특정 목적을 달성하는 절차 단위 (`probe_linux_host` 등) |
| **Experience** | 과거 작업 결과에서 추출한 패턴/교훈 (성공/실패 사례 요약) |

---

## 3. 구현 및 검증 내용

### WORK-63 — Tool 실행 경로 검증 + 버그 수정

**발견된 버그:** `registry_service.resolve_playbook()`이 step의 `metadata`(params)를 반환하지 않음

**수정 파일:** `packages/registry_service/__init__.py`

```python
# 수정 전: metadata 누락
resolved = {"order": ..., "type": ..., "ref": ..., "on_failure": ...}

# 수정 후: metadata 포함
resolved = {"order": ..., "type": ..., "ref": ..., "on_failure": ...,
            "metadata": step.get("metadata") or {}}  # WORK-63
```

**검증 결과:**
- `run_command` + `query_metric` + `read_file` → Playbook 실행 → SubAgent dispatch → **3/3 성공**
- stdout 확인: `echo opsclaw-tool-test && hostname` → `opsclaw-tool-test\nopsclaw`

### WORK-64 — skill_tools 링크 + Skill 검증

**발견된 문제:** `skill_tools` 테이블 0행 — Skill-Tool 링크 없음

**수정:** DB에 12개 링크 삽입

```sql
-- 모든 Skill → run_command (primary)
INSERT INTO skill_tools (skill_id, tool_id, usage_mode, order_hint) ...

-- 관련 Skill → fetch_log (optional)
-- probe_linux_host, summarize_incident_timeline, analyze_wazuh_alert_burst

-- 관련 Skill → query_metric (optional)
-- probe_linux_host, monitor_disk_growth, collect_web_latency_facts
```

**검증 결과:**
- `probe_linux_host` + `monitor_disk_growth` → Playbook 실행 → **2/2 성공**

### WORK-65 — Experience 생성→검색→참조 흐름

**검증 결과:**

| 단계 | 결과 |
|------|------|
| `build_task_memory(project_id)` | ✅ Task Memory 생성 |
| `promote_to_experience(task_memory_id, ...)` | ✅ Experience DB 저장 + retrieval 인덱싱 |
| `search_documents("probe linux disk", type="experience")` | ✅ 1건 검색 |
| `get_context_for_project(project_id)` | ✅ experiences 5개 context 주입 |

### WORK-66 — 미구현 부분 보완

| 항목 | 처리 |
|------|------|
| `resolve_playbook()` metadata 누락 | ✅ 수정 |
| `skill_tools` 0행 | ✅ 12개 삽입 |

### WORK-67 — Smoke 테스트 스크립트

**파일:** `scripts/m19_skill_smoke.py`

**테스트 항목 (30개):**
1. Tool Registry 조회 (7개)
2. Skill Registry 조회 (7개)
3. skill_tools 링크 확인 (1개)
4. 6개 Tool 스크립트 생성 (6개)
5. 6개 Skill 스크립트 생성 (6개)
6. SubAgent run_script dispatch (1개)
7. Experience 생성 + retrieval 검색 (2개)

---

## 4. Smoke 테스트 결과 (2026-03-22)

```
결과: 30/30 통과, 0건 실패
✅ PASS
```

**실행 환경:** localhost, subagent-runtime:8002, PostgreSQL 15

---

## 5. 실행 경로 전체 흐름

```
[Playbook Step] {step_type: "tool"/"skill", ref_id: "run_command"/"probe_linux_host", metadata: {...}}
        ↓
[playbook_engine.resolve_step_script(step, ctx)]
  - step_type="tool" → _TOOL_BUILDERS[ref](ctx, step.metadata)
  - step_type="skill" → _SKILL_BUILDERS[ref](ctx, step.metadata)
        ↓
[bash script string]
        ↓
[dispatch_command_to_subagent(project_id, script, subagent_url)]
        ↓
[SubAgent /a2a/run_script] → exit_code, stdout, stderr
        ↓
[evidence 자동 기록] → [build_task_memory] → [promote_to_experience]
        ↓
[retrieval_service.index_document()] → [검색 가능]
        ↓
[get_context_for_project()] → 신규 프로젝트 past_experiences에 자동 주입
```

---

## 6. 변경 파일 목록

| 파일 | 변경 내용 |
|------|---------|
| `packages/registry_service/__init__.py` | `resolve_playbook()` metadata 필드 추가 |
| `scripts/m19_skill_smoke.py` | 신규 — 30개 항목 smoke 테스트 |
| `scripts/m19_smoke_result.json` | 신규 — 테스트 결과 |
