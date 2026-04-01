"""
OpsClaw Memory Manager — 메모리 고도화 레이어.

기존 experience_service(Layer 2-3) + retrieval_service(Layer 4) 위에
자동 추출, 용량 관리, 메모리 유형 분류를 추가한다.

Claude Code의 memdir/ 패턴을 참고:
- 메모리 유형별 분류 (incident/runbook/failure/config)
- 용량 제한 (LRU)
- "저장하지 않을 것" 규칙
- 프로젝트 완료 시 자동 패턴 추출
"""

from packages.memory_manager.extractor import auto_extract_memories
from packages.memory_manager.capacity import enforce_capacity
from packages.memory_manager.types import MEMORY_TYPES, MemoryEntry

__all__ = [
    "auto_extract_memories",
    "enforce_capacity",
    "MEMORY_TYPES",
    "MemoryEntry",
]
