"""The service's whole contract, as pure functions over a request path.

Keeping the answers here (rather than in the HTTP glue) is what makes the
project testable without starting a server or building an image.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

SERVICE_NAME = "{{ npm_name }}"
VERSION = "0.1.0"


@dataclass
class State:
    """What the service knows that changes between requests."""

    started_at: float = field(default_factory=time.monotonic)
    requests: int = 0

    def uptime(self) -> float:
        return round(time.monotonic() - self.started_at, 3)


@dataclass
class Reply:
    status: int
    content_type: str
    body: str

    def as_dict(self) -> dict:
        return {"status": self.status, "content_type": self.content_type, "body": self.body}


ROUTES = {"/", "/health", "/metrics"}


def build_reply(path: str, state: State, *, method: str = "GET") -> Reply:
    """Answer one request. ``path`` may carry a query string, which is ignored."""
    state.requests += 1
    route = path.split("?", 1)[0].rstrip("/") or "/"

    if method != "GET":
        return Reply(405, "application/json", json.dumps({"error": "method not allowed"}) + "\n")

    if route == "/health":
        body = {"status": "ok", "service": SERVICE_NAME, "version": VERSION}
        return Reply(200, "application/json", json.dumps(body, sort_keys=True) + "\n")

    if route == "/metrics":
        lines = [
            "# HELP requests_total Requests served since start.",
            "# TYPE requests_total counter",
            f"requests_total {state.requests}",
            "# HELP uptime_seconds Seconds since the process started.",
            "# TYPE uptime_seconds gauge",
            f"uptime_seconds {state.uptime()}",
        ]
        return Reply(200, "text/plain; version=0.0.4", "\n".join(lines) + "\n")

    if route == "/":
        body = {"service": SERVICE_NAME, "version": VERSION, "endpoints": sorted(ROUTES)}
        return Reply(200, "application/json", json.dumps(body, sort_keys=True) + "\n")

    return Reply(404, "application/json", json.dumps({"error": "not found", "path": route}) + "\n")
