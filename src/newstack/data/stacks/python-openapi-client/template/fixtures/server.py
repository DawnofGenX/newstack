"""A tiny notes server, conforming by default and drifted on request.

Two ports, one script: `--drift` makes every note disagree with the spec in the
three ways a real service drifts - a wrong type, an undeclared member, and an
enum value the schema never allowed.
"""

from __future__ import annotations

import argparse
import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

NOTES = [
    {
        "id": "1",
        "title": "first",
        "tags": ["a"],
        "pinned": False,
        "body": None,
        "priority": "normal",
    },
    {"id": "2", "title": "second", "tags": [], "pinned": True, "priority": "high"},
]


def drifted(note: dict[str, object]) -> dict[str, object]:
    broken = dict(note)
    broken["tags"] = 7  # was an array
    broken["server_side"] = True  # not in the schema
    broken["priority"] = "urgent"  # not in the enum
    return broken


def make_handler(drift: bool) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: object) -> None:
            return

        def reply(self, status: int, payload: object) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/notes":
                notes = [drifted(note) if drift else note for note in NOTES]
                self.reply(HTTPStatus.OK, notes)
                return
            if path.startswith("/notes/"):
                wanted = path[len("/notes/") :]
                for note in NOTES:
                    if note["id"] == wanted:
                        self.reply(HTTPStatus.OK, drifted(note) if drift else note)
                        return
                self.reply(HTTPStatus.NOT_FOUND, {"error": "not_found", "detail": wanted})
                return
            self.reply(HTTPStatus.NOT_FOUND, {"error": "not_found", "detail": path})

        def do_POST(self) -> None:
            length = int(self.headers.get("content-length", "0"))
            raw = self.rfile.read(length) if length else b""
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.reply(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "invalid_json"})
                return
            if not isinstance(payload, dict) or not payload.get("title"):
                self.reply(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "missing_title"})
                return
            created = {
                "id": str(len(NOTES) + 1),
                "title": payload["title"],
                "tags": payload.get("tags", []),
                "pinned": False,
                "body": payload.get("body"),
                "priority": payload.get("priority", "normal"),
            }
            NOTES.append(created)
            self.reply(HTTPStatus.CREATED, drifted(created) if drift else created)

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="notes server")
    parser.add_argument("--port", type=int, default=5473)
    parser.add_argument(
        "--drift", action="store_true", help="answer with responses the spec forbids"
    )
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(args.drift))
    print(f"listening on http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever(poll_interval=0.05)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
