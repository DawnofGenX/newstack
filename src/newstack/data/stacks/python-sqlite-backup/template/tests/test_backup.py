import sqlite3
import tempfile
from pathlib import Path

from {{ package_name }}.backup import (
    BackupError,
    backup,
    integrity_ok,
    row_counts,
    verify_row_counts,
)


def make_db(path, n=7):
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE items(id INTEGER PRIMARY KEY, v TEXT)")
    conn.executemany("INSERT INTO items(v) VALUES (?)", [(f"row{i}",) for i in range(n)])
    conn.commit()
    conn.close()


def test_backup_creates_file_and_integrity():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "src.db"
        make_db(src)
        out = backup(src, Path(td) / "bak", keep=3)
        assert out.exists()
        assert integrity_ok(out)
        assert row_counts(src) == row_counts(out)


def test_rotation_keeps_newest():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "src.db"
        make_db(src)
        d = Path(td) / "bak"
        outs = [backup(src, d, keep=2) for _ in range(4)]
        files = sorted(d.glob("src-*.db"))
        assert len(files) == 2
        # newest kept
        assert outs[-1].name in {p.name for p in files}


def test_integrity_check_corrupted_copy():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "src.db"
        make_db(src)
        out = backup(src, Path(td) / "bak", keep=3)
        # corrupt
        with open(out, "rb+") as f:
            f.seek(100)
            f.write(b"\x00" * 16)
        assert not integrity_ok(out)


def test_row_count_mismatch_detection():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "src.db"
        make_db(src, n=5)
        out = backup(src, Path(td) / "bak", keep=3)
        # delete a row in copy to create mismatch
        conn = sqlite3.connect(str(out))
        conn.execute("DELETE FROM items WHERE id=1")
        conn.commit()
        conn.close()
        try:
            verify_row_counts(src, out)
        except BackupError:
            return
        raise AssertionError("expected BackupError")