"""RESP2 framing.

A Redis client writes an array of bulk strings; this module turns whichever
bytes `recv()` handed us into complete commands, and encodes replies the same
way the real server does.
"""

from __future__ import annotations

CRLF = b"\r\n"

# Redis' own limits. They exist so one client cannot make the parser allocate
# without bound.
MAX_BULK = 512 * 1024 * 1024
MAX_INLINE = 64 * 1024
MAX_ARGS = 1024


class ProtocolError(Exception):
    """The byte stream is not RESP2; the server closes the connection."""


def encode_simple(text: str) -> bytes:
    """+OK\\r\\n"""
    return b"+" + text.encode("utf-8") + CRLF


def encode_error(text: str) -> bytes:
    """-ERR message\\r\\n"""
    return b"-" + text.encode("utf-8") + CRLF


def encode_integer(value: int) -> bytes:
    """:42\\r\\n"""
    return b":" + str(int(value)).encode("ascii") + CRLF


def encode_bulk(data: bytes) -> bytes:
    """$5\\r\\nhello\\r\\n"""
    return b"$" + str(len(data)).encode("ascii") + CRLF + data + CRLF


def encode_array(items: list[bytes]) -> bytes:
    """*2\\r\\n<item><item>, where each item is already encoded."""
    return b"*" + str(len(items)).encode("ascii") + CRLF + b"".join(items)


NIL_BULK = b"$-1\r\n"
EMPTY_ARRAY = b"*0\r\n"


def _unquote(token: bytes) -> bytes:
    """Inline commands may quote an argument; support the common case."""
    if len(token) < 2 or token[:1] != b'"' or token[-1:] != b'"':
        return token
    body = token[1:-1]
    out = bytearray()
    index = 0
    while index < len(body):
        char = body[index : index + 1]
        if char == b"\\" and index + 1 < len(body):
            nxt = body[index + 1 : index + 2]
            mapping = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b'"': b'"', b"\\": b"\\"}
            if nxt in mapping:
                out.extend(mapping[nxt])
                index += 2
                continue
            if nxt == b"x" and index + 3 < len(body):
                try:
                    out.append(int(body[index + 2 : index + 4], 16))
                    index += 4
                    continue
                except ValueError:
                    pass
        out.extend(char)
        index += 1
    return bytes(out)


def _split_inline(line: bytes) -> list[bytes]:
    tokens: list[bytes] = []
    current = bytearray()
    quoted = False
    escaped = False
    for char in line:
        byte = bytes([char])
        if escaped:
            current.extend(byte)
            escaped = False
            continue
        if quoted and byte == b"\\":
            escaped = True
            current.extend(byte)
            continue
        if byte == b'"':
            quoted = not quoted
            current.extend(byte)
            continue
        if not quoted and byte in (b" ", b"\t"):
            if current:
                tokens.append(bytes(current))
                current.clear()
            continue
        current.extend(byte)
    if quoted:
        raise ProtocolError("unbalanced quotes in request")
    if current:
        tokens.append(bytes(current))
    return [_unquote(token) for token in tokens]


class CommandReader:
    """Incremental parser: feed bytes, get complete commands.

    TCP splits a command wherever it likes, so a parser that assumes one
    `recv()` equals one command works locally and fails under load.
    """

    def __init__(self, *, max_bulk: int = MAX_BULK, max_args: int = MAX_ARGS) -> None:
        self._buffer = bytearray()
        self._max_bulk = max_bulk
        self._max_args = max_args

    @property
    def pending(self) -> int:
        """Bytes held back waiting for the rest of a frame."""
        return len(self._buffer)

    def feed(self, chunk: bytes) -> list[list[bytes]]:
        self._buffer.extend(chunk)
        commands: list[list[bytes]] = []
        while True:
            command = self._next_command()
            if command is None:
                return commands
            if command:
                commands.append(command)

    def _line_end(self, start: int) -> int:
        return self._buffer.find(CRLF, start)

    def _next_command(self) -> list[bytes] | None:
        if not self._buffer:
            return None
        if self._buffer[:1] == b"*":
            return self._multibulk()
        return self._inline()

    def _inline(self) -> list[bytes] | None:
        end = self._buffer.find(b"\n")
        if end < 0:
            if len(self._buffer) > MAX_INLINE:
                raise ProtocolError("too big inline request")
            return None
        line = bytes(self._buffer[:end]).rstrip(b"\r")
        del self._buffer[: end + 1]
        if len(line) > MAX_INLINE:
            raise ProtocolError("too big inline request")
        return _split_inline(line.strip())

    def _multibulk(self) -> list[bytes] | None:
        buffer = self._buffer
        end = self._line_end(1)
        if end < 0:
            if len(buffer) > MAX_INLINE:
                raise ProtocolError("invalid multibulk length")
            return None
        try:
            count = int(bytes(buffer[1:end]))
        except ValueError as exc:
            raise ProtocolError("invalid multibulk length") from exc
        if count > self._max_args:
            raise ProtocolError("invalid multibulk length")
        position = end + 2
        if count <= 0:
            del buffer[:position]
            return []

        args: list[bytes] = []
        for _ in range(count):
            if position >= len(buffer):
                return None
            if buffer[position : position + 1] != b"$":
                raise ProtocolError("expected '$', got something else")
            header_end = self._line_end(position + 1)
            if header_end < 0:
                return None
            try:
                length = int(bytes(buffer[position + 1 : header_end]))
            except ValueError as exc:
                raise ProtocolError("invalid bulk length") from exc
            if length < 0 or length > self._max_bulk:
                raise ProtocolError("invalid bulk length")
            body_start = header_end + 2
            body_end = body_start + length
            if len(buffer) < body_end + 2:
                return None
            if buffer[body_end : body_end + 2] != CRLF:
                raise ProtocolError("invalid bulk length")
            args.append(bytes(buffer[body_start:body_end]))
            position = body_end + 2
        del buffer[:position]
        return args
