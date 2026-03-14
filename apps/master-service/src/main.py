from fastapi import FastAPI, APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Any

class ReviewReq(BaseModel):
    project_id: str
    reviewer_id: str
    comments: str | None = None


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health():
        return {"status": "master ok"}

    return router


def create_review_router() -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["review"])

    @router.post("/{project_id}/review")
    def review_project(project_id: str, req: ReviewReq):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "review not implemented in M0",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    @router.post("/{project_id}/replan")
    def replan_project(project_id: str, plan: Any):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "replan not implemented in M0",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    @router.post("/{project_id}/escalate")
    def escalate_project(project_id: str, level: int = 1):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "escalate not implemented in M0",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    return router


def create_app() -> FastAPI:
    app = FastAPI(title="OldClaw Master Service", version="0.1.0-m0")
    app.include_router(create_health_router())
    app.include_router(create_review_router())
    return app


app = create_app()
