#!/usr/bin/env python3
"""
M19 Smoke Test: Skill/Tool/Experience 전체 경로 자동 검증

실행:
    PYTHONPATH=. python3 tools/dev/m19_skill_smoke.py
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

PASS = "✅"
FAIL = "❌"
results: list[tuple[str, bool, str]] = []


def check(name: str, fn):
    try:
        fn()
        results.append((name, True, ""))
        print(f"  {PASS} {name}")
    except Exception as exc:
        results.append((name, False, str(exc)))
        print(f"  {FAIL} {name}: {exc}")
        traceback.print_exc()


# ── 1. Registry: Tool/Skill/Playbook ─────────────────────────────────────────

print("\n[1] Registry — Tool/Skill/Playbook")

from packages.registry_service import (
    list_tools, list_skills, list_playbooks,
    resolve_playbook, explain_playbook,
)

tools_ref: list = []
skills_ref: list = []
playbooks_ref: list = []


def _tools():
    global tools_ref
    tools_ref = list_tools()
    assert len(tools_ref) >= 6, f"Expected ≥6 tools, got {len(tools_ref)}"


def _skills():
    global skills_ref
    skills_ref = list_skills()
    assert len(skills_ref) >= 6, f"Expected ≥6 skills, got {len(skills_ref)}"


def _playbooks():
    global playbooks_ref
    playbooks_ref = list_playbooks(enabled=True)
    assert len(playbooks_ref) >= 10, f"Expected ≥10 playbooks, got {len(playbooks_ref)}"


check("list_tools (≥6)", _tools)
check("list_skills (≥6)", _skills)
check("list_playbooks (≥10)", _playbooks)


def _resolve_all():
    not_found_total = 0
    for pb in playbooks_ref[:10]:
        result = resolve_playbook(pb["id"])
        not_found = [
            s for s in result["steps"]
            if not s.get("skill") and not s.get("tool")
        ]
        not_found_total += len(not_found)
    assert not_found_total == 0, f"{not_found_total} unresolvable step refs"


def _explain():
    seed_pb = next((p for p in playbooks_ref if p["name"] == "cleanup_disk_usage"), playbooks_ref[0])
    result = explain_playbook(seed_pb["id"])
    assert "explanation" in result, "explain_playbook missing 'explanation' key"
    assert len(result["explanation"]) > 50


check("resolve_playbook (all 10 seed playbooks, 0 not_found)", _resolve_all)
check("explain_playbook returns explanation text", _explain)


# ── 2. ToolBridge.run_tool ────────────────────────────────────────────────────

print("\n[2] ToolBridge.run_tool")

from packages.pi_adapter import PiSession, ToolBridge

session = PiSession("m19-smoke")
session.start()
bridge = ToolBridge(session)


def _run_tool_success():
    r = bridge.run_tool("df", ["-h", "/"], timeout_s=10)
    assert r["exit_code"] == 0, f"df exit_code={r['exit_code']}"
    assert "Filesystem" in r["stdout"] or "/" in r["stdout"]


def _run_tool_not_found():
    r = bridge.run_tool("__nonexistent_tool_xyz__", [], timeout_s=5)
    assert r["exit_code"] == 127, f"expected 127, got {r['exit_code']}"
    assert "not found" in r["stderr"]


def _run_tool_timeout():
    r = bridge.run_tool("sleep", ["10"], timeout_s=2)
    assert r["exit_code"] == 124, f"expected 124, got {r['exit_code']}"
    assert "timeout" in r["stderr"]


check("run_tool success (df -h /)", _run_tool_success)
check("run_tool not_found → exit_code 127", _run_tool_not_found)
check("run_tool timeout → exit_code 124", _run_tool_timeout)


# ── 3. Experience 생성 → 검색 흐름 ───────────────────────────────────────────

print("\n[3] Experience → retrieval index → search")

from packages.experience_service import create_experience, list_experiences
from packages.retrieval_service import search_documents, get_context_for_project
import time

_smoke_title = f"M19-smoke-exp-{int(time.time())}"


def _create_and_search():
    exp = create_experience(
        category="operations",
        title=_smoke_title,
        summary="M19 smoke test experience for retrieval verification",
        outcome="success",
    )
    assert exp.get("id"), "create_experience returned no id"

    # FTS / ILIKE로 검색 가능해야 함
    results = search_documents("M19 smoke test", document_type="experience")
    titles = [r["title"] for r in results]
    assert _smoke_title in titles, (
        f"Expected '{_smoke_title}' in search results, got: {titles}"
    )


def _list_experiences():
    exps = list_experiences(category="operations", limit=50)
    found = any(e["title"] == _smoke_title for e in exps)
    assert found, f"'{_smoke_title}' not in list_experiences"


check("create_experience → auto-index → search_documents finds it", _create_and_search)
check("list_experiences returns created experience", _list_experiences)


# ── 4. Task Memory → promote → search ────────────────────────────────────────

print("\n[4] Task Memory → promote → search")

import psycopg2, os
from packages.experience_service import build_task_memory, promote_to_experience

_prj_id: str | None = None


def _find_project():
    global _prj_id
    conn = psycopg2.connect(os.environ.get("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw"))
    cur = conn.cursor()
    cur.execute("SELECT id FROM projects ORDER BY created_at DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    assert row, "No projects in DB"
    _prj_id = row[0]


def _build_memory():
    assert _prj_id, "No project to test with"
    tm = build_task_memory(_prj_id)
    assert tm.get("id"), "build_task_memory returned no id"
    assert tm.get("summary"), "build_task_memory returned empty summary"


def _promote():
    assert _prj_id, "No project"
    tm = build_task_memory(_prj_id)
    promo_title = f"M19-promote-{int(time.time())}"
    exp = promote_to_experience(
        task_memory_id=tm["id"],
        category="operations",
        title=promo_title,
        outcome="success",
    )
    assert exp.get("id"), "promote_to_experience returned no id"
    # 검색 가능해야 함
    results = search_documents(promo_title[:15])
    assert any(r["title"] == promo_title for r in results), (
        f"Promoted experience '{promo_title}' not found in search"
    )


check("find project in DB", _find_project)
check("build_task_memory", _build_memory)
check("promote_to_experience → auto-index → searchable", _promote)


# ── 5. get_context_for_project ───────────────────────────────────────────────

print("\n[5] get_context_for_project")


def _context():
    assert _prj_id
    ctx = get_context_for_project(_prj_id)
    assert isinstance(ctx.get("experiences"), list), "ctx missing 'experiences'"
    assert isinstance(ctx.get("documents"), list), "ctx missing 'documents'"
    assert isinstance(ctx.get("asset_history"), list), "ctx missing 'asset_history'"


check("get_context_for_project returns structured context", _context)


# ── 결과 요약 ─────────────────────────────────────────────────────────────────

total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print(f"\n{'='*50}")
print(f"M19 Smoke Test 결과: {passed}/{total} passed")
if failed:
    print(f"\n실패 항목:")
    for name, ok, err in results:
        if not ok:
            print(f"  {FAIL} {name}: {err}")
print(f"{'='*50}")

sys.exit(0 if failed == 0 else 1)
