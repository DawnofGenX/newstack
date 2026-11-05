"""Routes. The two streaming endpoints are the point of this stack."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .counts import count_text
from .wire import encode_comment, encode_json

router = APIRouter()

# Proxy and browser behaviour: without no-cache a buffering proxy holds the whole
# body until the last event, which turns a stream into a slow single response.
STREAM_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def not_found(request: Request) -> JSONResponse:
    target = request.url.path
    if request.url.query:
        target = f"{target}?{request.url.query}"
    return JSONResponse(
        status_code=404,
        content={"error": "not_found", "detail": f"no route for {request.method} {target}"},
    )


def method_not_allowed(request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=405,
        content={"error": "method_not_allowed", "detail": f"{request.method} is not allowed here"},
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/stream")
async def stream(
    request: Request,
    count: int = Query(5, ge=1, le=100),
    delay: float = Query(0.05, ge=0, le=1),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> StreamingResponse:
    """Emit *count* tick events, honouring a resume point.

    A reconnect sends the last id it saw, so the stream continues instead of
    replaying: the first event after a resume with ``Last-Event-ID: 2`` is 3.
    """
    start = 1
    if last_event_id is not None:
        try:
            start = int(last_event_id) + 1
        except ValueError:
            start = 1

    async def body() -> AsyncIterator[str]:
        yield encode_comment("stream open")
        for sequence in range(start, count + 1):
            if await request.is_disconnected():
                # Stop reading the clock for a client that is gone; otherwise the
                # generator keeps a connection slot until the whole count elapses.
                return
            yield encode_json({"seq": sequence}, event="tick", event_id=str(sequence))
            if delay and sequence < count:
                await asyncio.sleep(delay)
        yield encode_json({"ticks": count, "resumed_from": start - 1}, event="done")

    return StreamingResponse(body(), media_type="text/event-stream", headers=STREAM_HEADERS)


@router.get("/stats/stream")
async def stats_stream(
    text: str = Query(..., min_length=0, max_length=4096),
    size: int = Query(4, ge=1, le=64),
    delay: float = Query(0.0, ge=0, le=1),
) -> StreamingResponse:
    """Stream one event per slice of *text*, each carrying the running totals."""

    async def body() -> AsyncIterator[str]:
        yield encode_comment("stream open")
        seen = ""
        sequence = 0
        for index in range(0, max(len(text), 1), size):
            chunk = text[index : index + size]
            seen += chunk
            sequence += 1
            totals = count_text(seen)
            yield encode_json(
                {"seq": sequence, "chunk": chunk, **totals.as_dict()},
                event="chunk",
                event_id=str(sequence),
            )
            if delay:
                await asyncio.sleep(delay)
        yield encode_json({"ticks": sequence, **count_text(seen).as_dict()}, event="done")

    return StreamingResponse(body(), media_type="text/event-stream", headers=STREAM_HEADERS)


@router.post("/stream")
async def stream_post(request: Request) -> JSONResponse:
    """A POST body is a request, not a subscription: say so instead of streaming."""
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = None
    if payload is None:
        raise HTTPException(status_code=422, detail={"error": "invalid_json"})
    raise HTTPException(
        status_code=405,
        detail={"error": "method_not_allowed", "detail": "POST /stream does not stream"},
    )
