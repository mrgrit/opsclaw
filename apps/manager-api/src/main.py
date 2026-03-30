import asyncio
import json as _json
import os
import re as _re_mod
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import re as _re_secret

from fastapi import APIRouter, FastAPI, HTTPException, Request, WebSocket, status


# ── 시크릿 마스킹 (PAT, token, password 노출 방지) ─────────────────────────
_SECRET_PATTERNS = [
    (r'ghp_[A-Za-z0-9_]{36,}', 'ghp_****'),
    (r'github_pat_[A-Za-z0-9_]{22,}', 'github_pat_****'),
    (r'gho_[A-Za-z0-9_]{36,}', 'gho_****'),
    (r'ghs_[A-Za-z0-9_]{36,}', 'ghs_****'),
    (r'glpat-[A-Za-z0-9_\-]{20,}', 'glpat-****'),
    (r'https?://[^@\s]+@github\.com', 'https://****@github.com'),
]
_SECRET_COMPILED = [(_re_secret.compile(p), r) for p, r in _SECRET_PATTERNS]


def _mask_secrets(text: str) -> str:
    """문자열 내 시크릿(PAT, token 등)을 마스킹."""
    if not text:
        return text
    for pat, repl in _SECRET_COMPILED:
        text = pat.sub(repl, text)
    return text


def _mask_dict(d: dict) -> dict:
    """dict 내 문자열 필드 시크릿 마스킹."""
    masked = dict(d)
    for key in ('stdout', 'stderr', 'command', 'body_ref', 'stdout_ref',
                'command_text', 'instruction_prompt', 'original_command', 'summary'):
        if key in masked and isinstance(masked[key], str):
            masked[key] = _mask_secrets(masked[key])
    if 'detail' in masked and isinstance(masked['detail'], dict):
        masked['detail'] = _mask_dict(masked['detail'])
    return masked
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from packages.pi_adapter.runtime import PiRuntimeClient, PiRuntimeConfig
from packages.asset_registry import (
    AssetConflictError,
    AssetNotFoundError,
    AssetRegistryError,
    check_asset_health,
    create_asset,
    delete_asset,
    get_asset,
    list_assets,
    onboard_asset,
    resolve_target_from_asset,
    update_asset,
)
from packages.registry_service import (
    RegistryNotFoundError,
    explain_playbook,
    get_playbook,
    get_playbook_by_name,
    get_playbook_steps,
    get_skill_by_name,
    get_tool_by_name,
    list_playbook_versions,
    list_playbooks,
    list_skills,
    list_tools,
    resolve_playbook,
    rollback_playbook,
    snapshot_playbook,
    upsert_playbook,
    upsert_playbook_steps,
)
from packages.evidence_service import get_evidence_content, get_evidence_summary
from packages.validation_service import (
    get_validation_runs,
    get_validation_status,
    run_validation_check,
)
from packages.project_service import (
    ProjectNotFoundError,
    ProjectServiceError,
    ProjectStageError,
    close_project,
    create_async_job,
    create_minimal_evidence_record,
    create_project_record,
    execute_project_record,
    finalize_report_stage_record,
    get_assets,
    get_async_job,
    get_evidence_for_project,
    get_playbooks,
    get_project_assets,
    get_project_playbooks,
    get_project_record,
    get_project_report,
    get_project_targets,
    get_targets,
    link_asset_to_project,
    link_playbook_to_project,
    link_target_to_project,
    dispatch_command_to_subagent,
    list_async_jobs,
    list_projects,
    plan_project_record,
    replan_project,
    select_assets_for_project,
    resolve_targets_for_project,
    update_async_job,
    update_asset_subagent_status,
    validate_project_record,
)
from packages.approval_engine import get_approval_status, ApprovalError
from packages.graph_runtime import run_project_graph
from packages.scheduler_service import (
    create_schedule,
    get_schedule,
    list_schedules,
    update_schedule,
    delete_schedule,
    execute_due_schedule,
)
from packages.watch_service import (
    create_watch_job,
    get_watch_job,
    list_watch_jobs,
    update_watch_job_status,
    delete_watch_job,
    list_watch_events,
    run_watch_check,
    list_incidents,
    resolve_incident,
)
from packages.history_service import (
    ingest_event,
    get_project_history,
    get_asset_history,
)
from packages.experience_service import (
    build_task_memory,
    get_task_memory,
    list_task_memories,
    create_experience,
    promote_to_experience,
    list_experiences,
    get_experience,
)
from packages.retrieval_service import (
    index_document,
    search_documents,
    reindex_project,
    get_context_for_project,
)
from packages.audit_service import (
    log_audit_event,
    query_audit_logs,
    export_audit_json,
    export_audit_csv,
)
from packages.rbac_service import (
    create_role,
    list_roles,
    get_role,
    get_role_by_name,
    assign_role,
    revoke_role,
    get_actor_permissions,
    check_permission,
    update_role_permissions,
)
from packages.monitoring_service import (
    get_system_health,
    get_operational_metrics,
)
from packages.reporting_service import (
    generate_project_report,
    export_evidence_pack,
    export_evidence_pack_json,
)
from packages.backup_service import (
    create_backup,
    list_backups,
    get_backup_info,
)
from packages.notification_service import (
    create_channel,
    get_channel,
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
from packages.completion_report_service import (
    create_completion_report,
    get_completion_report,
    list_completion_reports,
    auto_generate_report,
)
from packages.pow_service import (
    generate_proof,
    verify_chain,
    get_agent_stats,
    get_leaderboard,
    get_project_pow,
    get_project_replay,
)


class ProjectCreateRequest(BaseModel):
    name: str
    request_text: str
    mode: str = "one_shot"
    master_mode: str = "native"   # "native" | "external" (M15 Platform Modes)


class RuntimePromptRequest(BaseModel):
    prompt: str
    role: str = "manager"


class MinimalEvidenceRequest(BaseModel):
    command: str
    stdout: str
    stderr: str = ""
    exit_code: int = 0


class DispatchRequest(BaseModel):
    command: str
    subagent_url: str | None = None
    timeout_s: int = 30
    mode: str = "auto"  # "auto" | "shell" | "adhoc"
    # auto: shell 문법이면 그대로, 자연어면 LLM 변환
    # shell: LLM 변환 없이 그대로 실행
    # adhoc: 항상 LLM으로 자연어 → shell 변환 후 실행


class PlaybookRunRequest(BaseModel):
    subagent_url: str | None = None
    dry_run: bool = False
    params: dict | None = None


class CompletionReportRequest(BaseModel):
    summary: str
    outcome: str = "unknown"          # success|partial|failed|unknown
    work_details: list | None = None
    issues: list | None = None
    next_steps: list | None = None
    reviewer_id: str | None = None
    auto: bool = False                # True면 evidence/report 자동 집계


class ExecutePlanRequest(BaseModel):
    """Master /master-plan 결과의 tasks 배열을 받아 순서대로 실행."""
    tasks: list[dict] = []     # [{order, title, playbook_hint, instruction_prompt, risk_level, subagent_url?}]
    playbook_id: str | None = None  # M22 A-02: 지정 시 해당 Playbook 직접 실행 (tasks 불필요)
    subagent_url: str | None = None
    dry_run: bool = False
    confirmed: bool = False    # B-05: True면 risk_level=critical 태스크도 실제 실행
    async_mode: bool = False   # M23 A-04: True면 백그라운드 실행, 즉시 job_id 반환
    parallel: bool = False     # M23 A-05: True면 병렬 dispatch (ThreadPoolExecutor)


class ScheduleCreateRequest(BaseModel):
    project_name: str
    schedule_type: str
    cron_expr: str | None = None
    metadata: dict | None = None


class SchedulePatchRequest(BaseModel):
    enabled: bool | None = None
    cron_expr: str | None = None


class WatcherCreateRequest(BaseModel):
    project_name: str
    watch_type: str
    metadata: dict | None = None


class WatcherStatusRequest(BaseModel):
    status: str


class HistoryIngestRequest(BaseModel):
    event: str
    context: dict | None = None
    job_run_id: str | None = None


class ExperienceCreateRequest(BaseModel):
    category: str
    title: str
    summary: str
    outcome: str | None = None
    asset_id: str | None = None
    metadata: dict | None = None


class ExperiencePromoteRequest(BaseModel):
    category: str
    title: str
    outcome: str | None = None
    asset_id: str | None = None


class RoleCreateRequest(BaseModel):
    name: str
    permissions: list[str]
    description: str | None = None


class RoleAssignRequest(BaseModel):
    actor_id: str
    role_id: str
    actor_type: str = "user"


class AuditExportRequest(BaseModel):
    format: str = "json"  # "json" | "csv"
    event_type: str | None = None
    project_id: str | None = None
    limit: int = 1000


class ChannelCreateRequest(BaseModel):
    name: str
    channel_type: str   # 'webhook', 'email', 'log'
    config: dict = {}
    enabled: bool = True


class ChannelPatchRequest(BaseModel):
    enabled: bool | None = None
    config: dict | None = None


class RuleCreateRequest(BaseModel):
    name: str
    event_type: str
    channel_id: str
    filter_conditions: dict = {}
    enabled: bool = True


class RulePatchRequest(BaseModel):
    enabled: bool | None = None


class NotificationTestRequest(BaseModel):
    event_type: str
    payload: dict = {}


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"]) 

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "manager-api"}

    return router


def create_runtime_router() -> APIRouter:
    router = APIRouter(prefix="/runtime", tags=["runtime"])
    client = PiRuntimeClient(PiRuntimeConfig())

    @router.post("/invoke")
    def invoke_runtime(payload: RuntimePromptRequest) -> dict[str, Any]:
        try:
            session_id = client.open_session("manager-api-runtime")
            result = client.invoke_model(
                payload.prompt,
                {
                    "session_id": session_id,
                    "role": payload.role,
                },
            )
            client.close_session(session_id)
            return {"status": "ok", "session_id": session_id, "result": result}
        except NotImplementedError as exc:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail={"message": str(exc)},
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": f"runtime invocation failed: {exc}"},
            ) from exc

    return router


def create_project_router() -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["projects"])

    @router.get("")
    def list_projects_endpoint(limit: int = 50) -> dict[str, Any]:
        items = list_projects(limit)
        return {"projects": items, "items": items}

    @router.post("")
    def create_project(payload: ProjectCreateRequest) -> dict[str, Any]:
        try:
            project = create_project_record(
                name=payload.name,
                request_text=payload.request_text,
                mode=payload.mode,
                master_mode=payload.master_mode,
            )
            return {"status": "ok", "project": project}
        except ProjectServiceError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"message": str(exc)},
            ) from exc

    @router.post("/{project_id}/plan")
    def plan_project(project_id: str) -> dict[str, Any]:
        try:
            project = plan_project_record(project_id)
            return {"status": "ok", "project": project}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}")
    def get_project(project_id: str) -> dict[str, Any]:
        try:
            project = get_project_record(project_id)
            return {"status": "ok", "project": project}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/execute")
    def execute_project(project_id: str) -> dict[str, Any]:
        try:
            result = execute_project_record(project_id)
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/validate")
    def validate_project(project_id: str) -> dict[str, Any]:
        try:
            result = validate_project_record(project_id)
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/report/finalize")
    def finalize_report(project_id: str) -> dict[str, Any]:
        try:
            result = finalize_report_stage_record(project_id)
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/evidence/minimal")
    def create_minimal_evidence(project_id: str, payload: MinimalEvidenceRequest) -> dict[str, Any]:
        try:
            evidence = create_minimal_evidence_record(
                project_id=project_id,
                command=payload.command,
                stdout=payload.stdout,
                stderr=payload.stderr,
                exit_code=payload.exit_code,
            )
            return {"status": "ok", "evidence": evidence}
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/report")
    def get_project_report_endpoint(project_id: str) -> dict[str, Any]:
        try:
            report = get_project_report(project_id)
            return {"status": "ok", "report": report}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/evidence")
    def get_project_evidence_endpoint(project_id: str) -> dict[str, Any]:
        try:
            raw = get_evidence_for_project(project_id)
            # Normalize fields for frontend compatibility
            normalized = []
            for ev in raw:
                item = dict(ev)
                # body_ref → command
                item["command"] = item.pop("body_ref", "") or ""
                # stdout_ref: "inline://stdout/ev_xxx:content" → extract content
                stdout_ref = item.pop("stdout_ref", "") or ""
                if stdout_ref.startswith("inline://stdout/"):
                    # format: inline://stdout/ev_id:actual_content
                    colon_idx = stdout_ref.find(":", len("inline://stdout/"))
                    item["stdout"] = stdout_ref[colon_idx + 1:] if colon_idx != -1 else stdout_ref
                else:
                    item["stdout"] = stdout_ref
                item["stderr"] = item.pop("stderr_ref", "") or ""
                normalized.append(_mask_dict(item))
            return {"status": "ok", "project_id": project_id, "evidence": normalized, "items": normalized}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/close")
    def close_project_endpoint(project_id: str) -> dict[str, Any]:
        try:
            project = close_project(project_id)
            return {"status": "ok", "project": project}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectStageError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/assets/{asset_id}")
    def link_project_asset(project_id: str, asset_id: str) -> dict[str, Any]:
        try:
            result = link_asset_to_project(project_id, asset_id)
            return {
                "status": "ok",
                "project_id": result["project_id"],
                "asset_id": result["asset_id"],
                "role": result["scope_role"],
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/assets")
    def get_project_assets_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_project_assets(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/targets/{target_id}")
    def link_project_target(project_id: str, target_id: str) -> dict[str, Any]:
        try:
            result = link_target_to_project(project_id, target_id)
            return {
                "status": "ok",
                "project_id": result["project_id"],
                "target_id": result["target_id"],
                "role": result["scope_role"],
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/targets")
    def get_project_targets_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_project_targets(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/playbooks/{playbook_id}")
    def link_project_playbook(project_id: str, playbook_id: str) -> dict[str, Any]:
        try:
            result = link_playbook_to_project(project_id, playbook_id)
            return {
                "status": "ok",
                "project_id": result["project_id"],
                "playbook_id": result["playbook_id"],
                "role": result["role"],
            }
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/playbooks")
    def get_project_playbooks_endpoint(project_id: str) -> dict[str, Any]:
        try:
            items = get_project_playbooks(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/dispatch")
    def dispatch_project(project_id: str, payload: DispatchRequest) -> dict[str, Any]:
        command = payload.command
        needs_llm = False

        if payload.mode == "adhoc":
            needs_llm = True
        elif payload.mode == "auto":
            # 간단한 휴리스틱: 한글 포함 또는 공백 많으면 자연어로 판단
            import re
            has_korean = bool(re.search(r"[\uAC00-\uD7A3]", command))
            looks_like_prose = len(command.split()) > 8 and not command.strip().startswith("#!")
            needs_llm = has_korean or looks_like_prose

        if needs_llm:
            # LLM으로 자연어 → shell script 변환
            try:
                from packages.pi_adapter.runtime.client import PiRuntimeClient, PiRuntimeConfig
                _pi = PiRuntimeClient(PiRuntimeConfig(default_role="manager"))
                llm_result = _pi.invoke_model(
                    prompt=(
                        f"Convert the following task instruction into a bash shell script that runs directly on the target Linux server.\n"
                        f"Rules: Output ONLY the bash script. No explanation. No markdown. No API calls. Use standard Linux commands (df, free, ps, systemctl, apt, etc.).\n\n"
                        f"Task: {command}"
                    ),
                    context={
                        "system_prompt": (
                            "You are a bash script generator for Linux servers. "
                            "Given a task description, output ONLY the bash script to execute on the server. "
                            "Use standard Linux CLI tools. Never call external APIs. No markdown fences. No explanation."
                        ),
                        "role": "manager",
                    },
                )
                converted = llm_result.get("stdout", "").strip()
                # 마크다운 코드블록 제거
                import re as _re
                converted = _re.sub(r"^```(?:bash|sh)?\n?", "", converted, flags=_re.MULTILINE)
                converted = _re.sub(r"\n?```\s*$", "", converted, flags=_re.MULTILINE)
                command = converted.strip() or command
            except Exception:
                pass  # 변환 실패 시 원본 명령 그대로 시도

        try:
            result = dispatch_command_to_subagent(
                project_id=project_id,
                command=command,
                subagent_url=payload.subagent_url,
                timeout_s=payload.timeout_s,
            )
            result["original_command"] = payload.command
            result["llm_converted"] = needs_llm
            return {"status": "ok", "result": _mask_dict(result)}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except (ProjectStageError, ProjectServiceError) as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/playbook/run")
    def run_playbook(project_id: str, payload: PlaybookRunRequest) -> dict[str, Any]:
        """
        프로젝트에 연결된 Playbook을 단계별로 실행한다.
        Playbook이 결정한 순서대로 각 Step을 A2A로 dispatch하고 evidence를 기록한다.
        dry_run=true 이면 실행 계획만 반환한다.
        """
        from packages.playbook_engine import run_playbook_steps

        try:
            result = run_playbook_steps(
                project_id=project_id,
                subagent_url=payload.subagent_url,
                dry_run=payload.dry_run,
                params=payload.params,
            )
            # B-01: Playbook run 완료 후 PoW 블록 자동 생성 (dry_run 제외)
            if not payload.dry_run:
                agent_id = payload.subagent_url or "local"
                for sr in result.get("step_results", []):
                    if sr.get("status") not in ("ok", "failed"):
                        continue
                    try:
                        generate_proof(
                            project_id=project_id,
                            agent_id=agent_id,
                            task_order=sr.get("order", 0),
                            task_title=sr.get("name", ""),
                            exit_code=sr.get("exit_code", 0 if sr.get("status") == "ok" else 1),
                            stdout=sr.get("stdout", ""),
                            stderr=sr.get("stderr", ""),
                            duration_s=sr.get("duration_s", 0.0),
                            risk_level="medium",
                        )
                    except Exception:
                        pass  # PoW 실패가 Playbook 결과에 영향 주지 않음
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except (ProjectStageError, ValueError) as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc

    # ── execute-plan 헬퍼 (M23: 순차/병렬/비동기 공용) ─────────────────────

    def _dispatch_single_task(
        project_id: str,
        task: dict,
        pb_map: dict[str, str],
        global_subagent_url: str | None,
        dry_run: bool,
        confirmed: bool,
    ) -> dict[str, Any]:
        """1개 task 실행 → step_result dict 반환. 순차/병렬 모두에서 호출."""
        from packages.playbook_engine import run_playbook_steps
        from packages.project_service import dispatch_command_to_subagent

        order = task.get("order", 0)
        title = task.get("title", f"task-{order}")
        hint = task.get("playbook_hint")
        prompt = task.get("instruction_prompt", title)
        risk = task.get("risk_level", "medium")
        # M23 A-05: task별 subagent_url (없으면 전역 사용)
        task_subagent = task.get("subagent_url") or global_subagent_url

        # M22 A-03: sudo 포함 명령은 risk_level 자동 high 상향
        sudo_elevated = False
        if _re_mod.search(r'\bsudo\b', prompt or "") and risk in ("low", "medium"):
            risk = "high"
            sudo_elevated = True

        # B-05: critical 태스크는 dry_run 강제 (confirmed=True이면 실제 실행)
        effective_dry_run = dry_run or (risk == "critical" and not confirmed)

        step_result: dict[str, Any] = {
            "order": order,
            "title": title,
            "risk_level": risk,
            "dry_run": effective_dry_run,
            "sudo_elevated": sudo_elevated,
            "method": None,
            "status": "pending",
            "detail": {},
        }

        t0 = time.time()
        try:
            pb_id = pb_map.get(hint) if hint else None
            if pb_id and not effective_dry_run:
                r = run_playbook_steps(
                    project_id=project_id,
                    subagent_url=task_subagent,
                    dry_run=False,
                    params={"task_title": title},
                )
                step_result["method"] = f"playbook:{hint}"
                step_result["status"] = r.get("status", "ok")
                step_result["detail"] = {
                    "steps_ok": r.get("steps_ok", 0),
                    "steps_failed": r.get("steps_failed", 0),
                }
            elif effective_dry_run:
                step_result["method"] = f"playbook:{hint}" if hint else "adhoc"
                step_result["status"] = "dry_run"
                step_result["detail"] = {"instruction_prompt": prompt[:200]}
            else:
                r = dispatch_command_to_subagent(
                    project_id=project_id,
                    command=prompt,
                    subagent_url=task_subagent,
                    timeout_s=120,
                )
                step_result["method"] = "adhoc"
                step_result["status"] = "ok" if r.get("exit_code", 1) == 0 else "failed"
                full_stdout = r.get("stdout") or ""
                step_result["_full_stdout"] = full_stdout
                step_result["detail"] = {
                    "exit_code": r.get("exit_code"),
                    "stdout": full_stdout[:4096],
                    "stderr": (r.get("stderr") or "")[:1024],
                }
        except Exception as exc:
            step_result["status"] = "error"
            step_result["detail"] = {"error": str(exc)}

        step_result["duration_s"] = round(time.time() - t0, 3)
        return step_result

    def _run_execute_plan_sync(
        project_id: str,
        payload: ExecutePlanRequest,
    ) -> dict[str, Any]:
        """execute-plan 동기 실행 로직. 순차/병렬 모두 처리. async에서도 호출됨."""
        from packages.playbook_engine import run_playbook_steps
        from packages.registry_service import list_playbooks

        # M22 A-02: playbook_id 직접 지정
        if payload.playbook_id and not payload.tasks:
            result = run_playbook_steps(
                project_id=project_id,
                subagent_url=payload.subagent_url,
                dry_run=payload.dry_run,
                params={"playbook_id": payload.playbook_id},
            )
            if not payload.dry_run:
                agent_id = payload.subagent_url or "local"
                for sr in result.get("step_results", []):
                    if sr.get("status") not in ("ok", "failed"):
                        continue
                    try:
                        generate_proof(
                            project_id=project_id, agent_id=agent_id,
                            task_order=sr.get("order", 0), task_title=sr.get("name", ""),
                            exit_code=sr.get("exit_code", 0 if sr.get("status") == "ok" else 1),
                            stdout=sr.get("stdout", ""), stderr=sr.get("stderr", ""),
                            duration_s=sr.get("duration_s", 0.0), risk_level="medium",
                        )
                    except Exception:
                        pass
            steps_ok = result.get("steps_ok", 0)
            steps_failed = result.get("steps_failed", 0)
            return {
                "status": "ok", "project_id": project_id,
                "tasks_total": result.get("steps_total", 0),
                "tasks_ok": steps_ok, "tasks_failed": steps_failed,
                "overall": result.get("status", "ok"),
                "playbook_id": payload.playbook_id, "result": result,
            }

        tasks = sorted(payload.tasks, key=lambda t: t.get("order", 0))
        pb_map: dict[str, str] = {}
        try:
            pb_map = {pb["name"]: pb["id"] for pb in list_playbooks()}
        except Exception:
            pass

        # ── M23 A-05: parallel=true 시 병렬 dispatch ─────────
        if payload.parallel and len(tasks) > 1 and not payload.dry_run:
            task_results: list[dict] = []
            with ThreadPoolExecutor(max_workers=min(len(tasks), 5)) as pool:
                futures = {
                    pool.submit(
                        _dispatch_single_task, project_id, t, pb_map,
                        payload.subagent_url, payload.dry_run, payload.confirmed,
                    ): t
                    for t in tasks
                }
                for future in as_completed(futures):
                    task_results.append(future.result())
            # order 순 정렬
            task_results.sort(key=lambda r: r.get("order", 0))
        else:
            # 순차 실행 (기존 동작)
            task_results = []
            for task in tasks:
                sr = _dispatch_single_task(
                    project_id, task, pb_map,
                    payload.subagent_url, payload.dry_run, payload.confirmed,
                )
                task_results.append(sr)

        tasks_ok = sum(1 for r in task_results if r["status"] in ("ok", "dry_run", "success", "partial"))
        tasks_failed = sum(1 for r in task_results if r["status"] not in ("ok", "dry_run", "success", "partial", "pending"))
        overall = "success" if tasks_failed == 0 else ("partial" if tasks_ok > 0 else "failed")
        if payload.dry_run:
            overall = "dry_run"

        # PoW 블록 생성 (dry_run 제외)
        if not payload.dry_run:
            for sr in task_results:
                if sr["status"] not in ("ok", "failed"):
                    continue
                detail = sr.get("detail") or {}
                agent_id = payload.subagent_url or "local"
                try:
                    generate_proof(
                        project_id=project_id, agent_id=agent_id,
                        task_order=sr.get("order", 0), task_title=sr.get("title", ""),
                        exit_code=detail.get("exit_code", 0 if sr["status"] == "ok" else 1),
                        stdout=sr.pop("_full_stdout", detail.get("stdout", "")),
                        stderr=detail.get("stderr", ""),
                        duration_s=sr.get("duration_s", 0.0),
                        risk_level=sr.get("risk_level", "low"),
                    )
                except Exception:
                    pass

        # M24: 고보상 에피소드 자동 경험 승급
        if not payload.dry_run:
            try:
                from packages.experience_service import auto_promote_high_reward
                auto_promote_high_reward(project_id)
            except Exception:
                pass  # 승급 실패가 실행 결과에 영향 주지 않음

        return {
            "status": "ok", "project_id": project_id,
            "tasks_total": len(tasks), "tasks_ok": tasks_ok,
            "tasks_failed": tasks_failed, "overall": overall,
            "task_results": [_mask_dict(tr) for tr in task_results],
        }

    def _execute_plan_background(job_id: str, project_id: str, payload: ExecutePlanRequest):
        """백그라운드 스레드에서 실행되는 async execute-plan."""
        update_async_job(job_id, "running")
        try:
            result = _run_execute_plan_sync(project_id, payload)
            update_async_job(job_id, "completed", result_json=result)
        except Exception as exc:
            update_async_job(job_id, "failed", error_message=str(exc))

    @router.post("/{project_id}/execute-plan")
    def execute_plan(project_id: str, payload: ExecutePlanRequest) -> dict[str, Any]:
        """
        Master /master-plan 결과의 tasks를 실행한다.

        옵션:
          - async_mode=true: 백그라운드 실행, 즉시 job_id 반환 (M23)
          - parallel=true: 여러 task를 동시 dispatch (M23)
          - playbook_id: 직접 Playbook 실행 (M22)
          - task별 subagent_url: 멀티에이전트 지원 (M23)
        """
        # M23 A-04: async_mode 시 백그라운드 실행
        if payload.async_mode:
            job = create_async_job(project_id, "execute_plan", payload.model_dump())
            thread = threading.Thread(
                target=_execute_plan_background,
                args=(job["id"], project_id, payload),
                daemon=True,
            )
            thread.start()
            return {"status": "accepted", "job_id": job["id"], "project_id": project_id}

        # 동기 실행
        try:
            return _run_execute_plan_sync(project_id, payload)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectServiceError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc

    # ── Async Jobs polling (M23) ──────────────────────────────────────────

    @router.get("/{project_id}/async-jobs")
    def list_async_jobs_endpoint(project_id: str, limit: int = 20) -> dict[str, Any]:
        jobs = list_async_jobs(project_id, limit=limit)
        return {"status": "ok", "project_id": project_id, "jobs": jobs}

    @router.get("/{project_id}/async-jobs/{job_id}")
    def get_async_job_endpoint(project_id: str, job_id: str) -> dict[str, Any]:
        job = get_async_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail={"message": f"Job not found: {job_id}"})
        return {"status": "ok", **job}

    @router.post("/{project_id}/completion-report")
    def create_completion_report_endpoint(project_id: str, payload: CompletionReportRequest) -> dict[str, Any]:
        """
        Playbook 작업 완료 후 완료보고서를 생성한다.
        auto=True 이면 evidence/report를 자동 집계하여 생성한다.
        생성 즉시 retrieval index에 등록되어 다음 유사 Playbook 생성 시 RAG 참조된다.
        """
        try:
            if payload.auto:
                report = auto_generate_report(project_id)
            else:
                project = get_project_record(project_id)
                pb_rows = []
                try:
                    from packages.project_service import get_project_playbooks
                    pb_rows = get_project_playbooks(project_id)
                except Exception:
                    pass
                pb = pb_rows[0].get("playbook") if pb_rows else {}
                report = create_completion_report(
                    project_id=project_id,
                    summary=payload.summary,
                    outcome=payload.outcome,
                    playbook_id=(pb or {}).get("id"),
                    playbook_name=(pb or {}).get("name"),
                    request_text=project.get("request_text"),
                    work_details=payload.work_details,
                    issues=payload.issues,
                    next_steps=payload.next_steps,
                    reviewer_id=payload.reviewer_id,
                )
            return {"status": "ok", "report": report}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/completion-reports")
    def list_project_completion_reports(project_id: str) -> dict[str, Any]:
        return {"status": "ok", "reports": list_completion_reports(project_id=project_id)}

    @router.get("/{project_id}/pow")
    def project_pow_blocks(project_id: str) -> dict[str, Any]:
        """프로젝트의 모든 PoW 블록 (M18)."""
        blocks = get_project_pow(project_id)
        return {"status": "ok", "total": len(blocks), "blocks": blocks}

    @router.get("/{project_id}/replay")
    def project_replay(project_id: str) -> dict[str, Any]:
        """프로젝트 작업 타임라인 Replay (M18)."""
        return {"status": "ok", **get_project_replay(project_id)}

    @router.post("/{project_id}/memory/build")
    def build_project_memory(project_id: str, promote: bool = False) -> dict[str, Any]:
        """
        프로젝트 실행 결과를 Task Memory로 집약한다.
        promote=true 이면 pi LLM으로 Experience 승격까지 수행한다.
        """
        from packages.experience_service import build_task_memory, auto_promote_experience
        try:
            tm = build_task_memory(project_id)
            result: dict[str, Any] = {"status": "ok", "task_memory": tm}
            if promote:
                exp = auto_promote_experience(project_id)
                result["experience"] = exp
            return result
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/validate/check")
    def validate_check(project_id: str, payload: dict) -> dict[str, Any]:
        try:
            result = run_validation_check(
                project_id=project_id,
                validator_name=payload.get("validator_name", "manual"),
                command=payload["command"],
                expected_contains=payload.get("expected_contains"),
                expected_exit_code=int(payload.get("expected_exit_code", 0)),
                subagent_url=payload.get("subagent_url"),
                asset_id=payload.get("asset_id"),
            )
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/validations")
    def list_validations(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        runs = get_validation_runs(project_id)
        val_status = get_validation_status(project_id)
        return {"status": "ok", "project_id": project_id, "validation_status": val_status, "items": runs}

    @router.get("/{project_id}/evidence/summary")
    def evidence_summary(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        summary = get_evidence_summary(project_id)
        return {"status": "ok", **summary}

    @router.post("/{project_id}/replan")
    def replan_project_endpoint(project_id: str, payload: dict) -> dict[str, Any]:
        try:
            project = replan_project(project_id, reason=payload.get("reason", "manager replan"))
            return {"status": "ok", "project": project}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except (ProjectStageError, ProjectServiceError) as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/select_assets")
    def select_assets_endpoint(project_id: str) -> dict[str, Any]:
        try:
            result = select_assets_for_project(project_id)
            return {"status": "ok", **result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except (ProjectStageError, ProjectServiceError) as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/resolve_targets")
    def resolve_targets_endpoint(project_id: str) -> dict[str, Any]:
        try:
            result = resolve_targets_for_project(project_id)
            return {"status": "ok", **result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except (ProjectStageError, ProjectServiceError) as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/approval")
    def get_project_approval(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        try:
            return {"status": "ok", **get_approval_status(project_id)}
        except ApprovalError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/run")
    def run_project_endpoint(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        state = run_project_graph(project_id)
        return {
            "status": "ok",
            "final_stage": state["current_stage"],
            "stop_reason": state.get("stop_reason"),
            "approval_required": state.get("approval_required"),
            "approval_cleared": state.get("approval_cleared"),
            "error": state.get("error"),
        }

    return router


def create_asset_router() -> APIRouter:
    router = APIRouter(prefix="/assets", tags=["assets"])

    @router.get("")
    def list_assets_endpoint(env: str | None = None, type: str | None = None) -> dict[str, Any]:
        return {"items": list_assets(env=env, type=type)}

    @router.post("")
    def create_asset_endpoint(payload: dict) -> dict[str, Any]:
        try:
            asset = create_asset(
                name=payload["name"],
                type=payload["type"],
                platform=payload["platform"],
                env=payload["env"],
                mgmt_ip=payload["mgmt_ip"],
                roles=payload.get("roles"),
                expected_subagent_port=int(payload.get("expected_subagent_port", 8002)),
                auth_ref=payload.get("auth_ref"),
                metadata=payload.get("metadata"),
            )
            return {"status": "ok", "asset": asset}
        except AssetConflictError as exc:
            raise HTTPException(status_code=409, detail={"message": str(exc)}) from exc
        except (KeyError, TypeError) as exc:
            raise HTTPException(status_code=400, detail={"message": f"Missing required field: {exc}"}) from exc

    @router.post("/onboard")
    def onboard_asset_endpoint(payload: dict) -> dict[str, Any]:
        try:
            result = onboard_asset(
                name=payload["name"],
                type=payload["type"],
                platform=payload["platform"],
                env=payload["env"],
                mgmt_ip=payload["mgmt_ip"],
                roles=payload.get("roles"),
                expected_subagent_port=int(payload.get("expected_subagent_port", 8002)),
                auth_ref=payload.get("auth_ref"),
                metadata=payload.get("metadata"),
                bootstrap=bool(payload.get("bootstrap", False)),
                ssh_user=payload.get("ssh_user", "root"),
                ssh_port=int(payload.get("ssh_port", 22)),
                ssh_key_path=payload.get("ssh_key_path"),
            )
            return {"status": "ok", **result}
        except AssetConflictError as exc:
            raise HTTPException(status_code=409, detail={"message": str(exc)}) from exc
        except (KeyError, TypeError) as exc:
            raise HTTPException(status_code=400, detail={"message": f"Missing required field: {exc}"}) from exc

    @router.get("/{asset_id}")
    def get_asset_endpoint(asset_id: str) -> dict[str, Any]:
        try:
            return {"status": "ok", "asset": get_asset(asset_id)}
        except AssetNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.put("/{asset_id}")
    def update_asset_endpoint(asset_id: str, payload: dict) -> dict[str, Any]:
        try:
            asset = update_asset(asset_id, payload)
            return {"status": "ok", "asset": asset}
        except AssetNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.delete("/{asset_id}")
    def delete_asset_endpoint(asset_id: str) -> dict[str, Any]:
        try:
            delete_asset(asset_id)
            return {"status": "ok", "deleted": asset_id}
        except AssetNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{asset_id}/resolve")
    def resolve_target_endpoint(asset_id: str) -> dict[str, Any]:
        try:
            result = resolve_target_from_asset(asset_id)
            return {"status": "ok", **result}
        except AssetNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/{asset_id}/health")
    def health_check_endpoint(asset_id: str) -> dict[str, Any]:
        try:
            result = check_asset_health(asset_id)
            return {"status": "ok", **result}
        except AssetNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/{asset_id}/bootstrap")
    def bootstrap_asset_endpoint(asset_id: str, payload: dict) -> dict[str, Any]:
        from packages.bootstrap_service import BootstrapConfig, BootstrapError, bootstrap_asset as do_bootstrap
        try:
            asset = get_asset(asset_id)
        except AssetNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

        cfg = BootstrapConfig(
            ssh_user=payload.get("ssh_user", "root"),
            ssh_pass=payload.get("ssh_pass"),
            ssh_port=int(payload.get("ssh_port", 22)),
            ssh_key_path=payload.get("ssh_key_path"),
            subagent_port=int(payload.get("subagent_port", asset.get("expected_subagent_port") or 8002)),
        )
        mgmt_ip = str(asset.get("mgmt_ip", ""))
        if not mgmt_ip:
            raise HTTPException(status_code=400, detail={"message": "Asset has no mgmt_ip"})

        try:
            from packages.bootstrap_service import BootstrapError
            result = do_bootstrap(mgmt_ip=mgmt_ip, config=cfg)
            new_status = "healthy" if result["exit_code"] == 0 else "unhealthy"
            update_asset(asset_id, {"subagent_status": new_status})
            return {"status": "ok", "bootstrap": result, "subagent_status": new_status}
        except BootstrapError as exc:
            update_asset(asset_id, {"subagent_status": "unhealthy"})
            raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc

    return router


def create_target_router() -> APIRouter:
    router = APIRouter(prefix="/targets", tags=["targets"])

    @router.get("")
    def list_targets() -> dict[str, Any]:
        return {"items": get_targets()}

    return router


def create_registry_router() -> APIRouter:
    router = APIRouter(tags=["registry"])

    # ── Tools ────────────────────────────────────────────────────────────────

    @router.get("/tools")
    def list_tools_endpoint(enabled: bool | None = None) -> dict[str, Any]:
        return {"items": list_tools(enabled=enabled)}

    @router.get("/tools/{tool_id}")
    def get_tool_endpoint(tool_id: str) -> dict[str, Any]:
        try:
            return {"status": "ok", "tool": get_tool_by_name(tool_id)}
        except RegistryNotFoundError:
            pass
        try:
            from packages.registry_service import get_tool
            return {"status": "ok", "tool": get_tool(tool_id)}
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    # ── Skills ───────────────────────────────────────────────────────────────

    @router.get("/skills")
    def list_skills_endpoint(category: str | None = None) -> dict[str, Any]:
        return {"items": list_skills(category=category)}

    @router.get("/skills/{skill_id}")
    def get_skill_endpoint(skill_id: str) -> dict[str, Any]:
        try:
            return {"status": "ok", "skill": get_skill_by_name(skill_id)}
        except RegistryNotFoundError:
            pass
        try:
            from packages.registry_service import get_skill
            return {"status": "ok", "skill": get_skill(skill_id)}
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    # ── Playbooks ────────────────────────────────────────────────────────────

    @router.get("/playbooks")
    def list_playbooks_endpoint(category: str | None = None, enabled: bool | None = None) -> dict[str, Any]:
        items = list_playbooks(category=category, enabled=enabled)
        return {"playbooks": items, "items": items}

    @router.post("/playbooks")
    def create_playbook_endpoint(payload: dict) -> dict[str, Any]:
        try:
            pb = upsert_playbook(
                name=payload["name"],
                version=payload.get("version", "1.0"),
                category=payload.get("category"),
                description=payload.get("description"),
                execution_mode=payload.get("execution_mode", "one_shot"),
                default_risk_level=payload.get("default_risk_level", "medium"),
                dry_run_supported=bool(payload.get("dry_run_supported", False)),
                explain_supported=bool(payload.get("explain_supported", True)),
                required_asset_roles=payload.get("required_asset_roles"),
                failure_policy=payload.get("failure_policy"),
                enabled=bool(payload.get("enabled", True)),
                metadata=payload.get("metadata"),
            )
            if payload.get("steps"):
                upsert_playbook_steps(pb["id"], payload["steps"])
            return {"status": "ok", "playbook": pb}
        except KeyError as exc:
            raise HTTPException(status_code=422, detail={"message": f"Missing field: {exc}"}) from exc

    @router.put("/playbooks/{playbook_id}")
    def update_playbook_endpoint(playbook_id: str, payload: dict) -> dict[str, Any]:
        try:
            existing = get_playbook(playbook_id)
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        pb = upsert_playbook(
            name=payload.get("name", existing["name"]),
            version=payload.get("version", existing["version"]),
            category=payload.get("category", existing.get("category")),
            description=payload.get("description", existing.get("description")),
            execution_mode=payload.get("execution_mode", existing.get("execution_mode", "one_shot")),
            default_risk_level=payload.get("default_risk_level", existing.get("default_risk_level", "medium")),
            dry_run_supported=bool(payload.get("dry_run_supported", existing.get("dry_run_supported", False))),
            explain_supported=bool(payload.get("explain_supported", existing.get("explain_supported", True))),
            required_asset_roles=payload.get("required_asset_roles", existing.get("required_asset_roles")),
            failure_policy=payload.get("failure_policy", existing.get("failure_policy")),
            enabled=bool(payload.get("enabled", existing.get("enabled", True))),
            metadata=payload.get("metadata", existing.get("metadata")),
        )
        if payload.get("steps") is not None:
            upsert_playbook_steps(pb["id"], payload["steps"])
        return {"status": "ok", "playbook": pb}

    @router.delete("/playbooks/{playbook_id}")
    def delete_playbook_endpoint(playbook_id: str) -> dict[str, Any]:
        try:
            from packages.registry_service import delete_playbook
            delete_playbook(playbook_id)
            return {"status": "ok", "deleted": playbook_id}
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.post("/playbooks/{playbook_id}/steps")
    def add_playbook_step_endpoint(playbook_id: str, payload: dict) -> dict[str, Any]:
        try:
            get_playbook(playbook_id)
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        try:
            from packages.registry_service import add_playbook_step
            step = add_playbook_step(
                playbook_id=playbook_id,
                step_order=int(payload["step_order"]),
                step_type=payload["step_type"],
                name=payload.get("name"),
                ref_id=payload.get("ref_id"),
                params=payload.get("params"),
                on_failure=payload.get("on_failure", "stop"),
            )
            return {"status": "ok", "step": step}
        except KeyError as exc:
            raise HTTPException(status_code=422, detail={"message": f"Missing field: {exc}"}) from exc

    @router.get("/playbooks/{playbook_id}")
    def get_playbook_endpoint(playbook_id: str) -> dict[str, Any]:
        try:
            return {"status": "ok", "playbook": get_playbook_by_name(playbook_id)}
        except RegistryNotFoundError:
            pass
        try:
            from packages.registry_service import get_playbook
            return {"status": "ok", "playbook": get_playbook(playbook_id)}
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/playbooks/{playbook_id}/steps")
    def get_playbook_steps_endpoint(playbook_id: str) -> dict[str, Any]:
        try:
            steps = get_playbook_steps(playbook_id)
            return {"status": "ok", "playbook_id": playbook_id, "steps": steps}
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/playbooks/{playbook_id}/resolve")
    def resolve_playbook_endpoint(playbook_id: str) -> dict[str, Any]:
        try:
            tree = resolve_playbook(playbook_id)
            return {"status": "ok", "resolved": tree}
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/playbooks/{playbook_id}/explain")
    def explain_playbook_endpoint(playbook_id: str) -> dict[str, Any]:
        try:
            md = explain_playbook(playbook_id)
            return {"status": "ok", "playbook_id": playbook_id, "explanation": md}
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    # ── Playbook 버전 관리 (M22) ──────────────────────────────────────────────

    @router.post("/playbooks/{playbook_id}/snapshot")
    def snapshot_playbook_endpoint(playbook_id: str, payload: dict = {}) -> dict[str, Any]:
        """현재 Playbook + Steps 상태를 버전 스냅샷으로 저장한다."""
        try:
            result = snapshot_playbook(playbook_id, note=payload.get("note"))
            return {"status": "ok", **result}
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc

    @router.get("/playbooks/{playbook_id}/versions")
    def list_playbook_versions_endpoint(playbook_id: str) -> dict[str, Any]:
        """Playbook 버전 목록 조회 (최신순)."""
        try:
            versions = list_playbook_versions(playbook_id)
            return {"status": "ok", "playbook_id": playbook_id, "versions": versions}
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc

    @router.post("/playbooks/{playbook_id}/rollback")
    def rollback_playbook_endpoint(playbook_id: str, payload: dict) -> dict[str, Any]:
        """지정 버전으로 Playbook + Steps 복원."""
        version_number = payload.get("version_number")
        if version_number is None:
            raise HTTPException(status_code=422, detail={"message": "version_number required"})
        try:
            result = rollback_playbook(playbook_id, int(version_number))
            return {"status": "ok", **result}
        except RegistryNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc

    @router.post("/playbook/run")
    def run_playbook_global(payload: dict) -> dict[str, Any]:
        """
        Global convenience endpoint for running a playbook on a project.
        Body: {playbook_id, project_id, subagent_url?, dry_run?, params?}
        """
        from packages.playbook_engine import run_playbook_steps
        project_id = payload.get("project_id")
        if not project_id:
            raise HTTPException(status_code=422, detail={"message": "project_id required"})
        try:
            result = run_playbook_steps(
                project_id=project_id,
                subagent_url=payload.get("subagent_url"),
                dry_run=payload.get("dry_run", False),
                params=payload.get("params"),
            )
            return {"status": "ok", "overall": result.get("status", "ok"), "result": result}
        except Exception as exc:
            raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc

    return router


def create_history_router() -> APIRouter:
    router = APIRouter(tags=["history"])

    @router.post("/projects/{project_id}/history/ingest")
    def ingest_history(project_id: str, payload: HistoryIngestRequest) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        event = ingest_event(
            project_id=project_id,
            event=payload.event,
            context=payload.context,
            job_run_id=payload.job_run_id,
        )
        return {"status": "ok", "event": event}

    @router.get("/projects/{project_id}/history")
    def project_history(project_id: str, limit: int = 50) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        return {"items": get_project_history(project_id, limit=limit)}

    @router.get("/assets/{asset_id}/history")
    def asset_history(asset_id: str, limit: int = 50) -> dict[str, Any]:
        return {"items": get_asset_history(asset_id, limit=limit)}

    @router.post("/projects/{project_id}/task-memory/build")
    def build_task_memory_endpoint(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        try:
            tm = build_task_memory(project_id)
            return {"status": "ok", "task_memory": tm}
        except Exception as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/projects/{project_id}/task-memory")
    def get_task_memory_endpoint(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        tm = get_task_memory(project_id)
        if tm is None:
            raise HTTPException(status_code=404, detail={"message": f"No task_memory for project: {project_id}"})
        return {"task_memory": tm}

    @router.post("/projects/{project_id}/reindex")
    def reindex_project_endpoint(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        result = reindex_project(project_id)
        return {"status": "ok", **result}

    @router.get("/projects/{project_id}/context")
    def project_context_endpoint(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        ctx = get_context_for_project(project_id)
        return {"status": "ok", **ctx}

    return router


def create_experience_router() -> APIRouter:
    router = APIRouter(prefix="/experience", tags=["experience"])

    @router.get("")
    def list_experience_endpoint(category: str | None = None, limit: int = 20) -> dict[str, Any]:
        return {"items": list_experiences(category=category, limit=limit)}

    @router.get("/search")
    def search_experience_endpoint(q: str, limit: int = 10) -> dict[str, Any]:
        docs = search_documents(q, document_type=None, limit=limit)
        # Also search experiences by category/title/summary match
        exps = list_experiences(limit=50)
        q_lower = q.lower()
        matched_exps = [
            e for e in exps
            if q_lower in (e.get("title") or "").lower()
            or q_lower in (e.get("summary") or "").lower()
            or q_lower in (e.get("category") or "").lower()
        ][:limit]
        return {"items": matched_exps, "documents": docs}

    @router.post("")
    def create_experience_endpoint(payload: ExperienceCreateRequest) -> dict[str, Any]:
        exp = create_experience(
            category=payload.category,
            title=payload.title,
            summary=payload.summary,
            outcome=payload.outcome,
            asset_id=payload.asset_id,
            metadata=payload.metadata,
        )
        return {"status": "ok", "experience": exp}

    @router.get("/{experience_id}")
    def get_experience_endpoint(experience_id: str) -> dict[str, Any]:
        exp = get_experience(experience_id)
        if exp is None:
            raise HTTPException(status_code=404, detail={"message": f"Experience not found: {experience_id}"})
        return {"experience": exp}

    @router.post("/task-memories/{task_memory_id}/promote")
    def promote_experience_endpoint(task_memory_id: str, payload: ExperiencePromoteRequest) -> dict[str, Any]:
        try:
            exp = promote_to_experience(
                task_memory_id=task_memory_id,
                category=payload.category,
                title=payload.title,
                outcome=payload.outcome,
                asset_id=payload.asset_id,
            )
            return {"status": "ok", "experience": exp}
        except ValueError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    return router


def create_schedule_router() -> APIRouter:
    router = APIRouter(prefix="/schedules", tags=["schedules"])

    @router.post("")
    def create_schedule_endpoint(payload: ScheduleCreateRequest) -> dict[str, Any]:
        project = create_project_record(
            name=payload.project_name,
            request_text=f"Batch schedule: {payload.project_name}",
            mode="batch",
        )
        schedule = create_schedule(
            project_id=project["id"],
            schedule_type=payload.schedule_type,
            cron_expr=payload.cron_expr,
            metadata=payload.metadata,
        )
        return {"schedule": schedule, "project": project}

    @router.get("")
    def list_schedules_endpoint() -> dict[str, Any]:
        return {"items": list_schedules(enabled_only=False)}

    @router.get("/{schedule_id}")
    def get_schedule_endpoint(schedule_id: str) -> dict[str, Any]:
        row = get_schedule(schedule_id)
        if row is None:
            raise HTTPException(status_code=404, detail={"message": f"Schedule not found: {schedule_id}"})
        return {"schedule": row}

    @router.patch("/{schedule_id}")
    def patch_schedule_endpoint(schedule_id: str, payload: SchedulePatchRequest) -> dict[str, Any]:
        row = update_schedule(schedule_id, enabled=payload.enabled, cron_expr=payload.cron_expr)
        return {"schedule": row}

    @router.delete("/{schedule_id}")
    def delete_schedule_endpoint(schedule_id: str) -> dict[str, Any]:
        delete_schedule(schedule_id)
        return {"ok": True}

    @router.post("/{schedule_id}/run")
    def run_schedule_now(schedule_id: str) -> dict[str, Any]:
        row = get_schedule(schedule_id)
        if row is None:
            raise HTTPException(status_code=404, detail={"message": f"Schedule not found: {schedule_id}"})
        result = execute_due_schedule(row)
        return {"result": result}

    return router


def create_watcher_router() -> APIRouter:
    router = APIRouter(prefix="/watchers", tags=["watchers"])

    @router.post("")
    def create_watcher_endpoint(payload: WatcherCreateRequest) -> dict[str, Any]:
        project = create_project_record(
            name=payload.project_name,
            request_text=f"Continuous watch: {payload.project_name}",
            mode="continuous",
        )
        watch_job = create_watch_job(
            project_id=project["id"],
            watch_type=payload.watch_type,
            metadata=payload.metadata,
        )
        return {"watch_job": watch_job, "project": project}

    @router.get("")
    def list_watchers_endpoint() -> dict[str, Any]:
        return {"items": list_watch_jobs()}

    @router.get("/{watch_job_id}")
    def get_watcher_endpoint(watch_job_id: str) -> dict[str, Any]:
        row = get_watch_job(watch_job_id)
        if row is None:
            raise HTTPException(status_code=404, detail={"message": f"Watch job not found: {watch_job_id}"})
        return {"watch_job": row}

    @router.patch("/{watch_job_id}/status")
    def patch_watcher_status(watch_job_id: str, payload: WatcherStatusRequest) -> dict[str, Any]:
        row = update_watch_job_status(watch_job_id, payload.status)
        return {"watch_job": row}

    @router.delete("/{watch_job_id}")
    def delete_watcher_endpoint(watch_job_id: str) -> dict[str, Any]:
        delete_watch_job(watch_job_id)
        return {"ok": True}

    @router.get("/{watch_job_id}/events")
    def list_watcher_events(watch_job_id: str) -> dict[str, Any]:
        return {"items": list_watch_events(watch_job_id)}

    @router.post("/{watch_job_id}/check")
    def check_watcher_now(watch_job_id: str) -> dict[str, Any]:
        row = get_watch_job(watch_job_id)
        if row is None:
            raise HTTPException(status_code=404, detail={"message": f"Watch job not found: {watch_job_id}"})
        result = run_watch_check(row)
        return {"result": result}

    return router


def create_incident_router() -> APIRouter:
    router = APIRouter(prefix="/incidents", tags=["incidents"])

    @router.get("")
    def list_incidents_endpoint(status: str | None = "open") -> dict[str, Any]:
        return {"items": list_incidents(status=status)}

    @router.post("/{incident_id}/resolve")
    def resolve_incident_endpoint(incident_id: str) -> dict[str, Any]:
        incident = resolve_incident(incident_id)
        return {"incident": incident}

    return router


def create_admin_router() -> APIRouter:
    router = APIRouter(prefix="/admin", tags=["admin"])

    @router.get("/health")
    def admin_health() -> dict[str, Any]:
        return get_system_health()

    @router.get("/metrics")
    def admin_metrics() -> dict[str, Any]:
        return get_operational_metrics()

    # ── Audit ────────────────────────────────────────────────────────────────

    @router.get("/audit")
    def admin_audit(
        event_type: str | None = None,
        actor_id: str | None = None,
        project_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        items = query_audit_logs(
            event_type=event_type,
            actor_id=actor_id,
            project_id=project_id,
            limit=limit,
        )
        return {"items": items, "count": len(items)}

    @router.post("/audit/export")
    def admin_audit_export(payload: AuditExportRequest) -> dict[str, Any]:
        fmt = payload.format.lower()
        if fmt == "csv":
            content = export_audit_csv(
                event_type=payload.event_type,
                project_id=payload.project_id,
                limit=payload.limit,
            )
            return {"format": "csv", "content": content, "rows": len(content.splitlines()) - 1}
        content = export_audit_json(
            event_type=payload.event_type,
            project_id=payload.project_id,
            limit=payload.limit,
        )
        return {"format": "json", "content": content}

    # ── RBAC ─────────────────────────────────────────────────────────────────

    @router.get("/roles")
    def admin_list_roles() -> dict[str, Any]:
        return {"items": list_roles()}

    @router.post("/roles")
    def admin_create_role(payload: RoleCreateRequest) -> dict[str, Any]:
        role = create_role(
            name=payload.name,
            permissions=payload.permissions,
            description=payload.description,
        )
        return {"status": "ok", "role": role}

    @router.get("/roles/{role_id}")
    def admin_get_role(role_id: str) -> dict[str, Any]:
        role = get_role(role_id)
        if role is None:
            raise HTTPException(status_code=404, detail={"message": f"Role not found: {role_id}"})
        return {"role": role}

    @router.post("/roles/assign")
    def admin_assign_role(payload: RoleAssignRequest) -> dict[str, Any]:
        ar = assign_role(
            actor_id=payload.actor_id,
            role_id=payload.role_id,
            actor_type=payload.actor_type,
        )
        return {"status": "ok", "assignment": ar}

    @router.get("/roles/actor/{actor_id}/permissions")
    def admin_actor_permissions(actor_id: str) -> dict[str, Any]:
        perms = get_actor_permissions(actor_id)
        return {"actor_id": actor_id, "permissions": perms}

    @router.get("/roles/actor/{actor_id}/check")
    def admin_check_permission(actor_id: str, permission: str) -> dict[str, Any]:
        ok = check_permission(actor_id, permission)
        return {"actor_id": actor_id, "permission": permission, "allowed": ok}

    # ── Backup ────────────────────────────────────────────────────────────────

    @router.post("/backup")
    def admin_create_backup() -> dict[str, Any]:
        result = create_backup()
        return {"status": "ok" if result["ok"] else "error", **result}

    @router.get("/backups")
    def admin_list_backups() -> dict[str, Any]:
        return {"items": list_backups()}

    return router


def create_reports_router() -> APIRouter:
    router = APIRouter(prefix="/reports", tags=["reports"])

    @router.get("/project/{project_id}")
    def get_full_report(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        try:
            report = generate_project_report(project_id)
            return {"status": "ok", "report": report}
        except Exception as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/project/{project_id}/evidence-pack")
    def get_evidence_pack(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        try:
            pack = export_evidence_pack(project_id)
            return {"status": "ok", "pack": pack}
        except Exception as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.get("/project/{project_id}/evidence-pack/json")
    def export_evidence_pack_endpoint(project_id: str) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        try:
            json_str = export_evidence_pack_json(project_id)
            return {"status": "ok", "project_id": project_id, "json": json_str}
        except Exception as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    return router


def create_notification_router() -> APIRouter:
    router = APIRouter(prefix="/notifications", tags=["notifications"])

    # ── Channels ─────────────────────────────────────────────────────────────

    @router.post("/channels")
    def create_channel_endpoint(payload: ChannelCreateRequest) -> dict[str, Any]:
        ch = create_channel(
            name=payload.name,
            channel_type=payload.channel_type,
            config=payload.config,
            enabled=payload.enabled,
        )
        return {"channel": ch}

    @router.get("/channels")
    def list_channels_endpoint(enabled_only: bool = False) -> dict[str, Any]:
        items = list_channels(enabled_only=enabled_only)
        return {"channels": items, "items": items}

    @router.get("/channels/{channel_id}")
    def get_channel_endpoint(channel_id: str) -> dict[str, Any]:
        ch = get_channel(channel_id)
        if ch is None:
            raise HTTPException(status_code=404, detail={"message": f"Channel not found: {channel_id}"})
        return {"channel": ch}

    @router.patch("/channels/{channel_id}")
    def patch_channel_endpoint(channel_id: str, payload: ChannelPatchRequest) -> dict[str, Any]:
        ch = update_channel(channel_id, enabled=payload.enabled, config=payload.config)
        return {"channel": ch}

    @router.delete("/channels/{channel_id}")
    def delete_channel_endpoint(channel_id: str) -> dict[str, Any]:
        delete_channel(channel_id)
        return {"ok": True}

    # ── Rules ─────────────────────────────────────────────────────────────────

    @router.post("/rules")
    def create_rule_endpoint(payload: RuleCreateRequest) -> dict[str, Any]:
        rule = create_rule(
            name=payload.name,
            event_type=payload.event_type,
            channel_id=payload.channel_id,
            filter_conditions=payload.filter_conditions,
            enabled=payload.enabled,
        )
        return {"rule": rule}

    @router.get("/rules")
    def list_rules_endpoint(event_type: str | None = None, enabled_only: bool = True) -> dict[str, Any]:
        items = list_rules(event_type=event_type, enabled_only=enabled_only)
        return {"rules": items, "items": items}

    @router.get("/rules/{rule_id}")
    def get_rule_endpoint(rule_id: str) -> dict[str, Any]:
        rule = get_rule(rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail={"message": f"Rule not found: {rule_id}"})
        return {"rule": rule}

    @router.patch("/rules/{rule_id}")
    def patch_rule_endpoint(rule_id: str, payload: RulePatchRequest) -> dict[str, Any]:
        rule = update_rule(rule_id, enabled=payload.enabled)
        return {"rule": rule}

    @router.delete("/rules/{rule_id}")
    def delete_rule_endpoint(rule_id: str) -> dict[str, Any]:
        delete_rule(rule_id)
        return {"ok": True}

    # ── Test & Logs ───────────────────────────────────────────────────────────

    @router.post("/test")
    def test_notification(payload: NotificationTestRequest) -> dict[str, Any]:
        logs = fire_event(payload.event_type, payload.payload)
        return {"logs": logs}

    @router.get("/logs")
    def list_logs_endpoint(
        event_type: str | None = None,
        channel_id: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        items = list_notification_logs(
            channel_id=channel_id,
            event_type=event_type,
            limit=limit,
        )
        return {"items": items}

    return router


def create_completion_report_router() -> APIRouter:
    """전역 완료보고서 조회 및 유사 보고서 검색 (RAG 참조용)."""
    router = APIRouter(prefix="/completion-reports", tags=["completion-reports"])

    @router.get("")
    def list_reports(
        playbook_name: str | None = None,
        outcome: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        return {
            "status": "ok",
            "reports": list_completion_reports(
                playbook_name=playbook_name, outcome=outcome, limit=limit
            ),
        }

    @router.get("/search")
    def search_reports(q: str, limit: int = 10) -> dict[str, Any]:
        """완료보고서 FTS 검색 — master-plan RAG 참조에 활용."""
        from packages.retrieval_service import search_documents
        docs = search_documents(q, document_type="completion_report", limit=limit)
        return {"status": "ok", "documents": docs}

    @router.get("/{report_id}")
    def get_report(report_id: str) -> dict[str, Any]:
        report = get_completion_report(report_id)
        if report is None:
            raise HTTPException(status_code=404, detail={"message": f"Report not found: {report_id}"})
        return {"status": "ok", "report": report}

    return router


def create_pow_router() -> APIRouter:
    """M18 Proof of Work & Blockchain Reward 라우터."""
    router = APIRouter(prefix="/pow", tags=["pow"])

    @router.get("/blocks")
    def list_pow_blocks(agent_id: str | None = None, limit: int = 50) -> dict[str, Any]:
        """PoW 블록 목록. agent_id 필터 가능."""
        from packages.project_service import get_connection
        from psycopg2.extras import RealDictCursor
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if agent_id:
                    cur.execute(
                        "SELECT * FROM proof_of_work WHERE agent_id=%s ORDER BY ts DESC LIMIT %s",
                        (agent_id, limit),
                    )
                else:
                    cur.execute(
                        "SELECT * FROM proof_of_work ORDER BY ts DESC LIMIT %s",
                        (limit,),
                    )
                blocks = [dict(r) for r in cur.fetchall()]
        return {"status": "ok", "total": len(blocks), "blocks": blocks}

    @router.get("/blocks/{pow_id}")
    def get_pow_block(pow_id: str) -> dict[str, Any]:
        from packages.project_service import get_connection
        from psycopg2.extras import RealDictCursor
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM proof_of_work WHERE id=%s", (pow_id,))
                row = cur.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail={"message": f"PoW block not found: {pow_id}"})
        return {"status": "ok", "block": dict(row)}

    @router.get("/verify")
    def verify_agent_chain(agent_id: str) -> dict[str, Any]:
        """에이전트의 블록 체인 무결성 검증. ?agent_id=<url>"""
        result = verify_chain(agent_id)
        return {"status": "ok", "result": result}

    @router.get("/leaderboard")
    def pow_leaderboard(limit: int = 10) -> dict[str, Any]:
        """보상 잔액 상위 에이전트 랭킹."""
        return {"status": "ok", "leaderboard": get_leaderboard(limit)}

    return router


def create_rewards_router() -> APIRouter:
    """M18 보상 조회 라우터."""
    router = APIRouter(prefix="/rewards", tags=["rewards"])

    @router.get("/agents")
    def agent_rewards(agent_id: str) -> dict[str, Any]:
        """에이전트 잔액 + 최근 보상 이력. ?agent_id=<url>"""
        return {"status": "ok", **get_agent_stats(agent_id)}

    return router


def create_rl_router() -> APIRouter:
    """Lightweight RL — Q-learning 정책 학습 & 추천."""
    router = APIRouter(prefix="/rl", tags=["rl"])

    @router.post("/train")
    def rl_train(
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 0.15,
        limit: int = 500,
    ) -> dict[str, Any]:
        from packages.rl_service import train
        result = train(alpha=alpha, gamma=gamma, epsilon=epsilon, limit=limit)
        return {"status": "ok", **result}

    @router.get("/recommend")
    def rl_recommend(
        agent_id: str,
        risk_level: str = "medium",
        task_order: int = 1,
        exploration: str = "greedy",  # M24: "greedy" | "ucb1" | "epsilon"
        ucb_c: float = 1.0,          # M24: UCB1 탐색 계수
    ) -> dict[str, Any]:
        from packages.rl_service import recommend
        result = recommend(
            agent_id=agent_id, risk_level=risk_level, task_order=task_order,
            exploration=exploration, ucb_c=ucb_c,
        )
        return {"status": "ok", **result}

    @router.get("/policy")
    def rl_policy() -> dict[str, Any]:
        from packages.rl_service import get_policy_stats
        return {"status": "ok", **get_policy_stats()}

    return router


def create_chat_router() -> APIRouter:
    """RAG 기반 컨텍스트 대화 라우터 — 프로젝트/에이전트/Playbook."""
    router = APIRouter(prefix="/chat", tags=["chat"])

    @router.post("")
    def chat(payload: dict) -> dict[str, Any]:
        """
        RAG + LLM 컨텍스트 기반 대화.
        Body: {message, context_type, context_id, history?}
        context_type: "project" | "agent" | "playbook"

        1) DB에서 직접 컨텍스트 수집 (evidence, report, reward 등)
        2) RAG: retrieval_documents FTS 검색으로 관련 경험/지식 보강
        3) LLM에 컨텍스트 + RAG 결과 + 대화이력 + 질문 전달
        """
        message = payload.get("message", "")
        ctx_type = payload.get("context_type", "")
        ctx_id = payload.get("context_id", "")
        history = payload.get("history", [])

        if not message:
            raise HTTPException(status_code=422, detail={"message": "message required"})

        # ── 1) 직접 컨텍스트 수집 ────────────────────────────────────────
        context_parts: list[str] = []
        rag_query_hints: list[str] = [message]  # RAG 검색 키워드

        try:
            if ctx_type == "project" and ctx_id:
                prj = get_project_record(ctx_id)
                context_parts.append(
                    f"[프로젝트] {prj['name']}\n"
                    f"요청: {prj['request_text']}\n"
                    f"단계: {prj['current_stage']} ({prj['status']})"
                )
                rag_query_hints.append(prj["name"])
                ev_list = get_evidence_for_project(ctx_id)
                if ev_list:
                    ev_summary = "\n".join(
                        f"  [{e.get('exit_code','')}] {(e.get('body_ref') or e.get('command_text') or '')[:100]}"
                        for e in ev_list[:15]
                    )
                    context_parts.append(f"[Evidence {len(ev_list)}건]\n{ev_summary}")
                try:
                    rpt = get_project_report(ctx_id)
                    if rpt:
                        context_parts.append(f"[보고서] {rpt.get('summary','')[:300]}")
                except Exception:
                    pass
                # completion reports
                try:
                    cr_list = list_completion_reports(ctx_id)
                    if cr_list:
                        for cr in cr_list[:3]:
                            context_parts.append(
                                f"[완료보고서] outcome={cr.get('outcome','')} summary={cr.get('summary','')[:200]}"
                            )
                except Exception:
                    pass

            elif ctx_type == "agent" and ctx_id:
                stats = get_agent_stats(ctx_id)
                ledger = stats.get("ledger", {})
                context_parts.append(
                    f"[에이전트] {ctx_id}\n"
                    f"잔액: {ledger.get('balance',0):.4f} / 총작업: {ledger.get('total_tasks',0)} "
                    f"성공: {ledger.get('success_count',0)} 실패: {ledger.get('fail_count',0)}"
                )
                recent = stats.get("recent_rewards", [])
                if recent:
                    rw_summary = "\n".join(
                        f"  task#{r.get('task_order',0)} {r.get('task_title','')[:50]} "
                        f"reward={r.get('total_reward',0)} exit={r.get('exit_code','')}"
                        for r in recent[:10]
                    )
                    context_parts.append(f"[최근 보상 이력]\n{rw_summary}")
                    rag_query_hints.extend(r.get("task_title", "") for r in recent[:3])
                # 체인 무결성
                try:
                    chain = verify_chain(ctx_id)
                    context_parts.append(
                        f"[블록체인] 블록={chain.get('blocks',0)} 무결성={'정상' if chain.get('valid') else '변조감지'}"
                    )
                except Exception:
                    pass

            elif ctx_type == "playbook" and ctx_id:
                try:
                    pb = get_playbook(ctx_id)
                    context_parts.append(
                        f"[Playbook] {pb.get('name','')} v{pb.get('version','')}\n"
                        f"설명: {pb.get('description','')}"
                    )
                    rag_query_hints.append(pb.get("name", ""))
                    steps = get_playbook_steps(ctx_id)
                    if steps:
                        step_summary = "\n".join(
                            f"  {s.get('step_order',0)}. [{s.get('step_type','')}] {s.get('name','')} "
                            f"(ref={s.get('ref_id','')}, on_fail={s.get('on_failure_action','abort')})"
                            for s in steps
                        )
                        context_parts.append(f"[Steps {len(steps)}개]\n{step_summary}")
                except Exception:
                    pass

        except Exception as exc:
            context_parts.append(f"(컨텍스트 로드 실패: {exc})")

        # ── 2) RAG: retrieval_documents FTS 검색 ─────────────────────────
        rag_parts: list[str] = []
        try:
            rag_query = " ".join(rag_query_hints)[:200]
            rag_results = search_documents(rag_query, limit=5)
            for doc in rag_results:
                rag_parts.append(
                    f"[{doc.get('document_type','')}] {doc.get('title','')}: "
                    f"{(doc.get('body','') or '')[:200]}"
                )
        except Exception:
            pass  # RAG 실패 시 직접 컨텍스트만으로 진행

        # ── 3) LLM 프롬프트 조립 ─────────────────────────────────────────
        context_block = "\n\n".join(context_parts) if context_parts else "(컨텍스트 없음)"
        rag_block = "\n".join(rag_parts) if rag_parts else ""

        history_block = ""
        if history:
            history_block = "\n".join(
                f"{'사용자' if h.get('role')=='user' else 'AI'}: {h.get('content','')}"
                for h in history[-6:]
            )

        system_prompt = (
            "당신은 OpsClaw IT운영·보안 자동화 플랫폼의 AI 어시스턴트입니다. "
            "아래에 제공된 [직접 컨텍스트]와 [관련 경험/지식(RAG)]를 참고하여 답변하세요. "
            "한국어로 간결하되 기술적으로 정확하게 답변하세요. "
            "컨텍스트에 없는 내용은 추측이라고 명시하세요."
        )
        prompt_text = f"[직접 컨텍스트]\n{context_block}\n\n"
        if rag_block:
            prompt_text += f"[관련 경험/지식 (RAG 검색 결과)]\n{rag_block}\n\n"
        if history_block:
            prompt_text += f"[대화 이력]\n{history_block}\n\n"
        prompt_text += f"[사용자 질문]\n{message}"

        try:
            pi = PiRuntimeClient(PiRuntimeConfig(default_role="manager"))
            result = pi.invoke_model(
                prompt=prompt_text,
                context={"system_prompt": system_prompt, "role": "manager"},
            )
            reply = (result.get("stdout") or result.get("text") or "").strip()
            if not reply:
                reply = "응답을 생성하지 못했습니다. 다시 시도해주세요."
        except Exception as exc:
            reply = f"LLM 호출 실패: {exc}"

        return {
            "status": "ok",
            "reply": reply,
            "context_type": ctx_type,
            "context_id": ctx_id,
            "rag_sources": len(rag_parts),
        }

    return router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpsClaw Manager API",
        version="0.10.0-m10",
        description="OpsClaw Manager API — lifecycle, evidence, assets, registry, validation, batch/watch, history/experience/retrieval, RBAC/audit/monitoring, notifications.",
    )

    @app.middleware("http")
    async def api_key_auth(request: Request, call_next):
        path = request.url.path
        # Whitelist: CORS pre-flight, health, UI, static assets, WebSocket upgrade
        if (
            request.method == "OPTIONS"
            or path in ("/health", "/", "/ui")
            or path.startswith("/app/")
            or path.startswith("/portal/")
            or request.headers.get("upgrade", "").lower() == "websocket"
        ):
            return await call_next(request)
        # No key configured → dev mode, skip auth
        if not _OPSCLAW_API_KEY:
            return await call_next(request)
        # Accept X-API-Key header or Authorization: Bearer <key>
        key = request.headers.get("X-API-Key", "")
        if not key:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                key = auth[7:]
        if not key or not secrets.compare_digest(key.encode(), _OPSCLAW_API_KEY.encode()):
            return JSONResponse(
                {"error": "Unauthorized", "detail": "Valid X-API-Key header required"},
                status_code=401,
            )
        return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:8000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(create_health_router())
    app.include_router(create_runtime_router())
    app.include_router(create_project_router())
    app.include_router(create_asset_router())
    app.include_router(create_target_router())
    app.include_router(create_registry_router())
    app.include_router(create_schedule_router())
    app.include_router(create_watcher_router())
    app.include_router(create_incident_router())
    app.include_router(create_history_router())
    app.include_router(create_experience_router())
    app.include_router(create_admin_router())
    app.include_router(create_reports_router())
    app.include_router(create_notification_router())
    app.include_router(create_completion_report_router())
    app.include_router(create_pow_router())
    app.include_router(create_rewards_router())
    app.include_router(create_rl_router())
    app.include_router(create_chat_router())

    # ── 자율 Purple Team ──────────────────────────────────────────────────────
    from pydantic import BaseModel as _BM

    class _PurpleAutoRequest(_BM):
        red_objective: str
        red_target: str = ""
        red_subagent_url: str = "http://localhost:8002"
        red_model: str = "gemma3:12b"
        blue_objective: str
        blue_subagent_url: str = "http://10.20.30.100:8002"
        blue_model: str = "llama3.1:8b"
        max_steps: int = 10
        timeout_s: int = 180

    @app.post("/projects/{project_id}/purple-auto")
    def purple_auto(project_id: str, payload: _PurpleAutoRequest):
        project = get_project_record(project_id)
        if not project:
            raise HTTPException(404, detail={"message": "Project not found"})

        import uuid as _uuid
        mission_id = _uuid.uuid4().hex[:12]

        # 관련 Playbook/Experience 조회 (지식 전이)
        playbook_ctx: list[dict] = []
        experience_ctx: list[str] = []
        try:
            from packages.retrieval_service import search_documents
            # Red용 경험 검색
            red_docs = search_documents(payload.red_objective, limit=5)
            experience_ctx_red = [d.get("title", "") + ": " + d.get("body", "")[:200]
                                  for d in red_docs]
            # Blue용 경험 검색
            blue_docs = search_documents(payload.blue_objective, limit=5)
            experience_ctx_blue = [d.get("title", "") + ": " + d.get("body", "")[:200]
                                   for d in blue_docs]
        except Exception:
            experience_ctx_red = []
            experience_ctx_blue = []

        # Playbook 검색 (datetime 제거하여 JSON 직렬화 보장)
        try:
            from packages.registry_service import list_playbooks, get_playbook_steps
            pbs = list_playbooks()
            for pb in pbs[:3]:
                steps = get_playbook_steps(pb["id"])
                for s in steps:
                    playbook_ctx.append({
                        "order": s.get("step_order", 0),
                        "name": s.get("name", ""),
                        "instruction_prompt": str(s.get("params", {}).get("command", s.get("name", ""))),
                    })
        except Exception:
            pass

        # Red + Blue 동시 실행
        from packages.a2a_protocol import A2AClient, A2AClientConfig

        def _run_red():
            client = A2AClient(A2AClientConfig(base_url=payload.red_subagent_url))
            return client.mission(
                mission_id=f"red-{mission_id}",
                role="red",
                objective=payload.red_objective,
                target=payload.red_target,
                model=payload.red_model,
                playbook_context=playbook_ctx,
                experience_context=experience_ctx_red,
                max_steps=payload.max_steps,
                timeout_s=payload.timeout_s,
            )

        def _run_blue():
            client = A2AClient(A2AClientConfig(base_url=payload.blue_subagent_url))
            return client.mission(
                mission_id=f"blue-{mission_id}",
                role="blue",
                objective=payload.blue_objective,
                target="siem-local",
                model=payload.blue_model,
                playbook_context=[],
                experience_context=experience_ctx_blue,
                max_steps=payload.max_steps,
                timeout_s=payload.timeout_s,
            )

        red_result = blue_result = None
        with ThreadPoolExecutor(max_workers=2) as executor:
            red_future = executor.submit(_run_red)
            blue_future = executor.submit(_run_blue)
            try:
                red_result = red_future.result(timeout=payload.timeout_s + 60)
            except Exception as exc:
                red_result = {"status": "error", "error": str(exc)}
            try:
                blue_result = blue_future.result(timeout=payload.timeout_s + 60)
            except Exception as exc:
                blue_result = {"status": "error", "error": str(exc)}

        # Evidence + PoW 기록 (각 step을 evidence로)
        from packages.pow_service import generate_proof
        from packages.project_service import create_minimal_evidence_record

        for label, result in [("red", red_result), ("blue", blue_result)]:
            if not isinstance(result, dict) or "results" not in result:
                continue
            for step in result.get("results", []):
                if not step.get("command"):
                    continue
                try:
                    create_minimal_evidence_record(
                        project_id, step["command"],
                        step.get("stdout", ""), step.get("stderr", ""),
                        step.get("exit_code", -1),
                    )
                    generate_proof(
                        project_id=project_id,
                        agent_id=payload.red_subagent_url if label == "red"
                                 else payload.blue_subagent_url,
                        task_order=step["step"],
                        task_title=f"{label}-{step.get('action', 'step')}",
                        stdout=step.get("stdout", ""),
                        stderr=step.get("stderr", ""),
                        exit_code=step.get("exit_code", -1),
                        duration_s=step.get("duration_s", 0),
                        risk_level="medium",
                    )
                except Exception:
                    pass

        return {
            "status": "ok",
            "project_id": project_id,
            "mission_id": mission_id,
            "red": red_result,
            "blue": blue_result,
        }

    # ── 자극 생성기: 보안 이벤트 무작위 발생 ──────────────────────────────────
    import random as _random

    class _StimulateRequest(_BM):
        target_url: str = "http://10.20.30.80:3000"  # 자극 대상
        subagent_url: str = "http://localhost:8002"   # 자극 실행 SubAgent
        count: int = 5                                 # 자극 횟수
        types: list[str] = []                          # 비어있으면 전체 유형

    @app.post("/projects/{project_id}/stimulate")
    def stimulate(project_id: str, payload: _StimulateRequest):
        """대상 서버에 무작위 보안 이벤트를 발생시켜 Daemon 탐지를 검증한다."""
        project = get_project_record(project_id)
        if not project:
            raise HTTPException(404, detail={"message": "Project not found"})

        stimulus_catalog = {
            "sqli": f"curl -s -X POST {payload.target_url}/rest/user/login -H 'Content-Type: application/json' -d '{{\"email\":\"\\' OR 1=1--\",\"password\":\"x\"}}'",
            "xss": f"curl -s '{payload.target_url}/?q=<script>alert(1)</script>'",
            "port_scan": f"for p in 22 80 443 3000 8080 8443; do echo | timeout 2 bash -c \"echo >/dev/tcp/{payload.target_url.split('//')[1].split(':')[0]}/$p\" 2>/dev/null && echo \"$p open\"; done",
            "path_traversal": f"curl -s '{payload.target_url}/../../etc/passwd'",
            "scanner_ua": f"curl -s -H 'User-Agent: sqlmap/1.6' '{payload.target_url}/'",
            "brute_login": f"for i in $(seq 1 5); do curl -s -X POST {payload.target_url}/rest/user/login -H 'Content-Type: application/json' -d '{{\"email\":\"admin@test.com\",\"password\":\"wrong'$i'\"}}'; done",
            "ftp_access": f"curl -s '{payload.target_url}/ftp/'",
            "admin_api": f"curl -s '{payload.target_url}/api/Users'",
        }

        types = payload.types or list(stimulus_catalog.keys())
        selected = _random.sample(types, min(payload.count, len(types)))

        from packages.a2a_protocol import A2AClient, A2AClientConfig, A2ARunRequest
        client = A2AClient(A2AClientConfig(base_url=payload.subagent_url))

        results = []
        for stype in selected:
            cmd = stimulus_catalog.get(stype, "echo unknown")
            try:
                import uuid as _uuid2
                resp = client.run_script(A2ARunRequest(
                    project_id=project_id,
                    job_run_id=f"stim_{_uuid2.uuid4().hex[:8]}",
                    script=cmd,
                    timeout_s=15,
                ))
                results.append({
                    "type": stype,
                    "command": cmd[:120],
                    "exit_code": resp.exit_code,
                    "stdout_preview": resp.stdout[:200],
                })
                # evidence 기록
                from packages.project_service import create_minimal_evidence_record
                create_minimal_evidence_record(project_id, f"[stimulus:{stype}] {cmd[:100]}",
                                              resp.stdout, resp.stderr, resp.exit_code)
            except Exception as exc:
                results.append({"type": stype, "error": str(exc)[:200]})

        return {
            "status": "ok",
            "project_id": project_id,
            "stimuli_sent": len(results),
            "results": results,
        }

    @app.websocket("/ws/projects/{project_id}")
    async def ws_project_status(websocket: WebSocket, project_id: str):
        await websocket.accept()
        last_stage = None
        try:
            while True:
                try:
                    project = get_project_record(project_id)
                    stage = project.get("current_stage")
                    if stage != last_stage:
                        last_stage = stage
                        await websocket.send_json({"stage": stage})
                except Exception:
                    break
                await asyncio.sleep(2)
        except Exception:
            pass

    _DASHBOARD = Path(__file__).parent.parent / "templates" / "dashboard.html"

    @app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
    def dashboard_ui():
        return HTMLResponse(content=_DASHBOARD.read_text(encoding="utf-8"))

    @app.get("/", include_in_schema=False)
    def root_redirect():
        return RedirectResponse(url="/app/")

    # Portal routes (education, auth, terminal)
    try:
        from .portal_routes import router as portal_router
        app.include_router(portal_router)
    except Exception as e:
        print(f"[WARN] Portal routes not loaded: {e}")

    _WEB_UI_DIST = Path(__file__).parent.parent.parent.parent / "apps" / "web-ui" / "dist"
    if _WEB_UI_DIST.exists():
        # Serve static assets (JS, CSS, images)
        app.mount("/app/assets", StaticFiles(directory=str(_WEB_UI_DIST / "assets")), name="web-assets")

        # SPA catch-all: any /app/* route returns index.html for client-side routing
        _index_html = (_WEB_UI_DIST / "index.html").read_text("utf-8")

        @app.get("/app/{full_path:path}", include_in_schema=False)
        async def spa_catchall(full_path: str):
            # Check if it's a real static file first
            static_file = _WEB_UI_DIST / full_path
            if static_file.is_file() and not full_path.endswith(".html"):
                from starlette.responses import FileResponse
                return FileResponse(str(static_file))
            # Otherwise return index.html for SPA routing
            return HTMLResponse(content=_index_html)

    return app


_OPSCLAW_API_KEY = os.getenv("OPSCLAW_API_KEY", "")

app = create_app()
