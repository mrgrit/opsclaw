from opsclaw.models import TaskRequest
from opsclaw.orchestrator import ManagerOrchestrator


def test_orchestrator_completes_without_master() -> None:
    orchestrator = ManagerOrchestrator()
    result = orchestrator.run(TaskRequest(task_id="t1", objective="deploy nginx"))

    assert result.status == "completed"
    assert result.validation_passed is True
    assert any(log.startswith("dispatch") for log in result.execution_log)


def test_orchestrator_blocks_sensitive_master_prompt() -> None:
    orchestrator = ManagerOrchestrator()
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
