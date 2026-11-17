"""Offline self-test: run a few ticks."""

from __future__ import annotations

from .worker import run_ticks


def run() -> int:
    result = run_ticks(2)
    assert result == 2
    print("selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())