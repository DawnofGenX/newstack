"""Masking WebSocket client for tests and smoke.sh (stdlib only).

Masks every client->server frame (RFC 6455 requires it) and exposes raw
send_frame() so tests can also emit deliberately broken frames.
"""

import contextlib
import socket

from .frames import (
    OP_CLOSE,
    OP_PING,
    OP_TEXT,
    FrameReader,
    close_payload,
    encode,
)
from .handshake import make_accept

DEFAULT_TIMEOUT = 5.0


def _recv_exactly(sock, n, buf):
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError("closed mid-read")
        buf += chunk
    return buf


class WSClient:
    def __init__(self, host: str, port: int, path: str = "/ws", timeout: float = DEFAULT_TIMEOUT):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        self._buf = bytearray()
        key = "dGhlIHNhbXBsZSBub25jZQ=="  # RFC 6455 example key
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        head = bytearray()
        while not head.endswith(b"\r\n\r\n"):
            head += self.sock.recv(1)
        self._assert_accept(head.decode("latin-1"), key)
        self.reader = _ClientReader(self.sock, self._buf)

    @staticmethod
    def _assert_accept(head: str, key: str) -> None:
        lines = head.split("\r\n")
        status = lines[0]
        if "101" not in status:
            raise ConnectionError(f"handshake failed: {status}")
        expected = make_accept(key)
        for line in lines[1:]:
            name, _, value = line.partition(":")
            if name.strip().lower() == "sec-websocket-accept":
                if value.strip() != expected:
                    raise ConnectionError("bad Sec-WebSocket-Accept")
                return
        raise ConnectionError("missing Sec-WebSocket-Accept")

    # -- sending -------------------------------------------------------------

    def send_frame(self, fin: bool, opcode: int, payload: bytes = b"", mask: bool = True) -> None:
        """Low-level send; mask=False exists only for violation tests."""
        self.sock.sendall(encode(opcode, payload, fin=fin, mask=mask))

    def send_text(self, text: str) -> None:
        self.send_frame(True, OP_TEXT, text.encode("utf-8"))

    def send_binary(self, data: bytes) -> None:
        self.send_frame(True, 0x2, data)

    def send_ping(self, data: bytes = b"") -> None:
        self.send_frame(True, OP_PING, data)

    def send_close(self, code: int = 1000) -> None:
        self.send_frame(True, OP_CLOSE, close_payload(code))

    # -- receiving -----------------------------------------------------------

    def receive(self, timeout: float | None = None):
        """Return the next Frame (auto-answering server pings is not needed:
        this server never pings). Raises EOFError on clean TCP close."""
        old = self.sock.gettimeout()
        if timeout is not None:
            self.sock.settimeout(timeout)
        try:
            return self.reader.read()
        finally:
            if timeout is not None:
                self.sock.settimeout(old)

    def recv_text(self, timeout: float | None = None) -> str:
        frame = self.receive(timeout)
        return frame.payload.decode("utf-8")

    def close(self) -> None:
        with contextlib.suppress(OSError):
            self.sock.close()

    def __enter__(self) -> "WSClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class _ClientReader(FrameReader):
    """FrameReader over a shared buffer so handshake leftovers stay readable."""

    def __init__(self, sock, buf: bytearray) -> None:
        self._sock = sock
        self._buf = buf
        self._require_mask = False

    def _exact(self, n: int) -> bytes:
        while len(self._buf) < n:
            chunk = self._sock.recv(n - len(self._buf))
            if not chunk:
                raise EOFError("connection closed mid-frame")
            self._buf += chunk
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out


def connect(host: str, port: int, path: str = "/ws", timeout: float = DEFAULT_TIMEOUT) -> WSClient:
    return WSClient(host, port, path, timeout)
