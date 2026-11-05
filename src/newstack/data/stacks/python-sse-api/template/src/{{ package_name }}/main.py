"""App factory: routes plus the error shapes the tests pin down."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import router


def _validation_detail(errors: list[dict]) -> str:
    if not errors:
        return "the request is not valid"
    first = errors[0]
    location = ".".join(str(part) for part in first.get("loc", ()) if part != "query")
    message = first.get("msg", "is not valid")
    return f"{location}: {message}" if location else message


def create_app() -> FastAPI:
    app = FastAPI(title="event-stream", version="0.1.0")
    app.include_router(router)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        # FastAPI's default body is a list of pydantic errors; a stream client wants
        # one sentence it can log, and a fixed shape it can branch on.
        return JSONResponse(
            status_code=422,
            content={"error": "invalid_request", "detail": _validation_detail(exc.errors())},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict):
            content = detail
        elif exc.status_code == 404:
            # Starlette's own 404 carries only "Not Found": the client is told which
            # request missed, and a query string is part of what it asked for.
            target = request.url.path
            if request.url.query:
                target = f"{target}?{request.url.query}"
            content = {"error": "not_found", "detail": f"no route for {request.method} {target}"}
        elif exc.status_code == 405:
            content = {
                "error": "method_not_allowed",
                "detail": f"{request.method} is not allowed here",
            }
        else:
            content = {"error": "http_error", "detail": str(detail)}
        return JSONResponse(status_code=exc.status_code, content=content)

    return app


app = create_app()
