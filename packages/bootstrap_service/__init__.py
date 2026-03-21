import os
from dataclasses import dataclass, field
from typing import Any

_HERE = os.path.dirname(os.path.abspath(__file__))
BOOTSTRAP_SCRIPT_PATH = os.path.join(_HERE, "..", "..", "deploy", "bootstrap", "install.sh")


class BootstrapError(Exception):
    pass


@dataclass
class BootstrapConfig:
    ssh_user: str = "root"
    ssh_pass: str | None = None
    ssh_port: int = 22
    ssh_key_path: str | None = None
    subagent_port: int = 8002
    install_dir: str = "/opt/opsclaw"
    timeout_s: int = 300


def bootstrap_asset(mgmt_ip: str, config: BootstrapConfig | None = None) -> dict[str, Any]:
    cfg = config or BootstrapConfig()

    script_path = os.path.normpath(BOOTSTRAP_SCRIPT_PATH)
    if not os.path.isfile(script_path):
        raise BootstrapError(f"Bootstrap script not found: {script_path}")

    with open(script_path) as f:
        script = f.read()

    try:
        import paramiko  # type: ignore
    except ImportError as exc:
        raise BootstrapError(
            "paramiko is required for bootstrap. Install with: pip install paramiko"
        ) from exc

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs: dict[str, Any] = {
        "hostname": mgmt_ip,
        "port": cfg.ssh_port,
        "username": cfg.ssh_user,
        "timeout": 15,
        "banner_timeout": 15,
        "auth_timeout": 15,
    }
    if cfg.ssh_key_path:
        connect_kwargs["key_filename"] = cfg.ssh_key_path
    elif cfg.ssh_pass:
        connect_kwargs["password"] = cfg.ssh_pass
        connect_kwargs["look_for_keys"] = False
        connect_kwargs["allow_agent"] = False

    try:
        client.connect(**connect_kwargs)
    except Exception as exc:
        raise BootstrapError(f"SSH connection failed to {mgmt_ip}:{cfg.ssh_port} — {exc}") from exc

    # 환경변수 export 후 스크립트 실행 (sudo -E로 env 유지)
    env_prefix = (
        f"export OPSCLAW_SUBAGENT_PORT={cfg.subagent_port} "
        f"OPSCLAW_INSTALL_DIR={cfg.install_dir}; "
    )
    remote_cmd = f"{env_prefix}sudo -E bash -s"

    try:
        stdin, stdout, stderr = client.exec_command(remote_cmd, timeout=cfg.timeout_s)
        stdin.write(script)
        stdin.channel.shutdown_write()

        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        exit_code = stdout.channel.recv_exit_status()

        return {
            "status": "ok" if exit_code == 0 else "error",
            "exit_code": exit_code,
            "stdout": out,
            "stderr": err,
        }
    except Exception as exc:
        raise BootstrapError(f"Remote command failed: {exc}") from exc
    finally:
        client.close()
