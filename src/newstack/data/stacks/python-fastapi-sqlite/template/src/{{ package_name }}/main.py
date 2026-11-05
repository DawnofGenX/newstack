"""Application factory: migrate on startup, mount the routes, expose ``app``."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import connect, migrate
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    connection = connect()
    try:
        migrate(connection)
    finally:
        connection.close()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="notes", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
