"""App wiring: migrations on boot, the ticker on the lifespan, errors in one shape."""

from __future__ import annotations

import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import db, routes
from .worker import Scheduler


def create_app(
    db_path: Path | str | None = None,
    *,
    tick: float | None = None,
    clock: Any = time.time,
    start_ticker: bool = True,
) -> FastAPI:
    path = Path(db_path) if db_path is not None else Path(os.environ.get("DB_PATH", "scheduler.db"))
    interval = tick if tick is not None else float(os.environ.get("TICK_SECONDS", "0.2"))

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        connection = db.connect(path)
        db.migrate(connection)
        connection.close()
        scheduler = Scheduler(path, tick=interval, clock=clock)
        app.state.scheduler = scheduler
        if start_ticker:
            scheduler.start()
        try:
            yield
        finally:
            scheduler.stop()

    app = FastAPI(title="scheduler", lifespan=lifespan)
    app.state.db_path = path
    app.state.clock = clock
    app.include_router(routes.router)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Only the errors this app raised itself carry a dict detail; anything
        # Starlette produced (a bare 404, a 405) gets the same envelope so a
        # client never has to guess which shape it is looking at.
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        method = request.method
        target = request.url.path
        if request.url.query:
            target += "?" + request.url.query
        if exc.status_code == 404:
            detail = {"error": "not_found", "detail": f"no route for {method} {request.url.path}"}
        elif exc.status_code == 405:
            detail = {
                "error": "method_not_allowed",
                "detail": f"{method} {target} does not accept that method",
            }
        else:
            detail = {"error": "http_error", "detail": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail)

    @app.exception_handler(RequestValidationError)
    async def _invalid(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {"loc": [], "msg": "invalid"}
        where = ".".join(str(part) for part in first.get("loc", ()) if part != "body")
        return JSONResponse(
            status_code=422,
            content={
                "error": "invalid_request",
                "detail": f"{where or 'body'}: {first.get('msg', 'invalid')}",
            },
        )

    return app


app = create_app()
