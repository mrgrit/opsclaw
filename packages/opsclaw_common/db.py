"""통합 DB 연결 유틸리티"""
import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw",
)

@contextmanager
def get_connection(database_url: str | None = None):
    """psycopg2 연결 컨텍스트 매니저."""
    conn = psycopg2.connect(database_url or DEFAULT_DATABASE_URL)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def raw_connection(database_url: str | None = None):
    """Non-context-manager 연결 (기존 호환)."""
    return psycopg2.connect(database_url or DEFAULT_DATABASE_URL)
