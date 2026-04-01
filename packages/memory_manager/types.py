"""메모리 유형 정의."""

from dataclasses import dataclass, field
from typing import Any


# Claude Code memdir의 메모리 유형을 IT 운영에 맞게 재정의
MEMORY_TYPES = {
    "incident": "보안 인시던트 대응 기록 — 탐지, 분석, 조치 경험",
    "runbook": "성공한 운영 절차 — 재현 가능한 작업 패턴",
    "failure": "실패 패턴 — 왜 실패했는지, 어떻게 해결했는지",
    "configuration": "설정 변경 기록 — 무엇을 왜 변경했는지",
    "optimization": "성능 최적화 — 측정 결과와 개선 방법",
}

# 저장하지 않을 것 (Claude Code의 WHAT_NOT_TO_SAVE 패턴)
DO_NOT_SAVE = [
    "stdout/stderr 원문 (evidence에 이미 저장됨)",
    "명령어 원본 (evidence.command에 저장됨)",
    "프로젝트 임시 상태 (project_service에서 관리)",
    "PoW 블록 해시 (pow_service에서 관리)",
    "LLM 호출 원문 (cost_tracker에 기록됨)",
]


@dataclass
class MemoryEntry:
    """하나의 메모리 항목."""
    memory_type: str                    # MEMORY_TYPES 중 하나
    title: str                          # 한 줄 요약
    content: str                        # 핵심 내용 (300자 이내 권장)
    project_id: str | None = None
    asset_id: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
