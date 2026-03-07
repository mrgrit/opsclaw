import os
import glob
import hashlib
from typing import Any, Dict, List, Optional

import yaml  # requires pyyaml

PLAYBOOK_DIR = os.getenv("PLAYBOOK_DIR", os.path.join(os.path.dirname(__file__), "playbooks"))

def _sha256_text(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()

def list_playbooks() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for p in sorted(glob.glob(os.path.join(PLAYBOOK_DIR, "*.y*ml"))):
        try:
            raw = open(p, "r", encoding="utf-8").read()
            obj = yaml.safe_load(raw) or {}
            items.append({
                "id": obj.get("id") or os.path.basename(p),
                "name": obj.get("name") or obj.get("id") or os.path.basename(p),
                "version": obj.get("version", 1),
                "path": p,
                "hash": _sha256_text(raw),
            })
        except Exception:
            # ignore broken playbooks in list
            continue
    return items

def load_playbook(playbook_id: str) -> Dict[str, Any]:
    # allow by id field match or filename match
    candidates = sorted(glob.glob(os.path.join(PLAYBOOK_DIR, "*.y*ml")))
    for p in candidates:
        raw = open(p, "r", encoding="utf-8").read()
        obj = yaml.safe_load(raw) or {}
        pid = obj.get("id") or ""
        fname = os.path.splitext(os.path.basename(p))[0]
        if playbook_id in (pid, fname, os.path.basename(p)):
            obj["_meta"] = {"path": p, "hash": _sha256_text(raw)}
            return obj
    raise FileNotFoundError(f"playbook not found: {playbook_id}")