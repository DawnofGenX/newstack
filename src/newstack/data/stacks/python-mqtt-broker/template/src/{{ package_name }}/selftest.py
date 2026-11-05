"""The checks the stack runs on itself, over real sockets."""

from __future__ import annotations

import contextlib
import socket
import time

from .broker import Broker
from .client import Client
from .packet import (
    ACCEPTED,
    BAD_PROTOCOL,
    SUB_FAILURE,
    ProtocolError,
    encode_remaining_length,
    read_remaining_length,
    read_utf8,
    utf8,
)
from .server import Server
from .topics import matches, valid_filter, valid_topic_name

HOST = "127.0.0.1"
PORT_MESSAGE = "PORT must be a number, got 'nope'"


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


def raises(function, *args) -> bool:
    try:
        function(*args)
    except (ProtocolError, ValueError):
        return True
    return False


def client(port: int, name: str, **options) -> Client:
    return Client(HOST, port, name, **options)


def drain(client_: Client, timeout: float = 0.4) -> int:
    """Read and drop whatever has already been queued for a subscriber."""
    dropped = 0
    while client_.next_publish(timeout) is not None:
        dropped += 1
    return dropped


def run() -> int:
    checks = Checker()

    # -- the varint that frames every packet ----------------------------
    checks.same("length 0 encodes to one zero byte", encode_remaining_length(0), b"\x00")
    checks.same("length 127 stays one byte", encode_remaining_length(127), b"\x7f")
    checks.same("length 128 needs two bytes", encode_remaining_length(128), b"\x80\x01")
    checks.same("length 16383 is still two bytes", encode_remaining_length(16383), b"\xff\x7f")
    checks.same("length 16384 needs three bytes", encode_remaining_length(16384), b"\x80\x80\x01")
    for size in (0, 127, 128, 16_383, 16_384, 2_097_151, 268_435_455):
        raw = b"\x00" + encode_remaining_length(size)
        checks.same(f"length {size} round-trips", read_remaining_length(raw), (size, len(raw)))
    checks.that("a truncated varint is an error", raises(read_remaining_length, b"\x00\x80"))
    too_long = b"\x00" + b"\xff" * 5
    checks.that("a five-byte varint is an error", raises(read_remaining_length, too_long))
    checks.that("a negative length is an error", raises(encode_remaining_length, -1))

    checks.same("a string keeps its bytes", read_utf8(utf8("héllo"), 0)[0], "héllo")
    checks.that("a short string field is an error", raises(read_utf8, b"\x00\x05ab", 0))
    checks.that("non-UTF-8 is a protocol error", raises(read_utf8, b"\x00\x02\xff\xfe", 0))

    # -- topic matching -------------------------------------------------
    checks.that("a plain name matches itself", matches("a/b", "a/b"))
    checks.that("a plain name does not match a longer topic", not matches("a/b", "a/b/c"))
    checks.that("+ covers exactly one level", matches("a/+/c", "a/b/c"))
    checks.that("+ does not cover two levels", not matches("a/+/c", "a/b/d/c"))
    checks.that("# covers the subtree", matches("a/#", "a/b/c"))
    checks.that("# also covers the parent", matches("a/#", "a"))
    checks.that("# covers a sibling", matches("a/#", "a/b"))
    checks.that("an empty level is a real level", matches("a/+/b", "a//b"))
    checks.that("a filter cannot put # mid-path", not valid_filter("a/#/b"))
    checks.that("a filter cannot mix + with text", not valid_filter("a+/b"))
    checks.that("# on its own is legal", valid_filter("#"))
    checks.that("a publish topic has no wildcards", not valid_topic_name("a/+/c"))
    checks.that("a publish topic cannot be empty", not valid_topic_name(""))

    # -- the broker, without sockets ------------------------------------
    broker = Broker()
    sent: list[bytes] = []
    session = broker.attach("unit", True, sent.append)
    checks.same("a subscribe is granted the requested QoS", broker.subscribe(session, "a/b", 1), 1)
    checks.same("a QoS of 5 is capped at 2", broker.subscribe(session, "a/c", 5), 2)
    checks.same("an invalid filter is refused", broker.subscribe(session, "a/#/b", 0), SUB_FAILURE)
    checks.same("a publish to nobody delivers to nobody", broker.publish("z", b"", 0, False), [])
    broker.publish("a/b", b"first", 1, True)
    checks.same("a retained message is remembered", list(broker.retained()), ["a/b"])
    broker.publish("a/b", b"", 0, True)
    checks.same("an empty retained payload deletes it", broker.retained(), {})

    # -- over sockets ----------------------------------------------------
    server = Server(HOST, 0).start()
    try:
        port = server.port

        chatty = client(port, "chatty")
        checks.same("CONNECT is accepted", chatty.connect(), ACCEPTED)
        chatty.ping()
        checks.that("PINGREQ is answered", True)
        granted = chatty.subscribe(("room/#", 1), ("a/+/c", 0))
        checks.same("SUBSCRIBE reports the granted QoS", granted, [1, 0])

        talker = client(port, "talker")
        talker.connect()
        talker.publish("room/1", b"hello")
        message = chatty.next_publish(2.0)
        arrived = (message.topic, message.payload)
        checks.same("a QoS 0 publish arrives", arrived, ("room/1", b"hello"))
        checks.same("and it arrives at QoS 0", message.qos, 0)
        checks.that("and is not marked retained", not message.retain)

        talker.publish("a/b/c", b"deep")
        deep = chatty.next_publish(2.0)
        checks.same("a + filter catches a deep topic", deep.payload, b"deep")

        second = client(port, "second")
        second.connect()
        second.subscribe(("room/1", 2))
        talker.publish("room/1", b"both")
        checks.same("two subscribers both get it", chatty.next_publish(2.0).payload, b"both")
        checks.same("the second one too", second.next_publish(2.0).payload, b"both")

        plain = client(port, "plain")
        plain.connect()
        plain.subscribe(("room/1", 0))
        talker.publish("room/1", b"qos-one", qos=1)
        checks.same("a QoS 2 subscriber receives it at QoS 1", second.next_publish(2.0).qos, 1)
        checks.same("a QoS 1 subscriber gets it at QoS 1", chatty.next_publish(2.0).qos, 1)
        checks.same("a QoS 0 subscriber gets it downgraded", plain.next_publish(2.0).qos, 0)

        # A retained publish is acknowledged, so the broker has stored it
        # before the assertion runs.
        talker.publish("room/9", b"kept", qos=1, retain=True)
        checks.same("a retained message is stored", list(server.broker.retained()), ["room/9"])
        latecomer = client(port, "latecomer")
        latecomer.connect()
        latecomer.subscribe(("room/#", 0))
        parked = latecomer.next_publish(2.0)
        checks.same("a new subscriber gets the retained message", parked.payload, b"kept")
        checks.that("and it is flagged as retained", parked.retain)
        talker.publish("room/9", b"", qos=1, retain=True)
        emptied = latecomer.next_publish(2.0)
        checks.same("an empty retained publish reaches the subscriber", emptied.payload, b"")
        checks.same("the retained record is gone", server.broker.retained(), {})

        # chatty also received the retained traffic for room/#; read it out
        # of the way so the next control packet it sees is the UNSUBACK.
        drain(chatty)
        chatty.unsubscribe("room/#")
        talker.publish("room/1", b"after-unsubscribe")
        still = second.next_publish(2.0)
        checks.same("the second subscriber still gets it", still.payload, b"after-unsubscribe")
        checks.same("the unsubscribed one does not", chatty.next_publish(0.6), None)

        twin = client(port, "talker")
        checks.same("a second connection with a live id is accepted", twin.connect(), ACCEPTED)
        try:
            gone = talker.sock.recv(16) == b""
        except OSError:
            gone = True
        checks.that("the broker closes the connection it took the id from", gone)
        talker = twin

        # A clean session forgets everything; a persistent one keeps its filters.
        ephemeral = client(port, "ephemeral", clean=True)
        ephemeral.connect()
        ephemeral.subscribe(("s/1", 0))
        ephemeral.disconnect()
        again = client(port, "ephemeral", clean=True)
        again.connect()
        talker.publish("s/1", b"lost")
        checks.same("a clean session drops its subscriptions", again.next_publish(0.6), None)

        keeper = client(port, "keeper", clean=False)
        keeper.connect()
        keeper.subscribe(("k/1", 0))
        keeper.disconnect()
        keeper_back = client(port, "keeper", clean=False)
        checks.same("a persistent session reconnects", keeper_back.connect(), ACCEPTED)
        talker.publish("k/1", b"kept-session")
        checks.same(
            "and keeps its subscriptions", keeper_back.next_publish(2.0).payload, b"kept-session"
        )

        # A publish topic with a wildcard is a protocol error: the server
        # answers nothing and closes the connection.
        rude = client(port, "rude")
        rude.connect()
        rude.publish("a/+/c", b"nope")
        rude.sock.settimeout(2.0)
        checks.same("a wildcard publish closes the connection", rude.sock.recv(16), b"")
        rude.close()

        # A bad filter is refused inside a SUBACK, and the session survives.
        picky = client(port, "picky")
        picky.connect()
        checks.same("an invalid filter is refused", picky.subscribe(("a/#/b", 0)), [SUB_FAILURE])
        picky.ping()
        checks.that("the session survives a refused filter", True)
        picky.disconnect()

        # A protocol level this broker does not speak gets a CONNACK and a close.
        older = Client(HOST, port, "older")
        body = utf8("MQTT") + bytes([3, 0x02]) + (30).to_bytes(2, "big") + utf8("older")
        older.send(bytes([0x10, len(body)]) + body)
        first, reply = older._read()
        checks.same("an old protocol level is refused", reply[1], BAD_PROTOCOL)
        older.close()

        # The framing must survive a packet split across many writes.
        slowwatch = client(port, "slowwatch")
        slowwatch.connect()
        slowwatch.subscribe(("room/1", 0))
        slow = socket.create_connection((HOST, port), timeout=5.0)
        connect_body = utf8("MQTT") + bytes([4, 0x02]) + (30).to_bytes(2, "big") + utf8("slow")
        connect_packet = bytes([0x10, len(connect_body)]) + connect_body
        for byte in connect_packet:
            slow.sendall(bytes([byte]))
            time.sleep(0.001)
        checks.same("a byte-at-a-time CONNECT is understood", slow.recv(4)[3], ACCEPTED)
        publish_body = utf8("room/1") + b"slow"
        publish_packet = bytes([0x30, len(publish_body)]) + publish_body
        for byte in publish_packet:
            slow.sendall(bytes([byte]))
            time.sleep(0.001)
        split = slowwatch.next_publish(2.0)
        checks.same("a byte-at-a-time PUBLISH is delivered", split.payload, b"slow")
        slow.close()
        slowwatch.disconnect()

        # A big payload has to be framed in more than three length bytes.
        drain(second)
        drain(plain)
        big = b"x" * 100_000
        talker.publish("room/1", big, qos=1)
        whole = second.next_publish(5.0)
        checks.same("a 100 KB payload is framed whole", len(whole.payload), 100_000)
        checks.that("and it is the same bytes", whole.payload == big)

        # The first packet must be CONNECT, whatever it claims to be.
        confusion = socket.create_connection((HOST, port), timeout=5.0)
        confusion.sendall(bytes([0x30, 0x03]) + utf8("a")[:1] + b"ok")
        checks.same("a non-CONNECT first packet is closed", confusion.recv(16), b"")
        confusion.close()

        checks.same("parse_port accepts 1883", parse_port_ok("1883"), 1883)
        checks.same("parse_port refuses nonsense", bad_port("nope"), PORT_MESSAGE)

        for done in (chatty, talker, second, plain, latecomer, again, keeper_back):
            with contextlib.suppress(OSError):
                done.disconnect()
        server.shutdown()
        checks.that("shutdown closes the listener", refuses(HOST, port))
    finally:
        server.shutdown()

    print(f"selftest: {checks.checks} checks, {checks.failures} failed")
    return 0 if checks.failures == 0 else 1


def parse_port_ok(raw: str) -> int:
    from .server import parse_port

    return parse_port(raw)


def bad_port(raw: str) -> str:
    from .server import parse_port

    try:
        parse_port(raw)
    except ValueError as error:
        return str(error)
    return ""


def refuses(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
            return False
    except OSError:
        return True

