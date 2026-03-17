from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status
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
    get_playbook_by_name,
    get_playbook_steps,
    get_skill_by_name,
    get_tool_by_name,
    list_playbooks,
    list_skills,
    list_tools,
    resolve_playbook,
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
    create_minimal_evidence_record,
    create_project_record,
    execute_project_record,
    finalize_report_stage_record,
    get_assets,
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
    plan_project_record,
    replan_project,
    select_assets_for_project,
    resolve_targets_for_project,
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


class ProjectCreateRequest(BaseModel):
    name: str
    request_text: str
    mode: str = "one_shot"


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

    @router.post("")
    def create_project(payload: ProjectCreateRequest) -> dict[str, Any]:
        try:
            project = create_project_record(
                name=payload.name,
                request_text=payload.request_text,
                mode=payload.mode,
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
            items = get_evidence_for_project(project_id)
            return {"status": "ok", "project_id": project_id, "items": items}
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
        try:
            result = dispatch_command_to_subagent(
                project_id=project_id,
                command=payload.command,
                subagent_url=payload.subagent_url,
                timeout_s=payload.timeout_s,
            )
            return {"status": "ok", "result": result}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except (ProjectStageError, ProjectServiceError) as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

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
                expected_subagent_port=int(payload.get("expected_subagent_port", 8001)),
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
                expected_subagent_port=int(payload.get("expected_subagent_port", 8001)),
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
            ssh_port=int(payload.get("ssh_port", 22)),
            ssh_key_path=payload.get("ssh_key_path"),
            subagent_port=int(payload.get("subagent_port", asset.get("expected_subagent_port") or 8001)),
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
        return {"items": list_playbooks(category=category, enabled=enabled)}

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


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpsClaw Manager API",
        version="0.8.0-m8",
        description="OpsClaw Manager API — lifecycle, evidence, assets, registry, validation, batch/watch, history/experience/retrieval.",
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

    return app


app = create_app()
