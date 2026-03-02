import os, json, zipfile, time
from typing import Dict, Any, Set, List

def _now_tag():
    return time.strftime("%Y%m%d_%H%M%S")

def _safe_exists(p: str) -> bool:
    try:
        return os.path.exists(p)
    except Exception:
        return False

def collect_evidence_refs(project_state: Dict[str, Any]) -> Set[str]:
    refs: Set[str] = set()

    # runs[] evidence
    for r in project_state.get("runs", []) or []:
        for p in r.get("evidence_refs", []) or []:
            refs.add(str(p))

    # workflow_runs[] dispatch_runs evidence
    for wf in project_state.get("workflow_runs", []) or []:
        for dr in wf.get("dispatch_runs", []) or []:
            for p in dr.get("evidence_refs", []) or []:
                refs.add(str(p))

    # 기타 필요하면 확장: tests, changes 등
    return refs

def write_project_audit(audit_jsonl_path: str, project_id: str, out_path: str) -> None:
    if not _safe_exists(audit_jsonl_path):
        # 없으면 빈 파일 생성
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("")
        return

    with open(audit_jsonl_path, "r", encoding="utf-8", errors="ignore") as f_in, \
         open(out_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            # audit 라인이 json이 아닐 수도 있으니 문자열 포함으로 필터(안전)
            if project_id in line:
                f_out.write(line)

def build_evidence_zip(
    project_id: str,
    project_state: Dict[str, Any],
    evidence_dir: str,
    audit_jsonl_path: str,
    out_dir: str = "/tmp"
) -> str:
    os.makedirs(out_dir, exist_ok=True)

    tag = _now_tag()
    zip_path = os.path.join(out_dir, f"opsclaw_evidence_{project_id}_{tag}.zip")

    # 임시 파일들
    tmp_state_path = os.path.join(out_dir, f"project_state_{project_id}_{tag}.json")
    tmp_audit_path = os.path.join(out_dir, f"audit_{project_id}_{tag}.jsonl")

    with open(tmp_state_path, "w", encoding="utf-8") as f:
        json.dump(project_state, f, ensure_ascii=False, indent=2)

    write_project_audit(audit_jsonl_path, project_id, tmp_audit_path)

    refs = collect_evidence_refs(project_state)

    # refs는 보통 "/data/evidence/..." 전체 경로
    # 없으면 evidence_dir + basename 형태로도 시도
    def resolve_ref(p: str) -> str:
        p = str(p)
        if _safe_exists(p):
            return p
        base = os.path.basename(p)
        cand = os.path.join(evidence_dir, base)
        if _safe_exists(cand):
            return cand
        return ""

    included: List[str] = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp_state_path, arcname="project_state.json")
        z.write(tmp_audit_path, arcname="audit_project.jsonl")

        # evidence 폴더로 모으기
        for ref in sorted(refs):
            real = resolve_ref(ref)
            if not real:
                continue
            arc = os.path.join("evidence", os.path.basename(real))
            try:
                z.write(real, arcname=arc)
                included.append(real)
            except Exception:
                # 하나 깨져도 전체 zip 생성은 계속
                continue

        # manifest 추가
        manifest = {
            "project_id": project_id,
            "included_evidence_files": [os.path.basename(x) for x in included],
            "included_count": len(included),
            "generated_at": tag,
        }
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    # 임시 파일 정리(zip은 남김)
    for p in (tmp_state_path, tmp_audit_path):
        try:
            os.remove(p)
        except Exception:
            pass

    return zip_path

def collect_approval_evidence_refs(approval_obj: Dict[str, Any]) -> Set[str]:
    refs: Set[str] = set()
    for r in approval_obj.get("apply_feedback_runs", []) or []:
        for p in r.get("evidence_refs", []) or []:
            refs.add(str(p))
    return refs

def write_approval_audit(audit_jsonl_path: str, approval_id: str, out_path: str) -> None:
    if not _safe_exists(audit_jsonl_path):
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("")
        return
    with open(audit_jsonl_path, "r", encoding="utf-8", errors="ignore") as f_in, \
         open(out_path, "w", encoding="utf-8") as f_out:
        for line in f_in:
            if approval_id in line:
                f_out.write(line)

def build_approval_evidence_zip(
    approval_id: str,
    approval_obj: Dict[str, Any],
    evidence_dir: str,
    audit_jsonl_path: str,
    out_dir: str = "/tmp"
) -> str:
    os.makedirs(out_dir, exist_ok=True)
    tag = _now_tag()
    zip_path = os.path.join(out_dir, f"opsclaw_approval_{approval_id}_{tag}.zip")

    tmp_approval_path = os.path.join(out_dir, f"approval_{approval_id}_{tag}.json")
    tmp_gate_path = os.path.join(out_dir, f"mastergate_{approval_id}_{tag}.json")
    tmp_prompt_path = os.path.join(out_dir, f"master_prompt_{approval_id}_{tag}.txt")
    tmp_reply_path = os.path.join(out_dir, f"master_reply_{approval_id}_{tag}.json")
    tmp_validate_path = os.path.join(out_dir, f"apply_feedback_validate_{approval_id}_{tag}.json")
    tmp_audit_path = os.path.join(out_dir, f"audit_approval_{approval_id}_{tag}.jsonl")

    with open(tmp_approval_path, "w", encoding="utf-8") as f:
        json.dump(approval_obj, f, ensure_ascii=False, indent=2)

    with open(tmp_gate_path, "w", encoding="utf-8") as f:
        json.dump(approval_obj.get("gate") or {}, f, ensure_ascii=False, indent=2)

    with open(tmp_prompt_path, "w", encoding="utf-8") as f:
        f.write((approval_obj.get("final_prompt") or "").strip() + "\n")

    with open(tmp_reply_path, "w", encoding="utf-8") as f:
        json.dump(approval_obj.get("master_reply"), f, ensure_ascii=False, indent=2)

    with open(tmp_validate_path, "w", encoding="utf-8") as f:
        json.dump(approval_obj.get("apply_feedback_validate") or {}, f, ensure_ascii=False, indent=2)

    write_approval_audit(audit_jsonl_path, approval_id, tmp_audit_path)

    refs = collect_approval_evidence_refs(approval_obj)

    def resolve_ref(p: str) -> str:
        p = str(p)
        if _safe_exists(p):
            return p
        base = os.path.basename(p)
        cand = os.path.join(evidence_dir, base)
        if _safe_exists(cand):
            return cand
        return ""

    included = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp_approval_path, arcname="approval.json")
        z.write(tmp_gate_path, arcname="mastergate.json")
        z.write(tmp_prompt_path, arcname="master_prompt.txt")
        z.write(tmp_reply_path, arcname="master_reply.json")
        z.write(tmp_validate_path, arcname="apply_feedback_validate.json")
        z.write(tmp_audit_path, arcname="audit_approval.jsonl")

        for ref in sorted(refs):
            real = resolve_ref(ref)
            if not real:
                continue
            arc = os.path.join("evidence", os.path.basename(real))
            try:
                z.write(real, arcname=arc)
                included.append(real)
            except Exception:
                continue

        manifest = {
            "approval_id": approval_id,
            "included_evidence_files": [os.path.basename(x) for x in included],
            "included_count": len(included),
            "generated_at": tag,
        }
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    for p in (tmp_approval_path, tmp_gate_path, tmp_prompt_path, tmp_reply_path, tmp_validate_path, tmp_audit_path):
        try:
            os.remove(p)
        except Exception:
            pass

    return zip_path
