"""The broker and the wire, exercised over real sockets."""

from __future__ import annotations

import contextlib
import socket
import time

import pytest

from {{ package_name }}.broker import Broker
from {{ package_name }}.client import Client
from {{ package_name }}.packet import (
    ACCEPTED,
    BAD_PROTOCOL,
    SUB_FAILURE,
    utf8,
)
from {{ package_name }}.server import Server, parse_port
from {{ package_name }}.topics import matches, valid_filter

HOST = "127.0.0.1"


@pytest.fixture()
def server():
    running = Server(HOST, 0).start()
    yield running
    running.shutdown()


@pytest.fixture()
def mk(server):
    made: list[Client] = []

    def factory(name: str, **options) -> Client:
        made.append(Client(HOST, server.port, name, **options))
        return made[-1]

    yield factory
    for created in made:
        with contextlib.suppress(OSError):
            created.close()


def connected(mk, name: str, **options) -> Client:
    made = mk(name, **options)
    assert made.connect() == ACCEPTED
    return made


def test_connect_is_accepted(mk):
    assert mk("one").connect() == ACCEPTED


def test_ping_is_answered(mk):
    talker = connected(mk, "pinger")
    talker.ping()


def test_a_subscription_is_granted_the_requested_qos(mk):
    reader = connected(mk, "reader")
    assert reader.subscribe(("room/1", 1), ("room/2", 2)) == [1, 2]


def test_an_invalid_filter_is_refused_and_the_session_lives(mk):
    reader = connected(mk, "picky")
    assert reader.subscribe(("room/#/x", 0)) == [SUB_FAILURE]
    reader.ping()


def test_a_qos_zero_publish_reaches_a_wildcard_subscriber(mk):
    reader = connected(mk, "reader")
    reader.subscribe(("room/#", 0))
    talker = connected(mk, "talker")
    talker.publish("room/1/2/3", b"body")
    message = reader.next_publish(2.0)
    assert (message.topic, message.payload, message.qos) == ("room/1/2/3", b"body", 0)
    assert message.retain is False


def test_a_qos_one_publish_is_acknowledged_and_downgraded(mk):
    eager = connected(mk, "eager")
    eager.subscribe(("m/1", 2))
    plain = connected(mk, "plain")
    plain.subscribe(("m/1", 0))
    talker = connected(mk, "talker")
    talker.publish("m/1", b"payload", qos=1)
    assert eager.next_publish(2.0).qos == 1
    assert plain.next_publish(2.0).qos == 0


def test_packet_ids_increase_with_each_qos_publish(mk):
    reader = connected(mk, "reader")
    reader.subscribe(("m/#", 0))
    talker = connected(mk, "talker")
    first = talker.publish("m/1", b"one", qos=1)
    second = talker.publish("m/2", b"two", qos=1)
    assert (first, second) == (1, 2)
    assert [m.payload for m in reader.collect(2, 2.0)] == [b"one", b"two"]


def test_a_retained_message_waits_for_the_next_subscriber(mk):
    talker = connected(mk, "talker")
    talker.publish("slow/1", b"kept", qos=1, retain=True)
    latecomer = connected(mk, "latecomer")
    latecomer.subscribe(("slow/#", 0))
    message = latecomer.next_publish(2.0)
    assert (message.payload, message.retain) == (b"kept", True)


def test_an_empty_retained_publish_deletes_the_record(mk):
    talker = connected(mk, "talker")
    talker.publish("slow/1", b"kept", qos=1, retain=True)
    talker.publish("slow/1", b"", qos=1, retain=True)
    latecomer = connected(mk, "latecomer")
    latecomer.subscribe(("slow/#", 0))
    assert latecomer.next_publish(0.6) is None


def test_unsubscribe_stops_delivery(mk):
    reader = connected(mk, "reader")
    reader.subscribe(("u/1", 0))
    talker = connected(mk, "talker")
    talker.publish("u/1", b"first")
    assert reader.next_publish(2.0).payload == b"first"
    reader.unsubscribe("u/1")
    talker.publish("u/1", b"second")
    assert reader.next_publish(0.6) is None


def test_a_second_connection_with_the_same_id_takes_the_session_over(mk):
    first = connected(mk, "twin")
    second = mk("twin")
    assert second.connect() == ACCEPTED
    try:
        gone = first.sock.recv(16) == b""
    except OSError:
        gone = True
    assert gone
    second.ping()


def test_a_clean_session_forgets_its_subscriptions(mk):
    first = connected(mk, "ephemeral", clean=True)
    first.subscribe(("c/1", 0))
    first.disconnect()
    again = mk("ephemeral", clean=True)
    assert again.connect() == ACCEPTED
    connected(mk, "talker").publish("c/1", b"lost")
    assert again.next_publish(0.6) is None


def test_a_persistent_session_keeps_its_subscriptions(mk):
    first = connected(mk, "keeper", clean=False)
    first.subscribe(("k/1", 0))
    first.disconnect()
    again = mk("keeper", clean=False)
    assert again.connect() == ACCEPTED
    connected(mk, "talker").publish("k/1", b"kept")
    assert again.next_publish(2.0).payload == b"kept"


def test_a_wildcard_publish_topic_closes_the_connection(mk):
    rude = connected(mk, "rude")
    rude.publish("a/+/c", b"nope")
    rude.sock.settimeout(2.0)
    assert rude.sock.recv(16) == b""


def test_a_packet_split_byte_by_byte_is_understood(server, mk):
    reader = connected(mk, "reader")
    reader.subscribe(("s/1", 0))
    raw = socket.create_connection((HOST, server.port), timeout=5.0)
    try:
        body = utf8("MQTT") + bytes([4, 0x02]) + (30).to_bytes(2, "big") + utf8("slow")
        for byte in bytes([0x10, len(body)]) + body:
            raw.sendall(bytes([byte]))
            time.sleep(0.001)
        assert raw.recv(4)[3] == ACCEPTED
        publish = utf8("s/1") + b"split"
        for byte in bytes([0x30, len(publish)]) + publish:
            raw.sendall(bytes([byte]))
            time.sleep(0.001)
        assert reader.next_publish(2.0).payload == b"split"
    finally:
        raw.close()


def test_a_large_payload_survives_the_framing(mk):
    reader = connected(mk, "reader")
    reader.subscribe(("big/1", 0))
    talker = connected(mk, "talker")
    payload = b"y" * 200_000
    talker.publish("big/1", payload, qos=1)
    assert reader.next_publish(5.0).payload == payload


def test_the_first_packet_must_be_a_connect(server):
    raw = socket.create_connection((HOST, server.port), timeout=5.0)
    try:
        raw.sendall(bytes([0x30, 0x03]) + b"\x00\x01ok")
        try:
            received = raw.recv(16)
        except ConnectionResetError:
            # The server closed with two bytes still unread, so the close
            # arrives as a reset rather than a clean end of stream.
            received = b""
        assert received == b""
    finally:
        raw.close()


def test_an_old_protocol_level_is_refused(server):
    raw = Client(HOST, server.port, "older")
    try:
        body = utf8("MQTT") + bytes([3, 0x02]) + (30).to_bytes(2, "big") + utf8("older")
        raw.send(bytes([0x10, len(body)]) + body)
        _, reply = raw._read()
        assert reply[1] == BAD_PROTOCOL
    finally:
        raw.close()


@pytest.mark.parametrize("filter_, topic, expected", [
    ("a/b", "a/b", True),
    ("a/b", "a/b/c", False),
    ("a/+/c", "a/b/c", True),
    ("a/+/c", "a/b/d/c", False),
    ("a/#", "a", True),
    ("a/#", "a/b/c", True),
    ("#", "anything/at/all", True),
    ("a/+/b", "a//b", True),
])
def test_topic_matching(filter_, topic, expected):
    assert matches(filter_, topic) is expected


@pytest.mark.parametrize("bad", ["a/#/b", "a+/b", "a/+b", "a/#/", ""])
def test_invalid_filters(bad):
    assert not valid_filter(bad)


def test_the_broker_stores_and_drops_retained_messages():
    broker = Broker()
    broker.publish("r/1", b"kept", 1, True)
    assert broker.retained() == {"r/1": (b"kept", 1)}
    broker.publish("r/1", b"", 0, True)
    assert broker.retained() == {}


def test_parse_port_rejects_nonsense():
    assert parse_port("1883") == 1883
    with pytest.raises(ValueError):
        parse_port("nonsense")
    with pytest.raises(ValueError):
        parse_port("70000")
