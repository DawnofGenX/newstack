"""Tiny HTTP server exposing the Prometheus metrics."""

from __future__ import annotations

import http.server
import socketserver

from .metrics import content_type, render_metrics, requests_total


class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            requests_total.labels(endpoint="/health").inc()
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/metrics":
            requests_total.labels(endpoint="/metrics").inc()
            body = render_metrics()
            self.send_response(200)
            self.send_header("Content-Type", content_type())
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True