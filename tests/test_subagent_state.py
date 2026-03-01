import json

from opsclaw.models import TaskResult
from opsclaw.state_store import JsonStateStore
from opsclaw.subagent import SubAgentExecutor


def test_subagent_executor_runs_script() -> None:
    executor = SubAgentExecutor(timeout_seconds=5)
    result = executor.run_script("echo hello")

    assert result.exit_code == 0
    assert result.stdout == "hello"
    assert result.stderr == ""


def test_subagent_blocks_dangerous_command() -> None:
    executor = SubAgentExecutor(timeout_seconds=5)
    result = executor.run_script("rm -rf /tmp/demo")

    assert result.exit_code == 126
    assert "guardrail:block dangerous command" in result.stderr


def test_subagent_blocks_sensitive_path_write_without_approval() -> None:
    executor = SubAgentExecutor(timeout_seconds=5, approval_mode=False)
    result = executor.run_script("sed -i 's/a/b/' /etc/hosts")

    assert result.exit_code == 126
    assert "sensitive path write requires approval mode" in result.stderr


def test_subagent_allows_sensitive_path_write_with_approval() -> None:
    executor = SubAgentExecutor(timeout_seconds=5, approval_mode=True)
    result = executor.run_script("echo ok")

    assert result.exit_code == 0


def test_json_state_store_saves_result(tmp_path) -> None:
    store = JsonStateStore(root_dir=str(tmp_path))
    task_result = TaskResult(
        task_id="state-1",
        status="completed",
        todo=["[1] prepare"],
        execution_log=["normalize:ok"],
        validation_passed=True,
    )

    path = store.save(task_result)
    assert path.exists()

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["task_id"] == "state-1"
    assert saved["status"] == "completed"
