"""An HTTP server whose shutdown sequence is the whole point.

The traps this file exists to handle:

* `ThreadingHTTPServer` ships `daemon_threads = True`; daemon threads are killed when
  the interpreter exits, so a request that was mid-response is simply cut off. We turn
  that off and do the joining ourselves, on a clock.
* `serve_forever()` and `shutdown()` deadlock if they run in the same thread, so the
  drain watcher is a separate thread.
* `shutdown()` stops accepting but leaves the listening socket open, so a client can
  still connect and wait forever. The listener is closed explicitly.
* A signal handler must not do the work: it flips state and returns, and the watcher
  performs the orderly part.
"""

from __future__ import annotations

import contextlib
import os
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .lifecycle import Lifecycle, Phase

EXIT_OK = 0
EXIT_DRAIN_TIMEOUT = 1
EXIT_FORCED = 130


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:
        """Silence per-request logging: the smoke test greps this stream."""

    @property
    def lifecycle(self) -> Lifecycle:
        return self.server.lifecycle  # type: ignore[attr-defined]

    def _body(self, status: int, payload: bytes, close: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        if close:
            self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            # Readiness, not liveness: a draining process must be taken out of rotation.
            if self.lifecycle.phase is Phase.RUNNING:
                self._body(200, b"ok\n")
            else:
                self.close_connection = True
                self._body(503, b"draining\n", close=True)
            return

        if not self.lifecycle.admit():
            self.close_connection = True
            self._body(503, b"draining\n", close=True)
            return

        try:
            if parsed.path != "/work":
                self._body(404, b"not found\n")
                return
            try:
                milliseconds = int(parse_qs(parsed.query).get("ms", ["100"])[0])
            except ValueError:
                self._body(400, b"ms must be an integer\n")
                return
            if milliseconds < 0 or milliseconds > 60_000:
                self._body(400, b"ms must be between 0 and 60000\n")
                return
            time.sleep(milliseconds / 1000)
            self._body(200, b"done\n")
        finally:
            self.lifecycle.release()


class Server(ThreadingHTTPServer):
    daemon_threads = False
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], lifecycle: Lifecycle) -> None:
        self.lifecycle = lifecycle
        super().__init__(address, Handler)


def _watch(server: Server, lifecycle: Lifecycle, stop: threading.Event) -> None:
    """Runs in its own thread: shutdown() cannot be called from the serving thread."""
    stop.wait()
    server.shutdown()
    # shutdown() stops accepting but leaves the socket bound: without this close a
    # client still connects and then waits for a process that is already leaving.
    with contextlib.suppress(OSError):
        server.socket.close()
    lifecycle.wait_for_idle()


def serve(port: int = 5477, host: str = "127.0.0.1", drain_timeout: float = 10.0) -> int:
    lifecycle = Lifecycle(drain_timeout)
    server = Server((host, port), lifecycle)
    print(f"listening {host}:{server.server_address[1]}", flush=True)

    stop = threading.Event()

    def on_signal(signum: int, _frame: object) -> None:
        if stop.is_set():
            # A second signal means someone is waiting for a deploy that will not finish.
            # os._exit skips cleanup on purpose: the alternative is a hung container.
            print(f"second signal {signum}: forcing exit", flush=True)
            os._exit(EXIT_FORCED)
        stop.set()
        lifecycle.begin_drain()
        print(f"signal {signum}: draining {lifecycle.in_flight} request(s)", flush=True)

    previous = {sig: signal.signal(sig, on_signal) for sig in (signal.SIGTERM, signal.SIGINT)}
    watcher = threading.Thread(target=_watch, args=(server, lifecycle, stop), name="drain")
    watcher.start()
    try:
        server.serve_forever(poll_interval=0.05)
        # The drain is still running here: restoring the default handlers now would turn
        # the second SIGTERM into an immediate kill instead of the 130 we promise.
        watcher.join()
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    if lifecycle.drain_ok:
        print(f"drained {lifecycle.served} request(s) in {lifecycle.drained_in:.2f}s", flush=True)
        server.server_close()
        print("stopped", flush=True)
        return EXIT_OK
    # A deadline you do not honour is not a deadline. server_close() joins the very
    # threads that blew it, so the deploy would hang until they finished anyway and the
    # timeout would be decoration. Leaving costs the in-flight work; that is the trade.
    still_running = lifecycle.in_flight
    print(
        f"drain timeout after {drain_timeout:g}s, {still_running} request(s) unfinished",
        flush=True,
    )
    os._exit(EXIT_DRAIN_TIMEOUT)
