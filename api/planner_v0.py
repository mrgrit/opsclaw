import re
from typing import Any, Dict, List, Tuple, Optional

WORD_RE = re.compile(r"[a-zA-Z0-9_가-힣]+")

def _norm(s: str) -> str:
    return (s or "").strip().lower()

def _tokens(s: str) -> List[str]:
    s = _norm(s)
    return WORD_RE.findall(s)

def _score_by_tokens(tokens: List[str], text: str, weight: int) -> int:
    if not text:
        return 0
    t = _norm(text)
    score = 0
    for w in tokens:
        if w and w in t:
            score += weight
    return score

def score_target(request_text: str, target: Dict[str, Any]) -> int:
    tokens = _tokens(request_text)
    score = 0
    tags = target.get("tags") or []
    name = target.get("name") or ""
    notes = target.get("notes") or ""
    tid = target.get("id") or ""

    # tag exact match boost
    for w in tokens:
        if w in [str(x).lower() for x in tags]:
            score += 5

    score += _score_by_tokens(tokens, name, 2)
    score += _score_by_tokens(tokens, notes, 1)
    score += _score_by_tokens(tokens, tid, 2)
    return score

def score_playbook(request_text: str, pb_meta: Dict[str, Any]) -> int:
    tokens = _tokens(request_text)
    score = 0
    pid = pb_meta.get("id") or ""
    name = pb_meta.get("name") or ""
    # 가벼운 키워드 매칭(향후 yaml keywords 섹션으로 확장)
    score += _score_by_tokens(tokens, pid, 4)
    score += _score_by_tokens(tokens, name, 2)

    # 간단 휴리스틱: suricata / health
    t = _norm(request_text)
    if "suricata" in t and "suricata" in _norm(pid + " " + name):
        score += 6
    if ("health" in t or "상태" in t or "점검" in t) and ("health" in _norm(pid + " " + name) or "ops health" in _norm(name)):
        score += 4
    return score

def pick_best(scored: List[Tuple[str, int]]) -> Tuple[Optional[str], int, Optional[str], int]:
    """returns: best_id, best_score, second_id, second_score"""
    scored = sorted(scored, key=lambda x: x[1], reverse=True)
    if not scored:
        return None, 0, None, 0
    best_id, best_score = scored[0]
    if len(scored) >= 2:
        second_id, second_score = scored[1]
    else:
        second_id, second_score = None, 0
    return best_id, best_score, second_id, second_score

def plan_request(
    *,
    request_text: str,
    targets: List[Dict[str, Any]],
    playbooks: List[Dict[str, Any]],
    default_target_id: str = "local-agent-1",
    min_score: int = 3,
    margin: int = 2,
) -> Dict[str, Any]:
    """
    returns:
      {status:'ready', selected_target_ids:[...], selected_playbook_id:'...', rationale:{...}}
      or
      {status:'needs_clarification', next_questions:[...], rationale:{...}}
    """
    rt = request_text or ""
    next_questions: List[str] = []
    rationale: Dict[str, Any] = {"request_text": rt}

    # targets scoring
    target_scored = []
    for t in targets:
        tid = t.get("id")
        if not tid:
            continue
        target_scored.append((tid, score_target(rt, t)))
    # always include default target as fallback candidate
    if default_target_id and all(tid != default_target_id for tid, _ in target_scored):
        target_scored.append((default_target_id, 0))

    best_tid, best_ts, second_tid, second_ts = pick_best(target_scored)
    rationale["target_scores"] = sorted(target_scored, key=lambda x: x[1], reverse=True)[:5]

    # playbooks scoring
    pb_scored = []
    for pb in playbooks:
        pid = pb.get("id")
        if not pid:
            continue
        pb_scored.append((pid, score_playbook(rt, pb)))
    best_pid, best_ps, second_pid, second_ps = pick_best(pb_scored)
    rationale["playbook_scores"] = sorted(pb_scored, key=lambda x: x[1], reverse=True)[:5]

    # decision
    needs = False

    if not best_pid or best_ps < min_score:
        needs = True
        next_questions.append("어떤 작업을 원하나요? (예: health 점검 / suricata 설치 / 네트워크 점검)")
    elif (best_ps - second_ps) < margin:
        needs = True
        next_questions.append(f"플레이북 선택이 모호합니다. '{best_pid}'로 진행할까요, 아니면 '{second_pid}'인가요?")

    if not best_tid or best_ts < min_score:
        needs = True
        # 후보 targets 3개만 제시
        cands = [tid for tid, sc in sorted(target_scored, key=lambda x: x[1], reverse=True)[:3]]
        if cands:
            next_questions.append(f"어느 타겟에서 실행할까요? 후보: {', '.join(cands)}")
        else:
            next_questions.append("어느 타겟에서 실행할까요? (remote-1 / local-agent-1 등)")
    elif (best_ts - second_ts) < margin and second_tid:
        needs = True
        next_questions.append(f"타겟 선택이 모호합니다. '{best_tid}' vs '{second_tid}' 중 어디에서 실행할까요?")

    if needs:
        return {
            "status": "needs_clarification",
            "next_questions": next_questions,
            "rationale": rationale,
        }

    return {
        "status": "ready",
        "selected_target_ids": [best_tid],
        "selected_playbook_id": best_pid,
        "rationale": rationale,
    }