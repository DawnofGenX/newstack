"""Offline self-test."""

from __future__ import annotations

import io
import json

from .jsonlog import JsonLogger


def run() -> int:
    buf = io.StringIO()
    log = JsonLogger("t", output=buf)
    log.info("hi", n=1)
    out = buf.getvalue().strip()
    assert out.startswith("{")
    obj = json.loads(out)
    assert obj["message"] == "hi"
    assert obj["n"] == 1
    print("selftest: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())