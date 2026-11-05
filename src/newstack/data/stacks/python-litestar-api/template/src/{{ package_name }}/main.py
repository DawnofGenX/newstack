"""Entry point: `--selftest` for the offline checks, everything else starts a server.

`PORT` is read here rather than by uvicorn so a bad value fails before the socket
exists, with a message, instead of a traceback from inside the server thread.
"""

from __future__ import annotations

import os
import sys

DEFAULT_PORT = 8080
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

    import uvicorn

    from .app import app

    # `uvicorn.run(app_object)` serves the same app the tests build; passing an
    # import string would import a second copy and let module-level state drift.
    uvicorn.run(app, host=host, port=port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
