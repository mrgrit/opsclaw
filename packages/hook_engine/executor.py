"""Hook 실행기 — 이벤트 발생 시 등록된 Hook들을 실행한다."""

import json
import subprocess
import time
from typing import Any

import httpx

from packages.hook_engine.events import BLOCKING_EVENTS
from packages.hook_engine.models import HookInput, HookResponse
from packages.hook_engine.registry import get_hooks_for_event


def fire_event(event_input: HookInput) -> list[HookResponse]:
    """이벤트를 발생시키고 등록된 모든 Hook을 실행한다.

    Args:
        event_input: 이벤트 데이터

    Returns:
        각 Hook의 실행 결과 리스트.
        pre_* 이벤트에서 can_block Hook이 continue_=False를 반환하면
        이후 Hook은 실행되지 않는다.
    """
    hooks = get_hooks_for_event(event_input.event)
    if not hooks:
        return []

    results: list[HookResponse] = []
    is_blocking_event = event_input.event in BLOCKING_EVENTS
    payload = _build_payload(event_input)

    for hook in hooks:
        # 조건 체크
        if hook.get("condition") and not _eval_condition(hook["condition"], payload):
            continue

        t0 = time.time()
        try:
            resp = _execute_hook(hook, payload)
        except Exception as exc:
            resp = HookResponse(
                hook_id=hook["id"],
                hook_name=hook.get("name", ""),
                event=event_input.event,
                success=False,
                reason=f"Hook execution error: {exc}",
            )
        resp.duration_ms = int((time.time() - t0) * 1000)
        results.append(resp)

        # blocking 이벤트에서 차단 결정 시 즉시 중단
        if is_blocking_event and hook.get("can_block") and not resp.continue_:
            break

    return results


def _build_payload(event_input: HookInput) -> dict[str, Any]:
    """HookInput을 JSON 직렬화 가능한 dict로 변환."""
    d: dict[str, Any] = {
        "event": event_input.event,
        "project_id": event_input.project_id,
        "context": event_input.context,
    }
    # None이 아닌 필드만 포함
    for field in ("command", "risk_level", "exit_code", "stdout", "stderr",
                  "step_order", "step_name", "severity", "agent_id"):
        val = getattr(event_input, field, None)
        if val is not None:
            d[field] = val
    # stdout/stderr 크기 제한
    if d.get("stdout"):
        d["stdout"] = d["stdout"][:4096]
    if d.get("stderr"):
        d["stderr"] = d["stderr"][:2048]
    return d


def _eval_condition(condition: str, payload: dict) -> bool:
    """안전한 조건 평가. payload의 키를 변수로 사용 가능.

    예: "risk_level == 'critical'" or "exit_code != 0"
    """
    try:
        # 안전한 builtins만 허용
        safe_builtins = {"True": True, "False": False, "None": None}
        return bool(eval(condition, {"__builtins__": safe_builtins}, payload))
    except Exception:
        return False  # 조건 평가 실패 → Hook 건너뜀


def _execute_hook(hook: dict, payload: dict) -> HookResponse:
    """Hook 유형에 따라 실행."""
    hook_type = hook["hook_type"]
    hook_id = hook["id"]
    hook_name = hook.get("name", "")
    timeout_s = hook.get("timeout_s", 15)
    event = payload["event"]

    if hook_type == "webhook":
        return _exec_webhook(hook_id, hook_name, event, hook["target"], payload, timeout_s)
    elif hook_type == "script":
        return _exec_script(hook_id, hook_name, event, hook["target"], payload, timeout_s)
    elif hook_type == "notification":
        return _exec_notification(hook_id, hook_name, event, hook["target"], payload)
    else:
        return HookResponse(
            hook_id=hook_id, hook_name=hook_name, event=event,
            success=False, reason=f"Unknown hook_type: {hook_type}",
        )


def _exec_webhook(
    hook_id: str, hook_name: str, event: str,
    url: str, payload: dict, timeout_s: int,
) -> HookResponse:
    """HTTP POST webhook 실행."""
    try:
        resp = httpx.post(url, json=payload, timeout=timeout_s)
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        return HookResponse(
            hook_id=hook_id, hook_name=hook_name, event=event,
            success=resp.is_success,
            continue_=data.get("continue", True),
            reason=data.get("reason", ""),
            modified_input=data.get("modified_input"),
            response_data=data,
        )
    except httpx.TimeoutException:
        return HookResponse(
            hook_id=hook_id, hook_name=hook_name, event=event,
            success=False, reason=f"Webhook timeout after {timeout_s}s: {url}",
        )
    except Exception as exc:
        return HookResponse(
            hook_id=hook_id, hook_name=hook_name, event=event,
            success=False, reason=f"Webhook error: {exc}",
        )


def _exec_script(
    hook_id: str, hook_name: str, event: str,
    script_path: str, payload: dict, timeout_s: int,
) -> HookResponse:
    """로컬 스크립트 실행. stdin으로 payload JSON 전달."""
    try:
        result = subprocess.run(
            [script_path],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        # stdout이 JSON이면 파싱
        data: dict = {}
        if result.stdout.strip():
            try:
                data = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                pass

        return HookResponse(
            hook_id=hook_id, hook_name=hook_name, event=event,
            success=result.returncode == 0,
            continue_=data.get("continue", True),
            reason=data.get("reason", result.stderr[:500] if result.returncode != 0 else ""),
            modified_input=data.get("modified_input"),
            response_data=data,
        )
    except subprocess.TimeoutExpired:
        return HookResponse(
            hook_id=hook_id, hook_name=hook_name, event=event,
            success=False, reason=f"Script timeout after {timeout_s}s",
        )
    except Exception as exc:
        return HookResponse(
            hook_id=hook_id, hook_name=hook_name, event=event,
            success=False, reason=f"Script error: {exc}",
        )


def _exec_notification(
    hook_id: str, hook_name: str, event: str,
    channel_id: str, payload: dict,
) -> HookResponse:
    """notification_service를 통한 알림 발행. 차단 불가."""
    try:
        from packages.notification_service import fire_event as notify_fire
        notify_fire(event, payload)
        return HookResponse(
            hook_id=hook_id, hook_name=hook_name, event=event,
            success=True,
        )
    except Exception as exc:
        return HookResponse(
            hook_id=hook_id, hook_name=hook_name, event=event,
            success=False, reason=f"Notification error: {exc}",
        )
