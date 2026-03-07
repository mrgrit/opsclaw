import os
import requests
from typing import Literal, Dict, Any, Optional

Provider = Literal["ollama", "openai", "anthropic", "yncai"]

def _timeout():
    return float(os.getenv("MASTER_TIMEOUT_S", "60"))

def call_master(provider: Provider, prompt: str) -> Dict[str, Any]:
    if provider == "ollama":
        return call_ollama(prompt)
    if provider == "openai":
        return call_openai(prompt)
    if provider == "anthropic":
        return call_anthropic(prompt)
    if provider == "yncai":
        base = os.getenv("YNCAI_BASE_URL", "https://factchat-cloud.mindlogic.ai/v1/gateway").rstrip("/")
        api_key = os.getenv("YNCAI_API_KEY", "")
        model = os.getenv("YNCAI_MODEL", "")
        return call_yncai(prompt, base_url=base, api_key=api_key, model=model)
    raise ValueError(f"unknown provider: {provider}")

def call_conn(conn: Dict[str, Any], prompt: str) -> Dict[str, Any]:
    provider = (conn.get("provider") or "").strip()

    if provider == "ollama":
        return call_ollama(
            prompt,
            base_url=(conn.get("base_url") or "").strip() or None,
            model=(conn.get("model") or "").strip() or None,
            timeout_s=conn.get("timeout_s"),
        )

    if provider == "openai":
        return call_openai(
            prompt,
            api_key=(conn.get("api_key") or "").strip() or None,
            model=(conn.get("model") or "").strip() or None,
            timeout_s=conn.get("timeout_s"),
        )

    if provider == "yncai":
        base_url = (conn.get("base_url") or "").strip() or "https://factchat-cloud.mindlogic.ai/v1/gateway"
        api_key = (conn.get("api_key") or "").strip()
        model = (conn.get("model") or "").strip()
        headers = conn.get("headers") or {}
        return call_yncai(
            prompt,
            base_url=base_url,
            api_key=api_key,
            model=model,
            headers=headers,
            timeout_s=conn.get("timeout_s"),
        )

    if provider == "anthropic":
        return call_anthropic(
            prompt,
            api_key=(conn.get("api_key") or "").strip() or None,
            model=(conn.get("model") or "").strip() or None,
            timeout_s=conn.get("timeout_s"),
        )

    raise ValueError(f"unknown provider: {provider}")

def call_ollama(prompt: str, base_url: Optional[str] = None, model: Optional[str] = None, timeout_s: Optional[int] = None) -> Dict[str, Any]:
    base = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
    model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    url = f"{base}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    r = requests.post(url, json=payload, timeout=float(timeout_s or _timeout()))
    r.raise_for_status()
    data = r.json()
    return {
        "provider": "ollama",
        "model": model,
        "text": data.get("response", ""),
        "raw": data,
    }

def call_openai(prompt: str, api_key: Optional[str] = None, model: Optional[str] = None, timeout_s: Optional[int] = None) -> Dict[str, Any]:
    api_key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is empty")
    model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "input": prompt
    }
    r = requests.post(url, headers=headers, json=payload, timeout=float(timeout_s or _timeout()))
    r.raise_for_status()
    data = r.json()

    text = ""
    try:
        out0 = (data.get("output") or [])[0]
        c0 = (out0.get("content") or [])[0]
        text = c0.get("text") or ""
    except Exception:
        text = ""

    return {
        "provider": "openai",
        "model": model,
        "text": text,
        "raw": data,
    }

def call_yncai(
    prompt: str,
    *,
    base_url: str,
    api_key: str = "",
    model: str = "",
    headers: Optional[Dict[str, str]] = None,
    timeout_s: Optional[int] = None,
) -> Dict[str, Any]:
    base = base_url.rstrip("/")

    # 게이트웨이 형식이 다를 수 있어서 우선 OpenAI-style responses 우선 시도
    candidates = [
        f"{base}/responses",
        f"{base}/chat/completions",
    ]

    req_headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        req_headers["Authorization"] = f"Bearer {api_key}"
    if headers:
        req_headers.update(headers)

    last_err = None
    for url in candidates:
        try:
            if url.endswith("/responses"):
                payload = {
                    "input": prompt,
                }
                if model:
                    payload["model"] = model
                r = requests.post(url, headers=req_headers, json=payload, timeout=float(timeout_s or _timeout()))
                r.raise_for_status()
                data = r.json()

                text = ""
                try:
                    out0 = (data.get("output") or [])[0]
                    c0 = (out0.get("content") or [])[0]
                    text = c0.get("text") or ""
                except Exception:
                    text = ""
                if not text:
                    try:
                        text = (((data.get("choices") or [])[0].get("message") or {}).get("content")) or ""
                    except Exception:
                        text = ""

                return {
                    "provider": "yncai",
                    "model": model,
                    "text": text,
                    "raw": data,
                }

            if url.endswith("/chat/completions"):
                payload = {
                    "messages": [{"role": "user", "content": prompt}],
                }
                if model:
                    payload["model"] = model
                r = requests.post(url, headers=req_headers, json=payload, timeout=float(timeout_s or _timeout()))
                r.raise_for_status()
                data = r.json()

                text = ""
                try:
                    text = (((data.get("choices") or [])[0].get("message") or {}).get("content")) or ""
                except Exception:
                    text = ""

                return {
                    "provider": "yncai",
                    "model": model,
                    "text": text,
                    "raw": data,
                }
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"yncai call failed: {last_err}")

def call_anthropic(prompt: str, api_key: Optional[str] = None, model: Optional[str] = None, timeout_s: Optional[int] = None) -> Dict[str, Any]:
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is empty")
    model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 800,
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=float(timeout_s or _timeout()))
    r.raise_for_status()
    data = r.json()

    text = ""
    try:
        c0 = (data.get("content") or [])[0]
        text = c0.get("text") or ""
    except Exception:
        text = ""

    return {
        "provider": "anthropic",
        "model": model,
        "text": text,
        "raw": data,
    }