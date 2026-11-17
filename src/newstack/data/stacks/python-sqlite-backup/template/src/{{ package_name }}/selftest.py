"""Offline self-test."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from .backup import backup, integrity_ok


def run() -> int:
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "a.db"
        conn = sqlite3.connect(str(src))
        conn.execute("CREATE TABLE t(x INTEGER)")
        conn.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(5)])
        conn.commit()
        conn.close()
        out = backup(src, Path(td) / "backups", keep=2)
        assert out.exists()
        assert integrity_ok(out)
    print("selftest: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())