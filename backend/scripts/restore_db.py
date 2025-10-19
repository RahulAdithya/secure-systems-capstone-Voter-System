from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent))
    from _backup_utils import (  # type: ignore  # noqa: F401
        BACKUPS_DIR,
        latest_snapshot,
        pragma_integrity_check,
        resolve_db_path,
        sha256_file,
    )
else:
    from ._backup_utils import (
        BACKUPS_DIR,
        latest_snapshot,
        pragma_integrity_check,
        resolve_db_path,
        sha256_file,
    )


def restore_db(snapshot: Path | None) -> int:
    db_path = resolve_db_path()
    target_snapshot = snapshot or latest_snapshot()
    if target_snapshot is None:
        print("[ERR] No snapshots found.")
        return 2

    meta_path = target_snapshot.with_suffix(".json")
    if not meta_path.exists():
        print(f"[ERR] Metadata file missing: {meta_path}")
        return 3

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    expected_sha = meta.get("sha256")

    actual_sha = sha256_file(target_snapshot)
    if expected_sha and actual_sha != expected_sha:
        print(f"[ERR] SHA256 mismatch! expected={expected_sha} actual={actual_sha}")
        return 4

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        ts = time.strftime("%Y%m%d-%H%M%S")
        pre_restore = db_path.with_suffix(f".pre-restore.{ts}.sqlite3")
        shutil.copy2(db_path, pre_restore)
        print(f"[INFO] Current DB backed up to: {pre_restore}")

    shutil.copy2(target_snapshot, db_path)
    print(f"[OK] Restored snapshot to: {db_path}")

    ok, integrity_msg = pragma_integrity_check(db_path)
    print(f"[INFO] integrity_check={integrity_msg}")
    return 0 if ok else 5


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restore a SQLite snapshot into the live DB."
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=None,
        help="Path to a specific snapshot (*.sqlite3). If omitted, uses latest.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    options = _parse_args()
    raise SystemExit(restore_db(options.snapshot))
