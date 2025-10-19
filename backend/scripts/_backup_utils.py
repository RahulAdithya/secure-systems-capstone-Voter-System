from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_FILE = BASE_DIR / "var" / "evp.sqlite3"
BACKUPS_DIR = BASE_DIR / "backups"

def _ensure_dirs() -> None:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_DB_FILE.parent.mkdir(parents=True, exist_ok=True)


def _from_database_url(env: Optional[str]) -> Optional[Path]:
    if not env:
        return None
    candidate = env.strip()
    parsed = urlparse(candidate)
    if parsed.scheme != "sqlite":
        return None
    path = parsed.path or ""
    # If a netloc is provided (rare for sqlite), include it.
    if parsed.netloc:
        path = f"/{parsed.netloc}{path}"
    # Normalise quadruple-slash absolute paths (sqlite:////var/db.sqlite3)
    while path.startswith("//"):
        path = path[1:]
    if not path:
        return None
    result = Path(path)
    return result.expanduser()


def resolve_db_path() -> Path:
    """
    Resolve DB file path (in order):
      1. Explicit DB_FILE env var.
      2. DATABASE_URL env (sqlite:///...).
      3. Default backend/var/evp.sqlite3.
    """
    _ensure_dirs()
    db_file_env = os.getenv("DB_FILE")
    if db_file_env:
        return Path(db_file_env)
    db_url = os.getenv("DATABASE_URL")
    path_from_url = _from_database_url(db_url)
    if path_from_url:
        return path_from_url
    return DEFAULT_DB_FILE


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_user_tables(db_path: Path) -> List[str]:
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cur.fetchall()]


def table_counts(db_path: Path) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cur.fetchall()]
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM '{table}'")
                counts[table] = int(cur.fetchone()[0])
            except Exception:
                counts[table] = -1
    return counts


def pragma_integrity_check(db_path: Path) -> Tuple[bool, str]:
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        row = cur.fetchone()
        if not row:
            return False, "no_result"
        msg = str(row[0])
        return (msg.lower() == "ok"), msg


def now_ts() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


@dataclass
class SnapshotMeta:
    timestamp: str
    db_file: str
    snapshot_file: str
    snapshot_size: int
    sha256: str
    integrity_check: str
    table_counts: Dict[str, int]

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2)


def latest_snapshot() -> Optional[Path]:
    snapshots = sorted(BACKUPS_DIR.glob("*.sqlite3"))
    return snapshots[-1] if snapshots else None
