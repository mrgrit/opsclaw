from __future__ import annotations

from dataclasses import asdict

from .a2a import build_run_script_message, build_status_update_message
from .audit import AuditLogger
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
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.mastergate = MasterGate()
        self.subagent = subagent or SubAgentExecutor()
        self.state_store = state_store or JsonStateStore()
        self.audit_logger = audit_logger or AuditLogger()

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
            self.audit_logger.record(
                actor="manager",
                role="system",
                action="mastergate_evaluate",
                decision=gate.decision.value,
                task_id=request.task_id,
                prompt=request.objective,
                details={"findings": gate.findings},
            )
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
                blocked.metadata["status_message"] = asdict(
                    build_status_update_message(
                        task_id=request.task_id,
                        status="blocked",
                        detail="mastergate blocked external call",
                    )
                )
                self.audit_logger.record(
                    actor="manager",
                    role="system",
                    action="task_blocked",
                    decision="block",
                    task_id=request.task_id,
                    details={"reason": "mastergate"},
                )
                return blocked
            master_prompt = gate.transformed_prompt

        dispatch_script = self._dispatch_script(todo, master_prompt)
        run_msg = build_run_script_message(
            task_id=request.task_id,
            script=dispatch_script,
            timeout_seconds=self.subagent.timeout_seconds,
        )
        execution_log.append("dispatch:subagent")

        collect = self._collect(dispatch_script)
        execution_log.append(f"collect:exit={collect.exit_code}")

        validation = self._validate(collect.exit_code)
        execution_log.append(f"validate:{validation}")

        status = "completed" if validation else "failed"
        status_msg = build_status_update_message(
            task_id=request.task_id,
            status=status,
            detail=f"subagent_exit={collect.exit_code}",
        )

        result = TaskResult(
            task_id=request.task_id,
            status=status,
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
                "a2a_run_script": asdict(run_msg),
                "a2a_status_update": asdict(status_msg),
            },
        )
        path = self.state_store.save(result)
        result.metadata["state_path"] = str(path)

        self.audit_logger.record(
            actor="manager",
            role="system",
            action="task_completed" if validation else "task_failed",
            decision="allow" if validation else "block",
            task_id=request.task_id,
            details={"exit_code": collect.exit_code},
        )

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
