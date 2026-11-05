"""DNS wire format: the parts a small authoritative server needs.

Queries arrive as bytes and answers leave as bytes; nothing here knows about
sockets, and nothing here needs a library.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field

HEADER = struct.Struct("!HHHHHH")

QR = 0x8000
OPCODE_MASK = 0x7800
AA = 0x0400
TC = 0x0200
RD = 0x0100
RA = 0x0080
RCODE_MASK = 0x000F

NOERROR = 0
FORMERR = 1
SERVFAIL = 2
NXDOMAIN = 3
NOTIMP = 4
REFUSED = 5

TYPE_A = 1
TYPE_NS = 2
TYPE_CNAME = 5
TYPE_SOA = 6
TYPE_MX = 15
TYPE_TXT = 16
TYPE_AAAA = 28
TYPE_OPT = 41
TYPE_ANY = 255
CLASS_IN = 1

MAX_NAME = 255
MAX_LABEL = 63
MAX_POINTER_HOPS = 16
DEFAULT_UDP_LIMIT = 512


class FormatError(ValueError):
    """The packet cannot be parsed; answer FORMERR (or drop it)."""


@dataclass(frozen=True)
class Question:
    name: str
    qtype: int
    qclass: int


@dataclass(frozen=True)
class Query:
    ident: int
    flags: int
    questions: tuple[Question, ...]
    udp_limit: int = DEFAULT_UDP_LIMIT
    has_edns: bool = False
    extra_rrs: int = 0

    @property
    def opcode(self) -> int:
        return (self.flags & OPCODE_MASK) >> 11

    @property
    def recursion_desired(self) -> bool:
        return bool(self.flags & RD)

    @property
    def question(self) -> Question | None:
        return self.questions[0] if self.questions else None


def read_name(data: bytes, offset: int) -> tuple[str, int]:
    """Return (dotted name, offset just past the name at this position).

    Compression pointers are followed, but a pointer that loops or a name that
    overgrows 255 bytes is a format error rather than an infinite loop.
    """
    labels: list[str] = []
    hops = 0
    position = offset
    jumped_from: int | None = None
    total = 0
    while True:
        if position >= len(data):
            raise FormatError("the name runs past the end of the packet")
        length = data[position]
        if length & 0xC0 == 0xC0:
            if position + 1 >= len(data):
                raise FormatError("a pointer is cut in half")
            pointer = ((length & 0x3F) << 8) | data[position + 1]
            if pointer >= position:
                raise FormatError("a pointer does not point backwards")
            hops += 1
            if hops > MAX_POINTER_HOPS:
                raise FormatError("too many compression pointers")
            if jumped_from is None:
                jumped_from = position + 2
            position = pointer
            continue
        if length & 0xC0:
            raise FormatError("unsupported label type")
        position += 1
        if length == 0:
            break
        if position + length > len(data):
            raise FormatError("a label runs past the end of the packet")
        label = data[position : position + length]
        if b"." in label:
            raise FormatError("a label contains a dot")
        labels.append(label.decode("latin-1"))
        total += length + 1
        if total > MAX_NAME:
            raise FormatError("the name is longer than 255 bytes")
        position += length
    name = ".".join(labels) if labels else "."
    return name, (jumped_from if jumped_from is not None else position)


def encode_name(name: str) -> bytes:
    if name in ("", "."):
        return b"\x00"
    out = bytearray()
    total = 0
    for label in name.rstrip(".").split("."):
        raw = label.encode("latin-1")
        if not raw or len(raw) > MAX_LABEL:
            raise FormatError(f"bad label {label!r}")
        out.append(len(raw))
        out.extend(raw)
        total += len(raw) + 1
    if total + 1 > MAX_NAME:
        raise FormatError("the name is longer than 255 bytes")
    out.append(0)
    return bytes(out)


def parse_query(data: bytes) -> Query:
    if len(data) < HEADER.size:
        raise FormatError("the packet is shorter than a header")
    ident, flags, qdcount, ancount, nscount, arcount = HEADER.unpack_from(data, 0)
    if flags & QR:
        raise FormatError("this is a response, not a query")
    if qdcount != 1:
        raise FormatError("exactly one question is supported")
    position = HEADER.size
    questions: list[Question] = []
    for _ in range(qdcount):
        name, position = read_name(data, position)
        if position + 4 > len(data):
            raise FormatError("the question is cut short")
        qtype, qclass = struct.unpack_from("!HH", data, position)
        position += 4
        questions.append(Question(name=name, qtype=qtype, qclass=qclass))

    udp_limit = DEFAULT_UDP_LIMIT
    has_edns = False
    # The additional section is only interesting for the EDNS0 OPT record, whose
    # CLASS field carries the sender's UDP payload size.
    for _ in range(ancount + nscount + arcount):
        if position >= len(data):
            break
        _, position = read_name(data, position)
        if position + 10 > len(data):
            break
        rtype, rclass, _ttl, rdlength = struct.unpack_from("!HHIH", data, position)
        position += 10
        if rtype == TYPE_OPT:
            has_edns = True
            udp_limit = max(DEFAULT_UDP_LIMIT, rclass)
        position += rdlength
    return Query(
        ident=ident,
        flags=flags,
        questions=tuple(questions),
        udp_limit=udp_limit,
        has_edns=has_edns,
        extra_rrs=arcount,
    )


@dataclass
class Response:
    ident: int = 0
    flags: int = 0
    questions: list[Question] = field(default_factory=list)
    answers: list[bytes] = field(default_factory=list)
    authority: list[bytes] = field(default_factory=list)

    def to_bytes(self) -> bytes:
        header = HEADER.pack(
            self.ident,
            self.flags,
            len(self.questions),
            len(self.answers),
            len(self.authority),
            0,
        )
        body = bytearray(header)
        for question in self.questions:
            body.extend(encode_name(question.name))
            body.extend(struct.pack("!HH", question.qtype, question.qclass))
        for record in self.answers + self.authority:
            body.extend(record)
        return bytes(body)


def resource_record(name: str, rtype: int, rdata: bytes, ttl: int) -> bytes:
    """One uncompressed RR. Compression is an optimisation, not a requirement."""
    encoded = encode_name(name)
    return encoded + struct.pack("!HHIH", rtype, CLASS_IN, ttl, len(rdata)) + rdata


def read_utf8_rdata(chunks: bytes) -> str:
    """TXT rdata is one or more length-prefixed strings; join them back."""
    out = bytearray()
    position = 0
    while position < len(chunks):
        length = chunks[position]
        position += 1
        out.extend(chunks[position : position + length])
        position += length
    return out.decode("utf-8", "replace")
