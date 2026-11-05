"""RFC 6455 frame codec. Server->client frames are unmasked; client->server
frames MUST be masked (RFC 6455 5.1 asymmetry)."""

OP_CONTINUATION = 0x0
OP_TEXT = 0x1
OP_BINARY = 0x2
OP_CLOSE = 0x8
OP_PING = 0x9
OP_PONG = 0xA
DATA_OPS = (OP_CONTINUATION, OP_TEXT, OP_BINARY)
CONTROL_OPS = (OP_CLOSE, OP_PING, OP_PONG)
KNOWN_OPS = DATA_OPS + CONTROL_OPS


class ProtocolError(Exception):
    """Fatal framing violation; carries the close code to send back."""

    def __init__(self, code: int, reason: str) -> None:
        super().__init__(f"{code}: {reason}")
        self.code = code
        self.reason = reason


class Frame:
    __slots__ = ("fin", "opcode", "payload")

    def __init__(self, fin: bool, opcode: int, payload: bytes) -> None:
        self.fin = fin
        self.opcode = opcode
        self.payload = payload

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Frame(fin={self.fin}, op=0x{self.opcode:x}, len={len(self.payload)})"


def encode(opcode: int, payload: bytes, fin: bool = True, mask: bool = False) -> bytes:
    """Encode one frame. ``mask=True`` only for client->server direction."""
    out = bytearray()
    b0 = opcode & 0x0F
    if fin:
        b0 |= 0x80
    out.append(b0)
    n = len(payload)
    len_bits = 126 if n < (1 << 16) else (127 if n < (1 << 64) else None)
    if len_bits is None:  # pragma: no cover - messages capped far below this
        raise ProtocolError(1009, "message too large")
    if n < 126:
        out.append((0x80 if mask else 0) | n)
    elif len_bits == 126:
        out.append((0x80 if mask else 0) | 126)
        out += n.to_bytes(2, "big")
    else:
        out.append((0x80 if mask else 0) | 127)
        out += n.to_bytes(8, "big")
    if mask:
        import os

        key = os.urandom(4)
        out += key
        payload = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    out += payload
    return bytes(out)


class FrameReader:
    """Read frames off a blocking socket. Raises ProtocolError on violations.

    ``require_mask`` is directional: True on the server (client-to-server
    frames MUST be masked), False on the client (server frames MUST NOT be
    masked - RFC 6455 5.1).
    """

    def __init__(self, sock, require_mask: bool = True) -> None:
        self._sock = sock
        self._require_mask = require_mask

    def _exact(self, n: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < n:
            chunk = self._sock.recv(n - len(chunks))
            if not chunk:
                raise EOFError("connection closed mid-frame")
            chunks += chunk
        return bytes(chunks)

    def read(self) -> Frame:
        head = self._exact(2)
        b0, b1 = head[0], head[1]
        fin = bool(b0 & 0x80)
        if (b0 >> 4) & 0x7:
            raise ProtocolError(1002, "protocol error: RSV bits must be zero")
        opcode = b0 & 0x0F
        if opcode not in KNOWN_OPS:
            raise ProtocolError(1002, "protocol error: unknown opcode")
        masked = bool(b1 & 0x80)
        if self._require_mask and not masked:
            # RFC 6455 5.1: client-to-server frames MUST be masked.
            raise ProtocolError(1002, "protocol error: client frame not masked")
        length = b1 & 0x7F
        if opcode in CONTROL_OPS:
            if not fin:
                raise ProtocolError(1002, "protocol error: fragmented control frame")
            if length > 125:
                raise raise_control_too_long()
        if length == 126:
            length = int.from_bytes(self._exact(2), "big")
        elif length == 127:
            length = int.from_bytes(self._exact(8), "big")
        key = self._exact(4) if masked else b""
        payload = self._exact(length)
        if masked:
            payload = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
        return Frame(fin, opcode, payload)


def raise_control_too_long() -> ProtocolError:
    return ProtocolError(1002, "protocol error: control frame payload over 125 bytes")


def close_payload(code: int, reason: str = "") -> bytes:
    return code.to_bytes(2, "big") + reason.encode("utf-8")


def parse_close(payload: bytes) -> int:
    """Echo code for a close frame; 1000 when no code present at all."""
    if len(payload) == 0:
        return 1000
    if len(payload) == 1:
        raise ProtocolError(1002, "protocol error: 1-byte close payload")
    code = int.from_bytes(payload[:2], "big")
    if not valid_close_code(code):
        raise ProtocolError(1002, "protocol error: invalid close code")
    return code


def valid_close_code(code: int) -> bool:
    if code in (1004, 1005, 1006, 1015) or (1016 <= code <= 2999):
        return False
    return 1000 <= code <= 1013 or 3000 <= code <= 4999
