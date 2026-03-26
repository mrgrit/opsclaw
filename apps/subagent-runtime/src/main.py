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

    # ── 로컬 지식 관리 ──────────────────────────────────────────────────────────
    import os as _os
    _KNOWLEDGE_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "..", "data", "local_knowledge")

    def _load_local_knowledge(server_hint: str = "") -> dict:
        """로컬 지식 파일 로드. server_hint 또는 hostname 기반."""
        import socket
        hostname = server_hint or socket.gethostname()
        for name in [hostname, hostname.split(".")[0]]:
            path = _os.path.join(_KNOWLEDGE_DIR, f"{name}.json")
            if _os.path.exists(path):
                try:
                    with open(path) as f:
                        return _json.load(f)
                except Exception:
                    pass
        return {}

    def _save_mission_learnings(server: str, mission_results: list[dict], role: str):
        """미션 성공 결과를 로컬 지식에 자동 추가."""
        knowledge = _load_local_knowledge(server)
        if not knowledge:
            knowledge = {"server": server, "role": role, "experiences": [], "tools": {}}
        existing_exp = knowledge.get("experiences", [])
        for r in mission_results:
            if r.get("exit_code") == 0 and r.get("command"):
                entry = f"[auto] {r.get('action','')}: {r['command'][:120]}"
                if entry not in existing_exp:
                    existing_exp.append(entry)
        knowledge["experiences"] = existing_exp[-30:]  # 최근 30건 유지
        knowledge["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        path = _os.path.join(_KNOWLEDGE_DIR, f"{server}.json")
        _os.makedirs(_os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w") as f:
                _json.dump(knowledge, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _knowledge_to_prompt(knowledge: dict) -> str:
        """로컬 지식을 시스템 프롬프트 텍스트로 변환."""
        if not knowledge:
            return ""
        parts = [f"\n\n=== Local Knowledge ({knowledge.get('server','unknown')}) ==="]
        tools = knowledge.get("tools", {})
        if tools:
            parts.append("Available tools/paths:")
            for k, v in list(tools.items())[:15]:
                parts.append(f"  {k}: {v}")
        exps = knowledge.get("experiences", [])
        if exps:
            parts.append("Past experiences on this server:")
            for e in exps[-10:]:
                parts.append(f"  - {e}")
        templates = knowledge.get("rule_templates", {})
        if templates:
            parts.append(f"Rule templates available: {', '.join(templates.keys())} (use local_rules.xml to deploy)")
        net = knowledge.get("network_map", {})
        if net:
            parts.append("Network map:")
            for k, v in net.items():
                parts.append(f"  {k}: {v.get('ip','')} [{', '.join(v.get('services',[]))}]")
        return "\n".join(parts)

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
        # 로컬 지식 로드 (서버별 축적된 경험)
        server_hint = "opsclaw"  # 기본값
        if "siem" in payload.objective.lower() or payload.role == "blue":
            server_hint = "siem"
        elif "web" in payload.target.lower() or "10.20.30.80" in payload.target:
            server_hint = "web"
        elif "secu" in payload.target.lower() or "10.20.30.1" in payload.target:
            server_hint = "secu"
        local_knowledge = _load_local_knowledge(server_hint)
        knowledge_prompt = _knowledge_to_prompt(local_knowledge)

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
                "IMPORTANT: You are running on the opsclaw control server, NOT on the SIEM server. "
                "ALL commands must be executed via SSH to the target server. "
                "ALWAYS prefix commands with: sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 '<command>' "
                "For sudo: sshpass -p1 ssh -o StrictHostKeyChecking=no siem@10.20.30.100 'echo 1 | sudo -S <command>' "
                "NEVER run Wazuh commands locally — they will fail."
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
        # 로컬 지식 주입
        if knowledge_prompt:
            sys_prompt += knowledge_prompt

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

        # 미션 결과를 로컬 지식에 자동 저장
        _save_mission_learnings(server_hint, results, payload.role)

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

    # ── 자율 탐색: 서버 환경 파악 + baseline 설정 ─────────────────────────────
    class ExploreRequest(BaseModel):
        server_name: str = ""
        model: str = "gemma3:12b"
        ssh_target: str = ""          # "siem@10.20.30.100" — 비어있으면 로컬
        ssh_password: str = "1"
        timeout_s: int = 60

    @router.post("/explore")
    def explore_server(payload: ExploreRequest) -> dict[str, Any]:
        """서버 환경을 자동 파악하고 watch_targets + baseline을 local_knowledge에 저장."""
        import socket
        server = payload.server_name or socket.gethostname()
        ssh_pre = ""
        if payload.ssh_target:
            ssh_pre = f"sshpass -p{payload.ssh_password} ssh -o StrictHostKeyChecking=no {payload.ssh_target} "

        # 탐색 명령 목록
        probes = [
            ("hostname", f"{ssh_pre}'hostname' 2>/dev/null" if ssh_pre else "hostname"),
            ("uptime", f"{ssh_pre}'uptime' 2>/dev/null" if ssh_pre else "uptime"),
            ("os", f"{ssh_pre}'cat /etc/os-release | head -3' 2>/dev/null" if ssh_pre else "cat /etc/os-release | head -3"),
            ("disk", f"{ssh_pre}'df -h / | tail -1' 2>/dev/null" if ssh_pre else "df -h / | tail -1"),
            ("memory", f"{ssh_pre}'free -m | head -2' 2>/dev/null" if ssh_pre else "free -m | head -2"),
            ("services", f"{ssh_pre}'systemctl list-units --type=service --state=running --no-pager | head -20' 2>/dev/null" if ssh_pre else "systemctl list-units --type=service --state=running --no-pager | head -20"),
            ("ports", f"{ssh_pre}'ss -tlnp 2>/dev/null | head -20' 2>/dev/null" if ssh_pre else "ss -tlnp 2>/dev/null | head -20"),
            ("processes", f"{ssh_pre}'ps aux --sort=-rss 2>/dev/null | head -10' 2>/dev/null" if ssh_pre else "ps aux --sort=-rss 2>/dev/null | head -10"),
            ("crontab", f"{ssh_pre}'crontab -l 2>/dev/null || echo none' 2>/dev/null" if ssh_pre else "crontab -l 2>/dev/null || echo none"),
            ("security_logs", f"{ssh_pre}'echo {payload.ssh_password} | sudo -S tail -5 /var/log/auth.log 2>/dev/null || echo none' 2>/dev/null" if ssh_pre else "tail -5 /var/log/auth.log 2>/dev/null || echo none"),
        ]

        results = {}
        for name, cmd in probes:
            stdout, stderr, ec = _run_shell(cmd, 15)
            results[name] = stdout.strip()[:500] if ec == 0 else f"error: {stderr.strip()[:100]}"

        # LLM에게 분석 요청: 감시 대상 + baseline 결정
        probe_text = "\n".join(f"[{k}]\n{v}" for k, v in results.items())
        llm_prompt = (
            f"You are a security-focused sysadmin. Analyze this server ({server}) and determine:\n"
            f"1. What are the critical services to monitor?\n"
            f"2. What files/logs should be watched for security events?\n"
            f"3. What are the normal baseline values (CPU, memory, disk)?\n"
            f"4. What security risks do you see?\n\n"
            f"Server probe results:\n{probe_text}\n\n"
            f"Respond ONLY with JSON:\n"
            f'{{"watch_targets":[{{"name":"...","command":"...","interval_s":60,"alert_pattern":"..."}}],'
            f'"baseline":{{"disk_pct":..,"mem_pct":..,"services_count":..}},'
            f'"security_risks":["..."],'
            f'"summary":"..."}}'
        )
        raw = _ollama_chat(payload.model, [
            {"role": "system", "content": "You are a security-focused system administrator. Respond only with valid JSON."},
            {"role": "user", "content": llm_prompt}
        ], max_tokens=800)
        analysis = _parse_llm_json(raw)

        # local_knowledge 업데이트
        knowledge = _load_local_knowledge(server)
        if not knowledge:
            knowledge = {"server": server, "role": "auto-explored", "tools": {}, "experiences": []}
        knowledge["explore_results"] = results
        knowledge["watch_targets"] = analysis.get("watch_targets", [])
        knowledge["baseline"] = analysis.get("baseline", {})
        knowledge["security_risks"] = analysis.get("security_risks", [])
        knowledge["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if payload.ssh_target:
            knowledge["ssh_target"] = payload.ssh_target
            knowledge["ssh_password"] = payload.ssh_password

        path = _os.path.join(_KNOWLEDGE_DIR, f"{server}.json")
        _os.makedirs(_os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            _json.dump(knowledge, f, ensure_ascii=False, indent=2)

        return {
            "server": server,
            "status": "explored",
            "probe_results": {k: v[:200] for k, v in results.items()},
            "watch_targets": analysis.get("watch_targets", []),
            "baseline": analysis.get("baseline", {}),
            "security_risks": analysis.get("security_risks", []),
            "summary": analysis.get("summary", ""),
        }

    # ── Agent Daemon: 상시 자율 감시 ─────────────────────────────────────────
    _active_daemons: dict[str, dict] = {}

    class DaemonRequest(BaseModel):
        daemon_id: str = ""
        server_name: str = ""
        model: str = "gemma3:12b"
        ssh_target: str = ""
        ssh_password: str = "1"
        callback_url: str = ""        # Manager callback for VWR
        max_cycles: int = 50          # 최대 순환 수 (테스트용, 0=무한)
        base_interval_s: int = 30     # 기본 감시 주기

    class DaemonStopRequest(BaseModel):
        daemon_id: str

    @router.post("/daemon")
    def start_daemon(payload: DaemonRequest) -> dict[str, Any]:
        """Agent Daemon 시작: explore 결과 기반 상시 자율 감시."""
        import socket, uuid
        daemon_id = payload.daemon_id or f"daemon-{uuid.uuid4().hex[:8]}"
        server = payload.server_name or socket.gethostname()

        if daemon_id in _active_daemons:
            return {"status": "already_running", "daemon_id": daemon_id}

        knowledge = _load_local_knowledge(server)
        if not knowledge.get("watch_targets"):
            return {"status": "error", "message": "No watch_targets. Run /a2a/explore first."}

        _active_daemons[daemon_id] = {"status": "running", "server": server, "cycles": 0, "events": []}

        import threading
        thread = threading.Thread(
            target=_daemon_loop,
            args=(daemon_id, server, payload),
            daemon=True
        )
        thread.start()

        return {"status": "started", "daemon_id": daemon_id, "server": server,
                "watch_targets": len(knowledge.get("watch_targets", []))}

    @router.post("/daemon/stop")
    def stop_daemon(payload: DaemonStopRequest) -> dict[str, Any]:
        """Agent Daemon 중지."""
        if payload.daemon_id in _active_daemons:
            _active_daemons[payload.daemon_id]["status"] = "stopping"
            return {"status": "stopping", "daemon_id": payload.daemon_id}
        return {"status": "not_found", "daemon_id": payload.daemon_id}

    @router.get("/daemon/status")
    def daemon_status() -> dict[str, Any]:
        """모든 Daemon 상태 조회."""
        return {"daemons": {k: {"status": v["status"], "server": v["server"],
                                "cycles": v["cycles"], "events": len(v["events"])}
                            for k, v in _active_daemons.items()}}

    def _daemon_loop(daemon_id: str, server: str, payload: DaemonRequest):
        """OBSERVE → THINK → ACT → REPORT → IMPROVE 루프."""
        ssh_pre = ""
        if payload.ssh_target:
            ssh_pre = f"sshpass -p{payload.ssh_password} ssh -o StrictHostKeyChecking=no {payload.ssh_target} "

        cycle = 0
        while _active_daemons.get(daemon_id, {}).get("status") == "running":
            cycle += 1
            if payload.max_cycles > 0 and cycle > payload.max_cycles:
                break

            knowledge = _load_local_knowledge(server)
            watch_targets = knowledge.get("watch_targets", [])
            interval = payload.base_interval_s
            events_this_cycle = []

            for target in watch_targets:
                cmd = target.get("command", "")
                if not cmd:
                    continue
                if ssh_pre and not cmd.startswith("sshpass"):
                    cmd = f"{ssh_pre}'{cmd}'"

                # OBSERVE
                stdout, stderr, ec = _run_shell(cmd, 15)
                output = stdout.strip()

                # 패턴 매칭 (빠른 체크 — LLM 호출 없이)
                alert_pattern = target.get("alert_pattern", "")
                severity = "normal"
                if alert_pattern and alert_pattern.lower() in output.lower():
                    severity = "investigate"
                elif ec != 0:
                    severity = "investigate"

                if severity == "normal":
                    continue

                # THINK — LLM 판단 (이상 감지 시에만)
                think_prompt = (
                    f"Server: {server}, Monitor: {target.get('name','')}\n"
                    f"Output:\n{output[:1000]}\n\n"
                    f"Is this a security issue? Respond JSON:\n"
                    f'{{"severity":"normal|warning|critical","action":"description",'
                    f'"command":"remediation command or empty","report":"brief summary"}}'
                )
                raw = _ollama_chat(payload.model, [
                    {"role": "system", "content": "You are a security analyst. Assess if this output indicates a security issue. Respond only JSON."},
                    {"role": "user", "content": think_prompt}
                ], max_tokens=200)
                decision = _parse_llm_json(raw)

                event = {
                    "cycle": cycle,
                    "target": target.get("name", ""),
                    "severity": decision.get("severity", "unknown"),
                    "action": decision.get("action", ""),
                    "report": decision.get("report", ""),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }

                # ACT — 자율 조치 (critical/warning 시)
                remediation_cmd = decision.get("command", "")
                if remediation_cmd and decision.get("severity") in ("warning", "critical"):
                    if ssh_pre and not remediation_cmd.startswith("sshpass"):
                        remediation_cmd = f"{ssh_pre}'{remediation_cmd}'"
                    act_stdout, act_stderr, act_ec = _run_shell(remediation_cmd, 15)
                    event["remediation"] = {
                        "command": remediation_cmd[:200],
                        "stdout": act_stdout[:500],
                        "exit_code": act_ec,
                    }

                events_this_cycle.append(event)

                # REPORT — Manager 콜백
                if payload.callback_url and decision.get("severity") in ("warning", "critical"):
                    try:
                        httpx.post(payload.callback_url, json={
                            "daemon_id": daemon_id, "server": server, "event": event
                        }, timeout=5.0)
                    except Exception:
                        pass

                # 적응적 주기
                if decision.get("severity") == "critical":
                    interval = min(interval, 5)
                elif decision.get("severity") == "warning":
                    interval = min(interval, 15)

            # IMPROVE — 이벤트 기록
            if events_this_cycle:
                _active_daemons[daemon_id]["events"].extend(events_this_cycle)
                # local_knowledge에 이벤트 저장
                knowledge = _load_local_knowledge(server)
                daemon_log = knowledge.get("daemon_events", [])
                daemon_log.extend(events_this_cycle)
                knowledge["daemon_events"] = daemon_log[-50:]  # 최근 50건
                knowledge["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                path = _os.path.join(_KNOWLEDGE_DIR, f"{server}.json")
                try:
                    with open(path, "w") as f:
                        _json.dump(knowledge, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass

            _active_daemons[daemon_id]["cycles"] = cycle
            time.sleep(interval)

        _active_daemons[daemon_id]["status"] = "stopped"

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
