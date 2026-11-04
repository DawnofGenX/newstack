"""Tiny HTTP server: the only file that knows about sockets."""

from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from service import State, build_reply

STATE = State()


class Handler(BaseHTTPRequestHandler):
    server_version = "TextStatService/0.1.0"

    def _reply(self) -> None:
        reply = build_reply(self.path, STATE, method=self.command)
        payload = reply.body.encode("utf-8")
        self.send_response(reply.status)
        self.send_header("Content-Type", reply.content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = _reply

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler naming
        self._reply()

    def log_message(self, fmt: str, *args) -> None:
        if os.environ.get("LOG_REQUESTS", "1") != "0":
            super().log_message(fmt, *args)


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"{{ npm_name }} listening on :{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
