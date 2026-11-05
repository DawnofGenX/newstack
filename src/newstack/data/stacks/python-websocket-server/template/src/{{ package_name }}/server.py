"""Threaded TCP server. Each connection is served on its own thread."""

from socketserver import ThreadingTCPServer

from .connection import handle

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5489


class WSServer(ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def make_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> WSServer:
    return WSServer((host, port), _Handler)


class _Handler:
    """socketserver-style handler delegating to connection.handle."""

    def __init__(self, request, client_addr, server) -> None:
        handle(request)


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = make_server(host, port)
    print(f"listening on ws://{host}:{port}/ws", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
