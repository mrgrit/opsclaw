#!/usr/bin/env python3
"""
M15 Mode B 통합 테스트

외부 AI(Claude Code)가 OpsClaw Manager API를 직접 호출하여
작업을 완료하는 시나리오를 검증한다.

시나리오: "신규 Ubuntu 서버에 패키지 업데이트 및 기본 현황 수집"
  1. Project 생성 (master_mode=external)
  2. Playbook + steps 생성 (skill: probe_linux_host, tool: query_metric)
  3. Playbook → Project 연결
  4. Stage 전환: intake → plan → execute
  5. Playbook 실행 → SubAgent dispatch
  6. Evidence 확인
  7. Completion Report 생성
  8. master_mode=external 프로젝트 목록 필터 확인

사용법:
  PYTHONPATH=. .venv/bin/python3 scripts/m15_mode_b_test.py
"""
import os, sys, time, json
import httpx

MANAGER = "http://localhost:8000"
SUBAGENT = "http://localhost:8002"


def post(path, body=None):
    r = httpx.post(f"{MANAGER}{path}", json=body or {}, timeout=60.0)
    return r.json()

def get(path):
    r = httpx.get(f"{MANAGER}{path}", timeout=10.0)
    return r.json()


def check(label, condition, detail=""):
    icon = "✅" if condition else "❌"
    print(f"  {icon} {label}" + (f" — {detail}" if detail else ""))
    return condition

results = []
print("\n" + "="*60)
print("M15 Mode B — External AI 오케스트레이션 통합 테스트")
print("="*60)

# ── 1. 프로젝트 생성 (master_mode=external) ────────────────────
print("\n[1] 프로젝트 생성 (master_mode=external)")
resp = post("/projects", {
    "name": "m15-mode-b-test",
    "request_text": "신규 Ubuntu 서버 기본 현황 수집 및 패키지 업데이트",
    "master_mode": "external",
})
project = resp.get("project", {})
project_id = project.get("id", "")
results.append(check("프로젝트 생성", bool(project_id), project_id))
results.append(check("master_mode=external 저장", project.get("master_mode") == "external"))

# ── 2. Playbook 생성 ────────────────────────────────────────────
print("\n[2] Playbook 생성 (skill + tool steps)")
pb_resp = post("/playbooks", {
    "name": "mode-b-verify",
    "version": "1.0",
    "description": "Mode B 검증용 — 호스트 탐색 + 메트릭 수집",
})
pb_id = pb_resp.get("playbook", {}).get("id", "")
results.append(check("Playbook 생성", bool(pb_id), pb_id))

# steps 추가
steps_ok = 0
for step in [
    {"step_order": 1, "step_type": "skill", "name": "probe_linux_host", "ref_id": "probe_linux_host"},
    {"step_order": 2, "step_type": "tool",  "name": "query_metric",     "ref_id": "query_metric"},
    {"step_order": 3, "step_type": "tool",  "name": "run_command",      "ref_id": "run_command",
     "params": {"command": "echo 'Mode B test OK' && date"}},
]:
    r = post(f"/playbooks/{pb_id}/steps", step)
    if r.get("status") == "ok":
        steps_ok += 1
results.append(check("Steps 3개 등록", steps_ok == 3, f"{steps_ok}/3"))

# ── 3. Playbook → Project 연결 ────────────────────────────────
print("\n[3] Playbook → Project 연결")
link = post(f"/projects/{project_id}/playbooks/{pb_id}")
results.append(check("Playbook 연결", link.get("status") == "ok"))

# ── 4. Stage 전환 ─────────────────────────────────────────────
print("\n[4] Stage 전환: intake → plan → execute")
r_plan = post(f"/projects/{project_id}/plan")
results.append(check("→ plan", r_plan.get("project", {}).get("current_stage") == "plan"))

r_exec = post(f"/projects/{project_id}/execute")
results.append(check("→ execute", r_exec.get("result", {}).get("project", {}).get("current_stage") == "execute"))

# ── 5. dry_run 검증 ───────────────────────────────────────────
print("\n[5] Playbook dry_run")
dry = post(f"/projects/{project_id}/playbook/run", {"dry_run": True, "subagent_url": SUBAGENT})
dr = dry.get("result", {})
results.append(check("dry_run status", dr.get("status") == "dry_run", dr.get("status")))
results.append(check("dry_run 3 steps", dr.get("steps_total") == 3, str(dr.get("steps_total"))))

# ── 6. 실제 실행 ──────────────────────────────────────────────
print("\n[6] Playbook 실제 실행 (→ SubAgent dispatch)")
t0 = time.time()
run = post(f"/projects/{project_id}/playbook/run", {"dry_run": False, "subagent_url": SUBAGENT})
elapsed = round(time.time() - t0, 1)
rr = run.get("result", {})
overall = rr.get("status", "")
steps_ok_cnt = rr.get("steps_ok", 0)
steps_total = rr.get("steps_total", 0)
results.append(check(f"실행 overall={overall}", overall == "success", f"{steps_ok_cnt}/{steps_total} ok, {elapsed}s"))
for s in rr.get("step_results", []):
    results.append(check(f"  step {s['order']} {s['name']}", s["status"] == "ok",
                         s.get("stdout","")[:50].replace("\n"," ")))

# ── 7. Evidence 확인 ──────────────────────────────────────────
print("\n[7] Evidence 확인")
ev = get(f"/projects/{project_id}/evidence/summary")
ev_data = ev.get("summary", {})
total_ev = ev_data.get("total", ev_data.get("count", len(get(f"/projects/{project_id}/evidence").get("items", []))))
results.append(check("Evidence 기록 존재", total_ev > 0, f"{total_ev}건"))

# ── 8. Completion Report ──────────────────────────────────────
print("\n[8] Completion Report 생성")
cr = post(f"/projects/{project_id}/completion-report", {
    "summary": "Mode B 검증: probe_linux_host + query_metric + run_command 성공",
    "outcome": "success",
    "work_details": [
        "probe_linux_host: 호스트 기본 정보 수집",
        "query_metric: CPU/메모리/디스크 현황 수집",
        "run_command: Mode B test OK",
    ],
    "issues": [],
    "next_steps": ["SSL 인증서 점검 Playbook 추가 권장"],
})
cr_id = cr.get("report", {}).get("id", "")
results.append(check("Completion Report 생성", bool(cr_id), cr_id[:8] if cr_id else "FAIL"))

# ── 9. master_mode 필터 확인 ─────────────────────────────────
print("\n[9] master_mode 필드 DB 저장 확인")
proj = get(f"/projects/{project_id}")
stored_mode = proj.get("project", {}).get("master_mode", "")
results.append(check("master_mode=external DB 저장", stored_mode == "external", stored_mode))

# ── 결과 요약 ────────────────────────────────────────────────
total = len(results)
passed = sum(results)
failed = total - passed
print(f"\n{'='*60}")
print(f"결과: {passed}/{total} 통과, {failed}건 실패")
print("✅ PASS" if failed == 0 else f"❌ FAIL — {failed}건 실패")
print("="*60)

out = {"total": total, "passed": passed, "failed": failed, "project_id": project_id}
out_path = os.path.join(os.path.dirname(__file__), "m15_mode_b_result.json")
with open(out_path, "w") as f:
    json.dump(out, f, indent=2)
print(f"결과 저장: {out_path}")
