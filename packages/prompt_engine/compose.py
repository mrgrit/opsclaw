"""시스템 프롬프트 조합 — 섹션들을 역할/컨텍스트에 따라 결합한다."""

from packages.prompt_engine.sections.identity import get_identity_section
from packages.prompt_engine.sections.safety import get_safety_section
from packages.prompt_engine.sections.workflow import get_workflow_section
from packages.prompt_engine.sections.tools import get_tools_section
from packages.prompt_engine.sections.environment import get_environment_section
from packages.prompt_engine.sections.experience import get_experience_section
from packages.prompt_engine.sections.output import get_output_section


# 정적/동적 경계 마커 — 이 마커 이전은 캐시 가능, 이후는 세션별
CACHE_BOUNDARY = "__OPSCLAW_PROMPT_CACHE_BOUNDARY__"


def compose(
    role: str,
    context: dict | None = None,
) -> str:
    """역할과 컨텍스트에 따라 시스템 프롬프트를 조합한다.

    Args:
        role: "manager" | "master" | "subagent" | "tutor"
        context: 동적 컨텍스트 (모두 선택적)
            - tools: list[dict]          활성 도구 목록
            - skills: list[dict]         활성 스킬 목록
            - server: str                대상 서버명
            - infra: dict                인프라 매핑 오버라이드
            - rag_results: list[dict]    RAG 검색 결과
            - local_knowledge: dict      서버별 로컬 지식
            - page_context: str          포털 페이지 내용 (tutor용)

    Returns:
        조합된 시스템 프롬프트 문자열.
    """
    ctx = context or {}

    # 정적 섹션 (역할이 같으면 항상 동일)
    static_sections = [
        get_identity_section(role),
        get_safety_section(role),
        get_workflow_section(role),
        get_output_section(role),
    ]

    # 동적 섹션 (컨텍스트에 따라 달라짐)
    dynamic_sections = [
        get_tools_section(
            tools=ctx.get("tools"),
            skills=ctx.get("skills"),
        ),
        get_environment_section(
            server=ctx.get("server"),
            infra=ctx.get("infra"),
        ),
        get_experience_section(
            rag_results=ctx.get("rag_results"),
            local_knowledge=ctx.get("local_knowledge"),
        ),
    ]

    # tutor 전용: 페이지 컨텍스트 삽입
    if role == "tutor" and ctx.get("page_context"):
        page_ctx = ctx["page_context"][:8000]
        dynamic_sections.append(
            f"# Current Page Content\n\n"
            f"--- Page Content ---\n{page_ctx}\n--- End ---"
        )

    # RAG 검색 결과 (tutor용)
    if role == "tutor" and ctx.get("rag_snippets"):
        rag_block = "# Related Learning Materials\n\n"
        for r in ctx["rag_snippets"][:3]:
            label = r.get("label", r.get("source_type", ""))
            rag_block += f"[{label}: {r.get('source_path', '')}] {r.get('title', '')}\n"
            rag_block += f"{r.get('snippet', '')}\n\n"
        dynamic_sections.append(rag_block)

    # None 제거 후 결합
    all_sections = [s for s in static_sections if s] + [s for s in dynamic_sections if s]
    return "\n\n".join(all_sections)


def compose_with_boundary(
    role: str,
    context: dict | None = None,
) -> tuple[str, str]:
    """정적/동적 부분을 분리하여 반환한다. 캐싱 최적화용.

    Returns:
        (static_prompt, dynamic_prompt)
    """
    ctx = context or {}

    static_parts = [
        get_identity_section(role),
        get_safety_section(role),
        get_workflow_section(role),
        get_output_section(role),
    ]
    static_prompt = "\n\n".join(s for s in static_parts if s)

    dynamic_parts = [
        get_tools_section(ctx.get("tools"), ctx.get("skills")),
        get_environment_section(ctx.get("server"), ctx.get("infra")),
        get_experience_section(ctx.get("rag_results"), ctx.get("local_knowledge")),
    ]
    dynamic_prompt = "\n\n".join(s for s in dynamic_parts if s)

    return static_prompt, dynamic_prompt
