"""Offline self-test."""

from __future__ import annotations

import tempfile
from pathlib import Path

from .store import Store


def run() -> int:
    with tempfile.TemporaryDirectory() as td:
        store = Store(Path(td) / "store")
        store.put(b"hello", name="greeting")
        assert store.get("greeting") == b"hello"
        assert store.verify()["ok"]
    print("selftest: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())