"""프로젝트 완료 시 자동 메모리 추출.

evidence와 report를 분석하여 재사용 가능한 경험을 추출한다.
"""

import os
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from packages.memory_manager.types import MemoryEntry


_DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")


def _conn():
    return psycopg2.connect(_DB_URL)


def auto_extract_memories(project_id: str) -> list[MemoryEntry]:
    """프로젝트의 evidence/report를 분석하여 메모리를 자동 추출한다.

    추출 규칙:
    - exit_code != 0인 evidence → failure 메모리
    - 재시작/설정변경 evidence → configuration 메모리
    - 전체 성공 프로젝트 → runbook 메모리
    - incident 관련 프로젝트 → incident 메모리

    Returns:
        추출된 MemoryEntry 리스트 (experience_service에 저장하려면 별도 호출 필요)
    """
    conn = _conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 프로젝트 정보
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = cur.fetchone()
            if not project:
                return []
            project = dict(project)

            # evidence 조회
            cur.execute(
                "SELECT command_text, stdout_ref, stderr_ref, exit_code "
                "FROM evidence WHERE project_id = %s ORDER BY started_at",
                (project_id,),
            )
            evidence_rows = [dict(r) for r in cur.fetchall()]

            # completion report 조회
            cur.execute(
                "SELECT summary, outcome, work_details, issues "
                "FROM completion_reports WHERE project_id = %s "
                "ORDER BY created_at DESC LIMIT 1",
                (project_id,),
            )
            report = cur.fetchone()
            report = dict(report) if report else {}
    finally:
        conn.close()

    memories: list[MemoryEntry] = []
    request_text = project.get("request_text", "")[:200]

    # 1. 실패 패턴 추출
    failures = [e for e in evidence_rows if (e.get("exit_code") or 0) != 0]
    if failures:
        failed_cmds = [
            f"{(e.get('command_text') or '')[:80]} → exit {e['exit_code']}"
            for e in failures[:5]
        ]
        memories.append(MemoryEntry(
            memory_type="failure",
            title=f"실패: {request_text[:60]}",
            content=(
                f"프로젝트 '{project.get('name', '')}' 에서 {len(failures)}건 실패.\n"
                + "\n".join(f"- {c}" for c in failed_cmds)
            ),
            project_id=project_id,
            tags=["auto-extracted", "failure"],
        ))

    # 2. 설정 변경 감지
    config_keywords = ("systemctl", "restart", "reload", "enable", "disable",
                       "write_file", "sed ", "echo ", "tee ", "iptables", "nft ")
    config_cmds = [
        e for e in evidence_rows
        if any(kw in (e.get("command_text") or "").lower() for kw in config_keywords)
        and (e.get("exit_code") or 0) == 0
    ]
    if config_cmds:
        cmds = [(e.get("command_text") or "")[:100] for e in config_cmds[:5]]
        memories.append(MemoryEntry(
            memory_type="configuration",
            title=f"설정 변경: {request_text[:60]}",
            content=(
                f"프로젝트에서 {len(config_cmds)}건 설정 변경 실행.\n"
                + "\n".join(f"- {c}" for c in cmds)
            ),
            project_id=project_id,
            tags=["auto-extracted", "config-change"],
        ))

    # 3. 전체 성공 → runbook
    outcome = report.get("outcome", project.get("status", ""))
    if outcome == "success" and evidence_rows:
        all_cmds = [(e.get("command_text") or "")[:80] for e in evidence_rows[:10]]
        memories.append(MemoryEntry(
            memory_type="runbook",
            title=f"성공: {request_text[:60]}",
            content=(
                f"프로젝트 '{project.get('name', '')}' 성공 완료.\n"
                f"요약: {report.get('summary', '')[:200]}\n"
                f"실행 명령 ({len(evidence_rows)}건):\n"
                + "\n".join(f"- {c}" for c in all_cmds)
            ),
            project_id=project_id,
            tags=["auto-extracted", "runbook", "success"],
        ))

    # 4. 인시던트 키워드 감지
    incident_keywords = ("incident", "alert", "compromise", "intrusion", "breach", "wazuh", "suricata")
    if any(kw in request_text.lower() for kw in incident_keywords):
        memories.append(MemoryEntry(
            memory_type="incident",
            title=f"인시던트 대응: {request_text[:60]}",
            content=(
                f"요청: {request_text}\n"
                f"결과: {outcome}\n"
                f"요약: {report.get('summary', '')[:200]}\n"
                f"이슈: {report.get('issues', [])}"
            ),
            project_id=project_id,
            tags=["auto-extracted", "incident"],
        ))

    return memories
