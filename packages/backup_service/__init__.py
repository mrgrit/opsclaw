"""OpsClaw Backup Service — PostgreSQL backup via pg_dump.

create_backup(backup_dir)  → runs pg_dump, returns backup metadata dict
list_backups(backup_dir)   → list backup files with metadata
get_backup_info(path)      → metadata for a single backup file
"""
from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DB_URL = os.getenv("DATABASE_URL", "postgresql://opsclaw:opsclaw@127.0.0.1:5432/opsclaw")
DEFAULT_BACKUP_DIR = os.getenv("OPSCLAW_BACKUP_DIR", "/tmp/opsclaw_backups")


def create_backup(
    backup_dir: str | None = None,
    database_url: str | None = None,
) -> dict:
    """Run pg_dump and save to backup_dir.

    Returns: {"ok": bool, "path": str|None, "size_bytes": int|None, "error": str|None}
    """
    dir_path = Path(backup_dir or DEFAULT_BACKUP_DIR)
    dir_path.mkdir(parents=True, exist_ok=True)
    url = database_url or DB_URL
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"opsclaw_backup_{ts}.sql"
    out_path = dir_path / filename

    try:
        result = subprocess.run(
            ["pg_dump", "--no-password", url, "-f", str(out_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return {
                "ok": False,
                "path": None,
                "size_bytes": None,
                "error": result.stderr.strip() or f"pg_dump exited {result.returncode}",
            }
        size = out_path.stat().st_size if out_path.exists() else 0
        return {
            "ok": True,
            "path": str(out_path),
            "filename": filename,
            "size_bytes": size,
            "created_at": ts,
            "error": None,
        }
    except FileNotFoundError:
        return {"ok": False, "path": None, "size_bytes": None, "error": "pg_dump not found in PATH"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "path": None, "size_bytes": None, "error": "pg_dump timed out"}
    except Exception as exc:
        return {"ok": False, "path": None, "size_bytes": None, "error": str(exc)}


def list_backups(backup_dir: str | None = None) -> list[dict]:
    """List backup files in backup_dir, sorted by mtime descending."""
    dir_path = Path(backup_dir or DEFAULT_BACKUP_DIR)
    if not dir_path.exists():
        return []
    files = sorted(dir_path.glob("opsclaw_backup_*.sql"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {
            "filename": f.name,
            "path": str(f),
            "size_bytes": f.stat().st_size,
            "created_at": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
        }
        for f in files
    ]


def get_backup_info(backup_path: str) -> dict | None:
    """Return metadata for a single backup file, or None if not found."""
    p = Path(backup_path)
    if not p.exists():
        return None
    return {
        "filename": p.name,
        "path": str(p),
        "size_bytes": p.stat().st_size,
        "created_at": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat(),
    }
