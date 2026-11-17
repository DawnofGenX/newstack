"""Entry point: `--selftest` for offline checks, otherwise serve metrics."""

from __future__ import annotations

import os
import sys

DEFAULT_PORT = 5501
DEFAULT_HOST = "127.0.0.1"


def port_from_env(raw: str | None) -> int:
    if raw is None or raw == "":
        return DEFAULT_PORT
    try:
        port = int(raw, 10)
    except ValueError:
        raise SystemExit(f"PORT={raw!r} is not a number") from None
    if not 1 <= port <= 65535:
        raise SystemExit(f"PORT={port} is outside 1-65535")
    return port


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from .selftest import run

        return run()
    port = port_from_env(os.environ.get("PORT"))
    host = os.environ.get("HOST") or DEFAULT_HOST

    from .server import MetricsHandler, ThreadingServer

    httpd = ThreadingServer((host, port), MetricsHandler)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())