"""A tiny RESP client, so tests and the selftest judge the bytes on the wire.

It binds nothing and knows nothing about the server's internals: it writes a
multibulk command and parses whatever comes back.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass


@dataclass(frozen=True)
class Status:
    """A `+simple string` reply (PONG, OK, ...)."""

    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Failure:
    """A `-error` reply; `message` is the text without the leading dash."""

    message: str

    def __str__(self) -> str:
        return self.message


class Client:
    def __init__(self, host: str = "127.0.0.1", port: int = 0, *, timeout: float = 5.0) -> None:
        self._socket = socket.create_connection((host, port), timeout=timeout)
        self._socket.settimeout(timeout)
        self._buffer = b""

    # -- raw access ------------------------------------------------------
    def send_bytes(self, payload: bytes) -> None:
        """Write exactly these bytes: used to prove the parser reads partial frames."""
        self._socket.sendall(payload)

    def send_command(self, *args: bytes | str) -> None:
        encoded = [arg if isinstance(arg, bytes) else arg.encode("utf-8") for arg in args]
        parts = [b"*%d\r\n" % len(encoded)]
        for arg in encoded:
            parts.append(b"$%d\r\n%s\r\n" % (len(arg), arg))
        self.send_bytes(b"".join(parts))

    def command(self, *args: bytes | str):
        self.send_command(*args)
        return self.read_reply()

    def read_raw(self, size: int = 16) -> bytes:
        """Whatever arrives next, without parsing: b"" means the server hung up."""
        while True:
            chunk = self._socket.recv(size)
            if chunk:
                return chunk
            return b""

    def close(self) -> None:
        try:
            self._socket.close()
        except OSError:
            pass

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    # -- parsing ---------------------------------------------------------
    def _fill(self) -> None:
        chunk = self._socket.recv(4096)
        if not chunk:
            raise ConnectionError("the server closed the connection")
        self._buffer += chunk

    def _line(self) -> bytes:
        while b"\r\n" not in self._buffer:
            self._fill()
        line, _, rest = self._buffer.partition(b"\r\n")
        self._buffer = rest
        return line

    def _exact(self, size: int) -> bytes:
        while len(self._buffer) < size:
            self._fill()
        data, self._buffer = self._buffer[:size], self._buffer[size:]
        return data

    def read_reply(self):
        line = self._line()
        kind, payload = line[:1], line[1:]
        if kind == b"+":
            return Status(payload.decode("utf-8"))
        if kind == b"-":
            return Failure(payload.decode("utf-8"))
        if kind == b":":
            return int(payload)
        if kind == b"$":
            length = int(payload)
            if length < 0:
                return None
            data = self._exact(length + 2)
            return data[:-2]
        if kind == b"*":
            count = int(payload)
            if count < 0:
                return None
            return [self.read_reply() for _ in range(count)]
        raise ValueError(f"unknown reply type {line!r}")
