"""MQTT 3.1.1 control packets, encoded and decoded by hand.

The framing rule that shapes everything else: the fixed header carries a
variable-length remaining length (1 to 4 bytes, seven bits each, the top bit
meaning "another byte follows"), so a reader must never assume it has a whole
packet just because it has some bytes.
"""

from __future__ import annotations

from dataclasses import dataclass

CONNECT = 1
CONNACK = 2
PUBLISH = 3
PUBACK = 4
SUBSCRIBE = 8
SUBACK = 9
UNSUBSCRIBE = 10
UNSUBACK = 11
PINGREQ = 12
PINGRESP = 13
DISCONNECT = 14

MAX_REMAINING = 268_435_455  # four seven-bit groups

# CONNACK return codes.
ACCEPTED = 0
BAD_PROTOCOL = 1
BAD_CLIENT_ID = 2
BAD_CREDENTIALS = 4
NOT_AUTHORIZED = 5

# SUBACK return codes: the granted QoS, or one refusal.
SUB_FAILURE = 0x80


class ProtocolError(Exception):
    """A packet that cannot be understood; the connection is closed politely."""


def encode_remaining_length(length: int) -> bytes:
    if length < 0 or length > MAX_REMAINING:
        raise ProtocolError(f"remaining length {length} out of range")
    out = bytearray()
    while True:
        digit = length % 128
        length //= 128
        if length:
            out.append(digit | 0x80)
        else:
            out.append(digit)
            return bytes(out)


def read_remaining_length(data: bytes, position: int = 1) -> tuple[int, int]:
    """Return (length, next_position). Raises when the varint is truncated."""
    value = 0
    multiplier = 1
    for offset in range(4):
        index = position + offset
        if index >= len(data):
            raise ProtocolError("truncated remaining length")
        byte = data[index]
        value += (byte & 0x7F) * multiplier
        if not byte & 0x80:
            return value, index + 1
        multiplier *= 128
    raise ProtocolError("remaining length is longer than four bytes")


def utf8(text: str) -> bytes:
    raw = text.encode("utf-8")
    if len(raw) > 65_535:
        raise ProtocolError("a string field is longer than 65535 bytes")
    return len(raw).to_bytes(2, "big") + raw


def read_utf8(data: bytes, position: int) -> tuple[str, int]:
    if position + 2 > len(data):
        raise ProtocolError("truncated string length")
    size = int.from_bytes(data[position : position + 2], "big")
    start = position + 2
    if start + size > len(data):
        raise ProtocolError("truncated string")
    try:
        return data[start : start + size].decode("utf-8"), start + size
    except UnicodeDecodeError as error:
        raise ProtocolError(f"a string field is not UTF-8: {error}") from error


def packet(first_byte: int, body: bytes = b"") -> bytes:
    return bytes([first_byte]) + encode_remaining_length(len(body)) + body


@dataclass(frozen=True)
class Connect:
    client_id: str
    clean_session: bool
    keepalive: int
    username: str | None = None
    password: str | None = None
    will_topic: str | None = None
    will_message: bytes | None = None
    protocol_level: int = 4


def parse_connect(body: bytes) -> Connect:
    if len(body) < 10:
        raise ProtocolError("CONNECT is too short")
    name, position = read_utf8(body, 0)
    if name != "MQTT":
        raise ProtocolError(f"unsupported protocol name {name!r}")
    level = body[position]
    flags = body[position + 1]
    keepalive = int.from_bytes(body[position + 2 : position + 4], "big")
    position += 4
    if flags & 0x01:
        raise ProtocolError("the reserved CONNECT flag must be zero")
    client_id, position = read_utf8(body, position)
    will_topic = will_message = None
    if flags & 0x04:
        will_topic, position = read_utf8(body, position)
        size = int.from_bytes(body[position : position + 2], "big")
        will_message = body[position + 2 : position + 2 + size]
        if len(will_message) != size:
            raise ProtocolError("truncated will message")
        position += 2 + size
    username = password = None
    if flags & 0x80:
        username, position = read_utf8(body, position)
    if flags & 0x40:
        password, position = read_utf8(body, position)
    return Connect(
        client_id=client_id,
        clean_session=bool(flags & 0x02),
        keepalive=keepalive,
        username=username,
        password=password,
        will_topic=will_topic,
        will_message=will_message,
        protocol_level=level,
    )


@dataclass(frozen=True)
class Publish:
    topic: str
    payload: bytes
    qos: int = 0
    retain: bool = False
    duplicate: bool = False
    packet_id: int | None = None


def parse_publish(first_byte: int, body: bytes) -> Publish:
    qos = (first_byte & 0x06) >> 1
    if qos == 3:
        raise ProtocolError("QoS 3 does not exist")
    topic, position = read_utf8(body, 0)
    packet_id = None
    if qos:
        if position + 2 > len(body):
            raise ProtocolError("a QoS publish needs a packet id")
        packet_id = int.from_bytes(body[position : position + 2], "big")
        if packet_id == 0:
            raise ProtocolError("a packet id of zero is reserved")
        position += 2
    return Publish(
        topic=topic,
        payload=body[position:],
        qos=qos,
        retain=bool(first_byte & 0x01),
        duplicate=bool(first_byte & 0x08),
        packet_id=packet_id,
    )


def encode_publish(publish: Publish) -> bytes:
    body = utf8(publish.topic)
    if publish.qos:
        body += (publish.packet_id or 0).to_bytes(2, "big")
    body += publish.payload
    first = 0x30 | (publish.qos << 1)
    if publish.retain:
        first |= 0x01
    if publish.duplicate:
        first |= 0x08
    return packet(first, body)


def connack(session_present: bool, code: int = ACCEPTED) -> bytes:
    return packet(0x20, bytes([1 if session_present else 0, code]))


def publish_ack(packet_id: int) -> bytes:
    return packet(0x40, packet_id.to_bytes(2, "big"))


def puback_of(body: bytes) -> int:
    if len(body) != 2:
        raise ProtocolError("PUBACK must carry exactly one packet id")
    return int.from_bytes(body, "big")


@dataclass(frozen=True)
class Subscription:
    filter: str
    qos: int


def parse_subscribe(body: bytes) -> tuple[int, list[Subscription]]:
    if len(body) < 2:
        raise ProtocolError("SUBSCRIBE is too short")
    packet_id = int.from_bytes(body[:2], "big")
    if packet_id == 0:
        raise ProtocolError("a packet id of zero is reserved")
    position = 2
    wanted: list[Subscription] = []
    while position < len(body):
        topic_filter, position = read_utf8(body, position)
        if position >= len(body):
            raise ProtocolError("a subscription has no requested QoS")
        qos = body[position]
        position += 1
        if qos > 2:
            raise ProtocolError(f"requested QoS {qos} is not a valid level")
        wanted.append(Subscription(topic_filter, qos))
    if not wanted:
        raise ProtocolError("SUBSCRIBE carries no topic filters")
    return packet_id, wanted


def parse_unsubscribe(body: bytes) -> tuple[int, list[str]]:
    if len(body) < 2:
        raise ProtocolError("UNSUBSCRIBE is too short")
    packet_id = int.from_bytes(body[:2], "big")
    position = 2
    filters: list[str] = []
    while position < len(body):
        topic_filter, position = read_utf8(body, position)
        filters.append(topic_filter)
    if not filters:
        raise ProtocolError("UNSUBSCRIBE carries no topic filters")
    return packet_id, filters


def suback(packet_id: int, codes: list[int]) -> bytes:
    return packet(0x90, packet_id.to_bytes(2, "big") + bytes(codes))


def unsuback(packet_id: int) -> bytes:
    return packet(0xB0, packet_id.to_bytes(2, "big"))


def pingresp() -> bytes:
    return packet(0xD0)
