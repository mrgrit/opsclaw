"""M6 Integrated Smoke Test — Registry CRUD + Composition + Explain via HTTP."""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Load manager-api app via importlib (hyphenated path)
spec = importlib.util.spec_from_file_location(
    "manager_api_main",
    ROOT / "apps" / "manager-api" / "src" / "main.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

from fastapi.testclient import TestClient

client = TestClient(mod.app)

passed = 0
failed = 0


def check(label: str, resp, expected_status: int = 200, key: str | None = None):
    global passed, failed
    ok = resp.status_code == expected_status
    if ok and key:
        ok = key in resp.json()
    status = "PASS" if ok else "FAIL"
    if status == "PASS":
        passed += 1
    else:
        failed += 1
        print(f"  [DEBUG] status={resp.status_code} body={resp.text[:200]}")
    print(f"  [{status}] {label}")


# ── Seed check: expect tools/skills/playbooks already loaded ────────────────

print("\n=== Registry List Endpoints ===")
r = client.get("/tools")
check("GET /tools returns list", r, key="items")
tools = r.json().get("items", [])
print(f"         tools count: {len(tools)}")

r = client.get("/skills")
check("GET /skills returns list", r, key="items")
skills = r.json().get("items", [])
print(f"         skills count: {len(skills)}")

r = client.get("/playbooks")
check("GET /playbooks returns list", r, key="items")
playbooks = r.json().get("items", [])
print(f"         playbooks count: {len(playbooks)}")

# ── Filter ────────────────────────────────────────────────────────────────────

print("\n=== Registry Filters ===")
r = client.get("/playbooks?category=reliability")
check("GET /playbooks?category=reliability", r, key="items")

r = client.get("/skills?category=operations")
check("GET /skills?category=operations", r, key="items")

# ── Playbook by name fallback ──────────────────────────────────────────────

print("\n=== Playbook Lookup ===")
if playbooks:
    pb = playbooks[0]
    pb_id = pb["id"]
    pb_name = pb["name"]

    r = client.get(f"/playbooks/{pb_name}")
    check(f"GET /playbooks/{{name}} '{pb_name}'", r, key="playbook")

    r = client.get(f"/playbooks/{pb_id}")
    check(f"GET /playbooks/{{id}} (fallback)", r, key="playbook")

    # Steps
    r = client.get(f"/playbooks/{pb_id}/steps")
    check(f"GET /playbooks/{{id}}/steps", r, key="steps")
    steps = r.json().get("steps", [])
    print(f"         steps count: {len(steps)}")

    # Resolve
    r = client.get(f"/playbooks/{pb_id}/resolve")
    check(f"GET /playbooks/{{id}}/resolve", r, key="resolved")

    # Explain
    r = client.get(f"/playbooks/{pb_id}/explain")
    check(f"GET /playbooks/{{id}}/explain", r, key="explanation")
    md = r.json().get("explanation", {}).get("explanation", "")
    print(f"         explain chars: {len(md)}")
else:
    print("  [SKIP] No playbooks seeded — run tools/dev/seed_loader.py first")

# ── Tool / Skill by name lookup ───────────────────────────────────────────

print("\n=== Tool / Skill Lookup ===")
if tools:
    t = tools[0]
    r = client.get(f"/tools/{t['name']}")
    check(f"GET /tools/{{name}} '{t['name']}'", r, key="tool")

if skills:
    s = skills[0]
    r = client.get(f"/skills/{s['name']}")
    check(f"GET /skills/{{name}} '{s['name']}'", r, key="skill")

# ── 404 guard ────────────────────────────────────────────────────────────────

print("\n=== 404 Guards ===")
r = client.get("/playbooks/no-such-playbook-xyz")
check("GET /playbooks/nonexistent → 404", r, expected_status=404)

r = client.get("/tools/no-such-tool-xyz")
check("GET /tools/nonexistent → 404", r, expected_status=404)

# ── Summary ───────────────────────────────────────────────────────────────────

print(f"\n{'='*50}")
total = passed + failed
print(f"M6 Smoke: {passed}/{total} passed, {failed} failed")
if failed:
    sys.exit(1)
