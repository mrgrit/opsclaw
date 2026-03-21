import json
import time
import warnings
from dataclasses import dataclass
from typing import Any

import httpx

from packages.pi_adapter.contracts import (
    ModelInvokeRequest,
    ModelInvokeResponse,
    PiAdapterErrorInfo,
    SessionOpenRequest,
    SessionOpenResponse,
)
from packages.pi_adapter.model_profiles import get_model_profile
from packages.pi_adapter.sessions import SessionRegistry
from packages.pi_adapter.tools.tool_bridge import PiToolBridge
from packages.pi_adapter.translators import build_prompt, normalize_output


_FALLBACK_OLLAMA_URL = "http://192.168.0.105:11434/v1"

# connect: TCP 연결 시간 / read: 스트리밍 청크 간격 최대 대기 (Ollama 멈춤 감지)
_CONNECT_TIMEOUT = 10.0
_CHUNK_READ_TIMEOUT = 60.0  # 첫 토큰 생성(모델 로딩 포함)까지 최대 60s


def _ollama_chat(
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, str, int]:
    """Ollama /v1/chat/completions 직접 스트리밍 호출.

    Returns:
        (stdout, stderr, exit_code) — subprocess 결과와 동일한 형식.

    Timeout 동작:
        - connect=10s: TCP 연결 실패 → 즉시 에러
        - read=60s: 스트리밍 청크 간격 — Ollama가 60s 이상 무응답이면 즉시 에러
          (cold-start 포함; 청크가 오기 시작하면 빠르게 도착)
    """
    url = (base_url or _FALLBACK_OLLAMA_URL).rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": True,
    }
    headers = {"Authorization": f"Bearer {api_key or 'ollama'}"}
    timeout = httpx.Timeout(
        connect=_CONNECT_TIMEOUT,
        read=_CHUNK_READ_TIMEOUT,
        write=10.0,
        pool=5.0,
    )

    collected: list[str] = []
    try:
        with httpx.stream("POST", url, json=payload, headers=headers, timeout=timeout) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line or line.strip() == "data: [DONE]":
                    continue
                if line.startswith("data: "):
                    line = line[6:]
                try:
                    chunk = json.loads(line)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        collected.append(delta)
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
        result = "".join(collected)
        return result, "", 0
    except httpx.ReadTimeout:
        partial = "".join(collected)
        if partial:
            # 부분 응답이 있으면 성공으로 처리 (청크 스트림 종료 신호 누락 케이스)
            return partial, "", 0
        return "", f"Ollama 응답 없음: 청크 간격 {_CHUNK_READ_TIMEOUT:.0f}s 초과 (모델 로딩/GPU 점유 가능성)", 1
    except httpx.ConnectTimeout:
        return "", f"Ollama 연결 시간 초과 ({_CONNECT_TIMEOUT:.0f}s) — 서버 주소 확인: {url}", 1
    except httpx.ConnectError as exc:
        return "", f"Ollama 연결 실패: {exc}", 1
    except httpx.HTTPStatusError as exc:
        return "", f"Ollama HTTP {exc.response.status_code}: {exc.response.text[:300]}", 1
    except Exception as exc:
        return "", f"Ollama 호출 오류: {type(exc).__name__}: {exc}", 1


def _ollama_wake_up(base_url: str, api_key: str, model: str) -> None:
    """Ollama 모델 wake-up 핑 — 짧은 프롬프트로 모델 로딩 유도."""
    try:
        _ollama_chat(
            base_url=base_url,
            api_key=api_key,
            model=model,
            system_prompt="You are a helpful assistant.",
            user_prompt="wake up",
        )
    except Exception:
        pass


_ROLE_SYSTEM_PROMPTS: dict[str, str] = {
    "manager": (
        "You are the OpsClaw Manager agent. You orchestrate IT operations workflows "
        "on internal network assets. You follow playbooks precisely — do not improvise. "
        "Produce structured JSON outputs when asked. Never skip validation or evidence steps."
    ),
    "master": (
        "You are the OpsClaw Master agent. You perform high-level reasoning, planning, "
        "and review of operations work. Validate evidence, review manager outputs, and "
        "produce authoritative assessment reports. Be precise and conservative."
    ),
    "subagent": (
        "You are the OpsClaw SubAgent. You execute specific operational commands on "
        "assigned assets. Follow instructions exactly, report stdout/stderr faithfully, "
        "and never exceed your assigned scope."
    ),
}


def _role_system_prompt(role: str) -> str:
    return _ROLE_SYSTEM_PROMPTS.get(role, _ROLE_SYSTEM_PROMPTS["manager"])


class PiAdapterError(Exception):
    def __init__(self, error: PiAdapterErrorInfo) -> None:
        super().__init__(error.message)
        self.error = error


class PiRuntimeInvocationError(PiAdapterError):
    pass


@dataclass
class PiRuntimeConfig:
    default_role: str = "manager"


class PiRuntimeClient:
    """
    OpsClaw-side LLM invocation adapter.

    Calls Ollama /v1/chat/completions directly via httpx (streaming).
    No subprocess / pi CLI dependency — avoids freeze caused by blocking subprocess waits.
    """

    def __init__(self, config: PiRuntimeConfig) -> None:
        self.config = config
        self.sessions = SessionRegistry()
        self.tool_bridge = PiToolBridge()

    def open_session(self, session_name: str, role: str | None = None) -> str:
        selected_role = role or self.config.default_role
        profile = get_model_profile(selected_role)
        session = self.sessions.create(
            session_name=session_name,
            role=selected_role,
            provider=profile.provider,
            model=profile.model,
        )
        response = SessionOpenResponse(
            session_id=session.session_id,
            session_name=session.session_name,
            role=session.role,
            provider=session.provider,
            model=session.model,
        )
        return response.session_id

    def invoke_model(self, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        request = ModelInvokeRequest(
            prompt=prompt,
            session_id=(context or {}).get("session_id"),
            role=(context or {}).get("role", self.config.default_role),
            context=context or {},
        )

        role = request.role or self.config.default_role
        profile = get_model_profile(role)
        session_id = request.session_id

        if session_id:
            session = self.sessions.get(session_id)
            if session is None:
                raise PiAdapterError(
                    PiAdapterErrorInfo(message=f"Unknown session id: {session_id}")
                )
            provider = session.provider
            model = session.model
        else:
            provider = profile.provider
            model = profile.model

        compiled_prompt = build_prompt(request.prompt, request.context)
        system_prompt = request.context.get("system_prompt") or _role_system_prompt(role)

        # tool_names는 직접 Ollama 호출 시 미지원 (tool calling은 향후 function_call API로 확장)
        tool_names = request.context.get("tool_names")
        if isinstance(tool_names, list) and tool_names:
            warnings.warn(
                f"tool_names {tool_names} passed but direct Ollama mode does not support tool calling. "
                "Proceeding without tools.",
                stacklevel=2,
            )

        base_url = profile.base_url or _FALLBACK_OLLAMA_URL

        # 직접 Ollama 호출: subprocess 없이 httpx 스트리밍
        # wake-up 포함 최대 2회 재시도
        MAX_RETRIES = 2
        stdout = stderr = ""
        exit_code = 1

        for attempt in range(MAX_RETRIES + 1):
            stdout, stderr, exit_code = _ollama_chat(
                base_url=base_url,
                api_key=profile.api_key,
                model=model,
                system_prompt=system_prompt,
                user_prompt=compiled_prompt,
            )
            if exit_code == 0 and stdout.strip():
                break
            if attempt < MAX_RETRIES:
                # 빈 응답 또는 오류 → wake-up 핑 후 재시도
                _ollama_wake_up(base_url, profile.api_key, model)
                time.sleep(3)

        command = [f"httpx→{base_url}/chat/completions", f"model={model}"]

        normalized = normalize_output(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
        )

        response = ModelInvokeResponse(
            session_id=session_id,
            provider=provider,
            model=model,
            command=command,
            stdout=normalized["stdout"],
            stderr=normalized["stderr"],
            exit_code=normalized["exit_code"],
        )

        if response.exit_code != 0:
            raise PiRuntimeInvocationError(
                PiAdapterErrorInfo(
                    message="pi runtime invocation failed",
                    command=response.command,
                    stdout=response.stdout,
                    stderr=response.stderr,
                    exit_code=response.exit_code,
                )
            )

        return {
            "session_id": response.session_id,
            "provider": response.provider,
            "model": response.model,
            "command": response.command,
            "stdout": response.stdout,
            "stderr": response.stderr,
            "exit_code": response.exit_code,
        }

    def close_session(self, session_id: str) -> None:
        self.sessions.remove(session_id)

    @staticmethod
    def _tool_request(tool_names: list[str]):
        from packages.pi_adapter.contracts import ToolCallRequest

        return ToolCallRequest(tool_names=tool_names)
