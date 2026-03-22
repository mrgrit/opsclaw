#!/usr/bin/env python3
"""
M19 Skill/Tool/Experience Smoke Test

Tool → Skill → Playbook → Experience 전체 경로 자동 검증

사용법:
  PYTHONPATH=. .venv/bin/python3 scripts/m19_skill_smoke.py
"""
import os
import sys
import json
import time

os.environ.setdefault("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

MANAGER_URL = "http://localhost:8000"
SUBAGENT_URL = "http://localhost:8002"


def _post(path, body):
    import httpx
    return httpx.post(f"{MANAGER_URL}{path}", json=body, timeout=30.0).json()

def _get(path):
    import httpx
    return httpx.get(f"{MANAGER_URL}{path}", timeout=10.0).json()


def check(label, condition, detail=""):
    icon = "✅" if condition else "❌"
    print(f"  {icon} {label}" + (f" — {detail}" if detail else ""))
    return condition


results = []

print("\n" + "="*60)
print("M19 Skill/Tool/Experience Smoke Test")
print("="*60)

# ── 1. Tool Registry 조회 ────────────────────────────────────────
print("\n[1] Tool Registry 조회")
tools = _get("/tools").get("items", [])
results.append(check("6개 seed tool 등록", len(tools) >= 6, f"{len(tools)}개"))
tool_names = {t["name"] for t in tools}
for name in ["run_command", "fetch_log", "query_metric", "restart_service", "read_file", "write_file"]:
    results.append(check(f"  tool: {name}", name in tool_names))

# ── 2. Skill Registry 조회 ────────────────────────────────────────
print("\n[2] Skill Registry 조회")
skills = _get("/skills").get("items", [])
results.append(check("6개 seed skill 등록", len(skills) >= 6, f"{len(skills)}개"))
skill_names = {s["name"] for s in skills}
for name in ["probe_linux_host", "check_tls_cert", "collect_web_latency_facts",
             "monitor_disk_growth", "summarize_incident_timeline", "analyze_wazuh_alert_burst"]:
    results.append(check(f"  skill: {name}", name in skill_names))

# ── 3. skill_tools 링크 확인 ─────────────────────────────────────
print("\n[3] Skill-Tool 링크 (skill_tools 테이블)")
import psycopg2
from psycopg2.extras import RealDictCursor
with psycopg2.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT COUNT(*) as cnt FROM skill_tools")
        cnt = cur.fetchone()["cnt"]
results.append(check("skill_tools 링크 존재", cnt > 0, f"{cnt}개"))

# ── 4. Tool Playbook 실행 (dry_run) ───────────────────────────────
print("\n[4] Tool Playbook dry_run")
from packages.playbook_engine import resolve_step_script

ctx = {"host": "localhost", "params": {}}
tool_tests = [
    ("run_command", {"command": "echo smoke-test"}),
    ("fetch_log",   {"log_path": "/var/log/syslog", "lines": 5}),
    ("query_metric", {}),
    ("read_file",   {"path": "/etc/hostname"}),
    ("write_file",  {"path": "/tmp/smoke.txt", "content": "ok"}),
    ("restart_service", {"service": "nginx"}),
]
for tool_name, meta in tool_tests:
    step = {"step_type": "tool", "ref_id": tool_name, "metadata": meta}
    script = resolve_step_script(step, ctx)
    ok = "Unknown" not in script and "no command" not in script and "no path" not in script and "no service" not in script
    results.append(check(f"  {tool_name} 스크립트 생성", ok, script.split('\n')[0][:50]))

# ── 5. Skill Playbook dry_run ─────────────────────────────────────
print("\n[5] Skill Playbook dry_run")
skill_tests = [
    ("probe_linux_host",            {"host": "192.168.0.107"}),
    ("check_tls_cert",              {"host": "example.com"}),
    ("collect_web_latency_facts",   {"url": "http://localhost"}),
    ("monitor_disk_growth",         {"path": "/"}),
    ("summarize_incident_timeline", {"since": "30 minutes ago"}),
    ("analyze_wazuh_alert_burst",   {"lines": 50}),
]
for skill_name, meta in skill_tests:
    step = {"step_type": "skill", "ref_id": skill_name, "metadata": meta}
    script = resolve_step_script(step, ctx)
    ok = "Unknown" not in script
    results.append(check(f"  {skill_name} 스크립트 생성", ok, script.split('\n')[0][:50]))

# ── 6. Tool 실제 실행 (subagent dispatch) ─────────────────────────
print("\n[6] Tool 실제 실행 (subagent API)")
import httpx
t0 = time.time()
resp = httpx.post(
    f"{SUBAGENT_URL}/a2a/run_script",
    json={"project_id": "smoke-test", "job_run_id": "s1",
          "script": "echo === tool-smoke ===\nhostname\nuptime"},
    timeout=30.0,
)
elapsed = round(time.time() - t0, 2)
if resp.status_code == 200:
    d = resp.json()
    detail = d.get("detail") or d
    ok = detail.get("exit_code") == 0
    stdout = (detail.get("stdout") or "")[:60].replace("\n"," ")
    results.append(check("run_script dispatch 성공", ok, f"{elapsed}s | {stdout}"))
else:
    results.append(check("run_script dispatch 성공", False, f"HTTP {resp.status_code}"))

# ── 7. Experience 생성 → 검색 ─────────────────────────────────────
print("\n[7] Experience 생성 → retrieval 검색")
from packages.experience_service import create_experience
from packages.retrieval_service import search_documents

exp = create_experience(
    category="operations",
    title="M19 smoke test experience",
    summary="M19 검증 중 생성된 smoke test experience. Tool/Skill/Playbook 전체 경로 정상 동작 확인.",
    outcome="success",
)
results.append(check("Experience DB 저장", bool(exp.get("id")), exp.get("id","")[:8]))

# 검색
time.sleep(0.5)
hits = search_documents("smoke test experience", document_type="experience", limit=5)
found = any("smoke" in (h.get("title","") + h.get("body","")).lower() for h in hits)
results.append(check("Experience retrieval 검색", found, f"{len(hits)}건 검색됨"))

# ── 결과 요약 ────────────────────────────────────────────────────
total = len(results)
passed = sum(1 for r in results if r)
failed = total - passed

print(f"\n{'='*60}")
print(f"결과: {passed}/{total} 통과, {failed}건 실패")
print("✅ PASS" if failed == 0 else f"❌ FAIL — {failed}건 실패")
print("="*60)

# JSON 결과 저장
out = {"total": total, "passed": passed, "failed": failed}
out_path = os.path.join(os.path.dirname(__file__), "m19_smoke_result.json")
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)
print(f"결과 저장: {out_path}")
