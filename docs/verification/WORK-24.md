# WORK-24

## 1. 작업 정보
- 작업 이름: M2 코드 주입 준비 / project_service · graph_runtime · manager-api 현행 본문 고정
- 현재 브랜치: main
- 현재 HEAD 커밋: 1ae14373a83f2a4f520220a63021f0c769fe1d42
- 작업 시각: 2026-03-15T00:53:27Z

## 2. 이번 작업에서 수정한 파일
- docs/verification/REVIEW-23.md
- docs/verification/NEXT-24.md
- docs/verification/WORK-24.md

## 3. 현재 파일 트리
- `find apps -maxdepth 3 -type f | sort`
```
apps/manager_api/__init__.py
apps/manager_api/__pycache__/__init__.cpython-310.pyc
apps/manager-api/src/main.py
apps/master_service/__init__.py
apps/master_service/__pycache__/__init__.cpython-310.pyc
apps/master-service/src/main.py
apps/scheduler-worker/src/main.py
apps/subagent_runtime/__init__.py
apps/subagent_runtime/__pycache__/__init__.cpython-310.pyc
apps/subagent-runtime/src/main.py
apps/watch-worker/src/main.py
```
- `find packages/project_service -maxdepth 3 -type f | sort 2>/dev/null || true`
```
packages/project_service/__init__.py
packages/project_service/__pycache__/__init__.cpython-310.pyc
```
- `find packages/graph_runtime -maxdepth 3 -type f | sort 2>/dev/null || true`
```
packages/graph_runtime/__init__.py
packages/graph_runtime/__pycache__/__init__.cpython-310.pyc
```
- `find docs -maxdepth 3 -type f | sort | grep '/m2/' || true`
```
(no output)
```
- `find tools/dev -maxdepth 2 -type f | sort 2>/dev/null || true`
```
tools/dev/pi_runtime_smoke.py
tools/dev/__pycache__/pi_runtime_smoke.cpython-310.pyc
tools/dev/__pycache__/service_adapter_smoke.cpython-310.pyc
tools/dev/__pycache__/service_http_smoke.cpython-310.pyc
tools/dev/service_adapter_smoke.py
tools/dev/service_http_smoke.py
```

## 4. 교체 예정 파일 현재 본문
- `apps/manager-api/src/main.py`
```
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status

from packages.pi_adapter.runtime import PiAdapterError, PiRuntimeClient, PiRuntimeConfig


@dataclass
class ProjectCreateRequest:
    name: str
    request_text: str
    mode: str = "one_shot"


@dataclass
class AssetCreateRequest:
    name: str
    asset_type: str
    platform: str
    mgmt_ip: str
    env: str


@dataclass
class RuntimePromptRequest:
    prompt: str
    role: str = "manager"


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "manager-api"}

    return router


def create_runtime_router() -> APIRouter:
    router = APIRouter(prefix="/runtime", tags=["runtime"])
    client = PiRuntimeClient(PiRuntimeConfig(default_role="manager"))

    @router.post("/invoke")
    def invoke_runtime(payload: RuntimePromptRequest) -> dict[str, Any]:
        try:
            session_id = client.open_session("manager-api-runtime", role=payload.role)
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


def create_project_router() -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["projects"])

    @router.post("")
    def create_project(payload: ProjectCreateRequest) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Project creation service is not implemented in M0.",
                "next_milestone": "M2",
                "payload": asdict(payload),
            },
        )

    @router.get("/{project_id}")
    def get_project(project_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Project query service is not implemented in M0.",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    @router.post("/{project_id}/execute")
    def execute_project(project_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Project execution orchestration is not implemented in M0.",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    @router.get("/{project_id}/report")
    def get_project_report(project_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Project report pipeline is not implemented in M0.",
                "next_milestone": "M2",
                "project_id": project_id,
            },
        )

    return router


def create_asset_router() -> APIRouter:
    router = APIRouter(prefix="/assets", tags=["assets"])

    @router.post("")
    def create_asset(payload: AssetCreateRequest) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Asset registry service is not implemented in M0.",
                "next_milestone": "M4",
                "payload": asdict(payload),
            },
        )

    @router.get("/{asset_id}")
    def get_asset(asset_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Asset query service is not implemented in M0.",
                "next_milestone": "M4",
                "asset_id": asset_id,
            },
        )

    @router.post("/{asset_id}/resolve")
    def resolve_asset(asset_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Asset resolve flow is not implemented in M0.",
                "next_milestone": "M4",
                "asset_id": asset_id,
            },
        )

    return router


def create_playbook_router() -> APIRouter:
    router = APIRouter(prefix="/playbooks", tags=["playbooks"])

    @router.get("")
    def list_playbooks() -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Playbook registry query is not implemented in M0.",
                "next_milestone": "M6",
            },
        )

    @router.post("/{playbook_id}/run")
    def run_playbook(playbook_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Playbook execution is not implemented in M0.",
                "next_milestone": "M6",
                "playbook_id": playbook_id,
            },
        )

    return router


def create_evidence_router() -> APIRouter:
    router = APIRouter(prefix="/evidence", tags=["evidence"])

    @router.get("/projects/{project_id}")
    def get_project_evidence(project_id: str) -> dict[str, Any]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Evidence query is not implemented in M0.",
                "next_milestone": "M5",
                "project_id": project_id,
            },
        )

    return router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpsClaw Manager API",
        version="0.1.0-m1",
        description="M1 manager API with minimal pi adapter integration endpoint.",
    )

    app.include_router(create_health_router())
    app.include_router(create_runtime_router())
    app.include_router(create_project_router())
    app.include_router(create_asset_router())
    app.include_router(create_playbook_router())
    app.include_router(create_evidence_router())

    return app


app = create_app()
```
- `packages/project_service/__init__.py`
```
(no content)
```
- `packages/graph_runtime/__init__.py`
```
(no content)
```
- `requirements.txt`
```
fastapi==0.116.1
pydantic==2.11.7
uvicorn==0.35.0
requests==2.32.5
```

## 5. 현재 DB 준비 상태 요약
- DATABASE_URL: (not set in environment)
- PostgreSQL 기동 상태: active (accepting connections on 5432)
- migration 적용 상태: 0001‑0004 적용, 핵심 테이블 모두 존재
- 사용 가능한 핵심 테이블: assets, projects, job_runs, evidence, reports, histories, task_memories, experiences, retrieval_documents, schedules, watch_jobs, watch_events, incidents, etc.
- 아직 비어 있는 패키지: packages/project_service (only __init__), packages/graph_runtime (only __init__)

## 6. 다음 단계에서 내가 직접 써야 할 파일 후보
- apps/manager-api/src/main.py – 현재 모든 `/projects` 엔드포인트가 `HTTP_501_NOT_IMPLEMENTED` 스텁, DB 로직 구현 필요
- packages/project_service/__init__.py – 비어 있음, 프로젝트 lifecycle 서비스 구현 필요
- packages/graph_runtime/__init__.py – 비어 있음, 상태기계 구현 필요
- requirements.txt – 향후 추가 의존성(예: SQLAlchemy, asyncpg 등) 필요
- docs/m2/opsclaw-m2-plan.md – 현재 없음, M2 설계·계획 문서 작성 필요
- docs/m2/opsclaw-m2-completion-report.md – 현재 없음, M2 완료 보고서 템플릿 필요
- tools/dev/project_service_smoke.py – 현재 없음, 프로젝트 서비스 smoke test 스크립트 필요
- tools/dev/manager_projects_http_smoke.py – 현재 없음, manager API HTTP smoke test 필요
- (optional) docs/architecture/README.md – 현재 placeholder, M2 아키텍처 문서 보강 필요
- (optional) tests/unit/project_service_test.py – 현재 없음, unit test 작성 필요

## 7. 미해결 사항
1. `DATABASE_URL` 환경변수가 설정되지 않아 로컬 실행 시 명시적으로 지정 필요
2. `project_service`와 `graph_runtime` 패키지는 비어 있어 실제 로직 구현이 선행돼야 함
3. `manager-api` `/projects` 라우터는 아직 DB 연동 로직이 없으며, 테스트용 엔드포인트가 구현되지 않음
