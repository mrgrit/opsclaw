import os
import requests
from typing import Literal, Dict, Any

Provider = Literal["ollama", "openai", "anthropic"]

def _timeout():
    return float(os.getenv("MASTER_TIMEOUT_S", "60"))

def call_master(provider: Provider, prompt: str) -> Dict[str, Any]:
    if provider == "ollama":
        return call_ollama(prompt)
    if provider == "openai":
        return call_openai(prompt)
    if provider == "anthropic":
        return call_anthropic(prompt)
    raise ValueError(f"unknown provider: {provider}")

def call_ollama(prompt: str) -> Dict[str, Any]:
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    url = f"{base}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    r = requests.post(url, json=payload, timeout=_timeout())
    r.raise_for_status()
    data = r.json()
    return {
        "provider": "ollama",
        "model": model,
        "text": data.get("response", ""),
        "raw": data,
    }

def call_openai(prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is empty")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    # Responses API: POST /v1/responses (OpenAI docs)
    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "input": prompt
    }
    r = requests.post(url, headers=headers, json=payload, timeout=_timeout())
    r.raise_for_status()
    data = r.json()

    # 텍스트 추출(응답 포맷 변화에 대비해 최대한 안전하게)
    text = ""
    try:
        # 흔한 형태: output[0].content[0].text
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

def call_anthropic(prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is empty")
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")

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
    r = requests.post(url, headers=headers, json=payload, timeout=_timeout())
    r.raise_for_status()
    data = r.json()

    text = ""
    try:
        # content: [{type:"text", text:"..."}]
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
