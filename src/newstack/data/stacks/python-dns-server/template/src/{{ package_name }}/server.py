"""Serve the zone over UDP and TCP, with the truncation rules DNS requires."""

from __future__ import annotations

import contextlib
import socket
import struct
import threading

from .protocol import (
    AA,
    CLASS_IN,
    FORMERR,
    NOERROR,
    NOTIMP,
    NXDOMAIN,
    QR,
    RA,
    REFUSED,
    TC,
    FormatError,
    Query,
    Response,
    parse_query,
    resource_record,
)
from .zone import Zone

TCP = socket.SOCK_STREAM
UDP = socket.SOCK_DGRAM


def answer(query: Query, zone: Zone) -> bytes:
    """Build the reply for one parsed query."""
    question = query.question
    base = Response(
        ident=query.ident,
        flags=QR | RA | (query.flags & 0x0100),
        questions=list(query.questions),
    )
    if question is None:
        base.flags |= FORMERR
        return base.to_bytes()
    if query.opcode != 0:
        base.flags |= NOTIMP
        return base.to_bytes()
    if question.qclass != CLASS_IN:
        base.flags |= NOTIMP
        return base.to_bytes()
    if not zone.owns(question.name):
        base.flags |= REFUSED
        return base.to_bytes()

    base.flags |= AA
    answers = zone.lookup(question.name, question.qtype)
    if answers:
        for owner, rtype, rdata, ttl in answers:
            base.answers.append(resource_record(owner, rtype, rdata, ttl))
        return base.to_bytes()

    soa = zone.soa_record()
    if zone.exists(question.name):
        # The name is here but not that type: NOERROR, no answer, SOA in authority.
        base.flags |= NOERROR
    else:
        base.flags |= NXDOMAIN
    if soa is not None:
        owner, rtype, rdata, ttl = soa
        base.authority.append(resource_record(owner, rtype, rdata, ttl))
    return base.to_bytes()


def respond(payload: bytes, zone: Zone, *, udp_limit: int | None = None) -> bytes:
    """`udp_limit` is the server maximum for datagrams; EDNS0 may ask for less."""
    """Parse a packet and answer it; a broken packet still gets a header back."""
    try:
        query = parse_query(payload)
    except FormatError:
        if len(payload) < 12:
            return b""
        ident = struct.unpack_from("!H", payload, 0)[0]
        flags = QR | (struct.unpack_from("!H", payload, 2)[0] & 0x0100) | FORMERR
        return struct.pack("!HHHHHH", ident, flags, 0, 0, 0, 0)
    reply = answer(query, zone)
    if udp_limit is None:
        return reply
    limit = query.udp_limit if query.has_edns else min(udp_limit, query.udp_limit)
    limit = min(limit, max(udp_limit, 4096))
    if len(reply) <= limit:
        return reply
    # Too big for this transport: say so, keep only the question.
    truncated = Response(
        ident=query.ident,
        flags=QR | RA | TC | (query.flags & 0x0100) | AA,
        questions=list(query.questions),
    )
    return truncated.to_bytes()


class Server:
    """Both transports share the same answer(), so they cannot disagree."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 53,
        *,
        zone: Zone | None = None,
        udp_limit: int = 512,
    ) -> None:
        self.zone = zone or Zone("example.test")
        self.host = host
        self._port = port
        self.udp_limit = udp_limit
        self._udp: socket.socket | None = None
        self._tcp: socket.socket | None = None
        self._threads: list[threading.Thread] = []
        self._stopping = threading.Event()

    @property
    def port(self) -> int:
        return self._port

    def start(self) -> Server:
        udp = socket.socket(socket.AF_INET, UDP)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp.bind((self.host, self._port))
        # Port 0 means "pick one": the TCP listener must then follow the UDP
        # socket to that number, not pick a second one of its own.
        self._port = udp.getsockname()[1]
        tcp = socket.socket(socket.AF_INET, TCP)
        tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp.bind((self.host, self._port))
        tcp.listen(16)
        udp.settimeout(0.2)
        tcp.settimeout(0.2)
        self._udp, self._tcp = udp, tcp
        for target in (self._serve_udp, self._serve_tcp):
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            self._threads.append(thread)
        return self

    def _serve_udp(self) -> None:
        assert self._udp is not None
        while not self._stopping.is_set():
            try:
                payload, address = self._udp.recvfrom(65535)
            except TimeoutError:
                continue
            except OSError:
                return
            reply = respond(payload, self.zone, udp_limit=self.udp_limit)
            if reply:
                with contextlib.suppress(OSError):
                    self._udp.sendto(reply, address)

    def _serve_tcp(self) -> None:
        assert self._tcp is not None
        while not self._stopping.is_set():
            try:
                connection, _ = self._tcp.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            with connection:
                connection.settimeout(5.0)
                with contextlib.suppress(OSError):
                    self._serve_connection(connection)

    def _serve_connection(self, connection: socket.socket) -> None:
        while not self._stopping.is_set():
            header = _recv_exactly(connection, 2)
            if len(header) != 2:
                return
            (length,) = struct.unpack("!H", header)
            payload = _recv_exactly(connection, length)
            if len(payload) != length:
                return
            reply = respond(payload, self.zone)  # TCP has no datagram limit
            connection.sendall(struct.pack("!H", len(reply)) + reply)

    def shutdown(self) -> None:
        self._stopping.set()
        for listener in (self._udp, self._tcp):
            if listener is not None:
                with contextlib.suppress(OSError):
                    listener.close()
        for thread in self._threads:
            thread.join(timeout=5)
        self._threads.clear()

    def serve_forever(self) -> None:
        try:
            while not self._stopping.wait(0.2):
                pass
        except KeyboardInterrupt:
            pass

    def __enter__(self) -> Server:
        return self.start()

    def __exit__(self, *_exc: object) -> None:
        self.shutdown()


def _recv_exactly(connection: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        try:
            chunk = connection.recv(size - len(chunks))
        except TimeoutError:
            return bytes(chunks)
        if not chunk:
            break
        chunks.extend(chunk)
    return bytes(chunks)


def parse_port(raw: str) -> int:
    try:
        value = int(raw, 10)
    except ValueError:
        raise ValueError(f"PORT must be a number, got {raw!r}") from None
    if not 0 <= value <= 65535:
        raise ValueError(f"PORT must be between 0 and 65535, got {value}")
    return value
