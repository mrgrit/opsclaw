import subprocess
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel

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


# ── A2A 확장 요청 모델 ────────────────────────────────────────────────────────

class InvokeLLMRequest(BaseModel):
    project_id: str
    job_run_id: str
    task: str                          # Manager가 SubAgent에게 주는 작업 지시
    context: dict | None = None        # 추가 컨텍스트 (asset 정보, 이전 실행 결과 등)
    system_prompt: str | None = None   # 역할 오버라이드
    timeout_s: int = 120


class InstallToolRequest(BaseModel):
    project_id: str
    job_run_id: str
    tool_name: str                     # 설치할 도구 이름 (예: "nmap", "curl", "jq")
    method: str = "apt"                # "apt" | "pip" | "npm" | "script"
    package: str | None = None        # 패키지명이 tool_name과 다를 때
    timeout_s: int = 120


class AnalyzeRequest(BaseModel):
    project_id: str
    job_run_id: str
    command_output: str               # 분석할 bash 실행 결과
    question: str                     # "이 출력에서 비정상적인 디스크 사용 패턴이 있는가?" 등
    context: dict | None = None
    timeout_s: int = 120


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
        import shutil, os
        _nvm_pi = os.path.expanduser("~/.nvm/versions/node/v22.22.1/bin/pi")
        pi_path = shutil.which("pi") or (_nvm_pi if os.path.isfile(_nvm_pi) else "")
        return {
            "service": "subagent-runtime",
            "version": "0.4.0-m12",
            "capabilities": [
                "health",
                "capabilities",
                "run_script",
                "invoke_llm",
                "install_tool",
                "analyze",
                "evidence_return",
                "runtime_invoke",
            ],
            "llm_available": bool(pi_path),
            "pi_path": pi_path,
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
    _llm_client = PiRuntimeClient(PiRuntimeConfig(default_role="subagent"))

    def _run_shell(script: str, timeout_s: int) -> tuple[str, str, int]:
        """bash 스크립트 실행 → (stdout, stderr, exit_code)"""
        try:
            r = subprocess.run(
                script, shell=True, capture_output=True, text=True, timeout=timeout_s,
            )
            return r.stdout, r.stderr, r.returncode
        except subprocess.TimeoutExpired:
            return "", f"Timed out after {timeout_s}s", -1

    # ── 기존: bash 스크립트 직접 실행 ─────────────────────────────────────────
    @router.post("/run_script")
    def run_script(payload: RunScriptRequest) -> A2ARunResponse:
        stdout, stderr, exit_code = _run_shell(payload.script, payload.timeout_s)
        return A2ARunResponse(
            status="ok" if exit_code == 0 else ("timeout" if exit_code == -1 else "error"),
            detail={
                "project_id": payload.project_id,
                "job_run_id": payload.job_run_id,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
            },
        )

    # ── 신규: LLM 기반 작업 실행 ─────────────────────────────────────────────
    @router.post("/invoke_llm")
    def invoke_llm(payload: InvokeLLMRequest) -> dict[str, Any]:
        """
        Manager가 고수준 작업 지시를 보내면 SubAgent LLM이 해석하여 응답한다.
        Playbook 기반 단계 중 '분석/판단'이 필요한 Step에서 호출된다.

        예:
          - "다음 시스템 로그에서 보안 이상 징후를 요약하라"
          - "TLS 인증서 점검 결과를 해석하고 만료 위험 여부를 판단하라"
        """
        ctx: dict[str, Any] = {"role": "subagent"}
        if payload.context:
            ctx.update(payload.context)
        if payload.system_prompt:
            ctx["system_prompt"] = payload.system_prompt

        try:
            result = _llm_client.invoke_model(payload.task, ctx)
            return {
                "status": "ok",
                "project_id": payload.project_id,
                "job_run_id": payload.job_run_id,
                "response": result.get("stdout", ""),
                "model": result.get("model"),
                "exit_code": result.get("exit_code", 0),
            }
        except PiAdapterError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": "LLM invocation failed", "error": exc.error.message},
            ) from exc

    # ── 신규: 도구 설치 ───────────────────────────────────────────────────────
    @router.post("/install_tool")
    def install_tool(payload: InstallToolRequest) -> dict[str, Any]:
        """
        SubAgent가 대상 시스템에 필요한 도구를 설치한다.
        method: "apt" | "pip" | "npm" | "script"
        """
        pkg = payload.package or payload.tool_name

        _INSTALL_SCRIPTS: dict[str, str] = {
            "apt": (
                f"export DEBIAN_FRONTEND=noninteractive\n"
                f"apt-get update -qq 2>&1 | tail -3\n"
                f"apt-get install -y --no-install-recommends {pkg} 2>&1"
            ),
            "pip": f"pip3 install --quiet {pkg} 2>&1",
            "npm": f"npm install -g {pkg} 2>&1",
            "script": pkg,  # script method: package 필드에 직접 스크립트 기입
        }

        script = _INSTALL_SCRIPTS.get(payload.method)
        if not script:
            raise HTTPException(
                status_code=400,
                detail={"message": f"Unknown install method: {payload.method}"},
            )

        stdout, stderr, exit_code = _run_shell(script, payload.timeout_s)
        return {
            "status": "ok" if exit_code == 0 else "error",
            "project_id": payload.project_id,
            "job_run_id": payload.job_run_id,
            "tool_name": payload.tool_name,
            "method": payload.method,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
        }

    # ── 신규: bash 출력 LLM 분석 ─────────────────────────────────────────────
    @router.post("/analyze")
    def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
        """
        bash 실행 결과를 SubAgent LLM이 분석/해석한다.
        분석형 Skill(analyze_wazuh_alert_burst, summarize_incident_timeline 등)에서 사용.
        """
        prompt = (
            f"다음은 시스템 명령 실행 결과이다:\n\n"
            f"```\n{payload.command_output[:4000]}\n```\n\n"
            f"질문: {payload.question}\n\n"
            f"간결하고 정확하게 한국어로 답하라. 불필요한 설명은 생략하라."
        )

        ctx: dict[str, Any] = {
            "role": "subagent",
            "system_prompt": (
                "You are the OpsClaw SubAgent analyzer. Analyze system command output "
                "and answer operational questions accurately and concisely in Korean. "
                "Focus only on facts visible in the output."
            ),
        }
        if payload.context:
            ctx.update(payload.context)

        try:
            result = _llm_client.invoke_model(prompt, ctx)
            return {
                "status": "ok",
                "project_id": payload.project_id,
                "job_run_id": payload.job_run_id,
                "analysis": result.get("stdout", ""),
                "model": result.get("model"),
                "exit_code": result.get("exit_code", 0),
            }
        except PiAdapterError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"message": "LLM analysis failed", "error": exc.error.message},
            ) from exc

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
