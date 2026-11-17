"""Offline self-test."""

from __future__ import annotations

import tempfile
from pathlib import Path

from .report import build_report


def run() -> int:
    with tempfile.TemporaryDirectory() as td:
        rows = [{"name": "a", "value": 1.5}, {"name": "b", "value": 2.5}]
        out = Path(td) / "r.xlsx"
        build_report(rows, out)
        assert out.exists()
    print("selftest: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())