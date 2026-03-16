import subprocess
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status

from packages.pi_adapter.runtime import PiAdapterError, PiRuntimeClient, PiRuntimeConfig


@dataclass
class RunScriptRequest:
    project_id: str
    job_run_id: str
    script: str
    timeout_s: int = 120


@dataclass
class A2ARunResponse:
    status: str
    detail: dict[str, Any]


@dataclass
class RuntimePromptRequest:
    prompt: str
    role: str = "subagent"


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "subagent-runtime"}

    return router


def create_capabilities_router() -> APIRouter:
    router = APIRouter(tags=["capabilities"])

    @router.get("/capabilities")
    def capabilities() -> dict[str, Any]:
        return {
            "service": "subagent-runtime",
            "capabilities": [
                "health",
                "capabilities",
                "run_script",
                "evidence_return",
                "runtime_invoke",
            ],
        }

    return router


def create_runtime_router() -> APIRouter:
    router = APIRouter(prefix="/runtime", tags=["runtime"])
    client = PiRuntimeClient(PiRuntimeConfig(default_role="subagent"))

    @router.post("/invoke")
    def invoke_runtime(payload: RuntimePromptRequest) -> dict[str, Any]:
        try:
            session_id = client.open_session("subagent-runtime", role=payload.role)
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


def create_a2a_router() -> APIRouter:
    router = APIRouter(prefix="/a2a", tags=["a2a"])

    @router.post("/run_script")
    def run_script(payload: RunScriptRequest) -> A2ARunResponse:
        try:
            result = subprocess.run(
                payload.script,
                shell=True,
                capture_output=True,
                text=True,
                timeout=payload.timeout_s,
            )
            return A2ARunResponse(
                status="ok" if result.returncode == 0 else "error",
                detail={
                    "project_id": payload.project_id,
                    "job_run_id": payload.job_run_id,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                },
            )
        except subprocess.TimeoutExpired:
            return A2ARunResponse(
                status="timeout",
                detail={
                    "project_id": payload.project_id,
                    "job_run_id": payload.job_run_id,
                    "stdout": "",
                    "stderr": f"Script timed out after {payload.timeout_s}s",
                    "exit_code": -1,
                },
            )

    return router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpsClaw SubAgent Runtime",
        version="0.3.0-m3",
        description="M3 subagent runtime: A2A run_script execution engine.",
    )

    app.include_router(create_health_router())
    app.include_router(create_capabilities_router())
    app.include_router(create_runtime_router())
    app.include_router(create_a2a_router())

    return app


app = create_app()
