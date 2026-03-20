"""Adapter layer exposing pi runtime to OpsClaw services.

* `PiSession` – thin wrapper for creating / destroying pi sessions.
* `ToolBridge` – execute OpsClaw tool calls as subprocess commands.
* `ModelProfile` – configuration for Master / Manager / SubAgent models.
"""

import subprocess


class PiSession:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.session = None

    def start(self):
        self.session = f"pi-session-{self.model_name}"
        return self.session

    def close(self):
        self.session = None


class ToolBridge:
    def __init__(self, session: PiSession):
        self.session = session

    def run_tool(
        self,
        tool_name: str,
        args: list[str] | None = None,
        timeout_s: int = 120,
        cwd: str | None = None,
    ) -> dict:
        """
        tool_name과 args를 subprocess로 실행하고 결과를 반환한다.

        예:
          run_tool("nmap", args=["-sV", "192.168.0.1"])
          run_tool("curl", args=["-s", "https://example.com"])
          run_tool("df", args=["-h"])
        """
        command = [tool_name] + (args or [])

        try:
            completed = subprocess.run(
                command,
                text=True,
                capture_output=True,
                timeout=timeout_s,
                cwd=cwd,
            )
            return {
                "tool": tool_name,
                "args": args or [],
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "exit_code": completed.returncode,
            }
        except FileNotFoundError:
            return {
                "tool": tool_name,
                "args": args or [],
                "stdout": "",
                "stderr": f"tool not found: {tool_name}",
                "exit_code": 127,
            }
        except subprocess.TimeoutExpired:
            return {
                "tool": tool_name,
                "args": args or [],
                "stdout": "",
                "stderr": f"timeout after {timeout_s}s",
                "exit_code": 124,
            }
