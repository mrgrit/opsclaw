from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel

from packages.master_review import (
    MasterReviewError,
    MasterReviewNotFoundError,
    create_master_review,
    get_all_master_reviews,
    get_latest_master_review,
)
from packages.pi_adapter.runtime import PiAdapterError, PiRuntimeClient, PiRuntimeConfig
from packages.project_service import (
    ProjectNotFoundError,
    ProjectServiceError,
    ProjectStageError,
    get_project_record,
    replan_project,
)
from packages.validation_service import get_validation_status


class ReviewRequest(BaseModel):
    reviewer_id: str
    review_status: str          # approved | rejected | needs_replan
    summary: str
    findings: dict | None = None
    auto_replan: bool = False   # if needs_replan, immediately replan project


class ReplanRequest(BaseModel):
    reason: str = "master-initiated replan"


class RuntimePromptRequest(BaseModel):
    prompt: str
    role: str = "master"


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "master-service"}

    return router


def create_runtime_router() -> APIRouter:
    router = APIRouter(prefix="/runtime", tags=["runtime"])
    client = PiRuntimeClient(PiRuntimeConfig(default_role="master"))

    @router.post("/invoke")
    def invoke_runtime(payload: RuntimePromptRequest) -> dict[str, Any]:
        try:
            session_id = client.open_session("master-service-runtime", role=payload.role)
            result = client.invoke_model(
                payload.prompt,
                {"session_id": session_id, "role": payload.role},
            )
            client.close_session(session_id)
            return {"status": "ok", "session_id": session_id, "result": result}
        except PiAdapterError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "pi adapter invocation failed",
                    "error": exc.error.message,
                    "stdout": exc.error.stdout,
                    "stderr": exc.error.stderr,
                    "exit_code": exc.error.exit_code,
                },
            ) from exc

    return router


def create_review_router() -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["review"])

    @router.post("/{project_id}/review")
    def review_project(project_id: str, req: ReviewRequest) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

        try:
            review = create_master_review(
                project_id=project_id,
                reviewer_agent_id=req.reviewer_id,
                status=req.review_status,
                review_summary=req.summary,
                findings=req.findings or {},
            )
        except MasterReviewError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

        replan_result = None
        if req.review_status == "needs_replan" and req.auto_replan:
            try:
                replan_result = replan_project(project_id, reason=req.summary)
            except ProjectStageError as exc:
                raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

        return {
            "status": "ok",
            "review": review,
            "replan": replan_result,
        }

    @router.get("/{project_id}/review")
    def get_review(project_id: str) -> dict[str, Any]:
        try:
            review = get_latest_master_review(project_id)
            return {"status": "ok", "review": review}
        except MasterReviewNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/reviews")
    def get_all_reviews(project_id: str) -> dict[str, Any]:
        return {"status": "ok", "reviews": get_all_master_reviews(project_id)}

    @router.post("/{project_id}/replan")
    def replan(project_id: str, req: ReplanRequest) -> dict[str, Any]:
        try:
            project = replan_project(project_id, reason=req.reason)
            return {"status": "ok", "project": project}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectStageError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/escalate")
    def escalate_project(project_id: str, payload: dict) -> dict[str, Any]:
        try:
            project = get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

        level = int(payload.get("level", 1))
        # Record escalation as a rejected review with escalation findings
        review = create_master_review(
            project_id=project_id,
            reviewer_agent_id=payload.get("reviewer_id", "master-service"),
            status="rejected",
            review_summary=f"Escalated to level {level}: {payload.get('reason', 'no reason given')}",
            findings={"escalation_level": level, "reason": payload.get("reason", "")},
        )
        return {"status": "ok", "review": review, "escalation_level": level}

    @router.get("/{project_id}/status")
    def project_status(project_id: str) -> dict[str, Any]:
        try:
            project = get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

        val_status = get_validation_status(project_id)

        latest_review: dict | None = None
        try:
            latest_review = get_latest_master_review(project_id)
        except MasterReviewNotFoundError:
            pass

        return {
            "status": "ok",
            "project": project,
            "validation_status": val_status,
            "latest_review": latest_review,
        }

    return router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpsClaw Master Service",
        version="0.3.0-m5",
        description="M5 master review, replan, escalation, validation oversight.",
    )
    app.include_router(create_health_router())
    app.include_router(create_runtime_router())
    app.include_router(create_review_router())
    return app


app = create_app()
