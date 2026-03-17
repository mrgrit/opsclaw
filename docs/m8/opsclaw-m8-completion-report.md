# OpsClaw M8 Completion Report — History / Experience / Retrieval

**Date:** 2026-03-18
**Milestone:** M8 — History / Experience / Retrieval
**Status:** COMPLETE
**Evidence:** 35/35 smoke tests passed, 30/30 pre-M7 + 14/14 M6 + 35/35 M7 regression tests passed

---

## Summary

M8 implements the 4-layer memory structure from the master plan:

| Layer | Table | Service |
|---|---|---|
| 1. Raw History | `histories` | `history_service` |
| 2. Structured Task Memory | `task_memories` | `experience_service.build_task_memory` |
| 3. Semantic Experience Memory | `experiences` | `experience_service.promote_to_experience` |
| 4. Working Context | `retrieval_documents` | `retrieval_service.get_context_for_project` |

Vector search is implemented via **PostgreSQL full-text search** (`plainto_tsquery` / `to_tsvector`) with ILIKE fallback — no external vector DB required.

---

## Work Items Completed

### WORK-49: `packages/history_service/__init__.py`
**Layer 1 — Raw History ingestion and retrieval.**

- `ingest_event(project_id, event, context, job_run_id)` → INSERT into `histories`
- `ingest_stage_event(project_id, stage, status, context, job_run_id)` → convenience wrapper
- `get_project_history(project_id, limit)` → project events, most recent first
- `get_asset_history(asset_id, limit)` → events where `context->>'asset_id' = asset_id`
- `list_histories(limit)` → global event list
- `get_history_event(history_id)` → single event by id

### WORK-50: `packages/experience_service/__init__.py`
**Layers 2 & 3 — Structured Task Memory and Experience promotion.**

- `build_task_memory(project_id)` → aggregates project + evidence + reports + assets + playbook → `task_memories` INSERT (idempotent: replaces existing)
- `get_task_memory(project_id)` → most recent task_memory for project
- `list_task_memories(limit)` → list all
- `promote_to_experience(task_memory_id, category, title, outcome, asset_id)` → promotes task_memory → `experiences`
- `create_experience(category, title, summary, ...)` → direct experience creation
- `list_experiences(category, limit)` → list with optional category filter
- `get_experience(experience_id)` → by id

### WORK-51: `packages/retrieval_service/__init__.py`
**Layer 4 — Working Context via smart retrieval.**

- `index_document(document_type, ref_id, title, body, metadata)` → INSERT into `retrieval_documents`
- `search_documents(query, document_type, limit)` → PostgreSQL FTS (`plainto_tsquery`) with ILIKE fallback
- `get_retrieval_document(doc_id)` → by id
- `list_retrieval_documents(document_type, limit)` → filtered list
- `reindex_project(project_id)` → indexes all project evidence + reports as retrieval_documents
- `get_context_for_project(project_id)` → assembles working context: asset_history + experiences + FTS documents

### WORK-52: Manager API v0.8.0-m8
Added to `apps/manager-api/src/main.py`:

**History routes (via project/asset routers):**
- `POST /projects/{id}/history/ingest` — record a history event
- `GET /projects/{id}/history` — get project history
- `GET /assets/{id}/history` — get asset history
- `POST /projects/{id}/task-memory/build` — build/rebuild task_memory
- `GET /projects/{id}/task-memory` — get task_memory
- `POST /projects/{id}/reindex` — index project docs into retrieval_documents
- `GET /projects/{id}/context` — get working context (Layer 4)

**Experience routes (`/experience`):**
- `GET /experience` — list experiences (optional category query param)
- `GET /experience/search?q=...` — search experiences + documents
- `POST /experience` — create experience directly
- `GET /experience/{id}` — get by id
- `POST /experience/task-memories/{id}/promote` — promote task_memory to experience

---

## Test Results

| Test Suite | Result |
|---|---|
| M8 Smoke (`m8_integrated_smoke.py`) | **35/35 PASS** |
| M7 Smoke (`m7_integrated_smoke.py`) | **35/35 PASS** |
| Pre-M7 Smoke (`pre_m7_smoke.py`) | **30/30 PASS** |
| M6 Smoke (`m6_integrated_smoke.py`) | **14/14 PASS** |

---

## Design Decisions

1. **No external vector DB** — PostgreSQL full-text search is production-ready, consistent with the psycopg2-only approach, and requires zero additional infrastructure.
2. **ILIKE fallback** — When FTS produces no results (e.g. short queries, single words), ILIKE pattern matching is used as fallback, ensuring reliable retrieval.
3. **4-layer memory structure** from master plan section 13:
   - Layer 1 (Raw History): never lost, audit-ready
   - Layer 2 (Task Memory): auto-built from project artifacts, idempotent
   - Layer 3 (Experience): only high-reuse-value patterns promoted
   - Layer 4 (Working Context): assembled on-demand per project
4. **Asset axis** for history retrieval: `context->>'asset_id'` allows filtering events by asset across all projects.
5. **Retrieval axes** covered: asset (via asset_history), experience (via list_experiences), document (via FTS on request_text).

---

## Files Changed

| File | Change |
|---|---|
| `packages/history_service/__init__.py` | Full implementation (was empty) |
| `packages/experience_service/__init__.py` | Full implementation (was empty) |
| `packages/retrieval_service/__init__.py` | Full implementation (was empty) |
| `apps/manager-api/src/main.py` | v0.8.0-m8, +history/experience routers (12 new endpoints) |
| `tools/dev/m8_integrated_smoke.py` | New (35 items) |
| `docs/m8/opsclaw-m8-completion-report.md` | This file |
| `README.md` | M8 완료 반영 |
