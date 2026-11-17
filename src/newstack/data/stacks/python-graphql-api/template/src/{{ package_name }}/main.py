"""Entry point: `--selftest` for offline checks, otherwise an HTTP server."""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_PORT = 5530
DEFAULT_HOST = "127.0.0.1"


def port_from_env(raw: str | None) -> int:
    if raw is None or raw == "":
        return DEFAULT_PORT
    try:
        port = int(raw, 10)
    except ValueError:
        raise SystemExit(f"PORT={raw!r} is not a number") from None
    if not 1 <= port <= 65535:
        raise SystemExit(f"PORT={port} is outside 1-65535")
    return port


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/health":
            body = json.dumps({"status": "ok"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404, "not found")

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/graphql":
            self.send_error(404, "not found")
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            payload = {}
        from graphql import graphql_sync

        from .schema import schema

        result = graphql_sync(
            schema,
            payload.get("query", ""),
            variable_values=payload.get("variables"),
            operation_name=payload.get("operationName"),
        )
        body = json.dumps(result.formatted, default=str).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:  # quiet
        return


def serve(host: str, port: int) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        from .selftest import run

        return run()
    port = port_from_env(os.environ.get("PORT"))
    host = os.environ.get("HOST") or DEFAULT_HOST
    serve(host, port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())