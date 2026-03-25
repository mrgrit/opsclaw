import json as _json
import subprocess
import time
from dataclasses import asdict, dataclass
from typing import Any

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel

from packages.pi_adapter.runtime import PiAdapterError, PiRuntimeClient, PiRuntimeConfig

# ── Ollama direct config (for mission autonomous loop) ────────────────────────
_OLLAMA_BASE = "http://192.168.0.105:11434/v1"


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


# ── 자율 미션 모델 ────────────────────────────────────────────────────────────

class MissionRequest(BaseModel):
    mission_id: str
    role: str                            # "red" | "blue"
    objective: str                       # 미션 목표
    target: str = ""                     # 공격/모니터링 대상
    model: str = "gemma3:12b"            # 사용할 Ollama 모델
    playbook_context: list[dict] = []    # 관련 Playbook steps
    experience_context: list[str] = []   # 축적된 경험 텍스트
    max_steps: int = 10
    timeout_s: int = 180


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

    # ── 신규: 자율 미션 루프 ──────────────────────────────────────────────────
    def _ollama_chat(model: str, messages: list[dict], max_tokens: int = 300) -> str:
        """Ollama /v1/chat/completions 직접 호출 (pi_adapter 우회)"""
        try:
            resp = httpx.post(
                f"{_OLLAMA_BASE}/chat/completions",
                json={"model": model, "messages": messages,
                      "temperature": 0.1, "max_tokens": max_tokens},
                timeout=60.0,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            return _json.dumps({"action": "error", "command": "", "done": True,
                                "summary": f"LLM call failed: {exc}"})

    def _parse_llm_json(raw: str) -> dict:
        """LLM 응답에서 JSON 추출 (```json 블록 또는 raw JSON)"""
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        # 첫 { 부터 마지막 } 까지 추출
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end+1]
        try:
            return _json.loads(text)
        except _json.JSONDecodeError:
            return {"action": "parse_error", "command": "", "done": True,
                    "summary": f"Failed to parse: {raw[:200]}"}

    @router.post("/mission")
    def run_mission(payload: MissionRequest) -> dict[str, Any]:
        """
        자율 미션 루프: 로컬 LLM이 미션 목표를 받고, 자율적으로 명령을 결정·실행·반복한다.
        Master/Manager를 매번 거치지 않고 SubAgent가 독립 행동.
        """
        # 시스템 프롬프트 구성
        role_desc = {
            "red": (
                "You are a Red Team penetration tester. "
                "Your goal is to find and exploit vulnerabilities on the target. "
                "You have bash access. Use curl, nmap, or any CLI tools. "
                "For remote commands: sshpass -p1 ssh -o StrictHostKeyChecking=no <user>@<ip> '<command>'. "
                "JuiceShop REST API uses JSON: curl -s -X POST <url> -H 'Content-Type: application/json' -d '{...}'."
            ),
            "blue": (
                "You are a Blue Team security analyst monitoring Wazuh SIEM. "
                "Your goal is to detect attacks and create detection rules. "
                "You have bash access. To run commands on remote servers, use: "
                "sshpass -p1 ssh -o StrictHostKeyChecking=no <user>@<ip> '<command>'. "
                "For sudo commands: sshpass -p1 ssh -o StrictHostKeyChecking=no <user>@<ip> 'echo 1 | sudo -S <command>'. "
                "SIEM server: siem@10.20.30.100, Web server: web@10.20.30.80, IPS: secu@10.20.30.1."
            ),
        }
        sys_prompt = role_desc.get(payload.role, role_desc["red"])
        sys_prompt += (
            f"\n\nObjective: {payload.objective}"
            f"\nTarget: {payload.target}"
        )
        if payload.playbook_context:
            pb_text = "\n".join(
                f"  Step {s.get('order',i+1)}: {s.get('instruction_prompt', s.get('name',''))}"
                for i, s in enumerate(payload.playbook_context)
            )
            sys_prompt += f"\n\nReference Playbook:\n{pb_text}"
        if payload.experience_context:
            exp_text = "\n".join(f"  - {e}" for e in payload.experience_context[:5])
            sys_prompt += f"\n\nPast Experience:\n{exp_text}"
        sys_prompt += (
            "\n\nEach turn, respond ONLY with JSON (no markdown, no explanation):\n"
            '{"action":"what you plan to do","command":"bash command to execute","done":false}\n'
            'When mission is complete: {"action":"done","command":"","done":true,"summary":"results"}\n'
        )

        messages: list[dict] = [{"role": "system", "content": sys_prompt}]
        messages.append({"role": "user", "content": "Begin the mission. What is your first action?"})

        results: list[dict] = []
        mission_start = time.time()

        for step_num in range(1, payload.max_steps + 1):
            elapsed = time.time() - mission_start
            if elapsed > payload.timeout_s:
                results.append({"step": step_num, "action": "timeout",
                                "command": "", "stdout": "", "stderr": "",
                                "exit_code": -1, "duration_s": 0,
                                "llm_reasoning": "Mission timeout"})
                break

            # LLM에게 다음 행동 요청
            raw_resp = _ollama_chat(payload.model, messages, max_tokens=300)
            decision = _parse_llm_json(raw_resp)

            action = decision.get("action", "unknown")
            command = decision.get("command", "")
            done = decision.get("done", False)

            if done or not command:
                results.append({
                    "step": step_num, "action": action,
                    "command": "", "stdout": "", "stderr": "",
                    "exit_code": 0, "duration_s": 0,
                    "llm_reasoning": decision.get("summary", raw_resp[:300]),
                })
                break

            # 명령 실행
            cmd_start = time.time()
            stdout, stderr, exit_code = _run_shell(command, min(30, payload.timeout_s - int(elapsed)))
            cmd_dur = round(time.time() - cmd_start, 3)

            step_result = {
                "step": step_num,
                "action": action,
                "command": command,
                "stdout": stdout[:2000],
                "stderr": stderr[:500],
                "exit_code": exit_code,
                "duration_s": cmd_dur,
                "llm_reasoning": raw_resp[:300],
            }
            results.append(step_result)

            # LLM에게 실행 결과 전달
            messages.append({"role": "assistant", "content": raw_resp})
            messages.append({"role": "user", "content":
                f"Command executed. exit_code={exit_code}\n"
                f"stdout:\n{stdout[:1500]}\n"
                f"stderr:\n{stderr[:300]}\n"
                f"Decide next action."
            })

        total_dur = round(time.time() - mission_start, 2)
        # 마지막 step에서 summary 추출
        summary = ""
        if results and results[-1].get("llm_reasoning"):
            summary = results[-1]["llm_reasoning"]

        return {
            "mission_id": payload.mission_id,
            "role": payload.role,
            "model": payload.model,
            "status": "completed" if any(r.get("action") == "done" for r in results)
                      else ("timeout" if total_dur >= payload.timeout_s else "max_steps"),
            "steps_executed": len(results),
            "total_duration_s": total_dur,
            "results": results,
            "summary": summary,
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
