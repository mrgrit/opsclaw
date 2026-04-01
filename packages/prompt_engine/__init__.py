"""
OpsClaw Prompt Engine — 시스템 프롬프트 동적 조합 시스템.

Claude Code의 getSystemPrompt() 패턴을 참고하여 구현.
역할/컨텍스트에 따라 14개 독립 섹션을 조건부 조합한다.
"""

from packages.prompt_engine.compose import compose, compose_with_boundary

__all__ = ["compose", "compose_with_boundary"]
