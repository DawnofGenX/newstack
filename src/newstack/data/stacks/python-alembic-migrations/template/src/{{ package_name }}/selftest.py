"""Offline self-test for migration metadata."""

from __future__ import annotations

from . import latest_revision


def run() -> int:
    assert latest_revision() == "0002"
    print("selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())