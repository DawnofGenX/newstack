"""Run the handler once per key; replay its stored answer after that."""

from __future__ import annotations

from collections.abc import Callable

from . import model
from .store import Store

Handler = Callable[[model.Request], model.Response]


def execute(
    store: Store,
    request: model.Request,
    handler: Handler,
    *,
    lease_s: float | None = None,
) -> model.Outcome:
    """Claim, run, complete. A replay never reaches the handler."""
    claim = store.claim(request, lease_s=lease_s)
    if claim.replay:
        return model.Outcome(
            key=request.key,
            status=int(claim.status or 200),
            body=claim.body or "",
            replay=True,
            attempts=claim.attempt,
        )
    try:
        response = handler(request)
    except BaseException:
        store.release(request, claim.attempt)
        raise
    store.complete(request, claim.attempt, response)
    return model.Outcome(
        key=request.key,
        status=response.status,
        body=response.body,
        replay=False,
        attempts=claim.attempt,
    )
