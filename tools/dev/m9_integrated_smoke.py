#!/usr/bin/env python3
"""M9 Integrated Smoke Test — 35 items
Covers:
  A. audit_service unit      (items 1-7)
  B. rbac_service unit       (items 8-15)
  C. monitoring_service unit (items 16-20)
  D. reporting_service unit  (items 21-25)
  E. backup_service unit     (items 26-28)
  F. Manager API /admin + /reports (items 29-35)
"""
import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BASE_URL = "http://127.0.0.1:8000"
DB_URL = "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw"
BACKUP_DIR = "/tmp/m9_smoke_backups"

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


# ── Setup ─────────────────────────────────────────────────────────────────────
from packages.project_service import (
    create_project_record,
    plan_project_record,
    execute_project_record,
    validate_project_record,
    finalize_report_stage_record,
    create_minimal_evidence_record,
)

_p = create_project_record("m9-smoke-main", "M9 smoke test", mode="one_shot", database_url=DB_URL)
_pid = _p["id"]
plan_project_record(_pid, database_url=DB_URL)
execute_project_record(_pid, database_url=DB_URL)
create_minimal_evidence_record(_pid, "echo smoke", "smoke output", "", 0, database_url=DB_URL)
validate_project_record(_pid, database_url=DB_URL)
finalize_report_stage_record(_pid, database_url=DB_URL)


# ─────────────────────────────────────────────────────────────────────────────
# A. audit_service unit (1-7)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== A. audit_service unit ===")

from packages.audit_service import (
    log_audit_event,
    query_audit_logs,
    get_audit_event,
    export_audit_json,
    export_audit_csv,
)

# 1. log_audit_event → dict with id
try:
    ev = log_audit_event("project.create", "manager", "manager-api", project_id=_pid,
                          payload={"smoke": True}, database_url=DB_URL)
    check(1, "log_audit_event → dict with id", "id" in ev and ev["event_type"] == "project.create")
    _aud_id = ev["id"]
except Exception as e:
    check(1, "log_audit_event → dict with id", False, str(e))
    _aud_id = None

# 2. get_audit_event → fields ok
if _aud_id:
    try:
        row = get_audit_event(_aud_id, database_url=DB_URL)
        fields_ok = row and all(k in row for k in ("id", "event_type", "actor_type", "actor_id", "created_at"))
        check(2, "get_audit_event → 필드 검증", bool(fields_ok))
    except Exception as e:
        check(2, "get_audit_event → 필드 검증", False, str(e))
else:
    check(2, "get_audit_event → 필드 검증", False, "no aud_id")

# 3. query_audit_logs → list not empty
try:
    rows = query_audit_logs(limit=10, database_url=DB_URL)
    check(3, "query_audit_logs → 리스트 반환", len(rows) > 0)
except Exception as e:
    check(3, "query_audit_logs → 리스트 반환", False, str(e))

# 4. query_audit_logs with event_type filter
try:
    rows = query_audit_logs(event_type="project.create", database_url=DB_URL)
    all_match = all(r["event_type"] == "project.create" for r in rows)
    check(4, "query_audit_logs event_type 필터 → 일치", all_match and len(rows) > 0)
except Exception as e:
    check(4, "query_audit_logs event_type 필터", False, str(e))

# 5. query_audit_logs with project_id filter
try:
    rows = query_audit_logs(project_id=_pid, database_url=DB_URL)
    all_match = all(r["project_id"] == _pid for r in rows)
    check(5, "query_audit_logs project_id 필터 → 일치", all_match and len(rows) > 0)
except Exception as e:
    check(5, "query_audit_logs project_id 필터", False, str(e))

# 6. export_audit_json → valid JSON string
try:
    j = export_audit_json(limit=5, database_url=DB_URL)
    import json as _json
    parsed = _json.loads(j)
    check(6, "export_audit_json → valid JSON", isinstance(parsed, list))
except Exception as e:
    check(6, "export_audit_json → valid JSON", False, str(e))

# 7. export_audit_csv → CSV with header line
try:
    csv_str = export_audit_csv(limit=5, database_url=DB_URL)
    lines = csv_str.splitlines()
    check(7, "export_audit_csv → CSV with header", len(lines) >= 2 and "event_type" in lines[0])
except Exception as e:
    check(7, "export_audit_csv → CSV with header", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# B. rbac_service unit (8-15)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== B. rbac_service unit ===")

from packages.rbac_service import (
    create_role,
    get_role,
    get_role_by_name,
    list_roles,
    assign_role,
    revoke_role,
    get_actor_roles,
    get_actor_permissions,
    check_permission,
    update_role_permissions,
    delete_role,
)

# 8. list_roles → seeded roles present
try:
    roles = list_roles(database_url=DB_URL)
    names = [r["name"] for r in roles]
    check(8, "list_roles → admin/operator/viewer/auditor 존재",
          all(n in names for n in ("admin", "operator", "viewer", "auditor")))
except Exception as e:
    check(8, "list_roles → seed roles", False, str(e))

# 9. create_role → dict with id
try:
    new_role = create_role("smoke_role", ["project:read", "evidence:read"], "smoke test role", database_url=DB_URL)
    check(9, "create_role → dict with id", "id" in new_role and new_role["name"] == "smoke_role")
    _new_role_id = str(new_role["id"])
except Exception as e:
    check(9, "create_role → dict with id", False, str(e))
    _new_role_id = None

# 10. get_role → fields ok
if _new_role_id:
    try:
        row = get_role(_new_role_id, database_url=DB_URL)
        check(10, "get_role → 필드 검증", row is not None and row["name"] == "smoke_role")
    except Exception as e:
        check(10, "get_role → 필드 검증", False, str(e))
else:
    check(10, "get_role → 필드 검증", False, "no role_id")

# 11. get_role_by_name → finds seeded 'admin' role
try:
    admin = get_role_by_name("admin", database_url=DB_URL)
    check(11, "get_role_by_name('admin') → found", admin is not None and "*" in (admin.get("permissions") or []))
    _admin_role_id = str(admin["id"])
except Exception as e:
    check(11, "get_role_by_name('admin') → found", False, str(e))
    _admin_role_id = None

# 12. assign_role → actor has role
if _new_role_id:
    try:
        ar = assign_role("smoke_actor", _new_role_id, database_url=DB_URL)
        check(12, "assign_role → assignment returned", ar["actor_id"] == "smoke_actor")
    except Exception as e:
        check(12, "assign_role → assignment returned", False, str(e))
else:
    check(12, "assign_role → assignment returned", False, "no role_id")

# 13. get_actor_permissions → correct perms
try:
    perms = get_actor_permissions("smoke_actor", database_url=DB_URL)
    check(13, "get_actor_permissions → project:read + evidence:read",
          "project:read" in perms and "evidence:read" in perms)
except Exception as e:
    check(13, "get_actor_permissions", False, str(e))

# 14. check_permission → True for allowed, False for denied
try:
    ok14a = check_permission("smoke_actor", "project:read", database_url=DB_URL)
    ok14b = not check_permission("smoke_actor", "asset:write", database_url=DB_URL)
    check(14, "check_permission → 허용/거부 정확", ok14a and ok14b)
except Exception as e:
    check(14, "check_permission", False, str(e))

# 15. admin actor with '*' has all permissions
if _admin_role_id:
    try:
        assign_role("admin_actor", _admin_role_id, database_url=DB_URL)
        ok15 = check_permission("admin_actor", "any:random:permission", database_url=DB_URL)
        check(15, "admin '*' → check_permission any permission → True", ok15)
    except Exception as e:
        check(15, "admin '*' → check_permission any", False, str(e))
else:
    check(15, "admin '*' → check_permission any", False, "no admin_role_id")


# ─────────────────────────────────────────────────────────────────────────────
# C. monitoring_service unit (16-20)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== C. monitoring_service unit ===")

from packages.monitoring_service import get_system_health, get_operational_metrics

# 16. get_system_health → required keys
try:
    h = get_system_health(database_url=DB_URL)
    required = {"status", "warnings", "collected_at", "projects", "assets", "incidents", "schedules", "watchers", "evidence_24h"}
    check(16, "get_system_health → required keys 존재", required.issubset(h.keys()), str(list(h.keys())))
except Exception as e:
    check(16, "get_system_health → required keys", False, str(e))

# 17. get_system_health → status is healthy or degraded
try:
    h = get_system_health(database_url=DB_URL)
    check(17, "get_system_health → status in (healthy, degraded)", h["status"] in ("healthy", "degraded"))
except Exception as e:
    check(17, "get_system_health → status valid", False, str(e))

# 18. get_system_health → projects.total > 0
try:
    h = get_system_health(database_url=DB_URL)
    check(18, "get_system_health → projects.total > 0", h["projects"]["total"] > 0)
except Exception as e:
    check(18, "get_system_health → projects.total > 0", False, str(e))

# 19. get_operational_metrics → required keys
try:
    m = get_operational_metrics(database_url=DB_URL)
    required = {"evidence", "validation", "recent_7d", "top_assets_by_evidence", "incidents", "audit", "memory"}
    check(19, "get_operational_metrics → required keys 존재", required.issubset(m.keys()))
except Exception as e:
    check(19, "get_operational_metrics → required keys", False, str(e))

# 20. get_operational_metrics → evidence.total numeric
try:
    m = get_operational_metrics(database_url=DB_URL)
    check(20, "get_operational_metrics → evidence.total >= 0", isinstance(m["evidence"]["total"], int) and m["evidence"]["total"] >= 0)
except Exception as e:
    check(20, "get_operational_metrics → evidence.total", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# D. reporting_service unit (21-25)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== D. reporting_service unit ===")

from packages.reporting_service import (
    generate_project_report,
    export_evidence_pack,
    export_evidence_pack_json,
)

# 21. generate_project_report → required keys
try:
    rpt = generate_project_report(_pid, database_url=DB_URL)
    required = {"generated_at", "project", "summary", "assets", "evidence", "validation_runs", "reports"}
    check(21, "generate_project_report → required keys 존재", required.issubset(rpt.keys()))
except Exception as e:
    check(21, "generate_project_report → required keys", False, str(e))

# 22. summary.evidence_count >= 1
try:
    rpt = generate_project_report(_pid, database_url=DB_URL)
    check(22, "generate_project_report → evidence_count >= 1", rpt["summary"]["evidence_count"] >= 1)
except Exception as e:
    check(22, "generate_project_report → evidence_count", False, str(e))

# 23. export_evidence_pack → pack_type, project_id
try:
    pack = export_evidence_pack(_pid, database_url=DB_URL)
    check(23, "export_evidence_pack → pack_type + project_id", pack.get("pack_type") == "evidence_pack" and pack.get("project_id") == _pid)
except Exception as e:
    check(23, "export_evidence_pack", False, str(e))

# 24. export_evidence_pack_json → valid JSON string
try:
    j = export_evidence_pack_json(_pid, database_url=DB_URL)
    import json as _json
    parsed = _json.loads(j)
    check(24, "export_evidence_pack_json → valid JSON", "pack_type" in parsed)
except Exception as e:
    check(24, "export_evidence_pack_json → valid JSON", False, str(e))

# 25. reports_count >= 1 (we finalized report stage)
try:
    rpt = generate_project_report(_pid, database_url=DB_URL)
    check(25, "generate_project_report → reports_count >= 1", rpt["summary"]["reports_count"] >= 1)
except Exception as e:
    check(25, "generate_project_report → reports_count", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# E. backup_service unit (26-28)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== E. backup_service unit ===")

from packages.backup_service import create_backup, list_backups, get_backup_info

# 26. create_backup → ok=True, size_bytes > 0
try:
    result = create_backup(BACKUP_DIR, database_url=DB_URL)
    check(26, "create_backup → ok=True, size_bytes > 0",
          result["ok"] is True and (result.get("size_bytes") or 0) > 0, str(result))
    _backup_path = result.get("path")
except Exception as e:
    check(26, "create_backup → ok=True, size_bytes > 0", False, str(e))
    _backup_path = None

# 27. list_backups → at least 1 file
try:
    bl = list_backups(BACKUP_DIR)
    check(27, "list_backups → 1개 이상", len(bl) >= 1, f"count={len(bl)}")
except Exception as e:
    check(27, "list_backups → 1개 이상", False, str(e))

# 28. get_backup_info → metadata dict
if _backup_path:
    try:
        info = get_backup_info(_backup_path)
        check(28, "get_backup_info → filename, size_bytes, created_at",
              info is not None and all(k in info for k in ("filename", "size_bytes", "created_at")))
    except Exception as e:
        check(28, "get_backup_info", False, str(e))
else:
    check(28, "get_backup_info", False, "no backup_path")


# ─────────────────────────────────────────────────────────────────────────────
# F. Manager API /admin + /reports (29-35)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== F. Manager API /admin + /reports ===")


def api(method, path, **kwargs):
    fn = getattr(requests, method)
    return fn(f"{BASE_URL}{path}", timeout=15, **kwargs)


# 29. GET /admin/health → status field
try:
    r = api("get", "/admin/health")
    ok29 = r.status_code == 200 and "status" in r.json()
    check(29, "GET /admin/health → 200, status 필드", ok29, f"{r.status_code} {r.text[:100]}")
except Exception as e:
    check(29, "GET /admin/health", False, str(e))

# 30. GET /admin/metrics → evidence.total
try:
    r = api("get", "/admin/metrics")
    ok30 = r.status_code == 200 and "evidence" in r.json()
    check(30, "GET /admin/metrics → 200, evidence 필드", ok30, f"{r.status_code} {r.text[:100]}")
except Exception as e:
    check(30, "GET /admin/metrics", False, str(e))

# 31. GET /admin/audit → items list
try:
    r = api("get", "/admin/audit", params={"limit": 10})
    ok31 = r.status_code == 200 and "items" in r.json()
    check(31, "GET /admin/audit → 200, items list", ok31, f"{r.status_code} count={len(r.json().get('items', []))}")
except Exception as e:
    check(31, "GET /admin/audit", False, str(e))

# 32. POST /admin/audit/export format=json
try:
    r = api("post", "/admin/audit/export", json={"format": "json", "limit": 5})
    ok32 = r.status_code == 200 and r.json().get("format") == "json" and "content" in r.json()
    check(32, "POST /admin/audit/export json → 200, content", ok32, f"{r.status_code} {r.text[:100]}")
except Exception as e:
    check(32, "POST /admin/audit/export json", False, str(e))

# 33. GET /admin/roles → seeded roles
try:
    r = api("get", "/admin/roles")
    names = [ro["name"] for ro in r.json().get("items", [])]
    ok33 = r.status_code == 200 and "admin" in names
    check(33, "GET /admin/roles → 200, admin role 존재", ok33, f"{r.status_code} {names}")
except Exception as e:
    check(33, "GET /admin/roles", False, str(e))

# 34. GET /reports/project/{id} → summary with evidence_count
try:
    r = api("get", f"/reports/project/{_pid}")
    ok34 = r.status_code == 200 and r.json().get("report", {}).get("summary", {}).get("evidence_count", 0) >= 1
    check(34, "GET /reports/project/{id} → 200, summary.evidence_count >= 1", ok34, f"{r.status_code} {r.text[:200]}")
except Exception as e:
    check(34, "GET /reports/project/{id}", False, str(e))

# 35. GET /reports/project/{id}/evidence-pack → pack_type
try:
    r = api("get", f"/reports/project/{_pid}/evidence-pack")
    ok35 = r.status_code == 200 and r.json().get("pack", {}).get("pack_type") == "evidence_pack"
    check(35, "GET /reports/project/{id}/evidence-pack → 200, pack_type=evidence_pack", ok35, f"{r.status_code} {r.text[:200]}")
except Exception as e:
    check(35, "GET /reports/project/{id}/evidence-pack", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
total = passed + failed
print(f"\n{'='*60}")
print(f"M9 Smoke Test Results: {passed}/{total} passed")
print(f"{'='*60}")
if failed > 0:
    print("\nFailed items:")
    for line in results:
        if "FAIL" in line:
            print(" ", line)
sys.exit(0 if failed == 0 else 1)
