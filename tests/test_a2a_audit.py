import json

from opsclaw.a2a import MessageType, build_run_script_message, build_status_update_message
from opsclaw.audit import AuditLogger


def test_build_run_script_message() -> None:
    msg = build_run_script_message(task_id="t1", script="echo hi", timeout_seconds=10)
    assert msg.message_type == MessageType.RUN_SCRIPT
    assert msg.payload["script"] == "echo hi"
    assert msg.payload["timeout_seconds"] == 10


def test_build_status_update_message() -> None:
    msg = build_status_update_message(task_id="t1", status="completed", detail="ok")
    assert msg.message_type == MessageType.STATUS_UPDATE
    assert msg.payload["status"] == "completed"


def test_audit_logger_records_event(tmp_path) -> None:
    logger = AuditLogger(log_path=str(tmp_path / "audit.log"))
    event = logger.record(
        actor="manager",
        role="system",
        action="task_completed",
        decision="allow",
        task_id="t1",
        prompt="sensitive prompt",
    )

    assert event["task_id"] == "t1"
    assert event["prompt_hash"]

    line = (tmp_path / "audit.log").read_text(encoding="utf-8").strip()
    saved = json.loads(line)
    assert saved["action"] == "task_completed"
