"""aiohttp application factory."""

from __future__ import annotations

import json

from aiohttp import web

from .stats import analyze


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def stats(request: web.Request) -> web.Response:
    if request.method == "GET":
        if "text" not in request.query:
            return web.json_response({"error": "missing_text"}, status=422)
        text = request.query["text"]
    else:
        try:
            payload = await request.json()
        except (json.JSONDecodeError, TypeError):
            return web.json_response({"error": "invalid_json"}, status=422)
        if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
            return web.json_response({"error": "missing_text"}, status=422)
        text = payload["text"]
    return web.json_response(analyze(text))


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get("/stats", stats)
    app.router.add_post("/stats", stats)
    return app