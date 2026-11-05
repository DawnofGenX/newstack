"""The zone: names to records, with the answers a small authoritative server owes."""

from __future__ import annotations

import socket
import struct

from .protocol import (
    CLASS_IN,
    TYPE_A,
    TYPE_AAAA,
    TYPE_ANY,
    TYPE_CNAME,
    TYPE_MX,
    TYPE_NS,
    TYPE_SOA,
    TYPE_TXT,
    encode_name,
)

DEFAULT_TTL = 300


def a(address: str) -> bytes:
    return socket.inet_pton(socket.AF_INET, address)


def aaaa(address: str) -> bytes:
    return socket.inet_pton(socket.AF_INET6, address)


def txt(text: str) -> bytes:
    """TXT rdata is a series of length-prefixed strings, 255 bytes each."""
    raw = text.encode("utf-8")
    out = bytearray()
    for start in range(0, len(raw), 255):
        chunk = raw[start : start + 255]
        out.append(len(chunk))
        out.extend(chunk)
    if not raw:
        out.append(0)
    return bytes(out)


def cname(target: str) -> bytes:
    return encode_name(target)


def ns(target: str) -> bytes:
    return encode_name(target)


def mx(preference: int, target: str) -> bytes:
    return struct.pack("!H", preference) + encode_name(target)


def soa(
    mname: str,
    rname: str,
    *,
    serial: int = 1,
    refresh: int = 3600,
    retry: int = 600,
    expire: int = 86400,
    minimum: int = 60,
) -> bytes:
    return (
        encode_name(mname)
        + encode_name(rname)
        + struct.pack("!IIIII", serial, refresh, retry, expire, minimum)
    )


class Zone:
    """`apex` is the name we are authoritative for; everything under it is ours."""

    def __init__(self, apex: str, *, ttl: int = DEFAULT_TTL) -> None:
        self.apex = apex.rstrip(".").lower()
        self.ttl = ttl
        self._records: dict[str, list[tuple[int, bytes]]] = {}

    # -- building --------------------------------------------------------
    def add(self, name: str, rtype: int, rdata: bytes) -> Zone:
        key = self._key(name)
        self._records.setdefault(key, []).append((rtype, rdata))
        return self

    def _key(self, name: str) -> str:
        clean = name.rstrip(".").lower()
        return clean

    # -- queries ---------------------------------------------------------
    def owns(self, name: str) -> bool:
        key = self._key(name)
        return key == self.apex or key.endswith("." + self.apex)

    def exists(self, name: str) -> bool:
        return self._key(name) in self._records

    def records(self, name: str) -> list[tuple[int, bytes]]:
        return list(self._records.get(self._key(name), []))

    def lookup(self, name: str, qtype: int) -> list[tuple[str, int, bytes, int]]:
        """Answer one question: follow a CNAME chain, then filter by type.

        Returns (owner name, type, rdata, ttl) tuples, ready to encode.
        """
        owner = self._key(name)
        answer: list[tuple[str, int, bytes, int]] = []
        seen: set[str] = set()
        for _ in range(8):
            records = self.records(owner)
            if not records:
                return answer
            if qtype == TYPE_ANY:
                answer.extend((owner, rtype, rdata, self.ttl) for rtype, rdata in records)
                return answer
            for rtype, rdata in records:
                if rtype == qtype:
                    answer.append((owner, rtype, rdata, self.ttl))
            chain = [rdata for rtype, rdata in records if rtype == TYPE_CNAME]
            if qtype == TYPE_CNAME or not chain:
                return answer
            # A CNAME is part of the answer, then the chain is followed.
            answer.append((owner, TYPE_CNAME, chain[0], self.ttl))
            target = _decode_name(chain[0])
            if target in seen:
                return answer
            seen.add(target)
            owner = target
        return answer

    def soa_record(self) -> tuple[str, int, bytes, int] | None:
        for rtype, rdata in self.records(self.apex):
            if rtype == TYPE_SOA:
                return (self.apex, TYPE_SOA, rdata, self.ttl)
        return None


def _decode_name(rdata: bytes) -> str:
    labels: list[str] = []
    position = 0
    while position < len(rdata):
        length = rdata[position]
        position += 1
        if length == 0:
            break
        labels.append(rdata[position : position + length].decode("latin-1"))
        position += length
    return ".".join(labels).lower()


def demo_zone(apex: str = "example.test") -> Zone:
    """A small zone with one of every record type the server can answer."""
    zone = Zone(apex)
    zone.add(apex, TYPE_SOA, soa(f"ns1.{apex}", f"hostmaster.{apex}", serial=2026110501))
    zone.add(apex, TYPE_NS, ns(f"ns1.{apex}"))
    zone.add(f"ns1.{apex}", TYPE_A, a("192.0.2.53"))
    zone.add(apex, TYPE_A, a("192.0.2.10"))
    zone.add(apex, TYPE_AAAA, aaaa("2001:db8::10"))
    zone.add(apex, TYPE_TXT, txt("v=spf1 -all"))
    zone.add(apex, TYPE_MX, mx(10, f"mail.{apex}"))
    zone.add(f"mail.{apex}", TYPE_A, a("192.0.2.25"))
    zone.add(f"www.{apex}", TYPE_A, a("192.0.2.11"))
    zone.add(f"www.{apex}", TYPE_A, a("192.0.2.12"))
    zone.add(f"alias.{apex}", TYPE_CNAME, cname(f"www.{apex}"))
    zone.add(f"chain.{apex}", TYPE_CNAME, cname(f"alias.{apex}"))
    zone.add(f"big.{apex}", TYPE_TXT, txt("x" * 255 + "y" * 255))
    return zone


def class_name(qclass: int) -> str:
    return "IN" if qclass == CLASS_IN else f"class {qclass}"
