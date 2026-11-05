"""App factory: collaborators arrive as arguments so the tests control the clock, the
secrets and the database file."""

from __future__ import annotations

import os
import time
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import db
from .routes import build_router

SECRET_ENV_PREFIX = "WEBHOOK_SECRET_"


def secrets_from_env() -> dict[str, str]:
    found = {}
    for key, value in os.environ.items():
        if key.startswith(SECRET_ENV_PREFIX) and value:
            found[key[len(SECRET_ENV_PREFIX) :].lower()] = value
    return found


def create_app(
    *,
    db_path: str | None = None,
    secrets: dict[str, str] | None = None,
    clock: Callable[[], float] = time.time,
) -> FastAPI:
    path = db_path or os.environ.get("DB_PATH", "events.db")
    configured = secrets if secrets is not None else secrets_from_env()

    # Opened here, not in a lifespan: the router needs the handle at build time, and a
    # sqlite connection is cheap. `check_same_thread=False` is safe because every handler
    # runs on the event loop.
    connection = db.connect(path)
    db.migrate(connection)

    app = FastAPI(title="webhook receiver")
    app.state.connection = connection

    def now() -> int:
        return int(clock())

    app.include_router(build_router(connection, configured, now))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            detail = f"no route for {request.method} {request.url.path}"
            return JSONResponse(status_code=404, content={"error": "not_found", "detail": detail})
        if exc.status_code == 405:
            return JSONResponse(status_code=405, content={"error": "method_not_allowed"})
        return JSONResponse(status_code=exc.status_code, content={"error": "http_error"})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first["loc"])
        return JSONResponse(
            status_code=422,
            content={"error": "invalid_request", "detail": f"{location}: {first['msg']}"},
        )

    return app


app = create_app()
