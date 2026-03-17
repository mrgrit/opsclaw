#!/usr/bin/env python3
"""M8 Integrated Smoke Test — 35 items
Covers:
  A. history_service unit    (items 1-8)
  B. experience_service unit (items 9-18)
  C. retrieval_service unit  (items 19-25)
  D. Manager API             (items 26-35)
"""
import sys
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


# ── Setup: shared project ──────────────────────────────────────────────────────
from packages.project_service import (
    create_project_record,
    plan_project_record,
    execute_project_record,
    validate_project_record,
    finalize_report_stage_record,
    create_minimal_evidence_record,
)
from packages.asset_registry import create_asset

_p = create_project_record("m8-smoke-main", "M8 smoke test project", mode="one_shot", database_url=DB_URL)
_pid = _p["id"]
plan_project_record(_pid, database_url=DB_URL)
execute_project_record(_pid, database_url=DB_URL)
create_minimal_evidence_record(_pid, "echo hello", "hello", "", 0, database_url=DB_URL)
validate_project_record(_pid, database_url=DB_URL)
finalize_report_stage_record(_pid, database_url=DB_URL)

# Create an asset to test asset_history axis
_asset = create_asset(
    name="m8-smoke-asset",
    type="server",
    platform="linux",
    env="lab",
    mgmt_ip="10.0.0.99",
    database_url=DB_URL,
)
_asset_id = _asset["id"]


# ─────────────────────────────────────────────────────────────────────────────
# Section A: history_service unit (1-8)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== A. history_service unit ===")

from packages.history_service import (
    ingest_event,
    ingest_stage_event,
    get_project_history,
    get_asset_history,
    list_histories,
    get_history_event,
)

# 1. ingest_event → dict with id
try:
    ev1 = ingest_event(_pid, "smoke_test_event", {"info": "test"}, database_url=DB_URL)
    check(1, "ingest_event → dict with id", "id" in ev1 and ev1["event"] == "smoke_test_event")
    _ev1_id = str(ev1["id"])
except Exception as e:
    check(1, "ingest_event → dict with id", False, str(e))
    _ev1_id = None

# 2. get_project_history → list, contains event
try:
    hist = get_project_history(_pid, database_url=DB_URL)
    ids = [str(h["id"]) for h in hist]
    check(2, "get_project_history → list, 포함", _ev1_id is not None and _ev1_id in ids, f"count={len(hist)}")
except Exception as e:
    check(2, "get_project_history → list, 포함", False, str(e))

# 3. ingest with context.asset_id
try:
    ev3 = ingest_event(_pid, "asset_touch", {"asset_id": _asset_id, "action": "check"}, database_url=DB_URL)
    check(3, "ingest_event with context.asset_id → ok", "id" in ev3)
    _ev3_id = str(ev3["id"])
except Exception as e:
    check(3, "ingest_event with context.asset_id → ok", False, str(e))
    _ev3_id = None

# 4. get_asset_history → finds event by asset_id
try:
    ahist = get_asset_history(_asset_id, database_url=DB_URL)
    ids = [str(h["id"]) for h in ahist]
    check(4, "get_asset_history → context.asset_id 매칭", _ev3_id is not None and _ev3_id in ids, f"count={len(ahist)}")
except Exception as e:
    check(4, "get_asset_history → context.asset_id 매칭", False, str(e))

# 5. ingest_stage_event → event starts with 'stage:'
try:
    sev = ingest_stage_event(_pid, "execute", status="ok", database_url=DB_URL)
    check(5, "ingest_stage_event → event='stage:execute'", sev["event"] == "stage:execute")
except Exception as e:
    check(5, "ingest_stage_event → event='stage:execute'", False, str(e))

# 6. list_histories → global list not empty
try:
    all_hist = list_histories(limit=10, database_url=DB_URL)
    check(6, "list_histories → 비어있지 않음", len(all_hist) > 0)
except Exception as e:
    check(6, "list_histories → 비어있지 않음", False, str(e))

# 7. get_project_history with limit=1
try:
    hist1 = get_project_history(_pid, limit=1, database_url=DB_URL)
    check(7, "get_project_history limit=1 → 최대 1개", len(hist1) == 1)
except Exception as e:
    check(7, "get_project_history limit=1 → 최대 1개", False, str(e))

# 8. get_history_event → correct fields
if _ev1_id:
    try:
        row = get_history_event(_ev1_id, database_url=DB_URL)
        fields_ok = row and all(k in row for k in ("id", "project_id", "event", "context", "created_at"))
        check(8, "get_history_event → 필드 검증", bool(fields_ok), str(row))
    except Exception as e:
        check(8, "get_history_event → 필드 검증", False, str(e))
else:
    check(8, "get_history_event → 필드 검증", False, "no ev1_id")


# ─────────────────────────────────────────────────────────────────────────────
# Section B: experience_service unit (9-18)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== B. experience_service unit ===")

from packages.experience_service import (
    build_task_memory,
    get_task_memory,
    list_task_memories,
    promote_to_experience,
    create_experience,
    list_experiences,
    get_experience,
)

# 9. build_task_memory → dict with id
try:
    tm = build_task_memory(_pid, database_url=DB_URL)
    check(9, "build_task_memory → dict with id", "id" in tm and "summary" in tm)
    _tm_id = str(tm["id"])
except Exception as e:
    check(9, "build_task_memory → dict with id", False, str(e))
    _tm_id = None

# 10. get_task_memory → summary 존재
if _tm_id:
    try:
        tm2 = get_task_memory(_pid, database_url=DB_URL)
        check(10, "get_task_memory → summary 존재", tm2 is not None and len(tm2.get("summary", "")) > 0, str(tm2)[:100] if tm2 else "None")
    except Exception as e:
        check(10, "get_task_memory → summary 존재", False, str(e))
else:
    check(10, "get_task_memory → summary 존재", False, "no tm_id")

# 11. list_task_memories → includes our record
if _tm_id:
    try:
        tms = list_task_memories(database_url=DB_URL)
        ids = [str(t["id"]) for t in tms]
        check(11, "list_task_memories → 포함", _tm_id in ids)
    except Exception as e:
        check(11, "list_task_memories → 포함", False, str(e))
else:
    check(11, "list_task_memories → 포함", False, "no tm_id")

# 12. promote_to_experience → dict with id
if _tm_id:
    try:
        exp = promote_to_experience(_tm_id, "remediation", "M8 Smoke Test Experience", outcome="success", database_url=DB_URL)
        check(12, "promote_to_experience → dict with id", "id" in exp and exp["category"] == "remediation")
        _exp_id = str(exp["id"])
    except Exception as e:
        check(12, "promote_to_experience → dict with id", False, str(e))
        _exp_id = None
else:
    check(12, "promote_to_experience → dict with id", False, "no tm_id")
    _exp_id = None

# 13. list_experiences → includes promoted experience
if _exp_id:
    try:
        exps = list_experiences(database_url=DB_URL)
        ids = [str(e["id"]) for e in exps]
        check(13, "list_experiences → 포함", _exp_id in ids)
    except Exception as e:
        check(13, "list_experiences → 포함", False, str(e))
else:
    check(13, "list_experiences → 포함", False, "no exp_id")

# 14. list_experiences with category filter
try:
    cat_exps = list_experiences(category="remediation", database_url=DB_URL)
    all_cat = all(e["category"] == "remediation" for e in cat_exps)
    check(14, "list_experiences category='remediation' → 카테고리 일치", all_cat and len(cat_exps) > 0)
except Exception as e:
    check(14, "list_experiences category filter", False, str(e))

# 15. get_experience → fields ok
if _exp_id:
    try:
        exp_row = get_experience(_exp_id, database_url=DB_URL)
        fields_ok = exp_row and all(k in exp_row for k in ("id", "category", "title", "summary"))
        check(15, "get_experience → 필드 검증", bool(fields_ok))
    except Exception as e:
        check(15, "get_experience → 필드 검증", False, str(e))
else:
    check(15, "get_experience → 필드 검증", False, "no exp_id")

# 16. create_experience with asset_id
try:
    exp2 = create_experience(
        "error_pattern", "SSH connect timeout on lab servers",
        "Increase ConnectTimeout to 30s in SSH config",
        outcome="workaround",
        asset_id=_asset_id,
        database_url=DB_URL,
    )
    check(16, "create_experience with asset_id → ok", "id" in exp2 and exp2.get("asset_id") == _asset_id)
    _exp2_id = str(exp2["id"])
except Exception as e:
    check(16, "create_experience with asset_id → ok", False, str(e))
    _exp2_id = None

# 17. list_experiences without filter includes create_experience result
if _exp2_id:
    try:
        all_exps = list_experiences(database_url=DB_URL)
        ids = [str(e["id"]) for e in all_exps]
        check(17, "list_experiences 전체 → create_experience 포함", _exp2_id in ids)
    except Exception as e:
        check(17, "list_experiences 전체 → create_experience 포함", False, str(e))
else:
    check(17, "list_experiences 전체 → create_experience 포함", False, "no exp2_id")

# 18. build_task_memory idempotent — second call replaces
try:
    tm_again = build_task_memory(_pid, database_url=DB_URL)
    tms_all = list_task_memories(database_url=DB_URL)
    same_project_tms = [t for t in tms_all if t["project_id"] == _pid]
    check(18, "build_task_memory 반복 호출 → idempotent (1개만 존재)", len(same_project_tms) == 1)
except Exception as e:
    check(18, "build_task_memory 반복 호출 → idempotent", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Section C: retrieval_service unit (19-25)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== C. retrieval_service unit ===")

from packages.retrieval_service import (
    index_document,
    search_documents,
    reindex_project,
    get_context_for_project,
    get_retrieval_document,
    list_retrieval_documents,
)

# 19. index_document → dict with id
try:
    doc = index_document(
        "report", _pid,
        "Nginx Restart Procedure",
        "Restart nginx service using systemctl restart nginx. Verify with systemctl status nginx.",
        database_url=DB_URL,
    )
    check(19, "index_document → dict with id", "id" in doc)
    _doc_id = str(doc["id"])
except Exception as e:
    check(19, "index_document → dict with id", False, str(e))
    _doc_id = None

# 20. search_documents (keyword match) → finds doc
try:
    results_s = search_documents("nginx restart", database_url=DB_URL)
    titles = [r["title"] for r in results_s]
    check(20, "search_documents 'nginx restart' → 문서 발견", any("Nginx" in t for t in titles), str(titles))
except Exception as e:
    check(20, "search_documents 'nginx restart' → 문서 발견", False, str(e))

# 21. search_documents (no match) → empty list
try:
    no_results = search_documents("xyzqwertyuiop123notexist", database_url=DB_URL)
    check(21, "search_documents (미매칭) → 빈 리스트", len(no_results) == 0)
except Exception as e:
    check(21, "search_documents (미매칭) → 빈 리스트", False, str(e))

# 22. search_documents with document_type filter
try:
    index_document("playbook", None, "SSH Key Rotation Playbook", "Rotate SSH keys on all servers monthly", database_url=DB_URL)
    report_docs = search_documents("nginx", document_type="report", database_url=DB_URL)
    playbook_docs = search_documents("nginx", document_type="playbook", database_url=DB_URL)
    check(22, "search_documents document_type 필터 작동", len(playbook_docs) == 0 or all(d.get("document_type") == "playbook" for d in playbook_docs))
except Exception as e:
    check(22, "search_documents document_type 필터", False, str(e))

# 23. get_context_for_project → has required keys
try:
    ctx = get_context_for_project(_pid, database_url=DB_URL)
    required_keys = {"project_id", "project_name", "asset_history", "experiences", "documents"}
    check(23, "get_context_for_project → required keys 존재", required_keys.issubset(ctx.keys()), str(list(ctx.keys())))
except Exception as e:
    check(23, "get_context_for_project → required keys 존재", False, str(e))

# 24. reindex_project → returns indexed_count >= 0
try:
    ridx = reindex_project(_pid, database_url=DB_URL)
    check(24, "reindex_project → indexed_count >= 0", "indexed_count" in ridx and ridx["indexed_count"] >= 0, str(ridx))
except Exception as e:
    check(24, "reindex_project → indexed_count >= 0", False, str(e))

# 25. list_retrieval_documents by type
try:
    report_docs = list_retrieval_documents(document_type="report", database_url=DB_URL)
    check(25, "list_retrieval_documents type='report' → 비어있지 않음", len(report_docs) > 0)
except Exception as e:
    check(25, "list_retrieval_documents type='report'", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Section D: Manager API (26-35)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== D. Manager API ===")


def api(method, path, **kwargs):
    fn = getattr(requests, method)
    return fn(f"{BASE_URL}{path}", timeout=10, **kwargs)


# 26. POST /projects/{id}/history/ingest → 200
try:
    r = api("post", f"/projects/{_pid}/history/ingest",
            json={"event": "api_test_event", "context": {"source": "smoke"}})
    ok26 = r.status_code == 200 and "id" in r.json().get("event", {})
    check(26, "POST /projects/{id}/history/ingest → 200", ok26, f"{r.status_code} {r.text[:100]}")
except Exception as e:
    check(26, "POST /projects/{id}/history/ingest → 200", False, str(e))

# 27. GET /projects/{id}/history → items list
try:
    r = api("get", f"/projects/{_pid}/history")
    ok27 = r.status_code == 200 and isinstance(r.json().get("items"), list) and len(r.json()["items"]) > 0
    check(27, "GET /projects/{id}/history → items list", ok27, f"{r.status_code} count={len(r.json().get('items', []))}")
except Exception as e:
    check(27, "GET /projects/{id}/history → items list", False, str(e))

# 28. GET /assets/{id}/history → items list
try:
    r = api("get", f"/assets/{_asset_id}/history")
    ok28 = r.status_code == 200 and "items" in r.json()
    check(28, "GET /assets/{id}/history → items list", ok28, f"{r.status_code} {r.text[:100]}")
except Exception as e:
    check(28, "GET /assets/{id}/history → items list", False, str(e))

# 29. POST /projects/{id}/task-memory/build → 200, task_memory.summary
try:
    r = api("post", f"/projects/{_pid}/task-memory/build")
    tm_res = r.json().get("task_memory", {})
    ok29 = r.status_code == 200 and len(tm_res.get("summary", "")) > 0
    check(29, "POST /projects/{id}/task-memory/build → 200, summary 존재", ok29, f"{r.status_code} {r.text[:200]}")
    _api_tm_id = tm_res.get("id")
except Exception as e:
    check(29, "POST /projects/{id}/task-memory/build → 200, summary 존재", False, str(e))
    _api_tm_id = None

# 30. GET /projects/{id}/task-memory → 200
try:
    r = api("get", f"/projects/{_pid}/task-memory")
    ok30 = r.status_code == 200 and "task_memory" in r.json()
    check(30, "GET /projects/{id}/task-memory → 200", ok30, f"{r.status_code} {r.text[:100]}")
except Exception as e:
    check(30, "GET /projects/{id}/task-memory → 200", False, str(e))

# 31. GET /experience → 200, items list
try:
    r = api("get", "/experience")
    ok31 = r.status_code == 200 and isinstance(r.json().get("items"), list)
    check(31, "GET /experience → 200, items list", ok31, f"{r.status_code} count={len(r.json().get('items', []))}")
except Exception as e:
    check(31, "GET /experience → 200, items list", False, str(e))

# 32. GET /experience/search?q=keyword → 200, items + documents
try:
    r = api("get", "/experience/search", params={"q": "nginx"})
    body = r.json()
    ok32 = r.status_code == 200 and "items" in body and "documents" in body
    check(32, "GET /experience/search?q=nginx → 200, items + documents", ok32, f"{r.status_code} {r.text[:200]}")
except Exception as e:
    check(32, "GET /experience/search?q=nginx", False, str(e))

# 33. POST /experience → 200, experience.id
try:
    r = api("post", "/experience", json={
        "category": "error_pattern",
        "title": "API-created experience",
        "summary": "Created via API smoke test",
        "outcome": "test",
    })
    ok33 = r.status_code == 200 and "id" in r.json().get("experience", {})
    check(33, "POST /experience → 200, experience.id 존재", ok33, f"{r.status_code} {r.text[:200]}")
    _api_exp_id = r.json().get("experience", {}).get("id")
except Exception as e:
    check(33, "POST /experience → 200, experience.id 존재", False, str(e))
    _api_exp_id = None

# 34. GET /projects/{id}/context → 200, has keys
try:
    r = api("get", f"/projects/{_pid}/context")
    body = r.json()
    ok34 = r.status_code == 200 and all(k in body for k in ("asset_history", "experiences", "documents"))
    check(34, "GET /projects/{id}/context → 200, asset_history + experiences + documents", ok34, f"{r.status_code} keys={list(body.keys())}")
except Exception as e:
    check(34, "GET /projects/{id}/context → 200", False, str(e))

# 35. POST /projects/{id}/reindex → 200, indexed_count >= 0
try:
    r = api("post", f"/projects/{_pid}/reindex")
    body = r.json()
    ok35 = r.status_code == 200 and "indexed_count" in body and body["indexed_count"] >= 0
    check(35, "POST /projects/{id}/reindex → 200, indexed_count >= 0", ok35, f"{r.status_code} {r.text[:200]}")
except Exception as e:
    check(35, "POST /projects/{id}/reindex → 200, indexed_count >= 0", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
total = passed + failed
print(f"\n{'='*60}")
print(f"M8 Smoke Test Results: {passed}/{total} passed")
print(f"{'='*60}")
if failed > 0:
    print("\nFailed items:")
    for line in results:
        if "FAIL" in line:
            print(" ", line)
sys.exit(0 if failed == 0 else 1)
