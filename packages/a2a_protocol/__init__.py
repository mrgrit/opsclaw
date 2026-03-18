import os
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

SUBAGENT_DEFAULT_URL = os.getenv("SUBAGENT_URL", "http://127.0.0.1:8001")


class A2AError(Exception):
    def __init__(self, message: str, status_code: int | None = None, detail: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


@dataclass
class A2ARunRequest:
    project_id: str
    job_run_id: str
    script: str
    timeout_s: int = 30


@dataclass
class A2ARunResult:
    status: str
    stdout: str
    stderr: str
    exit_code: int
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class A2AClientConfig:
    base_url: str = SUBAGENT_DEFAULT_URL
    timeout_s: int = 130


class A2AClient:
    def __init__(self, config: A2AClientConfig | None = None):
        self.config = config or A2AClientConfig()

    def health(self) -> dict[str, Any]:
        try:
            resp = httpx.get(f"{self.config.base_url}/health", timeout=5.0)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise A2AError(f"SubAgent health check failed: {exc}") from exc

    def capabilities(self) -> dict[str, Any]:
        try:
            resp = httpx.get(f"{self.config.base_url}/capabilities", timeout=5.0)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise A2AError(f"SubAgent capabilities check failed: {exc}") from exc

    def run_script(self, request: A2ARunRequest) -> A2ARunResult:
        try:
            resp = httpx.post(
                f"{self.config.base_url}/a2a/run_script",
                json={
                    "project_id": request.project_id,
                    "job_run_id": request.job_run_id,
                    "script": request.script,
                    "timeout_s": request.timeout_s,
                },
                timeout=float(self.config.timeout_s),
            )
            if resp.status_code == 501:
                raise A2AError(
                    "SubAgent run_script not implemented",
                    status_code=501,
                    detail=resp.json(),
                )
            resp.raise_for_status()
            data = resp.json()
            detail = data.get("detail", {})
            return A2ARunResult(
                status=data.get("status", "unknown"),
                stdout=detail.get("stdout", ""),
                stderr=detail.get("stderr", ""),
                exit_code=detail.get("exit_code", -1),
                detail=detail,
            )
        except A2AError:
            raise
        except httpx.HTTPError as exc:
            raise A2AError(f"A2A run_script call failed: {exc}") from exc

    def invoke_llm(
        self,
        project_id: str,
        task: str,
        context: dict[str, Any] | None = None,
        system_prompt: str | None = None,
        timeout_s: int = 120,
    ) -> dict[str, Any]:
        """SubAgent LLM에 고수준 작업 지시를 보낸다."""
        job_run_id = f"llm_{uuid.uuid4().hex[:12]}"
        try:
            resp = httpx.post(
                f"{self.config.base_url}/a2a/invoke_llm",
                json={
                    "project_id": project_id,
                    "job_run_id": job_run_id,
                    "task": task,
                    "context": context or {},
                    "system_prompt": system_prompt,
                    "timeout_s": timeout_s,
                },
                timeout=float(timeout_s + 15),
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise A2AError(f"A2A invoke_llm call failed: {exc}") from exc

    def install_tool(
        self,
        project_id: str,
        tool_name: str,
        method: str = "apt",
        package: str | None = None,
        timeout_s: int = 120,
    ) -> dict[str, Any]:
        """SubAgent에게 도구 설치를 지시한다."""
        job_run_id = f"install_{uuid.uuid4().hex[:12]}"
        try:
            resp = httpx.post(
                f"{self.config.base_url}/a2a/install_tool",
                json={
                    "project_id": project_id,
                    "job_run_id": job_run_id,
                    "tool_name": tool_name,
                    "method": method,
                    "package": package,
                    "timeout_s": timeout_s,
                },
                timeout=float(timeout_s + 15),
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise A2AError(f"A2A install_tool call failed: {exc}") from exc

    def analyze(
        self,
        project_id: str,
        command_output: str,
        question: str,
        context: dict[str, Any] | None = None,
        timeout_s: int = 120,
    ) -> dict[str, Any]:
        """bash 출력을 SubAgent LLM이 분석하게 한다."""
        job_run_id = f"analyze_{uuid.uuid4().hex[:12]}"
        try:
            resp = httpx.post(
                f"{self.config.base_url}/a2a/analyze",
                json={
                    "project_id": project_id,
                    "job_run_id": job_run_id,
                    "command_output": command_output,
                    "question": question,
                    "context": context or {},
                    "timeout_s": timeout_s,
                },
                timeout=float(timeout_s + 15),
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise A2AError(f"A2A analyze call failed: {exc}") from exc
