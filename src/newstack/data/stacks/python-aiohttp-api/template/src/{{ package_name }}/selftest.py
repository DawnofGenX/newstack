"""Offline contract check: `python -m {{ package_name }} --selftest`."""

from __future__ import annotations

from .stats import analyze


def run() -> int:
    result = analyze("hello world\n")
    assert result == {"text": "hello world\n", "lines": 1, "words": 2, "bytes": 12}
    empty = analyze("")
    assert empty == {"text": "", "lines": 0, "words": 0, "bytes": 0}
    print("selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())