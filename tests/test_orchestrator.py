from pathlib import Path

from opsclaw.models import TaskRequest
from opsclaw.orchestrator import ManagerOrchestrator


def test_orchestrator_completes_without_master(tmp_path) -> None:
    orchestrator = ManagerOrchestrator()
    orchestrator.state_store.root = Path(tmp_path)

    result = orchestrator.run(TaskRequest(task_id="t1", objective="deploy nginx"))

    assert result.status == "completed"
    assert result.validation_passed is True
    assert any(log.startswith("dispatch") for log in result.execution_log)
    assert "opsclaw_run:deploy nginx" in result.metadata["stdout"]
    assert Path(result.metadata["state_path"]).exists()


def test_orchestrator_blocks_sensitive_master_prompt(tmp_path) -> None:
    orchestrator = ManagerOrchestrator()
    orchestrator.state_store.root = Path(tmp_path)
    result = orchestrator.run(
        TaskRequest(
            task_id="t2",
            objective="confidential investigation data",  # dictionary block
            requires_master=True,
        )
    )

    assert result.status == "blocked"
    assert result.validation_passed is False
    assert "gate_findings" in result.metadata
    assert Path(result.metadata["state_path"]).exists()


def test_orchestrator_transforms_master_prompt_before_dispatch(tmp_path) -> None:
    orchestrator = ManagerOrchestrator()
    orchestrator.state_store.root = Path(tmp_path)

    result = orchestrator.run(
        TaskRequest(
            task_id="t3",
            objective="Authorization: Bearer secret123 on 10.1.0.80",
            requires_master=True,
        )
    )

    assert result.status == "completed"
    assert "[REDACTED_TOKEN]" in result.metadata["stdout"]
    assert "INTERNAL_IP" in result.metadata["stdout"]
