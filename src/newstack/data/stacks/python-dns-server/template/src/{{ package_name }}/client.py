"""A tiny resolver client: build a query, parse the reply, no library."""

from __future__ import annotations

import socket
import struct
from dataclasses import dataclass, field

from .protocol import (
    AA,
    CLASS_IN,
    HEADER,
    QR,
    RCODE_MASK,
    TC,
    TYPE_OPT,
    Question,
    encode_name,
    read_name,
    read_utf8_rdata,
)

TYPES = {
    "A": 1,
    "NS": 2,
    "CNAME": 5,
    "SOA": 6,
    "MX": 15,
    "TXT": 16,
    "AAAA": 28,
    "ANY": 255,
}


def build_query(
    name: str,
    qtype: int = 1,
    *,
    ident: int = 0x1234,
    qclass: int = CLASS_IN,
    recursion_desired: bool = True,
    edns: int | None = None,
) -> bytes:
    flags = 0x0100 if recursion_desired else 0
    header = HEADER.pack(ident, flags, 1, 0, 0, 1 if edns else 0)
    question = encode_name(name) + struct.pack("!HH", qtype, qclass)
    packet = header + question
    if edns is not None:
        # OPT: root name, type 41, class = the sender's UDP payload size.
        packet += b"\x00" + struct.pack("!HHIH", TYPE_OPT, edns, 0, 0)
    return packet


@dataclass(frozen=True)
class Record:
    name: str
    rtype: int
    ttl: int
    rdata: bytes

    def text(self) -> str:
        if self.rtype == 1 and len(self.rdata) == 4:
            return socket.inet_ntop(socket.AF_INET, self.rdata)
        if self.rtype == 28 and len(self.rdata) == 16:
            return socket.inet_ntop(socket.AF_INET6, self.rdata)
        if self.rtype == 16:
            return read_utf8_rdata(self.rdata)
        if self.rtype in (2, 5):
            return decode_name(self.rdata)
        if self.rtype == 15 and len(self.rdata) > 2:
            preference = struct.unpack_from("!H", self.rdata, 0)[0]
            return f"{preference} {decode_name(self.rdata[2:])}"
        return self.rdata.hex()


def decode_name(rdata: bytes) -> str:
    labels: list[str] = []
    position = 0
    while position < len(rdata):
        length = rdata[position]
        position += 1
        if length == 0:
            break
        labels.append(rdata[position : position + length].decode("latin-1"))
        position += length
    return ".".join(labels)


@dataclass
class Reply:
    ident: int
    flags: int
    questions: list[Question] = field(default_factory=list)
    answers: list[Record] = field(default_factory=list)
    authority: list[Record] = field(default_factory=list)
    additional: list[Record] = field(default_factory=list)

    @property
    def rcode(self) -> int:
        return self.flags & RCODE_MASK

    @property
    def authoritative(self) -> bool:
        return bool(self.flags & AA)

    @property
    def truncated(self) -> bool:
        return bool(self.flags & TC)

    def texts(self) -> list[str]:
        return [record.text() for record in self.answers]


def parse_reply(data: bytes) -> Reply:
    ident, flags, qdcount, ancount, nscount, arcount = HEADER.unpack_from(data, 0)
    if not flags & QR:
        raise ValueError("this packet is a query, not a reply")
    position = HEADER.size
    questions: list[Question] = []
    for _ in range(qdcount):
        name, position = read_name(data, position)
        qtype, qclass = struct.unpack_from("!HH", data, position)
        position += 4
        questions.append(Question(name=name, qtype=qtype, qclass=qclass))
    sections: list[list[Record]] = []
    for count in (ancount, nscount, arcount):
        records: list[Record] = []
        for _ in range(count):
            name, position = read_name(data, position)
            rtype, _rclass, ttl, rdlength = struct.unpack_from("!HHIH", data, position)
            position += 10
            records.append(Record(name, rtype, ttl, data[position : position + rdlength]))
            position += rdlength
        sections.append(records)
    return Reply(
        ident=ident,
        flags=flags,
        questions=questions,
        answers=sections[0],
        authority=sections[1],
        additional=sections[2],
    )


def ask_udp(host: str, port: int, payload: bytes, *, timeout: float = 5.0) -> bytes:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(payload, (host, port))
        reply, _ = sock.recvfrom(65535)
        return reply


def ask_tcp(host: str, port: int, payload: bytes, *, timeout: float = 5.0) -> bytes:
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(struct.pack("!H", len(payload)) + payload)
        header = _recv_exactly(sock, 2)
        (length,) = struct.unpack("!H", header)
        return _recv_exactly(sock, length)


def _recv_exactly(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("the connection closed before the reply finished")
        chunks.extend(chunk)
    return bytes(chunks)


def query(host: str, port: int, name: str, qtype: int = 1, **options: int) -> Reply:
    payload = build_query(name, qtype, **options)
    return parse_reply(ask_udp(host, port, payload))
