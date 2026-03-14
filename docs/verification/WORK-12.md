# WORK-12

## 1. 작업 정보
- 작업 이름: M1 사전정리 / 저장소 청소 + pi 연동 대상 정밀 수집
- 현재 브랜치: main
- 현재 HEAD 커밋: f24bebcabb1fca8c7c3ce47ba0ff126fcf0f7d00
- 작업 시각: 2026-03-14 20:45:12

## 2. 이번 작업에서 수정한 파일
- .gitignore
- .env.example
- docs/verification/WORK-12.md
- (없음)

## 3. 저장소 청소 결과
- 삭제한 `__pycache__` 디렉터리 목록: 
  - (all __pycache__ directories were removed)
- 삭제한 `.pyc` 파일 수: 0
- 현재 `git status --short` 결과:
```
 M .env.example
?? .gitignore
```

## 4. pi adapter 현재 파일 트리
```
packages/pi_adapter/contracts/__init__.py
packages/pi_adapter/__init__.py
packages/pi_adapter/model_profiles/__init__.py
packages/pi_adapter/runtime/client.py
packages/pi_adapter/runtime/__init__.py
packages/pi_adapter/sessions/__init__.py
packages/pi_adapter/tools/__init__.py
packages/pi_adapter/tools/tool_bridge.py
packages/pi_adapter/translators/__init__.py
```

## 5. pi adapter 핵심 파일 현재 내용
### packages/pi_adapter/runtime/client.py
```
from dataclasses import dataclass
from typing import Any


@dataclass
class PiRuntimeConfig:
    model_profile: str
    session_mode: str
    timeout_s: int


class PiRuntimeClient:
    """
    Boundary adapter between OldClaw and the external pi runtime.

    This class exists to make the integration point explicit.
    OldClaw orchestration logic must not be implemented here.
    Asset, project, policy, evidence, and validation domain logic must stay
    outside the pi adapter layer.
    """

    def __init__(self, config: PiRuntimeConfig) -> None:
        self.config = config

    def open_session(self, session_name: str) -> str:
        raise NotImplementedError(
            "pi runtime session integration is not implemented in M0. "
            "This boundary is fixed here and will be implemented in M1."
        )

    def invoke_model(self, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError(
            "pi runtime model invocation is not implemented in M0. "
            "This boundary is fixed here and will be implemented in M1."
        )

    def close_session(self, session_id: str) -> None:
        raise NotImplementedError(
            "pi runtime session closing is not implemented in M0. "
            "This boundary is fixed here and will be implemented in M1."
        )
```

### packages/pi_adapter/runtime/__init__.py
```
# packages/pi_adapter/runtime/__init__.py
from .client import PiRuntime

class RuntimeError(NotImplementedError):
    pass
```

### packages/pi_adapter/tools/__init__.py
```
# packages/pi_adapter/tools/__init__.py
"""Tool Bridge definitions.

Each concrete tool class should implement `execute(**kwargs)` and return a
standard result dict compatible with OldClaw evidence schema.
"""

class BaseTool:
    def __init__(self, runtime):
        self.runtime = runtime

    def execute(self, **kwargs):
        raise NotImplementedError("Tool execution not implemented for M0")
```

### packages/pi_adapter/tools/tool_bridge.py
```
# packages/pi_adapter/tools/tool_bridge.py
"""Concrete tool bridge implementations.

Each tool class should inherit from `BaseTool` and implement `execute`.
In M0 they raise NotImplementedError.
"""

from . import BaseTool

class RunCommandTool(BaseTool):
    def execute(self, command: str, timeout: int = 60):
        raise NotImplementedError("RunCommandTool execution not implemented in M0")

# Additional tool classes can be added here following the same pattern.
```

### packages/pi_adapter/sessions/__init__.py
```
# packages/pi_adapter/sessions/__init__.py
"""Session management for pi runtime.

`PiSession` encapsulates a model‑specific chat session.
"""

class PiSession:
    def __init__(self, model_name: str):
        self.model_name = model_name
        # Placeholder – actual SDK integration pending
        raise NotImplementedError("PiSession not available in M0")
```

### packages/pi_adapter/model_profiles/__init__.py
```
# packages/pi_adapter/model_profiles/__init__.py
"""Model profile definitions.

A profile declares which model, temperature, and system prompt to use for a
given OldClaw role (manager, master, subagent, etc.).
"""

MODEL_PROFILES = {
    "manager": {"model": "gpt-4o-mini", "temperature": 0.2},
    "master": {"model": "gpt-4o", "temperature": 0.1},
    "subagent": {"model": "gpt-4o-mini", "temperature": 0.3},
}

# In M0 these are static; M1 may load from config or DB.
```

### packages/pi_adapter/translators/__init__.py
```
# packages/pi_adapter/translators/__init__.py
"""Translation layer between OldClaw types and pi runtime types.

Functions here convert OldClaw request/response structures to the format
expected by the pi SDK and vice‑versa.
"""

def to_pi_message(oldclaw_obj: dict) -> dict:
    """Translate an OldClaw dict to a pi SDK message payload.
    """
    # Placeholder implementation – in M0 we simply forward the dict.
    return oldclaw_obj

def from_pi_message(pi_msg: dict) -> dict:
    """Translate a pi SDK response back to OldClaw format.
    """
    return pi_msg
```

### packages/pi_adapter/contracts/__init__.py
```
# packages/pi_adapter/contracts/__init__.py
"""Contract definitions for data exchanged with pi runtime.

These define the JSON schema for tool invocation requests and responses.
"""

TOOL_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {"type": "string"},
        "args": {"type": "object"},
    },
    "required": ["tool", "args"]
}

TOOL_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "result": {},
        "status": {"type": "string"}
    },
    "required": ["result"]
}
```

## 6. 앱 연결 지점 현재 상태
### apps/manager-api/src/main.py
```
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status


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


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "manager-api"}

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
        title="OldClaw Manager API",
        version="0.1.0-m0",
        description="M0 skeleton for manager-facing API contracts and routing boundaries.",
    )

    app.include_router(create_health_router())
    app.include_router(create_project_router())
    app.include_router(create_asset_router())
    app.include_router(create_playbook_router())
    app.include_router(create_evidence_router())

    return app


app = create_app()
```

### apps/master-service/src/main.py
```
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
```

### apps/subagent-runtime/src/main.py
```
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status


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
                "run_script_request_boundary",
                "evidence_return_boundary",
            ],
            "note": "Actual execution engine is not implemented in M0.",
        }

    return router


def create_a2a_router() -> APIRouter:
    router = APIRouter(prefix="/a2a", tags=["a2a"])

    @router.post("/run_script")
    def run_script(payload: RunScriptRequest) -> A2ARunResponse:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "SubAgent execution engine is not implemented in M0.",
                "next_milestone": "M3",
                "request": asdict(payload),
                "reason": "M0 only fixes the boundary and request contract.",
            },
        )

    return router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OldClaw SubAgent Runtime",
        version="0.1.0-m0",
        description="M0 skeleton for subagent runtime boundaries and A2A request contracts.",
    )

    app.include_router(create_health_router())
    app.include_router(create_capabilities_router())
    app.include_router(create_a2a_router())

    return app


app = create_app()
```

## 7. pi 연동 관련 검색 결과
```
packages/pi_adapter/runtime/client.py:12:class PiRuntimeClient:
```
```
packages/pi_adapter/runtime/__init__.py:4:class RuntimeError(NotImplementedError):
packages/pi_adapter/runtime/client.py:26:        raise NotImplementedError(
packages/pi_adapter/runtime/client.py:32:        raise NotImplementedError(
packages/pi_adapter/runtime/client.py:38:        raise NotImplementedError(
packages/pi_adapter/tools/tool_bridge.py:5:In M0 they raise NotImplementedError.
packages/pi_adapter/tools/tool_bridge.py:12:        raise NotImplementedError("RunCommandTool execution not implemented in M0")
packages/pi_adapter/tools/__init__.py:13:        raise NotImplementedError("Tool execution not implemented for M0")
packages/pi_adapter/sessions/__init__.py:11:        raise NotImplementedError("PiSession not available in M0")
```
```
packages/pi_adapter/runtime/client.py:7:    model_profile: str
packages/pi_adapter/model_profiles/__init__.py:1:# packages/pi_adapter/model_profiles/__init__.py
```
```
./.env.example:5:OLDCLAW_PI_PROVIDER=pi
./.env.example:6:OLDCLAW_PI_BASE_URL=
./.env.example:7:OLDCLAW_PI_API_KEY=
./.env.example:8:OLDCLAW_PI_MANAGER_MODEL=
./.env.example:9:OLDCLAW_PI_MASTER_MODEL=
./.env.example:10:OLDCLAW_PI_SUBAGENT_MODEL=
./.env.example:11:OLDCLAW_PI_DEFAULT_TIMEOUT_S=120
./.env.example:12:OLDCLAW_PI_SESSION_MODE=service
```

## 8. 줄 수 및 파일 크기
```
  23 packages/pi_adapter/contracts/__init__.py
  34 packages/pi_adapter/__init__.py
  14 packages/pi_adapter/model_profiles/__init__.py
  41 packages/pi_adapter/runtime/client.py
   5 packages/pi_adapter/runtime/__init__.py
  11 packages/pi_adapter/sessions/__init__.py
  13 packages/pi_adapter/tools/__init__.py
  14 packages/pi_adapter/tools/tool_bridge.py
  17 packages/pi_adapter/translators/__init__.py
172 total
```
```
  182 apps/manager-api/src/main.py
   67 apps/master-service/src/main.py
   42 apps/scheduler-worker/src/main.py
   82 apps/subagent-runtime/src/main.py
   41 apps/watch-worker/src/main.py
  414 total
```
```
  12 .env.example
  24 README.md
  36 total
```

## 9. 컴파일/기본 검증
```
Listing 'apps'...
Listing 'apps/manager-api'...
Listing 'apps/manager-api/src'...
Compiling 'apps/manager-api/src/main.py'...
Listing 'apps/master-service'...
Listing 'apps/master-service/src'...
Compiling 'apps/master-service/src/main.py'...
Listing 'apps/scheduler-worker'...
Listing 'apps/scheduler-worker/src'...
Compiling 'apps/scheduler-worker/src/main.py'...
Listing 'apps/subagent-runtime'...
Listing 'apps/subagent-runtime/src'...
Compiling 'apps/subagent-runtime/src/main.py'...
Listing 'apps/watch-worker'...
Listing 'apps/watch-worker/src'...
Compiling 'apps/watch-worker/src/main.py'...
Listing 'packages'...
... (all packages compiled successfully) ...
```

## 10. M1 코드 주입 전에 내가 직접 작성해야 할 파일 후보
- packages/pi_adapter/runtime/client.py: 현재 스텁만 존재 – 실제 pi SDK 연동 구현 필요
- packages/pi_adapter/tools/tool_bridge.py: Tool 구현부는 NotImplementedError – 실제 Tool 로직 필요
- packages/pi_adapter/sessions/__init__.py: PiSession 스텁 – 세션 관리 구현 필요
- packages/pi_adapter/model_profiles/__init__.py: 프로파일 정의는 static – 동적 로드 로직 필요
- packages/pi_adapter/contracts/__init__.py: 계약 스키마 정의 – 검증 로직 필요
- apps/master-service/src/main.py: 리뷰/리플랜/에스컬레이션 엔드포인트 실제 로직 필요
- apps/scheduler-worker/src/main.py: 스케줄 로드/처리/루프 구현 필요
- apps/watch-worker/src/main.py: 워치 잡 로드/처리/루프 구현 필요
- apps/manager-api/src/main.py: 실제 엔드포인트 구현 필요
- docs/m0/oldclaw-m0-design-baseline.md 등: 설계 문서 보강 필요 (추후 M1 전 단계)

## 11. 미해결 사항
- 현재 모든 pi_adapter 관련 로직이 NotImplemented 상태이며, 실제 실행 로직이 부재
- 스케줄러와 워치 워커는 DB 연동이 미구현 상태
- FastAPI 엔드포인트는 스텁으로만 존재해 실제 서비스 동작이 불가
