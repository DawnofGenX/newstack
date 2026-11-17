"""Offline self-test."""

from __future__ import annotations

from .fts import add_document, connect, ensure_schema, search


def run() -> int:
    conn = connect(":memory:")
    ensure_schema(conn)
    add_document(conn, 1, "hello world", "the quick brown fox")
    add_document(conn, 2, "goodbye", "nothing relevant here")
    res = search(conn, "quick")
    assert len(res) >= 1
    assert res[0]["id"] == 1
    conn.close()
    print("selftest: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())