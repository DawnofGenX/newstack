"""SQLite backup helpers using the connection backup API."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class BackupError(Exception):
    pass


def row_counts(conn_or_path) -> dict[str, int]:
    if hasattr(conn_or_path, "execute"):
        conn = conn_or_path
        close = False
    else:
        conn = sqlite3.connect(str(conn_or_path))
        close = True
    try:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        ]
        out: dict[str, int] = {}
        for t in tables:
            out[t] = conn.execute(f"SELECT COUNT(*) FROM \"{t}\"").fetchone()[0]
        return out
    finally:
        if close:
            conn.close()


def integrity_ok(db_path: Path | str) -> bool:
    try:
        conn = sqlite3.connect(str(db_path))
    except (sqlite3.Error, OSError):
        return False
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        return result == "ok"
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def verify_row_counts(src_path: Path | str, copy_path: Path | str) -> None:
    src = sqlite3.connect(str(src_path))
    dst = sqlite3.connect(str(copy_path))
    try:
        if row_counts(src) != row_counts(dst):
            raise BackupError(f"row count mismatch: {row_counts(src)} vs {row_counts(dst)}")
    finally:
        src.close()
        dst.close()


def backup(src: Path | str, dest_dir: Path | str, keep: int = 5) -> Path:
    src_path = Path(src)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = dest / f"{src_path.stem}-{ts}.db"

    src_conn = sqlite3.connect(str(src_path))
    try:
        dst_conn = sqlite3.connect(str(out))
        try:
            # Uses the stdlib Connection.backup API.
            src_conn.backup(dst_conn)
            dst_conn.commit()
        finally:
            dst_conn.close()
        # integrity check on copy
        if not integrity_ok(out):
            out.unlink(missing_ok=True)
            raise BackupError("integrity check failed on copy")
        verify_row_counts(src_path, out)
    finally:
        src_conn.close()

    # rotation: keep newest N by name (timestamp embedded)
    copies = sorted(dest.glob(f"{src_path.stem}-*.db"), key=lambda p: p.name)
    while len(copies) > keep:
        oldest = copies.pop(0)
        oldest.unlink(missing_ok=True)

    return out