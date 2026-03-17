#!/usr/bin/env python3
"""M7 Integrated Smoke Test — 35 items
Covers:
  A. scheduler_service unit (items 1-10)
  B. watch_service unit     (items 11-22)
  C. Manager API /schedules (items 23-28)
  D. Manager API /watchers + /incidents (items 29-35)
"""
import sys
import time
import subprocess
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BASE_URL = "http://127.0.0.1:8000"
DB_URL = "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw"

passed = 0
failed = 0
results = []


def check(n: int, desc: str, ok: bool, detail: str = ""):
    global passed, failed
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
    tag = f"[{n:02d}]"
    line = f"{tag} {status} — {desc}"
    if not ok and detail:
        line += f"\n       detail: {detail}"
    results.append(line)
    print(line)


# ─────────────────────────────────────────────────────────────────────────────
# Section A: scheduler_service unit (1-10)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== A. scheduler_service unit ===")

# 1. croniter import
try:
    from croniter import croniter as _cron
    check(1, "croniter import 성공", True)
except ImportError as e:
    check(1, "croniter import 성공", False, str(e))

from packages.scheduler_service import (
    create_schedule,
    delete_schedule,
    execute_due_schedule,
    get_due_schedules,
    get_schedule,
    list_schedules,
    mark_schedule_ran,
    update_schedule,
)
from packages.project_service import create_project_record

# Create a batch project for scheduler tests
_sp = create_project_record("m7-smoke-sched", "batch smoke", mode="batch", database_url=DB_URL)
_sp_id = _sp["id"]

# 2. create_schedule
try:
    _sched = create_schedule(_sp_id, "cron", "*/5 * * * *", database_url=DB_URL)
    check(2, "create_schedule → dict with id", "id" in _sched, str(_sched))
    _sched_id = str(_sched["id"])
except Exception as e:
    check(2, "create_schedule → dict with id", False, str(e))
    _sched_id = None

# 3. get_schedule — field validation
if _sched_id:
    try:
        row = get_schedule(_sched_id, database_url=DB_URL)
        fields_ok = row and all(k in row for k in ("id", "project_id", "cron_expr", "next_run", "enabled"))
        check(3, "get_schedule → 필드 검증 (id, project_id, cron_expr, next_run, enabled)", bool(fields_ok), str(row))
    except Exception as e:
        check(3, "get_schedule → 필드 검증", False, str(e))
else:
    check(3, "get_schedule → 필드 검증", False, "no schedule_id")

# 4. list_schedules → contains our schedule
if _sched_id:
    try:
        items = list_schedules(enabled_only=False, database_url=DB_URL)
        ids = [str(r["id"]) for r in items]
        check(4, "list_schedules → 포함", _sched_id in ids)
    except Exception as e:
        check(4, "list_schedules → 포함", False, str(e))
else:
    check(4, "list_schedules → 포함", False, "no schedule_id")

# 5. update_schedule enabled=False
if _sched_id:
    try:
        row = update_schedule(_sched_id, enabled=False, database_url=DB_URL)
        check(5, "update_schedule enabled=False → disabled", row["enabled"] is False, str(row))
    except Exception as e:
        check(5, "update_schedule enabled=False → disabled", False, str(e))
else:
    check(5, "update_schedule enabled=False → disabled", False, "no schedule_id")

# 6. list_schedules enabled_only=True → disabled excluded
if _sched_id:
    try:
        items = list_schedules(enabled_only=True, database_url=DB_URL)
        ids = [str(r["id"]) for r in items]
        check(6, "list_schedules enabled_only=True → disabled 제외", _sched_id not in ids)
    except Exception as e:
        check(6, "list_schedules enabled_only=True → disabled 제외", False, str(e))
else:
    check(6, "list_schedules enabled_only=True → disabled 제외", False, "no schedule_id")

# 7. get_due_schedules → future next_run excluded
try:
    due = get_due_schedules(database_url=DB_URL)
    # our schedule has a future next_run, so it should NOT be in due list
    due_ids = [str(r["id"]) for r in due]
    ok7 = (_sched_id is None) or (_sched_id not in due_ids)
    check(7, "get_due_schedules → 미래 next_run 제외", ok7)
except Exception as e:
    check(7, "get_due_schedules → 미래 next_run 제외", False, str(e))

# 8. execute_due_schedule → cycle_result, error=None
# Re-enable and force next_run to past for testing
if _sched_id:
    try:
        import psycopg2
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE schedules SET enabled=true, next_run = NOW() - INTERVAL '1 second' WHERE id = %s",
                    (_sched_id,)
                )
        row = get_schedule(_sched_id, database_url=DB_URL)
        result = execute_due_schedule(row, database_url=DB_URL)
        ok8 = "cycle_result" in result and result.get("error") is None
        check(8, "execute_due_schedule → cycle_result, error=None", ok8, str(result))
    except Exception as e:
        check(8, "execute_due_schedule → cycle_result, error=None", False, str(e))
else:
    check(8, "execute_due_schedule → cycle_result, error=None", False, "no schedule_id")

# 9. mark_schedule_ran → last_run 갱신 + next_run 갱신
if _sched_id:
    try:
        # reset next_run to a known past value so we can detect the advance
        import psycopg2
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE schedules SET next_run = '2000-01-01 00:00:00+00' WHERE id = %s",
                    (_sched_id,)
                )
        before = get_schedule(_sched_id, database_url=DB_URL)
        mark_schedule_ran(_sched_id, database_url=DB_URL)
        after = get_schedule(_sched_id, database_url=DB_URL)
        ok9 = after["last_run"] is not None and after["next_run"] != before["next_run"]
        check(9, "mark_schedule_ran → last_run 갱신 + next_run 갱신", ok9, f"before={before['next_run']} after={after['next_run']}")
    except Exception as e:
        check(9, "mark_schedule_ran → last_run 갱신 + next_run 갱신", False, str(e))
else:
    check(9, "mark_schedule_ran → last_run 갱신 + next_run 갱신", False, "no schedule_id")

# 10. delete_schedule → False on re-query (None)
if _sched_id:
    try:
        delete_schedule(_sched_id, database_url=DB_URL)
        after = get_schedule(_sched_id, database_url=DB_URL)
        check(10, "delete_schedule → 재조회 시 None", after is None)
    except Exception as e:
        check(10, "delete_schedule → 재조회 시 None", False, str(e))
else:
    check(10, "delete_schedule → 재조회 시 None", False, "no schedule_id")


# ─────────────────────────────────────────────────────────────────────────────
# Section B: watch_service unit (11-22)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== B. watch_service unit ===")

from packages.watch_service import (
    create_incident,
    create_watch_job,
    delete_watch_job,
    get_watch_job,
    list_incidents,
    list_watch_events,
    list_watch_jobs,
    record_watch_event,
    resolve_incident,
    run_watch_check,
    update_watch_job_status,
)

_wp = create_project_record("m7-smoke-watch", "watch smoke", mode="continuous", database_url=DB_URL)
_wp_id = _wp["id"]

# 11. create_watch_job
try:
    _wj = create_watch_job(_wp_id, "http_check", {"check_command": "echo ok", "threshold": 2}, database_url=DB_URL)
    check(11, "create_watch_job → dict with id", "id" in _wj, str(_wj))
    _wj_id = str(_wj["id"])
except Exception as e:
    check(11, "create_watch_job → dict with id", False, str(e))
    _wj_id = None

# 12. get_watch_job → 필드 검증
if _wj_id:
    try:
        row = get_watch_job(_wj_id, database_url=DB_URL)
        fields_ok = row and all(k in row for k in ("id", "project_id", "watch_type", "status"))
        check(12, "get_watch_job → 필드 검증", bool(fields_ok), str(row))
    except Exception as e:
        check(12, "get_watch_job → 필드 검증", False, str(e))
else:
    check(12, "get_watch_job → 필드 검증", False, "no wj_id")

# 13. list_watch_jobs status=running → contains
if _wj_id:
    try:
        items = list_watch_jobs(status="running", database_url=DB_URL)
        ids = [str(r["id"]) for r in items]
        check(13, "list_watch_jobs status=running → 포함", _wj_id in ids)
    except Exception as e:
        check(13, "list_watch_jobs status=running → 포함", False, str(e))
else:
    check(13, "list_watch_jobs status=running → 포함", False, "no wj_id")

# 14. record_watch_event
if _wj_id:
    try:
        ev = record_watch_event(_wj_id, "check_ok", {"stdout": "ok"}, database_url=DB_URL)
        check(14, "record_watch_event → event with id", "id" in ev)
        _ev_id = str(ev["id"])
    except Exception as e:
        check(14, "record_watch_event → event with id", False, str(e))
        _ev_id = None
else:
    check(14, "record_watch_event → event with id", False, "no wj_id")
    _ev_id = None

# 15. list_watch_events → only job's events
if _wj_id:
    try:
        evs = list_watch_events(_wj_id, database_url=DB_URL)
        all_match = all(str(e["watch_job_id"]) == _wj_id for e in evs)
        check(15, "list_watch_events → 해당 job 이벤트만", all_match and len(evs) > 0)
    except Exception as e:
        check(15, "list_watch_events → 해당 job 이벤트만", False, str(e))
else:
    check(15, "list_watch_events → 해당 job 이벤트만", False, "no wj_id")

# 16. create_incident
try:
    _inc = create_incident(_wp_id, "warning", "smoke test incident", database_url=DB_URL)
    check(16, "create_incident → id, status=open", "id" in _inc and _inc["status"] == "open")
    _inc_id = str(_inc["id"])
except Exception as e:
    check(16, "create_incident → id, status=open", False, str(e))
    _inc_id = None

# 17. list_incidents status=open → contains
if _inc_id:
    try:
        items = list_incidents(status="open", database_url=DB_URL)
        ids = [str(r["id"]) for r in items]
        check(17, "list_incidents status=open → 포함", _inc_id in ids)
    except Exception as e:
        check(17, "list_incidents status=open → 포함", False, str(e))
else:
    check(17, "list_incidents status=open → 포함", False, "no inc_id")

# 18. resolve_incident → status=resolved
if _inc_id:
    try:
        row = resolve_incident(_inc_id, database_url=DB_URL)
        check(18, "resolve_incident → status=resolved", row["status"] == "resolved")
    except Exception as e:
        check(18, "resolve_incident → status=resolved", False, str(e))
else:
    check(18, "resolve_incident → status=resolved", False, "no inc_id")

# 19. list_incidents open → resolved excluded
if _inc_id:
    try:
        items = list_incidents(status="open", database_url=DB_URL)
        ids = [str(r["id"]) for r in items]
        check(19, "list_incidents status=open → resolved 건 제외", _inc_id not in ids)
    except Exception as e:
        check(19, "list_incidents status=open → resolved 건 제외", False, str(e))
else:
    check(19, "list_incidents status=open → resolved 건 제외", False, "no inc_id")

# 20. run_watch_check (ok cmd) → ok=True, incident_id=None
_wj_ok = create_watch_job(_wp_id, "ok_check",
                           {"check_command": "echo hello", "expected_contains": "hello", "threshold": 3},
                           database_url=DB_URL)
try:
    res = run_watch_check(dict(_wj_ok), database_url=DB_URL)
    check(20, "run_watch_check (ok cmd) → ok=True, incident_id=None",
          res["ok"] is True and res["incident_id"] is None, str(res))
except Exception as e:
    check(20, "run_watch_check (ok cmd) → ok=True, incident_id=None", False, str(e))

# 21. run_watch_check (fail cmd, threshold=1) → ok=False, incident_id not None
_wj_fail = create_watch_job(_wp_id, "fail_check",
                             {"check_command": "exit 1", "threshold": 1},
                             database_url=DB_URL)
try:
    res = run_watch_check(dict(_wj_fail), database_url=DB_URL)
    check(21, "run_watch_check (fail cmd, threshold=1) → ok=False, incident_id not None",
          res["ok"] is False and res["incident_id"] is not None, str(res))
except Exception as e:
    check(21, "run_watch_check (fail cmd, threshold=1) → ok=False, incident_id not None", False, str(e))

# 22. update_watch_job_status paused
if _wj_id:
    try:
        row = update_watch_job_status(_wj_id, "paused", database_url=DB_URL)
        check(22, "update_watch_job_status paused → status=paused", row["status"] == "paused")
    except Exception as e:
        check(22, "update_watch_job_status paused → status=paused", False, str(e))
else:
    check(22, "update_watch_job_status paused → status=paused", False, "no wj_id")


# ─────────────────────────────────────────────────────────────────────────────
# Section C: Manager API /schedules (23-28)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== C. Manager API /schedules ===")

def api(method, path, **kwargs):
    fn = getattr(requests, method)
    return fn(f"{BASE_URL}{path}", timeout=10, **kwargs)

# 23. POST /schedules
try:
    r = api("post", "/schedules", json={"project_name": "m7-api-sched", "schedule_type": "cron", "cron_expr": "0 * * * *"})
    ok23 = r.status_code == 200 and "id" in r.json().get("schedule", {})
    check(23, "POST /schedules → 200, schedule.id 존재", ok23, f"{r.status_code} {r.text[:200]}")
    _api_sched_id = r.json().get("schedule", {}).get("id")
except Exception as e:
    check(23, "POST /schedules → 200, schedule.id 존재", False, str(e))
    _api_sched_id = None

# 24. GET /schedules
try:
    r = api("get", "/schedules")
    ok24 = r.status_code == 200 and "items" in r.json()
    check(24, "GET /schedules → items 포함", ok24, f"{r.status_code} {r.text[:100]}")
except Exception as e:
    check(24, "GET /schedules → items 포함", False, str(e))

# 25. GET /schedules/{id}
if _api_sched_id:
    try:
        r = api("get", f"/schedules/{_api_sched_id}")
        ok25 = r.status_code == 200 and "schedule" in r.json()
        check(25, "GET /schedules/{id} → 200", ok25, f"{r.status_code} {r.text[:100]}")
    except Exception as e:
        check(25, "GET /schedules/{id} → 200", False, str(e))
else:
    check(25, "GET /schedules/{id} → 200", False, "no api_sched_id")

# 26. PATCH /schedules/{id} enabled=False
if _api_sched_id:
    try:
        r = api("patch", f"/schedules/{_api_sched_id}", json={"enabled": False})
        ok26 = r.status_code == 200 and r.json().get("schedule", {}).get("enabled") is False
        check(26, "PATCH /schedules/{id} enabled=False → enabled=False", ok26, f"{r.status_code} {r.text[:200]}")
    except Exception as e:
        check(26, "PATCH /schedules/{id} enabled=False → enabled=False", False, str(e))
else:
    check(26, "PATCH /schedules/{id} enabled=False → enabled=False", False, "no api_sched_id")

# 27. POST /schedules/{id}/run
if _api_sched_id:
    try:
        r = api("post", f"/schedules/{_api_sched_id}/run")
        ok27 = r.status_code == 200 and "cycle_result" in r.json().get("result", {})
        check(27, "POST /schedules/{id}/run → 200, result.cycle_result 존재", ok27, f"{r.status_code} {r.text[:300]}")
    except Exception as e:
        check(27, "POST /schedules/{id}/run → 200, result.cycle_result 존재", False, str(e))
else:
    check(27, "POST /schedules/{id}/run → 200, result.cycle_result 존재", False, "no api_sched_id")

# 28. DELETE /schedules/{id}
if _api_sched_id:
    try:
        r = api("delete", f"/schedules/{_api_sched_id}")
        ok28 = r.status_code == 200 and r.json().get("ok") is True
        check(28, "DELETE /schedules/{id} → 200", ok28, f"{r.status_code} {r.text[:100]}")
    except Exception as e:
        check(28, "DELETE /schedules/{id} → 200", False, str(e))
else:
    check(28, "DELETE /schedules/{id} → 200", False, "no api_sched_id")


# ─────────────────────────────────────────────────────────────────────────────
# Section D: Manager API /watchers + /incidents (29-35)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== D. Manager API /watchers + /incidents ===")

# 29. POST /watchers
try:
    r = api("post", "/watchers", json={
        "project_name": "m7-api-watch",
        "watch_type": "http_check",
        "metadata": {"check_command": "echo monitor", "threshold": 3},
    })
    ok29 = r.status_code == 200 and "id" in r.json().get("watch_job", {})
    check(29, "POST /watchers → 200, watch_job.id 존재", ok29, f"{r.status_code} {r.text[:200]}")
    _api_wj_id = r.json().get("watch_job", {}).get("id")
except Exception as e:
    check(29, "POST /watchers → 200, watch_job.id 존재", False, str(e))
    _api_wj_id = None

# 30. GET /watchers
try:
    r = api("get", "/watchers")
    ok30 = r.status_code == 200 and "items" in r.json()
    check(30, "GET /watchers → items 포함", ok30, f"{r.status_code} {r.text[:100]}")
except Exception as e:
    check(30, "GET /watchers → items 포함", False, str(e))

# 31. PATCH /watchers/{id}/status status=paused
if _api_wj_id:
    try:
        r = api("patch", f"/watchers/{_api_wj_id}/status", json={"status": "paused"})
        ok31 = r.status_code == 200
        check(31, "PATCH /watchers/{id}/status status=paused → 200", ok31, f"{r.status_code} {r.text[:200]}")
    except Exception as e:
        check(31, "PATCH /watchers/{id}/status status=paused → 200", False, str(e))
else:
    check(31, "PATCH /watchers/{id}/status status=paused → 200", False, "no api_wj_id")

# 32. POST /watchers/{id}/check
if _api_wj_id:
    try:
        r = api("post", f"/watchers/{_api_wj_id}/check")
        body = r.json()
        ok32 = r.status_code == 200 and "ok" in body.get("result", {})
        check(32, "POST /watchers/{id}/check → 200, result.ok bool", ok32, f"{r.status_code} {r.text[:200]}")
    except Exception as e:
        check(32, "POST /watchers/{id}/check → 200, result.ok bool", False, str(e))
else:
    check(32, "POST /watchers/{id}/check → 200, result.ok bool", False, "no api_wj_id")

# 33. GET /watchers/{id}/events
if _api_wj_id:
    try:
        r = api("get", f"/watchers/{_api_wj_id}/events")
        ok33 = r.status_code == 200 and "items" in r.json()
        check(33, "GET /watchers/{id}/events → items list", ok33, f"{r.status_code} {r.text[:200]}")
    except Exception as e:
        check(33, "GET /watchers/{id}/events → items list", False, str(e))
else:
    check(33, "GET /watchers/{id}/events → items list", False, "no api_wj_id")

# 34. GET /incidents
try:
    r = api("get", "/incidents")
    ok34 = r.status_code == 200 and "items" in r.json()
    check(34, "GET /incidents → 200, items list", ok34, f"{r.status_code} {r.text[:100]}")
    # find an open incident for item 35
    _open_incidents = [i for i in r.json().get("items", []) if i.get("status") == "open"]
    _api_inc_id = _open_incidents[0]["id"] if _open_incidents else None
except Exception as e:
    check(34, "GET /incidents → 200, items list", False, str(e))
    _api_inc_id = None

# 35. POST /incidents/{id}/resolve
if _api_inc_id:
    try:
        r = api("post", f"/incidents/{_api_inc_id}/resolve")
        ok35 = r.status_code == 200 and r.json().get("incident", {}).get("status") == "resolved"
        check(35, "POST /incidents/{id}/resolve → 200, status=resolved", ok35, f"{r.status_code} {r.text[:200]}")
    except Exception as e:
        check(35, "POST /incidents/{id}/resolve → 200, status=resolved", False, str(e))
else:
    # Create an incident via watch_service and then resolve via API
    try:
        _tmp_inc = create_incident(_wp_id, "info", "api resolve test", database_url=DB_URL)
        _api_inc_id = str(_tmp_inc["id"])
        r = api("post", f"/incidents/{_api_inc_id}/resolve")
        ok35 = r.status_code == 200 and r.json().get("incident", {}).get("status") == "resolved"
        check(35, "POST /incidents/{id}/resolve → 200, status=resolved", ok35, f"{r.status_code} {r.text[:200]}")
    except Exception as e:
        check(35, "POST /incidents/{id}/resolve → 200, status=resolved", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
total = passed + failed
print(f"\n{'='*60}")
print(f"M7 Smoke Test Results: {passed}/{total} passed")
print(f"{'='*60}")
if failed > 0:
    print("\nFailed items:")
    for line in results:
        if "FAIL" in line:
            print(" ", line)
sys.exit(0 if failed == 0 else 1)
