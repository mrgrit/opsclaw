"""
packages/playbook_engine/__init__.py
=====================================
Playbook Execution Engine — M12-2

핵심 원칙:
  - Playbook이 법이다. LLM이 즉흥적으로 명령을 만들지 않는다.
  - 각 Step은 Skill/Tool 정의에서 파생된 결정론적 스크립트를 실행한다.
  - 파라미터 우선순위: step.metadata → run-time params → project context → 내장 기본값
  - 실행 결과는 모두 evidence로 기록한다.
  - on_failure 정책(abort/continue)을 반드시 준수한다.
"""

from __future__ import annotations

import time
import uuid
from typing import Any


# ── 내장 Skill 스크립트 템플릿 ─────────────────────────────────────────────
# Skill 이름 → (project_ctx, step_meta) → bash script 문자열
# project_ctx: {"host": str, "targets": [...], "assets": [...], ...}

def _skill_probe_linux_host(ctx: dict, meta: dict) -> str:
    host = meta.get("host") or ctx.get("host", "localhost")
    cmds = meta.get("commands") or [
        "hostname -f",
        "uptime",
        "uname -r",
        "df -h",
        "free -m",
        "ps aux --sort=-%cpu | head -10",
        "ss -tlnp 2>/dev/null | head -20",
    ]
    script_lines = [f"echo '=== probe_linux_host: {host} ==='"]
    script_lines += [f"{c} 2>&1" for c in cmds]
    return "\n".join(script_lines)


def _skill_check_tls_cert(ctx: dict, meta: dict) -> str:
    host = meta.get("host") or ctx.get("host", "localhost")
    port = meta.get("port", 443)
    return (
        f"echo '=== check_tls_cert: {host}:{port} ==='\n"
        f"echo | openssl s_client -connect {host}:{port} -servername {host} 2>/dev/null "
        f"| openssl x509 -noout -subject -issuer -dates 2>&1 "
        f"|| echo 'TLS check failed or openssl not available'"
    )


def _skill_collect_web_latency_facts(ctx: dict, meta: dict) -> str:
    host = meta.get("host") or ctx.get("host", "localhost")
    url = meta.get("url") or f"http://{host}"
    return (
        f"echo '=== collect_web_latency_facts: {url} ==='\n"
        f"for i in 1 2 3; do\n"
        f"  curl -o /dev/null -s -w 'attempt $i: total=%{{time_total}}s connect=%{{time_connect}}s status=%{{http_code}}\\n' {url}\n"
        f"done\n"
        f"curl -o /dev/null -s -w 'https: total=%{{time_total}}s status=%{{http_code}}\\n' "
        f"https://{host} 2>/dev/null || echo 'https probe skipped'"
    )


def _skill_monitor_disk_growth(ctx: dict, meta: dict) -> str:
    path = meta.get("path", "/")
    return (
        f"echo '=== monitor_disk_growth: {path} ==='\n"
        f"df -h {path}\n"
        f"du -sh {path}/* 2>/dev/null | sort -rh | head -20"
    )


def _skill_summarize_incident_timeline(ctx: dict, meta: dict) -> str:
    since = meta.get("since", "1 hour ago")
    return (
        f"echo '=== summarize_incident_timeline (since: {since}) ==='\n"
        f"journalctl --since '{since}' -p err..emerg 2>/dev/null | tail -100 "
        f"|| grep -i 'error\\|warn\\|crit\\|fail' /var/log/syslog 2>/dev/null | tail -50 "
        f"|| echo 'No systemd journal available; checked syslog'"
    )


def _skill_analyze_wazuh_alert_burst(ctx: dict, meta: dict) -> str:
    n = meta.get("lines", 200)
    return (
        f"echo '=== analyze_wazuh_alert_burst ==='\n"
        f"if [ -f /var/ossec/logs/alerts/alerts.log ]; then\n"
        f"  tail -n {n} /var/ossec/logs/alerts/alerts.log\n"
        f"else\n"
        f"  echo 'Wazuh alerts log not found; is wazuh-agent installed?'\n"
        f"  systemctl status wazuh-agent 2>&1 | head -10 || true\n"
        f"fi"
    )


_SKILL_BUILDERS: dict[str, Any] = {
    "probe_linux_host":            _skill_probe_linux_host,
    "check_tls_cert":              _skill_check_tls_cert,
    "collect_web_latency_facts":   _skill_collect_web_latency_facts,
    "monitor_disk_growth":         _skill_monitor_disk_growth,
    "summarize_incident_timeline": _skill_summarize_incident_timeline,
    "analyze_wazuh_alert_burst":   _skill_analyze_wazuh_alert_burst,
}


# ── 내장 Tool 스크립트 템플릿 ──────────────────────────────────────────────

def _tool_run_command(ctx: dict, meta: dict) -> str:
    cmd = meta.get("command") or ctx.get("command")
    if not cmd:
        return "echo 'run_command: no command specified in step metadata'"
    return f"echo '=== run_command ==='\n{cmd} 2>&1"


def _tool_fetch_log(ctx: dict, meta: dict) -> str:
    path = meta.get("log_path") or meta.get("path", "/var/log/syslog")
    lines = meta.get("lines", 100)
    return (
        f"echo '=== fetch_log: {path} ==='\n"
        f"tail -n {lines} {path} 2>/dev/null || echo 'Log file not found: {path}'"
    )


def _tool_query_metric(ctx: dict, meta: dict) -> str:
    return (
        "echo '=== query_metric ==='\n"
        "echo '--- CPU/Load ---'\n"
        "top -bn1 2>/dev/null | head -15 || uptime\n"
        "echo '--- Memory ---'\n"
        "free -m\n"
        "echo '--- Disk ---'\n"
        "df -h\n"
        "echo '--- Network ---'\n"
        "ss -s 2>/dev/null || netstat -s 2>/dev/null | head -20 || true"
    )


def _tool_restart_service(ctx: dict, meta: dict) -> str:
    svc = meta.get("service") or ctx.get("service", "")
    if not svc:
        return "echo 'restart_service: no service specified in step metadata'"
    return (
        f"echo '=== restart_service: {svc} ==='\n"
        f"systemctl status {svc} 2>&1 | head -5 || true\n"
        f"systemctl restart {svc} 2>&1\n"
        f"sleep 2\n"
        f"systemctl status {svc} 2>&1 | head -10"
    )


def _tool_read_file(ctx: dict, meta: dict) -> str:
    path = meta.get("path", "")
    if not path:
        return "echo 'read_file: no path specified in step metadata'"
    return (
        f"echo '=== read_file: {path} ==='\n"
        f"cat {path} 2>/dev/null || echo 'File not found: {path}'"
    )


def _tool_write_file(ctx: dict, meta: dict) -> str:
    path = meta.get("path", "")
    content = meta.get("content", "")
    if not path:
        return "echo 'write_file: no path specified in step metadata'"
    safe_content = content.replace("'", "'\\''")
    return (
        f"echo '=== write_file: {path} ==='\n"
        f"mkdir -p $(dirname {path}) 2>/dev/null || true\n"
        f"cat > {path} << 'OPSCLAW_EOF'\n{content}\nOPSCLAW_EOF\n"
        f"echo 'written: {path}'\n"
        f"wc -c {path}"
    )


_TOOL_BUILDERS: dict[str, Any] = {
    "run_command":     _tool_run_command,
    "fetch_log":       _tool_fetch_log,
    "query_metric":    _tool_query_metric,
    "restart_service": _tool_restart_service,
    "read_file":       _tool_read_file,
    "write_file":      _tool_write_file,
}


# ── 분석형 Skill (bash 실행 후 LLM 해석이 필요한 종류) ──────────────────────
# 이 Skill들은 run_script + analyze 두 단계로 실행된다.
# bash로 원시 데이터를 수집 → SubAgent LLM이 해석 → analysis 반환
_ANALYSIS_SKILLS: dict[str, str] = {
    "analyze_wazuh_alert_burst": "Wazuh 알림 로그에서 비정상적인 알림 급증 패턴을 탐지하고, 주요 위협 유형과 대응 권고를 요약하라.",
    "summarize_incident_timeline": "시스템 오류 로그를 분석하여 인시던트 타임라인을 재구성하고, 근본 원인 가설과 영향 범위를 요약하라.",
}


# ── 스크립트 해석기 ─────────────────────────────────────────────────────────

def resolve_step_script(
    step: dict[str, Any],
    project_ctx: dict[str, Any],
) -> str:
    """
    Playbook step → 실행할 bash script 문자열 반환.

    우선순위:
      1. step.metadata["script"] 직접 지정 (escape hatch)
      2. skill/tool 이름 기반 내장 템플릿
      3. 알 수 없는 경우 안전한 no-op

    project_ctx keys:
      host, targets, assets, params, ...
    """
    step_meta: dict = (step.get("metadata") or {})
    ref = step.get("ref_id") or step.get("ref") or ""
    step_type = step.get("step_type") or step.get("type") or "tool"

    # Escape hatch: step에 직접 script가 지정된 경우
    if "script" in step_meta:
        return step_meta["script"]

    # step metadata + run-time params 병합 (run-time params가 override)
    merged_meta = {**step_meta, **project_ctx.get("params", {})}

    if step_type == "skill":
        builder = _SKILL_BUILDERS.get(ref)
        if builder:
            return builder(project_ctx, merged_meta)
        return f"echo 'Unknown skill: {ref} — step skipped'"

    if step_type == "tool":
        builder = _TOOL_BUILDERS.get(ref)
        if builder:
            return builder(project_ctx, merged_meta)
        return f"echo 'Unknown tool: {ref} — step skipped'"

    return f"echo 'Unknown step type: {step_type} ref={ref}'"


# ── 메인 실행 엔진 ──────────────────────────────────────────────────────────

def run_playbook_steps(
    project_id: str,
    subagent_url: str | None = None,
    dry_run: bool = False,
    params: dict[str, Any] | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """
    프로젝트에 연결된 Playbook을 단계별로 실행한다.

    - Playbook이 없으면 오류 반환
    - 각 Step: 스크립트 빌드 → A2A dispatch → evidence 기록
    - on_failure='abort' 이면 해당 Step 실패 시 즉시 중단
    - on_failure='continue' 이면 실패해도 다음 Step으로
    - dry_run=True 이면 실행 없이 실행 계획만 반환

    반환:
      {
        "project_id": str,
        "playbook_id": str,
        "playbook_name": str,
        "dry_run": bool,
        "steps_total": int,
        "steps_ok": int,
        "steps_failed": int,
        "steps_skipped": int,
        "status": "success"|"partial"|"failed"|"dry_run",
        "step_results": [
          {
            "order": int,
            "name": str,
            "type": str,
            "ref": str,
            "script": str,
            "status": "ok"|"failed"|"skipped"|"dry_run",
            "exit_code": int|None,
            "stdout": str,
            "stderr": str,
            "evidence_id": str|None,
            "duration_s": float,
          }
        ]
      }
    """
    from packages.project_service import (
        get_project_record,
        get_project_assets,
        get_project_targets,
        get_project_playbooks,
        create_minimal_evidence_record,
        dispatch_command_to_subagent,
        ProjectStageError,
    )
    from packages.registry_service import resolve_playbook

    # ── 1. 프로젝트 상태 확인 ───────────────────────────────────────────────
    project = get_project_record(project_id, database_url=database_url)
    if project["current_stage"] not in ("execute", "plan") and not dry_run:
        raise ProjectStageError(
            f"Project must be in execute stage to run playbook "
            f"(current: {project['current_stage']})"
        )

    # ── 2. Playbook 조회 ────────────────────────────────────────────────────
    pb_rows = get_project_playbooks(project_id, database_url=database_url)
    if not pb_rows:
        raise ValueError(f"No playbook linked to project {project_id}")
    playbook_id = pb_rows[0]["playbook_id"]
    playbook_name = pb_rows[0].get("playbook", {}).get("name", playbook_id)

    # ── 3. Playbook steps resolve ───────────────────────────────────────────
    resolved = resolve_playbook(playbook_id, database_url=database_url)
    steps = sorted(resolved.get("steps", []), key=lambda s: s.get("order", 0))
    if not steps:
        raise ValueError(f"Playbook {playbook_name} has no steps")

    # ── 4. Project context 구성 ─────────────────────────────────────────────
    assets = get_project_assets(project_id, database_url=database_url)
    targets = get_project_targets(project_id, database_url=database_url)

    # 첫 번째 target의 endpoint에서 host 추출
    primary_host = "localhost"
    if targets:
        endpoint = targets[0].get("target", {}).get("endpoint") or targets[0].get("endpoint", "")
        if endpoint:
            # "http://192.168.1.100:8080" → "192.168.1.100"
            primary_host = endpoint.replace("http://", "").replace("https://", "").split(":")[0].split("/")[0]

    project_ctx: dict[str, Any] = {
        "project_id": project_id,
        "project_name": project.get("name", ""),
        "host": primary_host,
        "assets": assets,
        "targets": targets,
        "params": params or {},
    }

    # ── 4b. 과거 경험 컨텍스트 주입 (retrieval pipeline) ─────────────────────
    if not dry_run:
        try:
            from packages.retrieval_service import get_context_for_project
            past_ctx = get_context_for_project(project_id, database_url=database_url)
            project_ctx["past_experiences"] = past_ctx.get("experiences", [])
            project_ctx["asset_history"] = past_ctx.get("asset_history", [])
            project_ctx["documents"] = past_ctx.get("documents", [])
        except Exception:
            project_ctx["past_experiences"] = []
            project_ctx["asset_history"] = []
            project_ctx["documents"] = []

    # ── 5. Step별 실행 ──────────────────────────────────────────────────────
    step_results: list[dict[str, Any]] = []
    steps_ok = 0
    steps_failed = 0
    steps_skipped = 0
    abort_triggered = False

    for step in steps:
        order = step.get("order", 0)
        name = step.get("name") or step.get("ref_id") or f"step-{order}"
        step_type = step.get("type") or step.get("step_type") or "tool"
        ref = step.get("ref_id") or step.get("ref") or ""
        on_failure = step.get("on_failure") or "abort"

        if abort_triggered:
            step_results.append({
                "order": order, "name": name, "type": step_type, "ref": ref,
                "script": "", "status": "skipped", "exit_code": None,
                "stdout": "", "stderr": "Skipped: previous step aborted",
                "evidence_id": None, "duration_s": 0.0,
            })
            steps_skipped += 1
            continue

        # 스크립트 결정 — LLM이 아니라 Playbook 기반
        script = resolve_step_script(step, project_ctx)
        # 분석형 Skill 여부 판단 (bash 수집 + LLM 해석 두 단계)
        analysis_question = _ANALYSIS_SKILLS.get(ref) if step_type == "skill" else None

        if dry_run:
            mode = "dry_run+analyze" if analysis_question else "dry_run"
            step_results.append({
                "order": order, "name": name, "type": step_type, "ref": ref,
                "script": script, "status": "dry_run", "mode": mode,
                "exit_code": None, "stdout": "", "stderr": "",
                "evidence_id": None, "duration_s": 0.0,
            })
            continue

        # ── 실행 ────────────────────────────────────────────────────────────
        t0 = time.monotonic()
        evidence_id = None
        analysis = None
        try:
            result = dispatch_command_to_subagent(
                project_id=project_id,
                command=script,
                subagent_url=subagent_url,
                timeout_s=120,
                database_url=database_url,
            )
            duration = time.monotonic() - t0
            exit_code = result.get("exit_code", 0)
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            evidence_id = result.get("evidence_id")
            status = "ok" if exit_code == 0 else "failed"

            # ── 분석형 Skill: bash 결과를 SubAgent LLM이 해석 ──────────────
            if analysis_question and stdout and subagent_url:
                from packages.a2a_protocol import A2AClient, A2AClientConfig
                try:
                    a2a = A2AClient(A2AClientConfig(base_url=subagent_url, timeout_s=150))
                    ar = a2a.analyze(
                        project_id=project_id,
                        command_output=stdout,
                        question=analysis_question,
                    )
                    analysis = ar.get("analysis", "")
                except Exception as ae:
                    analysis = f"[분석 실패: {ae}]"

        except Exception as exc:
            duration = time.monotonic() - t0
            exit_code = -1
            stdout = ""
            stderr = str(exc)
            status = "failed"
            try:
                ev = create_minimal_evidence_record(
                    project_id=project_id,
                    command=script[:500],
                    stdout="",
                    stderr=stderr,
                    exit_code=-1,
                    database_url=database_url,
                )
                evidence_id = ev.get("id")
            except Exception:
                pass

        step_result: dict[str, Any] = {
            "order": order, "name": name, "type": step_type, "ref": ref,
            "script": script, "status": status, "exit_code": exit_code,
            "stdout": stdout[:2000],  # 스냅샷 (full은 evidence에)
            "stderr": stderr[:500],
            "evidence_id": evidence_id,
            "duration_s": round(duration, 2),
        }
        if analysis is not None:
            step_result["analysis"] = analysis
        step_results.append(step_result)

        if status == "ok":
            steps_ok += 1
        else:
            steps_failed += 1
            if on_failure == "abort":
                abort_triggered = True

    # ── 6. 종합 상태 ────────────────────────────────────────────────────────
    if dry_run:
        overall = "dry_run"
    elif steps_failed == 0:
        overall = "success"
    elif steps_ok == 0:
        overall = "failed"
    else:
        overall = "partial"

    # ── 7. 실행 완료 후 히스토리 기록 + Task Memory 구성 ─────────────────────
    if not dry_run:
        import uuid
        job_run_id = str(uuid.uuid4())
        try:
            from packages.history_service import ingest_event
            ingest_event(
                project_id=project_id,
                event="playbook:run",
                context={
                    "playbook_id": playbook_id,
                    "playbook_name": playbook_name,
                    "status": overall,
                    "steps_ok": steps_ok,
                    "steps_failed": steps_failed,
                    "steps_skipped": steps_skipped,
                    "subagent_url": subagent_url,
                },
                job_run_id=job_run_id,
                database_url=database_url,
            )
        except Exception:
            pass
        try:
            from packages.experience_service import build_task_memory
            build_task_memory(project_id, database_url=database_url)
        except Exception:
            pass

    return {
        "project_id": project_id,
        "playbook_id": playbook_id,
        "playbook_name": playbook_name,
        "dry_run": dry_run,
        "steps_total": len(steps),
        "steps_ok": steps_ok,
        "steps_failed": steps_failed,
        "steps_skipped": steps_skipped,
        "status": overall,
        "step_results": step_results,
    }
