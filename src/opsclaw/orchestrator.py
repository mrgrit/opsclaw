from __future__ import annotations

from dataclasses import asdict

from .mastergate import MasterGate
from .models import Decision, TaskRequest, TaskResult


class ManagerOrchestrator:
    """MVP manager pipeline: intake -> plan -> todo -> dispatch -> collect -> validate -> report."""

    def __init__(self) -> None:
        self.mastergate = MasterGate()

    def run(self, request: TaskRequest) -> TaskResult:
        execution_log: list[str] = []

        normalized = self._normalize(request)
        execution_log.append("normalize:ok")

        plan = self._plan(normalized)
        execution_log.append("plan:ok")

        todo = self._todo(plan)
        execution_log.append("todo:ok")

        if request.requires_master:
            gate = self.mastergate.evaluate(request.objective)
            execution_log.append(f"mastergate:{gate.decision.value}")
            if gate.decision == Decision.BLOCK:
                return TaskResult(
                    task_id=request.task_id,
                    status="blocked",
                    todo=todo,
                    execution_log=execution_log,
                    validation_passed=False,
                    metadata={"gate_findings": gate.findings},
                )

        dispatch = self._dispatch(todo)
        execution_log.append(dispatch)
        collect = self._collect()
        execution_log.append(collect)

        validation = self._validate(collect)
        execution_log.append(f"validate:{validation}")

        return TaskResult(
            task_id=request.task_id,
            status="completed" if validation else "failed",
            todo=todo,
            execution_log=execution_log,
            validation_passed=validation,
            metadata={"request": asdict(request)},
        )

    def _normalize(self, request: TaskRequest) -> dict[str, object]:
        return {
            "task_id": request.task_id,
            "objective": request.objective.strip(),
            "constraints": request.constraints,
        }

    def _plan(self, normalized: dict[str, object]) -> dict[str, object]:
        return {
            "objective": normalized["objective"],
            "milestones": [
                "prepare",
                "execute",
                "validate",
                "report",
            ],
        }

    def _todo(self, plan: dict[str, object]) -> list[str]:
        milestones = plan.get("milestones", [])
        return [f"[{i + 1}] {name}" for i, name in enumerate(milestones)]

    def _dispatch(self, todo: list[str]) -> str:
        _ = todo
        return "dispatch:subagent-simulated"

    def _collect(self) -> str:
        return "collect:stdout=ok"

    def _validate(self, collect_result: str) -> bool:
        return "ok" in collect_result
