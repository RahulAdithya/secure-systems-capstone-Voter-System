from __future__ import annotations

import argparse
import shutil

from pathlib import Path

from _backup_utils import (
    BACKUPS_DIR,
    SnapshotMeta,
    now_ts,
    pragma_integrity_check,
    resolve_db_path,
    sha256_file,
    table_counts,
)


def backup_db() -> int:
    db_path = resolve_db_path()
    if not db_path.exists():
        print(f"[ERR] DB file not found: {db_path}")
        return 2

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = now_ts()
    snapshot = BACKUPS_DIR / f"snapshot-{ts}.sqlite3"
    meta_path = BACKUPS_DIR / f"snapshot-{ts}.json"

    shutil.copy2(db_path, snapshot)

    sha = sha256_file(snapshot)
    ok, integrity_msg = pragma_integrity_check(snapshot)
    counts = table_counts(snapshot)

    meta = SnapshotMeta(
        timestamp=ts,
        db_file=str(db_path),
        snapshot_file=str(snapshot),
        snapshot_size=snapshot.stat().st_size,
        sha256=sha,
        integrity_check=integrity_msg,
        table_counts=counts,
    )
    meta_path.write_text(meta.to_json(), encoding="utf-8")

    print(
        "[OK] Backup created:\n"
        f"- DB: {db_path}\n"
        f"- SNAPSHOT: {snapshot}\n"
        f"- META: {meta_path}"
    )
    print(
        f"[INFO] sha256={sha} integrity_check={integrity_msg} tables={len(counts)}"
    )
    return 0 if ok else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a timestamped SQLite snapshot with metadata."
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    raise SystemExit(backup_db())
