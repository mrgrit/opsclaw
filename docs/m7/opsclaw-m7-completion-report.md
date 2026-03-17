# OpsClaw M7 Completion Report — Batch/Continuous Execution

**Date:** 2026-03-17
**Milestone:** M7 — Batch/Continuous Execution
**Status:** COMPLETE
**Evidence:** 35/35 smoke tests passed, 30/30 pre-M7 + 14/14 M6 regression tests passed

---

## Summary

M7 implements schedule-based batch execution and continuous watch (monitoring) execution on top of the DB schema introduced in migration 0004. The implementation uses a polling-loop approach (no APScheduler), psycopg2 for direct DB access, and croniter for cron next-run calculation.

---

## Work Items Completed

### WORK-44: `packages/scheduler_service/__init__.py`
Full implementation of schedule CRUD and batch execution logic.

**Functions implemented:**
- `create_schedule` — INSERT into schedules, compute next_run via croniter
- `get_schedule` — SELECT by id
- `list_schedules` — SELECT with optional enabled_only filter
- `update_schedule` — UPDATE enabled / cron_expr (with next_run recalc)
- `delete_schedule` — DELETE by id
- `get_due_schedules` — SELECT WHERE enabled=true AND next_run <= now()
- `mark_schedule_ran` — UPDATE last_run=NOW(), next_run=next cron tick
- `execute_due_schedule` — plan→execute→validate→report cycle with replan guard

### WORK-45: `packages/watch_service/__init__.py` (new package)
Full implementation of watch_job / watch_event / incident CRUD and monitoring execution.

**Functions implemented:**
- `create_watch_job`, `get_watch_job`, `list_watch_jobs`, `update_watch_job_status`, `delete_watch_job`
- `record_watch_event`, `list_watch_events`
- `create_incident`, `list_incidents`, `resolve_incident`
- `run_watch_check` — subprocess command execution, check_ok/check_fail event recording, consecutive-failure threshold → incident creation

### WORK-46: Worker stubs → real polling loops
- `apps/scheduler-worker/src/main.py` — real `load_schedules` / `process_schedule` / `run_loop`
- `apps/watch-worker/src/main.py` — real `load_watch_jobs` / `process_watch_job` / `run_loop`

### WORK-47: Manager API v0.7.0-m7
Added 3 new routers to `apps/manager-api/src/main.py`:

**`/schedules`**
- `POST /schedules` — creates batch project + schedule
- `GET /schedules` — list all schedules
- `GET /schedules/{id}` — get by id
- `PATCH /schedules/{id}` — update enabled/cron_expr
- `DELETE /schedules/{id}` — delete
- `POST /schedules/{id}/run` — trigger immediate cycle

**`/watchers`**
- `POST /watchers` — creates continuous project + watch_job
- `GET /watchers` — list all watch_jobs
- `GET /watchers/{id}` — get by id
- `PATCH /watchers/{id}/status` — update status (running/paused/stopped)
- `DELETE /watchers/{id}` — delete
- `GET /watchers/{id}/events` — list events
- `POST /watchers/{id}/check` — trigger immediate check

**`/incidents`**
- `GET /incidents` — list (default: open)
- `POST /incidents/{id}/resolve` — resolve incident

### WORK-48: Smoke tests
- `tools/dev/m7_integrated_smoke.py` — 35 items across 4 sections (A–D)

---

## Test Results

| Test Suite | Result |
|---|---|
| M7 Smoke (`m7_integrated_smoke.py`) | **35/35 PASS** |
| Pre-M7 Smoke (`pre_m7_smoke.py`) | **30/30 PASS** |
| M6 Smoke (`m6_integrated_smoke.py`) | **14/14 PASS** |

---

## Design Decisions

1. **Polling loop, not APScheduler** — Simple `while True: ... time.sleep(N)` in both workers. No external scheduler dependency.
2. **croniter for next_run** — `croniter(cron_expr, now).get_next(datetime)` gives next UTC tick.
3. **Batch cycle**: plan → execute → validate → report (no close). If project is stuck in execute/validate/report, `replan_project` resets it before the next cycle.
4. **Watch failure threshold** — consecutive `check_fail` events counted from most-recent events. When `>= threshold`, one incident is created per threshold crossing.
5. **psycopg2 direct** — consistent with all other packages in the codebase. No ORM.

---

## Files Changed

| File | Change |
|---|---|
| `packages/scheduler_service/__init__.py` | Full implementation (was empty) |
| `packages/watch_service/__init__.py` | New package |
| `apps/scheduler-worker/src/main.py` | Stub → real polling loop |
| `apps/watch-worker/src/main.py` | Stub → real polling loop |
| `apps/manager-api/src/main.py` | +3 routers, version 0.7.0-m7 |
| `tools/dev/m7_integrated_smoke.py` | New (35 items) |
| `docs/m7/opsclaw-m7-completion-report.md` | This file |
| `README.md` | M7 complete |
