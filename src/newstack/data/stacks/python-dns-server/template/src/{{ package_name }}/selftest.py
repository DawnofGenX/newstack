"""The checks the stack runs on itself, over real sockets."""

from __future__ import annotations

import socket
import struct

from .client import ask_tcp, ask_udp, build_query, parse_reply
from .protocol import (
    CLASS_IN,
    FORMERR,
    NOERROR,
    NOTIMP,
    NXDOMAIN,
    REFUSED,
    TYPE_A,
    TYPE_AAAA,
    TYPE_ANY,
    TYPE_CNAME,
    TYPE_MX,
    TYPE_TXT,
    FormatError,
    encode_name,
    read_name,
)
from .server import Server, parse_port, respond
from .zone import demo_zone

HOST = "127.0.0.1"
APEX = "example.test"


class Checker:
    def __init__(self) -> None:
        self.checks = 0
        self.failures = 0

    def that(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks += 1
        if ok:
            print(f"ok {self.checks} - {name}")
            return
        self.failures += 1
        print(f"FAIL {self.checks} - {name}" + (f": {detail}" if detail else ""))

    def same(self, name: str, got: object, want: object) -> None:
        self.that(name, got == want, f"want {want!r}, got {got!r}")


def ask(port: int, name: str, qtype: int = TYPE_A, **options: int):
    return parse_reply(ask_udp(HOST, port, build_query(name, qtype, **options)))


def rcode(payload: bytes) -> int:
    return struct.unpack_from("!H", payload, 2)[0] & 0xF


def refuses(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return False
    except OSError:
        return True


def run() -> int:
    checks = Checker()
    zone = demo_zone(APEX)

    # -- the wire format, without a socket ------------------------------
    encoded = encode_name(f"www.{APEX}")
    checks.same("encode then read a name", read_name(encoded, 0)[0], f"www.{APEX}")
    pointed = b"\x03www\x07example\x04test\x00\x03ftp\xc0\x04"
    checks.same("a compression pointer is followed", read_name(pointed, 18)[0], f"ftp.{APEX}")
    try:
        read_name(b"\x03www\xc0\x0a", 0)
        checks.that("a forward pointer is rejected", False, "no error raised")
    except FormatError as error:
        checks.that("a forward pointer is rejected", "backwards" in str(error), str(error))
    try:
        read_name(b"\x03www", 0)
        checks.that("a truncated name is rejected", False, "no error raised")
    except FormatError:
        checks.that("a truncated name is rejected", True)

    # -- over UDP --------------------------------------------------------
    server = Server(HOST, 0, zone=zone).start()
    try:
        port = server.port
        reply = ask(port, f"www.{APEX}", ident=0x4242)
        checks.same("the transaction id comes back", reply.ident, 0x4242)
        checks.that("the answer is authoritative", reply.authoritative)
        checks.same("A records in zone order", reply.texts(), ["192.0.2.11", "192.0.2.12"])
        checks.same("rcode is NOERROR", reply.rcode, NOERROR)
        checks.same("the question is echoed", reply.questions[0].name, f"www.{APEX}")

        reply = ask(port, APEX, TYPE_AAAA)
        checks.same("AAAA text", reply.texts(), ["2001:db8::10"])

        reply = ask(port, APEX, TYPE_TXT)
        checks.same("TXT text", reply.texts(), ["v=spf1 -all"])

        reply = ask(port, APEX, TYPE_MX)
        checks.same("MX text carries the preference", reply.texts(), [f"10 mail.{APEX}"])

        reply = ask(port, f"alias.{APEX}")
        checks.same("a CNAME is followed", reply.texts()[-1], "192.0.2.12")
        checks.same("the chain starts at the CNAME", reply.answers[0].rtype, TYPE_CNAME)
        checks.same("alias resolves to two addresses", len(reply.answers), 3)

        reply = ask(port, f"chain.{APEX}")
        checks.same("two CNAME hops resolve", reply.texts()[-1], "192.0.2.12")
        checks.same("the chain is four records", len(reply.answers), 4)

        reply = ask(port, "WWW.Example.Test")
        checks.same("names are case insensitive", reply.texts(), ["192.0.2.11", "192.0.2.12"])

        reply = ask(port, f"www.{APEX}", TYPE_ANY)
        checks.same("ANY returns every type at the name", len(reply.answers), 2)

        reply = ask(port, f"nope.{APEX}")
        checks.same("an unknown name is NXDOMAIN", reply.rcode, NXDOMAIN)
        checks.same("NXDOMAIN is still authoritative", reply.authoritative, True)
        checks.same("NXDOMAIN carries the SOA", [r.rtype for r in reply.authority], [6])
        checks.same("NXDOMAIN has no answers", reply.answers, [])

        reply = ask(port, f"www.{APEX}", TYPE_MX)
        checks.same("a known name with no such type is NOERROR", reply.rcode, NOERROR)
        checks.same("it carries the SOA instead", [r.rtype for r in reply.authority], [6])

        reply = ask(port, "example.org")
        checks.same("a name outside the zone is REFUSED", reply.rcode, REFUSED)
        checks.same("REFUSED is not authoritative", reply.authoritative, False)

        reply = ask(port, f"www.{APEX}", qclass=3)
        checks.same("a non-IN class is NOTIMP", reply.rcode, NOTIMP)

        # A big TXT does not fit 512 bytes, and EDNS0 raises the ceiling.
        reply = ask(port, f"big.{APEX}", TYPE_TXT)
        checks.that("an oversized UDP answer is truncated", reply.truncated)
        checks.same("a truncated answer has no records", reply.answers, [])
        checks.same("a truncated answer echoes the question", reply.questions[0].qtype, TYPE_TXT)

        reply = ask(port, f"big.{APEX}", TYPE_TXT, edns=4096)
        checks.that("EDNS0 lets the big answer through", not reply.truncated)
        checks.same("the big TXT is 510 bytes of text", len(reply.texts()[0]), 510)

        # -- over TCP: the 2-byte length prefix, no truncation -----------
        payload = ask_tcp(HOST, port, build_query(f"big.{APEX}", TYPE_TXT))
        reply = parse_reply(payload)
        checks.that("TCP is never truncated", not reply.truncated)
        checks.same("TCP returns the whole big TXT", len(reply.texts()[0]), 510)

        reply = parse_reply(ask_tcp(HOST, port, build_query(f"www.{APEX}", TYPE_A)))
        checks.same("TCP answers the same as UDP", reply.texts(), ["192.0.2.11", "192.0.2.12"])

        # -- broken packets ---------------------------------------------
        checks.that("a two-byte packet is dropped", respond(b"\x12\x34", zone) == b"")
        cut = respond(b"\x12\x34\x01\x00\x00\x01" + b"\x00" * 6 + b"\x03www", zone)
        checks.same("a truncated question is FORMERR", rcode(cut), FORMERR)
        checks.same("FORMERR keeps the transaction id", struct.unpack_from("!H", cut, 0)[0], 0x1234)

        doubled = bytearray(build_query(f"www.{APEX}", TYPE_A))
        struct.pack_into("!H", doubled, 4, 2)
        doubled += encode_name(f"www.{APEX}") + struct.pack("!HH", TYPE_A, CLASS_IN)
        checks.same("two questions is FORMERR", rcode(respond(bytes(doubled), zone)), FORMERR)

        opcode = bytearray(build_query(f"www.{APEX}", TYPE_A))
        opcode[2] = (opcode[2] & 0x87) | 0x08  # opcode 1 = IQUERY
        checks.same("a non-zero opcode is NOTIMP", rcode(respond(bytes(opcode), zone)), NOTIMP)

        checks.same("a bad port is refused", bad_port("nope"), "PORT must be a number, got 'nope'")
        checks.same("parse_port accepts 5353", parse_port("5353"), 5353)

        # -- shutdown ----------------------------------------------------
        server.shutdown()
        checks.that("shutdown closes the sockets", refuses(HOST, port))
    finally:
        server.shutdown()

    print(f"selftest: {checks.checks} checks, {checks.failures} failed")
    return 0 if checks.failures == 0 else 1


def bad_port(raw: str) -> str:
    try:
        parse_port(raw)
    except ValueError as error:
        return str(error)
    return ""
