"""Tool 스키마 정의 및 로딩."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas" / "registry" / "tools"


@dataclass
class ToolSchema:
    """Tool의 입출력 스키마 + 메타데이터."""
    name: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None = None
    is_read_only: bool = False
    is_destructive: bool = False
    default_risk_level: str = "medium"
    timeout_s: int = 120


# 도구별 안전 분류 (Claude Code의 isReadOnly/isDestructive 패턴)
_TOOL_SAFETY: dict[str, dict] = {
    "run_command": {"is_read_only": False, "is_destructive": False, "default_risk_level": "medium"},
    "fetch_log": {"is_read_only": True, "is_destructive": False, "default_risk_level": "low"},
    "query_metric": {"is_read_only": True, "is_destructive": False, "default_risk_level": "low"},
    "read_file": {"is_read_only": True, "is_destructive": False, "default_risk_level": "low"},
    "write_file": {"is_read_only": False, "is_destructive": False, "default_risk_level": "medium"},
    "restart_service": {"is_read_only": False, "is_destructive": False, "default_risk_level": "high"},
}


def load_tool_schemas(schemas_dir: str | Path | None = None) -> dict[str, ToolSchema]:
    """schemas/registry/tools/ 에서 모든 Tool 스키마를 로드한다.

    Returns:
        {tool_name: ToolSchema} 매핑
    """
    base = Path(schemas_dir) if schemas_dir else SCHEMAS_DIR
    schemas: dict[str, ToolSchema] = {}

    if not base.is_dir():
        return schemas

    # tool_name.input.json 파일 찾기
    for f in sorted(base.glob("*.input.json")):
        tool_name = f.name.replace(".input.json", "")
        try:
            input_schema = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        # output schema 로드 (선택)
        output_file = base / f"{tool_name}.output.json"
        output_schema = None
        if output_file.is_file():
            try:
                output_schema = json.loads(output_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass

        safety = _TOOL_SAFETY.get(tool_name, {})
        schemas[tool_name] = ToolSchema(
            name=tool_name,
            input_schema=input_schema,
            output_schema=output_schema,
            **safety,
        )

    return schemas
