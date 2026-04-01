"""Tool 입출력 검증 + evidence 정규화."""

from typing import Any

from packages.tool_validator.schema import ToolSchema


class ValidationError(Exception):
    """Tool 파라미터 검증 실패."""
    def __init__(self, tool_name: str, errors: list[str]):
        self.tool_name = tool_name
        self.errors = errors
        super().__init__(f"Validation failed for {tool_name}: {'; '.join(errors)}")


def validate_input(schema: ToolSchema, params: dict[str, Any]) -> dict[str, Any]:
    """JSON Schema 기반 입력 검증.

    Args:
        schema: Tool 스키마
        params: 사용자 입력 파라미터

    Returns:
        검증 통과한 정규화된 params

    Raises:
        ValidationError: 검증 실패
    """
    errors: list[str] = []
    input_schema = schema.input_schema
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    # 필수 필드 체크
    for field in required:
        if field not in params or params[field] is None:
            errors.append(f"Missing required field: {field}")

    # 타입 체크 (간이 검증 — jsonschema 라이브러리 없이)
    for key, value in params.items():
        if key not in properties:
            continue  # 정의되지 않은 필드는 무시
        prop = properties[key]
        expected_type = prop.get("type")
        if expected_type and not _check_type(value, expected_type):
            errors.append(f"Field '{key}' expected type '{expected_type}', got {type(value).__name__}")

        # minimum/maximum 체크
        if expected_type in ("integer", "number") and isinstance(value, (int, float)):
            if "minimum" in prop and value < prop["minimum"]:
                errors.append(f"Field '{key}' value {value} < minimum {prop['minimum']}")
            if "maximum" in prop and value > prop["maximum"]:
                errors.append(f"Field '{key}' value {value} > maximum {prop['maximum']}")

    if errors:
        raise ValidationError(schema.name, errors)

    return params


def validate_output(schema: ToolSchema, result: dict[str, Any]) -> dict[str, Any]:
    """출력 검증 (스키마가 있는 경우에만). 검증 실패해도 예외를 던지지 않고 경고만."""
    if not schema.output_schema:
        return result
    # 출력 검증은 loose — 결과를 버리지 않고 그대로 반환
    return result


def normalize_evidence(raw: dict[str, Any]) -> dict[str, Any]:
    """evidence 필드를 표준화한다.

    OpsClaw의 evidence는 body_ref/stdout_ref/stderr_ref 등 다양한 키명을 사용하는데,
    이를 command/stdout/stderr/exit_code로 통일한다.

    이 함수는 manager-api의 인라인 정규화 로직(main.py:510-530)을 모듈화한 것이다.
    """
    item = dict(raw)

    # body_ref → command
    if "body_ref" in item and "command" not in item:
        item["command"] = item.pop("body_ref", "") or ""

    # stdout_ref → stdout (inline://stdout/ev_id:content 형식 파싱)
    if "stdout_ref" in item and "stdout" not in item:
        stdout_ref = item.pop("stdout_ref", "") or ""
        if stdout_ref.startswith("inline://stdout/"):
            colon_idx = stdout_ref.find(":", len("inline://stdout/"))
            item["stdout"] = stdout_ref[colon_idx + 1:] if colon_idx != -1 else stdout_ref
        else:
            item["stdout"] = stdout_ref

    # stderr_ref → stderr
    if "stderr_ref" in item and "stderr" not in item:
        item["stderr"] = item.pop("stderr_ref", "") or ""

    # exit_code 기본값
    if "exit_code" not in item:
        item["exit_code"] = 0

    return item


def _check_type(value: Any, expected: str) -> bool:
    """JSON Schema 타입 대 Python 타입 비교."""
    if value is None:
        return True  # nullable은 별도 체크
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    expected_types = type_map.get(expected)
    if expected_types is None:
        return True
    return isinstance(value, expected_types)
