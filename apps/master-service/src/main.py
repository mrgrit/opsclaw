import json
import re
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel

from packages.master_review import (
    MasterReviewError,
    MasterReviewNotFoundError,
    create_master_review,
    get_all_master_reviews,
    get_latest_master_review,
)
from packages.pi_adapter.runtime import PiAdapterError, PiRuntimeClient, PiRuntimeConfig
from packages.project_service import (
    ProjectNotFoundError,
    ProjectServiceError,
    ProjectStageError,
    get_project_record,
    replan_project,
)
from packages.validation_service import get_validation_status


class ReviewRequest(BaseModel):
    reviewer_id: str
    review_status: str          # approved | rejected | needs_replan
    summary: str
    findings: dict | None = None
    auto_replan: bool = False   # if needs_replan, immediately replan project


class ReplanRequest(BaseModel):
    reason: str = "master-initiated replan"


class RuntimePromptRequest(BaseModel):
    prompt: str
    role: str = "master"


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "master-service"}

    return router


def create_runtime_router() -> APIRouter:
    router = APIRouter(prefix="/runtime", tags=["runtime"])
    client = PiRuntimeClient(PiRuntimeConfig(default_role="master"))

    @router.post("/invoke")
    def invoke_runtime(payload: RuntimePromptRequest) -> dict[str, Any]:
        try:
            session_id = client.open_session("master-service-runtime", role=payload.role)
            result = client.invoke_model(
                payload.prompt,
                {"session_id": session_id, "role": payload.role},
            )
            client.close_session(session_id)
            return {"status": "ok", "session_id": session_id, "result": result}
        except PiAdapterError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "message": "pi adapter invocation failed",
                    "error": exc.error.message,
                    "stdout": exc.error.stdout,
                    "stderr": exc.error.stderr,
                    "exit_code": exc.error.exit_code,
                },
            ) from exc

    return router


def create_review_router() -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["review"])

    @router.post("/{project_id}/master-plan")
    def master_plan(project_id: str) -> dict[str, Any]:
        """
        Master가 프로젝트 요구사항을 분석하여 Playbook 단위 작업 계획을 생성한다.

        반환:
          - tasks: [{order, title, playbook_hint, instruction_prompt, risk_level}]
          - summary: 전체 계획 요약
          - similar_playbooks: DB에서 찾은 유사 Playbook 목록
        """
        try:
            project = get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

        request_text = project.get("request_text") or project.get("name") or ""

        # 유사 Playbook 검색 (RAG — completion_reports 및 playbooks 참조)
        similar_playbooks: list[dict] = []
        try:
            from packages.registry_service import list_playbooks
            from packages.retrieval_service import search_documents
            pb_docs = search_documents(request_text[:200], document_type=None, limit=5)
            all_pbs = {pb["name"]: pb for pb in list_playbooks()}
            similar_playbooks = [
                {"name": d["title"], "id": d.get("ref_id"), "relevance": "retrieval"}
                for d in pb_docs if d.get("document_type") == "playbook"
            ]
            # 키워드 직접 매칭 보완
            kw = request_text.lower()
            for pb_name, pb in all_pbs.items():
                if any(w in kw for w in pb_name.replace("_", " ").split()):
                    if not any(s["name"] == pb_name for s in similar_playbooks):
                        similar_playbooks.append({"name": pb_name, "id": pb["id"], "relevance": "keyword"})
        except Exception:
            pass

        # 유사 완료보고서 검색
        past_reports: list[dict] = []
        try:
            from packages.retrieval_service import search_documents
            report_docs = search_documents(request_text[:200], document_type="completion_report", limit=3)
            past_reports = [{"title": d["title"], "body": (d.get("body") or "")[:300]} for d in report_docs]
        except Exception:
            pass

        # LLM으로 작업 계획 생성
        _pi = PiRuntimeClient(PiRuntimeConfig(default_role="master"))

        similar_pb_text = "\n".join(f"- {p['name']}" for p in similar_playbooks) or "없음"
        past_report_text = "\n".join(f"- {r['title']}: {r['body']}" for r in past_reports) or "없음"

        prompt = (
            f"당신은 IT 운영 자동화 시스템 OpsClaw의 Master Agent다.\n"
            f"SubAgent가 대상 Linux 서버에서 bash 명령을 직접 실행한다.\n\n"
            f"사용자 요구사항:\n{request_text}\n\n"
            f"참고할 수 있는 기존 Playbook:\n{similar_pb_text}\n\n"
            f"과거 유사 작업 보고서:\n{past_report_text}\n\n"
            f"위 요구사항을 달성하기 위한 작업 계획을 JSON으로 반환하라.\n\n"
            f"중요 규칙:\n"
            f"- instruction_prompt는 반드시 Linux bash에서 바로 실행 가능한 명령어여야 한다\n"
            f"- 자연어 설명이 아닌 실제 셸 명령어를 작성하라 (예: hostname && uptime)\n"
            f"- sudo가 필요하면 sudo를 포함하라 (NOPASSWD 설정됨)\n"
            f"- 여러 명령은 && 또는 ;로 연결하라\n"
            f"- SSH 접속 명령은 불필요 (SubAgent가 이미 대상 서버에서 실행됨)\n\n"
            f"형식: {{\"summary\": \"<전체계획 1~2문장>\", \"tasks\": ["
            f"{{\"order\": 1, \"title\": \"<작업제목>\", \"playbook_hint\": null, "
            f"\"instruction_prompt\": \"<bash 명령어>\", \"risk_level\": \"<low|medium|high|critical>\"}}]}}\n"
            f"JSON만 출력하라. 설명 불필요."
        )

        plan_tasks: list[dict] = []
        plan_summary = ""
        raw_output = ""
        try:
            result = _pi.invoke_model(prompt, {"role": "master"})
            raw_output = result.get("stdout", "").strip()
            # 마크다운 코드블록 제거
            raw_output = re.sub(r"^```(?:json)?\n?", "", raw_output, flags=re.MULTILINE)
            raw_output = re.sub(r"\n?```\s*$", "", raw_output, flags=re.MULTILINE)
            m = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
                plan_tasks = parsed.get("tasks", [])
                plan_summary = parsed.get("summary", "")
        except (PiAdapterError, json.JSONDecodeError, Exception):
            # LLM 실패 시 단순 단일 태스크 플랜 반환
            plan_tasks = [{
                "order": 1,
                "title": request_text[:60],
                "playbook_hint": similar_playbooks[0]["name"] if similar_playbooks else None,
                "instruction_prompt": f"다음 작업을 수행하라: {request_text}",
                "risk_level": "medium",
            }]
            plan_summary = f"요구사항 '{request_text[:60]}' 을 단일 태스크로 처리."

        return {
            "status": "ok",
            "project_id": project_id,
            "request_text": request_text,
            "summary": plan_summary,
            "tasks": plan_tasks,
            "similar_playbooks": similar_playbooks,
            "past_reports_referenced": len(past_reports),
        }

    @router.post("/{project_id}/review")
    def review_project(project_id: str, req: ReviewRequest) -> dict[str, Any]:
        try:
            get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

        try:
            review = create_master_review(
                project_id=project_id,
                reviewer_agent_id=req.reviewer_id,
                status=req.review_status,
                review_summary=req.summary,
                findings=req.findings or {},
            )
        except MasterReviewError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

        replan_result = None
        if req.review_status == "needs_replan" and req.auto_replan:
            try:
                replan_result = replan_project(project_id, reason=req.summary)
            except ProjectStageError as exc:
                raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

        return {
            "status": "ok",
            "review": review,
            "replan": replan_result,
        }

    @router.get("/{project_id}/review")
    def get_review(project_id: str) -> dict[str, Any]:
        try:
            review = get_latest_master_review(project_id)
            return {"status": "ok", "review": review}
        except MasterReviewNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

    @router.get("/{project_id}/reviews")
    def get_all_reviews(project_id: str) -> dict[str, Any]:
        return {"status": "ok", "reviews": get_all_master_reviews(project_id)}

    @router.post("/{project_id}/replan")
    def replan(project_id: str, req: ReplanRequest) -> dict[str, Any]:
        try:
            project = replan_project(project_id, reason=req.reason)
            return {"status": "ok", "project": project}
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc
        except ProjectStageError as exc:
            raise HTTPException(status_code=400, detail={"message": str(exc)}) from exc

    @router.post("/{project_id}/escalate")
    def escalate_project(project_id: str, payload: dict) -> dict[str, Any]:
        try:
            project = get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

        level = int(payload.get("level", 1))
        # Record escalation as a rejected review with escalation findings
        review = create_master_review(
            project_id=project_id,
            reviewer_agent_id=payload.get("reviewer_id", "master-service"),
            status="rejected",
            review_summary=f"Escalated to level {level}: {payload.get('reason', 'no reason given')}",
            findings={"escalation_level": level, "reason": payload.get("reason", "")},
        )
        return {"status": "ok", "review": review, "escalation_level": level}

    @router.get("/{project_id}/status")
    def project_status(project_id: str) -> dict[str, Any]:
        try:
            project = get_project_record(project_id)
        except ProjectNotFoundError as exc:
            raise HTTPException(status_code=404, detail={"message": str(exc)}) from exc

        val_status = get_validation_status(project_id)

        latest_review: dict | None = None
        try:
            latest_review = get_latest_master_review(project_id)
        except MasterReviewNotFoundError:
            pass

        return {
            "status": "ok",
            "project": project,
            "validation_status": val_status,
            "latest_review": latest_review,
        }

    return router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpsClaw Master Service",
        version="0.3.0-m5",
        description="M5 master review, replan, escalation, validation oversight.",
    )
    app.include_router(create_health_router())
    app.include_router(create_runtime_router())
    app.include_router(create_review_router())
    return app


app = create_app()
