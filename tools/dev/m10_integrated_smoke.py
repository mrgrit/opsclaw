#!/usr/bin/env python3
"""M10 Integrated Smoke Test — 30 items
Covers:
  A. notification_service unit — Channel (items 1-7)
  B. notification_service unit — Rule & Delivery (items 8-15)
  C. integration hooks (items 16-20)
  D. Manager API /notifications (items 21-30)
"""
import sys
import uuid
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BASE_URL = "http://127.0.0.1:8000"
DB_URL = "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw"

# Unique prefix per run to avoid duplicate name conflicts
_RUN = uuid.uuid4().hex[:8]

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
    line = f"[{n:02d}] {status} — {desc}"
    if not ok and detail:
        line += f"\n       detail: {detail}"
    results.append(line)
    print(line)


# ─────────────────────────────────────────────────────────────────────────────
# A. notification_service unit — Channel (1-7)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== A. notification_service unit — Channel ===")

from packages.notification_service import (
    create_channel,
    get_channel,
    get_channel_by_name,
    list_channels,
    update_channel,
    delete_channel,
    create_rule,
    get_rule,
    list_rules,
    update_rule,
    delete_rule,
    fire_event,
    list_notification_logs,
)

_ch_webhook = None
_ch_log = None

# 1. create_channel 'webhook' → dict with id
try:
    _ch_webhook = create_channel(
        f"smoke-webhook-{_RUN}",
        "webhook",
        config={"url": "http://127.0.0.1:19999/no-such-endpoint"},
        database_url=DB_URL,
    )
    check(1, "create_channel 'webhook' → dict with id", "id" in _ch_webhook and _ch_webhook["channel_type"] == "webhook")
except Exception as e:
    check(1, "create_channel 'webhook' → dict with id", False, str(e))
    _ch_webhook = {"id": None}

# 2. create_channel 'log' → dict with id
try:
    _ch_log = create_channel(f"smoke-log-{_RUN}", "log", database_url=DB_URL)
    check(2, "create_channel 'log' → dict with id", "id" in _ch_log and _ch_log["channel_type"] == "log")
except Exception as e:
    check(2, "create_channel 'log' → dict with id", False, str(e))
    _ch_log = {"id": None}

# 3. get_channel → fields present
try:
    ch = get_channel(str(_ch_log["id"]), database_url=DB_URL)
    check(3, "get_channel → fields present", ch is not None and "name" in ch and "channel_type" in ch)
except Exception as e:
    check(3, "get_channel → fields present", False, str(e))

# 4. get_channel_by_name → found
try:
    ch = get_channel_by_name(f"smoke-log-{_RUN}", database_url=DB_URL)
    check(4, "get_channel_by_name → found", ch is not None and str(ch["id"]) == str(_ch_log["id"]))
except Exception as e:
    check(4, "get_channel_by_name → found", False, str(e))

# 5. list_channels → two channels present
try:
    channels = list_channels(database_url=DB_URL)
    names = [c["name"] for c in channels]
    check(5, "list_channels → two smoke channels present",
          f"smoke-webhook-{_RUN}" in names and f"smoke-log-{_RUN}" in names)
except Exception as e:
    check(5, "list_channels → two smoke channels present", False, str(e))

# 6. update_channel enabled=False → disabled
try:
    updated = update_channel(str(_ch_webhook["id"]), enabled=False, database_url=DB_URL)
    check(6, "update_channel enabled=False → disabled", updated["enabled"] is False)
except Exception as e:
    check(6, "update_channel enabled=False → disabled", False, str(e))

# 7. list_channels enabled_only=True → disabled excluded
try:
    enabled = list_channels(enabled_only=True, database_url=DB_URL)
    names = [c["name"] for c in enabled]
    check(7, "list_channels enabled_only=True → disabled excluded",
          f"smoke-webhook-{_RUN}" not in names and f"smoke-log-{_RUN}" in names)
except Exception as e:
    check(7, "list_channels enabled_only=True → disabled excluded", False, str(e))

# Re-enable webhook for subsequent tests
try:
    update_channel(str(_ch_webhook["id"]), enabled=True, database_url=DB_URL)
except Exception:
    pass

# ─────────────────────────────────────────────────────────────────────────────
# B. notification_service unit — Rule & Delivery (8-15)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== B. notification_service unit — Rule & Delivery ===")

_rule_incident = None
_rule_wildcard = None

# 8. create_rule event_type='incident.created' → dict with id
try:
    _rule_incident = create_rule(
        f"smoke-incident-rule-{_RUN}",
        "incident.created",
        str(_ch_log["id"]),
        database_url=DB_URL,
    )
    check(8, "create_rule event_type='incident.created' → dict with id", "id" in _rule_incident)
except Exception as e:
    check(8, "create_rule event_type='incident.created' → dict with id", False, str(e))
    _rule_incident = {"id": None}

# 9. create_rule event_type='*' (wildcard) → dict with id
try:
    _rule_wildcard = create_rule(
        f"smoke-wildcard-rule-{_RUN}",
        "*",
        str(_ch_log["id"]),
        database_url=DB_URL,
    )
    check(9, "create_rule event_type='*' (wildcard) → dict with id", "id" in _rule_wildcard)
except Exception as e:
    check(9, "create_rule event_type='*' (wildcard) → dict with id", False, str(e))
    _rule_wildcard = {"id": None}

# 10. list_rules → both rules present
try:
    rules = list_rules(enabled_only=False, database_url=DB_URL)
    rule_ids = [str(r["id"]) for r in rules]
    check(10, "list_rules → both smoke rules present",
          str(_rule_incident["id"]) in rule_ids and str(_rule_wildcard["id"]) in rule_ids)
except Exception as e:
    check(10, "list_rules → both smoke rules present", False, str(e))

# 11. fire_event('incident.created', payload) → logs ≥ 2
try:
    logs = fire_event("incident.created", {"severity": "warning", "summary": "smoke"}, database_url=DB_URL)
    check(11, "fire_event('incident.created') → logs ≥ 2 (rule + wildcard)", len(logs) >= 2, f"got {len(logs)}")
except Exception as e:
    check(11, "fire_event('incident.created') → logs ≥ 2", False, str(e))

# 12. fire_event('schedule.failed') → logs ≥ 1 (wildcard matches)
try:
    logs = fire_event("schedule.failed", {"schedule_id": "x", "error": "smoke"}, database_url=DB_URL)
    check(12, "fire_event('schedule.failed') → logs ≥ 1 (wildcard)", len(logs) >= 1, f"got {len(logs)}")
except Exception as e:
    check(12, "fire_event('schedule.failed') → logs ≥ 1", False, str(e))

# 13. fire_event('unknown.event') → logs == wildcard rule count
try:
    logs_before = list_notification_logs(database_url=DB_URL)
    logs = fire_event("unknown.event", {}, database_url=DB_URL)
    # Only wildcard should match
    wildcard_rules = [r for r in list_rules(enabled_only=True, database_url=DB_URL) if r["event_type"] == "*"]
    check(13, "fire_event('unknown.event') → only wildcard rules match", len(logs) == len(wildcard_rules), f"got {len(logs)}, expected {len(wildcard_rules)}")
except Exception as e:
    check(13, "fire_event('unknown.event') → only wildcard rules match", False, str(e))

# 14. list_notification_logs event_type='incident.created' → len ≥ 1
try:
    logs = list_notification_logs(event_type="incident.created", database_url=DB_URL)
    check(14, "list_notification_logs event_type='incident.created' → ≥ 1", len(logs) >= 1, f"got {len(logs)}")
except Exception as e:
    check(14, "list_notification_logs event_type='incident.created' → ≥ 1", False, str(e))

# 15. delete_rule → fire_event after returns fewer logs
try:
    # create a throwaway rule to delete
    tmp_rule = create_rule(f"smoke-tmp-rule-{_RUN}", "incident.created", str(_ch_log["id"]), database_url=DB_URL)
    before = fire_event("incident.created", {"test": "before_delete"}, database_url=DB_URL)
    delete_rule(str(tmp_rule["id"]), database_url=DB_URL)
    after = fire_event("incident.created", {"test": "after_delete"}, database_url=DB_URL)
    check(15, "delete_rule → fire_event after returns fewer logs", len(after) < len(before), f"before={len(before)}, after={len(after)}")
except Exception as e:
    check(15, "delete_rule → fire_event after returns fewer logs", False, str(e))

# ─────────────────────────────────────────────────────────────────────────────
# C. integration hooks (16-20)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== C. integration hooks ===")

from packages.watch_service import create_incident
from packages.scheduler_service import create_schedule, execute_due_schedule
from packages.project_service import create_project_record

# 16. watch_service.create_incident() → notification_logs incident.created entry exists
try:
    logs_before = list_notification_logs(event_type="incident.created", database_url=DB_URL)
    incident = create_incident(
        project_id=None,
        severity="critical",
        summary="M10 smoke hook test",
        database_url=DB_URL,
    )
    logs_after = list_notification_logs(event_type="incident.created", database_url=DB_URL)
    check(16, "create_incident() fires incident.created notification", len(logs_after) > len(logs_before))
except Exception as e:
    check(16, "create_incident() fires incident.created notification", False, str(e))

# 17. log payload has severity field matching
try:
    logs = list_notification_logs(event_type="incident.created", limit=5, database_url=DB_URL)
    latest = logs[0] if logs else {}
    payload = latest.get("payload") or {}
    check(17, "notification log payload has severity='critical'", payload.get("severity") == "critical", str(payload))
except Exception as e:
    check(17, "notification log payload has severity='critical'", False, str(e))

# 18. execute_due_schedule error → schedule.failed log exists
try:
    logs_before = list_notification_logs(event_type="schedule.failed", database_url=DB_URL)
    # Create a schedule pointing to a non-existent project to force error
    bad_project = create_project_record("m10-smoke-sched-fail", "smoke fail test", mode="batch", database_url=DB_URL)
    bad_sched = create_schedule(
        project_id=str(bad_project["id"]),
        schedule_type="batch",
        cron_expr="0 0 1 1 0",  # next year
        database_url=DB_URL,
    )
    # Force an error by deleting the project before executing
    import psycopg2
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DELETE FROM projects WHERE id = %s", (str(bad_project["id"]),))
    cur.close()
    conn.close()
    result = execute_due_schedule(bad_sched, database_url=DB_URL)
    logs_after = list_notification_logs(event_type="schedule.failed", database_url=DB_URL)
    check(18, "execute_due_schedule error → schedule.failed notification", len(logs_after) > len(logs_before))
except Exception as e:
    check(18, "execute_due_schedule error → schedule.failed notification", False, str(e))

# 19. update_rule enabled=False → fire_event after does not increment that rule's logs
try:
    update_rule(str(_rule_incident["id"]), enabled=False, database_url=DB_URL)
    logs_before = list_notification_logs(event_type="incident.created", database_url=DB_URL)
    fire_event("incident.created", {"test": "disabled_rule"}, database_url=DB_URL)
    logs_after = list_notification_logs(event_type="incident.created", database_url=DB_URL)
    # The disabled rule should not have been fired — only wildcard matches
    # Logs may increase by 1 (wildcard), but incident-specific rule should not appear
    disabled_rule_logs_after = [
        l for l in logs_after if str(l.get("rule_id")) == str(_rule_incident["id"])
    ]
    disabled_rule_logs_before = [
        l for l in logs_before if str(l.get("rule_id")) == str(_rule_incident["id"])
    ]
    check(19, "disabled rule → no new log entries for that rule",
          len(disabled_rule_logs_after) == len(disabled_rule_logs_before))
    # Re-enable for cleanup
    update_rule(str(_rule_incident["id"]), enabled=True, database_url=DB_URL)
except Exception as e:
    check(19, "disabled rule → no new log entries for that rule", False, str(e))

# 20. delete_channel → cascade → channel's rules gone
try:
    tmp_ch = create_channel(f"smoke-cascade-ch-{_RUN}", "log", database_url=DB_URL)
    tmp_r = create_rule(f"smoke-cascade-rule-{_RUN}", "incident.created", str(tmp_ch["id"]), database_url=DB_URL)
    delete_channel(str(tmp_ch["id"]), database_url=DB_URL)
    # The rule should be cascade-deleted
    rules_after = list_rules(enabled_only=False, database_url=DB_URL)
    rule_ids = [str(r["id"]) for r in rules_after]
    check(20, "delete_channel cascade deletes associated rules", str(tmp_r["id"]) not in rule_ids)
except Exception as e:
    check(20, "delete_channel cascade deletes associated rules", False, str(e))

# ─────────────────────────────────────────────────────────────────────────────
# D. Manager API /notifications (21-30)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== D. Manager API /notifications ===")

_api_ch_id = None
_api_rule_id = None

# 21. POST /notifications/channels webhook → 200, channel.id
try:
    r = requests.post(f"{BASE_URL}/notifications/channels", json={
        "name": f"api-smoke-webhook-{_RUN}",
        "channel_type": "webhook",
        "config": {"url": "http://127.0.0.1:19999/hook"},
    }, timeout=10)
    data = r.json()
    _api_ch_id = data.get("channel", {}).get("id")
    check(21, "POST /notifications/channels webhook → 200, channel.id", r.status_code == 200 and _api_ch_id is not None)
except Exception as e:
    check(21, "POST /notifications/channels webhook → 200, channel.id", False, str(e))

# 22. GET /notifications/channels → 200, items list
try:
    r = requests.get(f"{BASE_URL}/notifications/channels", timeout=10)
    data = r.json()
    check(22, "GET /notifications/channels → 200, items list", r.status_code == 200 and "items" in data)
except Exception as e:
    check(22, "GET /notifications/channels → 200, items list", False, str(e))

# 23. GET /notifications/channels/{id} → 200, name matches
try:
    r = requests.get(f"{BASE_URL}/notifications/channels/{_api_ch_id}", timeout=10)
    data = r.json()
    ch_name = data.get("channel", {}).get("name")
    check(23, "GET /notifications/channels/{id} → 200, name matches", r.status_code == 200 and ch_name == f"api-smoke-webhook-{_RUN}")
except Exception as e:
    check(23, "GET /notifications/channels/{id} → 200, name matches", False, str(e))

# 24. POST /notifications/channels log → 200
try:
    r = requests.post(f"{BASE_URL}/notifications/channels", json={
        "name": f"api-smoke-log-{_RUN}",
        "channel_type": "log",
    }, timeout=10)
    check(24, "POST /notifications/channels log → 200", r.status_code == 200)
    _api_log_ch_id = r.json().get("channel", {}).get("id")
except Exception as e:
    check(24, "POST /notifications/channels log → 200", False, str(e))
    _api_log_ch_id = None

# 25. POST /notifications/rules → 200, rule.id
try:
    r = requests.post(f"{BASE_URL}/notifications/rules", json={
        "name": "api-smoke-rule",
        "event_type": "incident.created",
        "channel_id": _api_log_ch_id or _api_ch_id,
    }, timeout=10)
    data = r.json()
    _api_rule_id = data.get("rule", {}).get("id")
    check(25, "POST /notifications/rules → 200, rule.id", r.status_code == 200 and _api_rule_id is not None)
except Exception as e:
    check(25, "POST /notifications/rules → 200, rule.id", False, str(e))

# 26. GET /notifications/rules → 200, items present
try:
    r = requests.get(f"{BASE_URL}/notifications/rules", timeout=10)
    data = r.json()
    check(26, "GET /notifications/rules → 200, items present", r.status_code == 200 and "items" in data and len(data["items"]) > 0)
except Exception as e:
    check(26, "GET /notifications/rules → 200, items present", False, str(e))

# 27. POST /notifications/test → 200, logs list
try:
    r = requests.post(f"{BASE_URL}/notifications/test", json={
        "event_type": "incident.created",
        "payload": {"severity": "info", "summary": "api smoke test"},
    }, timeout=10)
    data = r.json()
    check(27, "POST /notifications/test → 200, logs list", r.status_code == 200 and "logs" in data)
except Exception as e:
    check(27, "POST /notifications/test → 200, logs list", False, str(e))

# 28. GET /notifications/logs → 200, items list
try:
    r = requests.get(f"{BASE_URL}/notifications/logs", timeout=10)
    data = r.json()
    check(28, "GET /notifications/logs → 200, items list", r.status_code == 200 and "items" in data)
except Exception as e:
    check(28, "GET /notifications/logs → 200, items list", False, str(e))

# 29. DELETE /notifications/rules/{id} → 200, ok=true
try:
    r = requests.delete(f"{BASE_URL}/notifications/rules/{_api_rule_id}", timeout=10)
    data = r.json()
    check(29, "DELETE /notifications/rules/{id} → 200, ok=true", r.status_code == 200 and data.get("ok") is True)
except Exception as e:
    check(29, "DELETE /notifications/rules/{id} → 200, ok=true", False, str(e))

# 30. DELETE /notifications/channels/{id} → 200, ok=true
try:
    r = requests.delete(f"{BASE_URL}/notifications/channels/{_api_ch_id}", timeout=10)
    data = r.json()
    check(30, "DELETE /notifications/channels/{id} → 200, ok=true", r.status_code == 200 and data.get("ok") is True)
except Exception as e:
    check(30, "DELETE /notifications/channels/{id} → 200, ok=true", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"M10 Smoke Test: {passed}/{passed + failed} passed")
if failed:
    print("FAILED items:")
    for r in results:
        if "FAIL" in r:
            print(f"  {r}")
print(f"{'='*60}")
sys.exit(0 if failed == 0 else 1)
