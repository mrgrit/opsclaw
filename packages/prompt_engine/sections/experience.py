"""경험/RAG 섹션 — 검색된 과거 경험과 관련 지식을 프롬프트에 삽입."""


def get_experience_section(
    rag_results: list[dict] | None = None,
    local_knowledge: dict | None = None,
) -> str | None:
    """RAG 검색 결과와 로컬 지식을 프롬프트 섹션으로 포맷한다.

    Args:
        rag_results: retrieval_service 검색 결과
            [{"title": "...", "body": "...", "document_type": "experience"}, ...]
        local_knowledge: 서버별 로컬 지식 (data/local_knowledge/*.json)
            {"server": "secu", "tools": {...}, "experiences": [...], "network_map": {...}}

    둘 다 없으면 None 반환 (섹션 생략).
    """
    parts: list[str] = []

    if rag_results:
        rag_lines = ["## Related Experience (RAG)", ""]
        for i, doc in enumerate(rag_results[:5], 1):
            title = doc.get("title", "untitled")
            body = (doc.get("body") or "")[:300]
            doc_type = doc.get("document_type", "unknown")
            rag_lines.append(f"{i}. [{doc_type}] **{title}**")
            if body:
                rag_lines.append(f"   {body}")
            rag_lines.append("")
        parts.append("\n".join(rag_lines))

    if local_knowledge:
        kn_lines = [f"## Local Knowledge ({local_knowledge.get('server', 'unknown')})", ""]

        tools = local_knowledge.get("tools", {})
        if tools:
            kn_lines.append("Available tools/paths:")
            for k, v in list(tools.items())[:15]:
                kn_lines.append(f"  {k}: {v}")
            kn_lines.append("")

        exps = local_knowledge.get("experiences", [])
        if exps:
            kn_lines.append("Past experiences on this server:")
            for e in exps[-10:]:
                kn_lines.append(f"  - {e}")
            kn_lines.append("")

        net = local_knowledge.get("network_map", {})
        if net:
            kn_lines.append("Network map:")
            for k, v in net.items():
                services = ", ".join(v.get("services", []))
                kn_lines.append(f"  {k}: {v.get('ip', '')} [{services}]")
            kn_lines.append("")

        parts.append("\n".join(kn_lines))

    if not parts:
        return None

    return "# Context & Experience\n\n" + "\n".join(parts)
