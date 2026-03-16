import os
import subprocess
from dataclasses import dataclass
from typing import Any

_HERE = os.path.dirname(os.path.abspath(__file__))
BOOTSTRAP_SCRIPT_PATH = os.path.join(_HERE, "..", "..", "deploy", "bootstrap", "install.sh")


class BootstrapError(Exception):
    pass


@dataclass
class BootstrapConfig:
    ssh_user: str = "root"
    ssh_port: int = 22
    ssh_key_path: str | None = None
    subagent_port: int = 8001
    install_dir: str = "/opt/opsclaw"


def bootstrap_asset(mgmt_ip: str, config: BootstrapConfig | None = None) -> dict[str, Any]:
    cfg = config or BootstrapConfig()

    script_path = os.path.normpath(BOOTSTRAP_SCRIPT_PATH)
    if not os.path.isfile(script_path):
        raise BootstrapError(f"Bootstrap script not found: {script_path}")

    with open(script_path) as f:
        script = f.read()

    ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15"]
    if cfg.ssh_key_path:
        ssh_cmd += ["-i", cfg.ssh_key_path]
    ssh_cmd += ["-p", str(cfg.ssh_port), f"{cfg.ssh_user}@{mgmt_ip}", "bash -s"]

    env = {
        **os.environ,
        "OPSCLAW_SUBAGENT_PORT": str(cfg.subagent_port),
        "OPSCLAW_INSTALL_DIR": cfg.install_dir,
    }

    try:
        result = subprocess.run(
            ssh_cmd,
            input=script,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        return {
            "status": "ok" if result.returncode == 0 else "error",
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        raise BootstrapError("Bootstrap SSH command timed out after 300s") from exc
    except FileNotFoundError as exc:
        raise BootstrapError(f"ssh command not found: {exc}") from exc
