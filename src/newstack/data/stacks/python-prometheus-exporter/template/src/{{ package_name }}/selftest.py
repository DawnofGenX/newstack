"""Offline self-test: render metrics and assert exposition format."""

from __future__ import annotations

from .metrics import render_metrics


def run() -> int:
    body = render_metrics()
    assert b"app_up" in body
    assert b"# HELP" in body
    assert b"# TYPE" in body
    print("selftest ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())