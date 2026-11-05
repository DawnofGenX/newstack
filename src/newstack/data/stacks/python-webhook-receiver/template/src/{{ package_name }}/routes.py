"""The HTTP layer. The order of the checks is the whole point of this service."""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from . import signature

SIGNATURE_HEADER = "X-Signature"
TIMESTAMP_HEADER = "X-Timestamp"
EVENT_HEADER = "X-Event-Id"

Clock = Callable[[], int]


def error(status: int, kind: str, detail: str | None = None) -> JSONResponse:
    body: dict[str, Any] = {"error": kind}
    if detail is not None:
        body["detail"] = detail
    return JSONResponse(status_code=status, content=body)


def build_router(connection: sqlite3.Connection, secrets: dict[str, str], clock: Clock) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, Any]:
        count = connection.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
        return {"status": "ok", "events": count}

    @router.get("/events")
    def events() -> dict[str, Any]:
        rows = connection.execute(
            "SELECT id, source, received_at FROM events ORDER BY received_at, id"
        ).fetchall()
        return {"events": [dict(row) for row in rows]}

    @router.post("/webhooks/{source}", status_code=202)
    async def receive(
        request: Request,
        source: str,
        x_signature: str | None = Header(default=None),
        x_timestamp: str | None = Header(default=None),
        x_event_id: str | None = Header(default=None),
    ):
        secret = secrets.get(source)
        if secret is None:
            return error(404, "unknown_source", f"no secret configured for source {source}")

        # Read the bytes once. Every later decision uses `raw`; a re-serialised dict
        # (`json.dumps(json.loads(raw))`) is a different byte string — spacing, key order and
        # unicode escapes all move — and the digest would never match.
        raw = await request.body()

        failure = signature.verify(
            secret=secret,
            header=x_signature,
            timestamp=x_timestamp,
            body=raw,
            now=clock(),
        )
        if failure is not None:
            return error(401, failure.kind)

        if not x_event_id:
            return error(400, "missing_event_id")

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            return error(422, "invalid_json", f"{exc.msg} at column {exc.colno}")

        received_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(clock()))
        try:
            connection.execute(
                "INSERT INTO events (id, source, received_at, body, signature) "
                "VALUES (?, ?, ?, ?, ?)",
                (x_event_id, source, received_at, raw.decode("utf-8"), x_signature),
            )
        except sqlite3.IntegrityError:
            # A sender that retries the same event id gets a 200 and no second row.
            return JSONResponse(
                status_code=200,
                content={"status": "duplicate", "id": x_event_id, "source": source},
            )
        kind = payload.get("kind") if isinstance(payload, dict) else None
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "id": x_event_id,
                "source": source,
                "kind": kind,
            },
        )

    return router
