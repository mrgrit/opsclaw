#!/usr/bin/env python3
"""
OpsClaw CLI — 터미널에서 바로 작업을 지시하는 커맨드라인 인터페이스

사용법:
  opsclaw "v-secu 방화벽 점검해줘"
  opsclaw "v-web의 Apache 상태를 확인해줘" --target 192.168.0.110
  opsclaw status <project_id>
  opsclaw list
  opsclaw replay <project_id>
"""

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    print("requests 패키지가 필요합니다: pip install requests")
    sys.exit(1)

MANAGER_URL = os.environ.get("OPSCLAW_MANAGER_URL", "http://localhost:8000")
MASTER_URL = os.environ.get("OPSCLAW_MASTER_URL", "http://localhost:8001")
API_KEY = os.environ.get("OPSCLAW_API_KEY", "opsclaw-api-key-2026")

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
}

# 서버 별명 → IP 매핑
SERVER_ALIASES = {
    "secu": "http://192.168.208.150:8002",
    "web": "http://192.168.208.151:8002",
    "siem": "http://192.168.208.152:8002",
    "v-secu": "http://192.168.0.108:8002",
    "v-web": "http://192.168.0.110:8002",
    "v-siem": "http://192.168.0.109:8002",
    "local": "http://localhost:8002",
}


def resolve_target(target: str) -> str:
    """서버 별명을 SubAgent URL로 변환"""
    if target in SERVER_ALIASES:
        return SERVER_ALIASES[target]
    if target.startswith("http"):
        return target
    return f"http://{target}:8002"


def api(method, path, base=None, **kwargs):
    """API 호출 헬퍼"""
    url = f"{base or MANAGER_URL}{path}"
    resp = getattr(requests, method)(url, headers=HEADERS, **kwargs)
    return resp.json()


def cmd_run(args):
    """자연어 작업 지시 → native 모드로 자동 실행"""
    request_text = " ".join(args.request)
    target = resolve_target(args.target) if args.target else "http://localhost:8002"

    print(f"📋 요청: {request_text}")
    print(f"🎯 대상: {target}")
    print()

    # 1. 프로젝트 생성
    mode = "native" if not args.manual else "external"
    r = api("post", "/projects", json={
        "name": f"cli-{int(time.time())}",
        "request_text": request_text,
        "master_mode": mode,
    })
    pid = r["project"]["id"]
    print(f"📁 프로젝트: {pid}")

    if args.manual:
        # external 모드 — dispatch만
        api("post", f"/projects/{pid}/plan")
        api("post", f"/projects/{pid}/execute")
        print(f"⚡ dispatch 실행 중...")
        r = api("post", f"/projects/{pid}/dispatch", json={
            "command": request_text,
            "mode": "auto",
            "subagent_url": target,
        })
        result = r.get("result", {})
        print(f"\n{'='*50}")
        print(result.get("stdout", ""))
        if result.get("stderr"):
            print(f"[stderr] {result['stderr']}")
        print(f"{'='*50}")
        print(f"✅ exit={result.get('exit_code')} | evidence={result.get('evidence_id', 'none')}")
        return

    # native 모드 — Master가 계획 수립
    print(f"🧠 Master LLM이 계획 수립 중...")
    plan = api("post", f"/projects/{pid}/master-plan", base=MASTER_URL, json={
        "subagent_url": target,
    })

    tasks = plan.get("tasks", [])
    print(f"📝 {len(tasks)}개 태스크 생성:")
    for t in tasks:
        print(f"   [{t['order']}] {t['title']}")

    # 2. Stage 전환 + 실행
    api("post", f"/projects/{pid}/plan")
    api("post", f"/projects/{pid}/execute")

    # tasks에 subagent_url 추가
    for t in tasks:
        t["subagent_url"] = target

    print(f"\n⚡ 실행 중...")
    r = api("post", f"/projects/{pid}/execute-plan", json={
        "tasks": tasks,
        "subagent_url": target,
        "parallel": not args.sequential,
    })

    # 3. 결과 출력
    print(f"\n{'='*60}")
    print(f"📊 결과: {r.get('overall', '?')} | "
          f"성공: {r.get('tasks_ok', '?')}/{r.get('tasks_total', '?')}")
    print(f"{'='*60}")

    for tr in r.get("task_results", []):
        detail = tr.get("detail", {})
        status = "✅" if tr.get("status") == "ok" else "❌"
        print(f"\n{status} [{tr['order']}] {tr['title']} ({tr.get('duration_s', 0):.2f}s)")
        stdout = detail.get("stdout", "").strip()
        if stdout:
            for line in stdout.split("\n")[:10]:
                print(f"   {line}")
        if detail.get("stderr"):
            print(f"   [stderr] {detail['stderr'][:100]}")

    # 4. Evidence 요약
    ev = api("get", f"/projects/{pid}/evidence/summary")
    print(f"\n📦 Evidence: {ev.get('total_evidence', ev.get('total', 0))}건 | "
          f"성공률: {ev.get('success_rate', '?')}")

    # 5. 완료 보고서
    api("post", f"/projects/{pid}/completion-report", json={
        "summary": f"CLI 실행 완료: {request_text}",
        "outcome": r.get("overall", "unknown"),
        "work_details": [f"[{t['order']}] {t['title']}" for t in tasks],
    })
    print(f"📄 보고서 생성 완료")
    print(f"\n🔗 프로젝트 ID: {pid}")


def cmd_dispatch(args):
    """단일 명령 직접 실행"""
    command = " ".join(args.command)
    target = resolve_target(args.target)

    r = api("post", "/projects", json={
        "name": f"dispatch-{int(time.time())}",
        "request_text": command,
        "master_mode": "external",
    })
    pid = r["project"]["id"]
    api("post", f"/projects/{pid}/plan")
    api("post", f"/projects/{pid}/execute")

    r = api("post", f"/projects/{pid}/dispatch", json={
        "command": command,
        "subagent_url": target,
    })
    result = r.get("result", {})
    print(result.get("stdout", ""))
    if result.get("stderr"):
        print(result["stderr"], file=sys.stderr)


def cmd_list(args):
    """프로젝트 목록"""
    r = api("get", "/projects")
    projects = r.get("projects", [])
    if args.limit:
        projects = projects[-args.limit:]
    print(f"{'ID':14s} {'Name':40s} {'Stage':10s} {'Mode':8s}")
    print("-" * 75)
    for p in projects:
        print(f"{p['id'][:14]:14s} {p['name'][:40]:40s} "
              f"{p.get('current_stage', '?'):10s} {p.get('master_mode', '?'):8s}")


def cmd_status(args):
    """프로젝트 상태 조회"""
    r = api("get", f"/projects/{args.project_id}")
    p = r.get("project", r)
    print(f"ID:      {p.get('id')}")
    print(f"Name:    {p.get('name')}")
    print(f"Stage:   {p.get('current_stage')}")
    print(f"Mode:    {p.get('master_mode')}")
    print(f"Request: {p.get('request_text', '')[:80]}")

    ev = api("get", f"/projects/{args.project_id}/evidence/summary")
    print(f"Evidence: {ev.get('total_evidence', ev.get('total', 0))}건")


def cmd_replay(args):
    """프로젝트 실행 이력 재현"""
    r = api("get", f"/projects/{args.project_id}/replay")
    timeline = r.get("timeline", r.get("steps", []))
    print(f"📼 Replay — {len(timeline)} events")
    for t in timeline:
        ts = t.get("ts", t.get("created_at", ""))[:19]
        action = t.get("action", t.get("title", "?"))
        result = t.get("result", t.get("stdout", ""))[:60]
        print(f"  [{ts}] {action[:40]:40s} → {result}")


def cmd_servers(args):
    """등록된 서버 목록 + 상태"""
    print(f"{'Alias':10s} {'URL':35s} {'Status'}")
    print("-" * 55)
    for alias, url in sorted(SERVER_ALIASES.items()):
        try:
            r = requests.get(f"{url.replace(':8002', ':8002')}/health", timeout=2)
            status = "✅ online" if r.status_code == 200 else f"⚠️ {r.status_code}"
        except Exception:
            status = "❌ offline"
        print(f"{alias:10s} {url:35s} {status}")


def main():
    parser = argparse.ArgumentParser(
        prog="opsclaw",
        description="OpsClaw CLI — 보안 운영 자동화 플랫폼",
    )
    sub = parser.add_subparsers(dest="cmd")

    # run (기본)
    p_run = sub.add_parser("run", help="자연어로 작업 지시 (native 모드)")
    p_run.add_argument("request", nargs="+", help="작업 내용")
    p_run.add_argument("-t", "--target", default="local", help="대상 서버 (v-secu, v-web, v-siem, IP)")
    p_run.add_argument("--manual", action="store_true", help="external 모드 (LLM 계획 없이 직접 실행)")
    p_run.add_argument("--sequential", action="store_true", help="순차 실행 (기본: 병렬)")

    # dispatch
    p_disp = sub.add_parser("dispatch", aliases=["d"], help="단일 명령 직접 실행")
    p_disp.add_argument("command", nargs="+")
    p_disp.add_argument("-t", "--target", default="local")

    # list
    p_list = sub.add_parser("list", aliases=["ls"], help="프로젝트 목록")
    p_list.add_argument("-n", "--limit", type=int, default=10)

    # status
    p_stat = sub.add_parser("status", aliases=["st"], help="프로젝트 상태")
    p_stat.add_argument("project_id")

    # replay
    p_replay = sub.add_parser("replay", help="프로젝트 실행 이력")
    p_replay.add_argument("project_id")

    # servers
    sub.add_parser("servers", aliases=["sv"], help="서버 목록 + 상태")

    args = parser.parse_args()

    # 기본 명령: 인자가 있지만 서브커맨드가 없으면 run으로 간주
    if args.cmd is None:
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            args = parser.parse_args(["run"] + sys.argv[1:])
        else:
            parser.print_help()
            return

    handlers = {
        "run": cmd_run,
        "dispatch": cmd_dispatch, "d": cmd_dispatch,
        "list": cmd_list, "ls": cmd_list,
        "status": cmd_status, "st": cmd_status,
        "replay": cmd_replay,
        "servers": cmd_servers, "sv": cmd_servers,
    }
    handlers[args.cmd](args)


if __name__ == "__main__":
    main()
