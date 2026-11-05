"""Per-connection loop: handshake I/O then the framed message loop."""

import contextlib
import socket

from . import frames
from .frames import (
    CONTROL_OPS,
    OP_BINARY,
    OP_CLOSE,
    OP_CONTINUATION,
    OP_PING,
    OP_PONG,
    OP_TEXT,
    FrameReader,
    ProtocolError,
)
from .handshake import HandshakeError, accept_response, parse_request, rejection_response
from .protocol import MAX_MESSAGE_BYTES, dispatch

HEADER_SEP = b"\r\n\r\n"


def _read_headers(sock) -> bytes:
    """Read up to the header terminator byte-wise so trailing WS frame
    bytes stay in the socket for FrameReader (recv(4096) would swallow them)."""
    buf = bytearray()
    while not buf.endswith(HEADER_SEP):
        chunk = sock.recv(1)
        if not chunk:
            raise EOFError("closed during handshake")
        buf += chunk
        if len(buf) > 16384:
            raise HandshakeError(400, "Bad Request", "request head too large")
    return bytes(buf)


def _send(sock, opcode: int, payload: bytes = b"") -> None:
    sock.sendall(frames.encode(opcode, payload, mask=False))


def _close(sock, code: int, reason: str = "") -> None:
    with contextlib.suppress(OSError):
        sock.sendall(
            frames.encode(OP_CLOSE, frames.close_payload(code, reason), mask=False)
        )


class Session:
    """One websocket conversation. run() drives it to completion."""

    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.reader = FrameReader(sock)
        self.frag_op = None
        self.frag = bytearray()

    def run(self) -> None:
        try:
            request = _read_headers(self.sock)
        except HandshakeError as err:
            self.sock.sendall(rejection_response(err))
            return
        except EOFError:
            return
        try:
            info = parse_request(request)
        except HandshakeError as err:
            self.sock.sendall(rejection_response(err))
            return
        self.sock.sendall(accept_response(info["key"]))
        try:
            self._loop()
        except EOFError:
            pass
        except ProtocolError as err:
            _close(self.sock, err.code, str(err).split(": ", 1)[-1])
        finally:
            with contextlib.suppress(OSError):
                self.sock.shutdown(socket.SHUT_RDWR)

    def _loop(self) -> None:
        while True:
            frame = self.reader.read()
            if frame.opcode in CONTROL_OPS:
                done = self._control(frame)
                if done:
                    return
                continue
            self._data(frame)

    def _control(self, frame) -> bool:
        if frame.opcode == OP_CLOSE:
            code = frames.parse_close(frame.payload)
            _close(self.sock, code)
            return True
        if frame.opcode == OP_PING:
            _send(self.sock, OP_PONG, frame.payload)
            return False
        return False  # PONG from client: ignore

    def _data(self, frame) -> None:
        if frame.opcode == OP_CONTINUATION:
            if self.frag_op is None:
                raise ProtocolError(1002, "protocol error: continuation with no start")
            self._absorb(frame.payload)
            if not frame.fin:
                return
            op, payload = self.frag_op, bytes(self.frag)
            self.frag_op, self.frag = None, bytearray()
        else:
            if self.frag_op is not None:
                raise ProtocolError(1002, "protocol error: data frame while fragmenting")
            if not frame.fin:
                self.frag_op = frame.opcode
                self._absorb(frame.payload)
                return
            op, payload = frame.opcode, frame.payload
            if len(payload) > MAX_MESSAGE_BYTES:
                raise ProtocolError(1009, "message larger than 64 KiB")
        if op == OP_BINARY:
            raise ProtocolError(1003, "binary messages are not handled by this service")
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as err:
            raise ProtocolError(1007, "invalid utf-8 in text frame") from err
        reply = dispatch(payload)
        if reply is not None:
            _send(self.sock, OP_TEXT, reply.encode("utf-8"))

    def _absorb(self, payload: bytes) -> None:
        self.frag.extend(payload)
        if len(self.frag) > MAX_MESSAGE_BYTES:
            raise ProtocolError(1009, "message larger than 64 KiB")


def handle(sock: socket.socket) -> None:
    """Entry point used by the server: serve one connection to completion."""
    try:
        Session(sock).run()
    finally:
        sock.close()
