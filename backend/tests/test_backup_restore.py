from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from subprocess import check_call

HERE = Path(__file__).parent
ROOT = HERE.parent
SCRIPTS = ROOT / "scripts"
BACKUPS = ROOT / "backups"


def _init_temp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "tmp.sqlite3"
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS ballots (id INTEGER PRIMARY KEY, title TEXT)"
        )
        cur.executemany(
            "INSERT INTO users(email) VALUES (?)",
            [(f"user{i}@example.com",) for i in range(5)],
        )
        cur.executemany(
            "INSERT INTO ballots(title) VALUES (?)",
            [(f"ballot-{i}",) for i in range(3)],
        )
        conn.commit()
    return db_path


def _clean_backups_dir() -> None:
    if not BACKUPS.exists():
        return
    for artefact in BACKUPS.glob("*"):
        artefact.unlink()


def test_backup_and_restore_roundtrip(tmp_path: Path, monkeypatch) -> None:
    db_file = _init_temp_db(tmp_path)
    monkeypatch.setenv("DB_FILE", str(db_file))

    BACKUPS.mkdir(parents=True, exist_ok=True)
    _clean_backups_dir()

    # 1) Create a backup snapshot.
    check_call([sys.executable, str(SCRIPTS / "backup_db.py")])

    snapshots = sorted(BACKUPS.glob("snapshot-*.sqlite3"))
    metadata_files = sorted(BACKUPS.glob("snapshot-*.json"))
    assert len(snapshots) == 1
    assert len(metadata_files) == 1

    meta = json.loads(metadata_files[0].read_text(encoding="utf-8"))
    assert meta["integrity_check"].lower() == "ok"
    assert meta["table_counts"]["users"] == 5
    assert meta["table_counts"]["ballots"] == 3

    # 2) Corrupt live DB to simulate data loss.
    with sqlite3.connect(str(db_file)) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM users")
        cur.execute("DELETE FROM ballots")
        conn.commit()

    # 3) Restore from snapshot.
    check_call(
        [
            sys.executable,
            str(SCRIPTS / "restore_db.py"),
            "--snapshot",
            str(snapshots[0]),
        ]
    )

    with sqlite3.connect(str(db_file)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        restored_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM ballots")
        restored_ballots = cur.fetchone()[0]

    assert restored_users == 5
    assert restored_ballots == 3
