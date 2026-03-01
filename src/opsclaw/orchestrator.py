from __future__ import annotations

from dataclasses import asdict

from .mastergate import MasterGate
from .models import Decision, TaskRequest, TaskResult
from .state_store import JsonStateStore
from .subagent import SubAgentExecutor


class ManagerOrchestrator:
    """MVP manager pipeline: intake -> plan -> todo -> dispatch -> collect -> validate -> report."""

    def __init__(
        self,
        subagent: SubAgentExecutor | None = None,
        state_store: JsonStateStore | None = None,
    ) -> None:
        self.mastergate = MasterGate()
        self.subagent = subagent or SubAgentExecutor()
        self.state_store = state_store or JsonStateStore()

    def run(self, request: TaskRequest) -> TaskResult:
        execution_log: list[str] = []

        normalized = self._normalize(request)
        execution_log.append("normalize:ok")

        plan = self._plan(normalized)
        execution_log.append("plan:ok")

        todo = self._todo(plan)
        execution_log.append("todo:ok")

        master_prompt = request.objective
        if request.requires_master:
            gate = self.mastergate.evaluate(request.objective)
            execution_log.append(f"mastergate:{gate.decision.value}")
            if gate.decision == Decision.BLOCK:
                blocked = TaskResult(
                    task_id=request.task_id,
                    status="blocked",
                    todo=todo,
                    execution_log=execution_log,
                    validation_passed=False,
                    metadata={"gate_findings": gate.findings},
                )
                path = self.state_store.save(blocked)
                blocked.metadata["state_path"] = str(path)
                return blocked
            master_prompt = gate.transformed_prompt

        dispatch_script = self._dispatch_script(todo, master_prompt)
        execution_log.append("dispatch:subagent")

        collect = self._collect(dispatch_script)
        execution_log.append(f"collect:exit={collect.exit_code}")

        validation = self._validate(collect.exit_code)
        execution_log.append(f"validate:{validation}")

        result = TaskResult(
            task_id=request.task_id,
            status="completed" if validation else "failed",
            todo=todo,
            execution_log=execution_log,
            validation_passed=validation,
            metadata={
                "request": asdict(request),
                "stdout": collect.stdout,
                "stderr": collect.stderr,
            },
        )
        path = self.state_store.save(result)
        result.metadata["state_path"] = str(path)
        return result

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

    def _dispatch_script(self, todo: list[str], objective: str) -> str:
        _ = todo
        safe_objective = objective.replace('"', "'")
        return f'echo "opsclaw_run:{safe_objective}"'

    def _collect(self, script: str):
        return self.subagent.run_script(script)

    def _validate(self, exit_code: int) -> bool:
        return exit_code == 0
