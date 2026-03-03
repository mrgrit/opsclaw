import os
from typing import Any, Dict, List, Tuple

KNOWLEDGE_DIR = os.getenv("KNOWLEDGE_DIR", "/data/knowledge")

os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

def list_docs() -> List[Dict[str, Any]]:
    items = []
    if not os.path.isdir(KNOWLEDGE_DIR):
        return items
    for fn in sorted(os.listdir(KNOWLEDGE_DIR)):
        if fn.lower().endswith((".md", ".txt")):
            p = os.path.join(KNOWLEDGE_DIR, fn)
            items.append({"name": fn, "path": p, "size": os.path.getsize(p)})
    return items

def search(q: str, k: int = 5) -> List[Dict[str, Any]]:
    q = (q or "").strip().lower()
    if not q:
        return []
    hits: List[Tuple[int, Dict[str, Any]]] = []

    for d in list_docs():
        try:
            txt = open(d["path"], "r", encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        low = txt.lower()
        score = low.count(q)
        if score <= 0:
            continue

        # snippet: first occurrence +- 300 chars
        i = low.find(q)
        s = max(0, i - 300)
        e = min(len(txt), i + 300)
        snippet = txt[s:e].strip()

        hits.append((score, {"doc": d["name"], "score": score, "snippet": snippet}))

    hits.sort(key=lambda x: x[0], reverse=True)
    return [x[1] for x in hits[: max(1, int(k))]]