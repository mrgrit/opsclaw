import requests
from typing import Dict, Any

def run_script(subagent_url: str, run_req: Dict[str, Any], timeout_s: int = 120) -> Dict[str, Any]:
    r = requests.post(f"{subagent_url}/a2a/run_script", json=run_req, timeout=timeout_s)
    r.raise_for_status()
    return r.json()