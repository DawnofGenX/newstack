"""The socket side: one thread per connection, one shared keyspace."""

from __future__ import annotations

import socket
import threading
import time

from . import commands, protocol
from .protocol import CommandReader, ProtocolError
from .store import Store

RECV_SIZE = 4096


class Server:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        *,
        store: Store | None = None,
        idle: float = 30.0,
        backlog: int = 64,
        accept_timeout: float = 0.2,
    ) -> None:
        self.host = host
        self._port = port
        self.store = store or Store()
        self.idle = idle
        self.backlog = backlog
        self.accept_timeout = accept_timeout
        self._listener: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stopping = threading.Event()
        self._clients: set[socket.socket] = set()
        self._lock = threading.Lock()
        self.connections = 0

    # -- lifecycle -------------------------------------------------------
    def start(self) -> Server:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, self._port))
        listener.listen(self.backlog)
        listener.settimeout(self.accept_timeout)
        self._port = listener.getsockname()[1]
        self._listener = listener
        self._thread = threading.Thread(target=self.serve_forever, name="resp-accept", daemon=True)
        self._thread.start()
        return self

    @property
    def port(self) -> int:
        return self._port

    def serve_forever(self) -> None:
        assert self._listener is not None
        while not self._stopping.is_set():
            try:
                connection, _ = self._listener.accept()
            except TimeoutError:
                continue
            except OSError:
                break
            with self._lock:
                self._clients.add(connection)
                self.connections += 1
            threading.Thread(
                target=self._serve_client, args=(connection,), name="resp-client", daemon=True
            ).start()

    def shutdown(self) -> None:
        self._stopping.set()
        if self._listener is not None:
            try:
                self._listener.close()
            except OSError:
                pass
        with self._lock:
            clients = list(self._clients)
            self._clients.clear()
        for connection in clients:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                connection.close()
            except OSError:
                pass
        if self._thread is not None:
            self._thread.join(timeout=5)

    def __enter__(self) -> Server:
        return self.start()

    def __exit__(self, *exc_info) -> None:
        self.shutdown()

    # -- one connection --------------------------------------------------
    def _serve_client(self, connection: socket.socket) -> None:
        reader = CommandReader()
        try:
            connection.settimeout(self.idle)
            while not self._stopping.is_set():
                try:
                    chunk = connection.recv(RECV_SIZE)
                except TimeoutError:
                    break
                except OSError:
                    break
                if not chunk:
                    break
                try:
                    parsed = reader.feed(chunk)
                except ProtocolError as exc:
                    _send(connection, protocol.encode_error(f"ERR Protocol error: {exc}"))
                    break
                for args in parsed:
                    if not args:
                        continue
                    reply = commands.execute(self.store, args)
                    if not _send(connection, reply):
                        return
        finally:
            with self._lock:
                self._clients.discard(connection)
            try:
                connection.close()
            except OSError:
                pass


def _send(connection: socket.socket, payload: bytes) -> bool:
    """write() in a loop: a partial send is normal, a lost socket is not."""
    try:
        connection.sendall(payload)
    except OSError:
        return False
    return True


def parse_port(raw: str) -> int:
    try:
        port = int(raw)
    except ValueError as exc:
        raise ValueError(f"PORT must be a number, got {raw!r}") from exc
    if not 0 <= port <= 65535:
        raise ValueError(f"PORT must be between 0 and 65535, got {port}")
    return port


def wait_until_ready(host: str, port: int, timeout: float = 5.0) -> bool:
    """Poll with a real connection: listen() succeeding is not the same as serving."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.01)
    return False
