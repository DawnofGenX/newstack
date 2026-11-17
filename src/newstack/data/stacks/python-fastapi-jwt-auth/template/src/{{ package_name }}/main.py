"""Application factory and entry point."""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routes import router

DEFAULT_PORT = 5520
DEFAULT_HOST = "127.0.0.1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="jwt-auth", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()


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

    uvicorn.run(app, host=host, port=port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())