"""config_client — Central Config 서비스 클라이언트

각 시스템이 기동 시 Central에서 설정을 가져오거나,
Central 미접속 시 환경변수/기본값으로 폴백한다.

Usage:
    from packages.opsclaw_common.config_client import get_config, get_bundle

    # 단일 설정 조회
    ollama_url = get_config("llm.ollama.url", fallback="http://localhost:11434")

    # 번들 조회 (시스템 기동 시)
    bundle = get_bundle("bastion")
    db_url = bundle.get("db.url", "postgresql://...")
"""
from __future__ import annotations
import os
from typing import Any

import httpx

CENTRAL_URL = os.getenv("CENTRAL_SERVER_URL", "http://localhost:7000")
CENTRAL_API_KEY = os.getenv("CENTRAL_API_KEY", "central-api-key-2026")

_cache: dict[str, Any] = {}


def _headers() -> dict[str, str]:
    return {"X-API-Key": CENTRAL_API_KEY, "Content-Type": "application/json"}


def get_config(key: str, fallback: Any = None, use_cache: bool = True) -> Any:
    """Central에서 단일 설정 조회. 실패 시 fallback 반환."""
    if use_cache and key in _cache:
        return _cache[key]

    try:
        r = httpx.get(f"{CENTRAL_URL}/config/{key}", headers=_headers(), timeout=5.0)
        if r.status_code == 200:
            val = r.json().get("value", fallback)
            _cache[key] = val
            return val
    except Exception:
        pass

    # 환경변수 폴백 (key를 환경변수 이름으로 변환: infra.secu.ip → INFRA_SECU_IP)
    env_key = key.upper().replace(".", "_")
    env_val = os.getenv(env_key)
    if env_val is not None:
        return env_val

    return fallback


def get_bundle(instance_type: str) -> dict[str, Any]:
    """Central에서 인스턴스 타입별 설정 번들 조회. 실패 시 빈 dict."""
    try:
        r = httpx.get(
            f"{CENTRAL_URL}/config-bundle/{instance_type}",
            headers=_headers(), timeout=10.0,
        )
        if r.status_code == 200:
            bundle = r.json().get("config", {})
            _cache.update(bundle)
            return bundle
    except Exception:
        pass
    return {}


def clear_cache():
    """캐시 초기화"""
    _cache.clear()


def set_central_url(url: str):
    """Central URL 변경 (테스트용)"""
    global CENTRAL_URL
    CENTRAL_URL = url
