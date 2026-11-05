"""The tests talk RESP over a real socket; nothing here imports the handler.

That is deliberate: a unit test that calls `commands.execute` would pass even if
the framing were broken, and framing is the part that breaks.
"""

from __future__ import annotations

import threading

import pytest

from {{ package_name }}.client import Client, Failure, Status
from {{ package_name }}.protocol import CommandReader
from {{ package_name }}.server import Server, parse_port
from {{ package_name }}.store import NotAnInteger, Store


@pytest.fixture()
def server():
    instance = Server(port=0, idle=5.0).start()
    yield instance
    instance.shutdown()


@pytest.fixture()
def client(server):
    with Client(server.host, server.port) as connection:
        yield connection


def test_ping_and_echo(client):
    assert client.command("PING") == Status("PONG")
    assert client.command("PING", "hi") == b"hi"
    assert client.command("ECHO", "hello") == b"hello"


def test_set_get_del(client):
    assert client.command("SET", "k", "v") == Status("OK")
    assert client.command("GET", "k") == b"v"
    assert client.command("DEL", "k") == 1
    assert client.command("GET", "k") is None
    assert client.command("EXISTS", "k") == 0


def test_exists_counts_every_named_key(client):
    client.command("SET", "a", "1")
    assert client.command("EXISTS", "a", "a", "missing") == 2


def test_counters(client):
    assert client.command("INCR", "n") == 1
    assert client.command("INCR", "n") == 2
    assert client.command("DECR", "n") == 1
    client.command("SET", "text", "abc")
    answer = client.command("INCR", "text")
    assert isinstance(answer, Failure)
    assert answer.message == "ERR value is not an integer or out of range"
    assert client.command("GET", "text") == b"abc"


def test_expiry_uses_an_injectable_clock():
    now = [500.0]
    server = Server(port=0, store=Store(clock=lambda: now[0])).start()
    try:
        with Client(server.host, server.port) as client:
            client.command("SET", "session", "token", "EX", "10")
            assert client.command("TTL", "session") == 10
            now[0] += 4.4
            assert client.command("TTL", "session") == 6
            now[0] += 6.0
            assert client.command("GET", "session") is None
            assert client.command("TTL", "session") == -2
            assert client.command("DBSIZE") == 0
    finally:
        server.shutdown()


def test_ttl_of_a_key_without_expiry_is_minus_one(client):
    client.command("SET", "plain", "v")
    assert client.command("TTL", "plain") == -1
    assert client.command("TTL", "missing") == -2


def test_a_command_split_across_writes(client):
    payload = b"*3\r\n$3\r\nSET\r\n$5\r\nsplit\r\n$5\r\nvalue\r\n"
    for byte in payload:
        client.send_bytes(bytes([byte]))
    assert client.read_reply() == Status("OK")
    assert client.command("GET", "split") == b"value"


def test_two_commands_in_one_write_get_two_replies(client):
    client.send_bytes(b"*1\r\n$4\r\nPING\r\n*2\r\n$4\r\nECHO\r\n$2\r\nhi\r\n")
    assert client.read_reply() == Status("PONG")
    assert client.read_reply() == b"hi"


def test_inline_commands_and_quoted_arguments(client):
    client.send_bytes(b"PING\r\n")
    assert client.read_reply() == Status("PONG")
    client.send_bytes(b'SET quoted "two words"\r\n')
    assert client.read_reply() == Status("OK")
    assert client.command("GET", "quoted") == b"two words"
    client.send_bytes(b'SET escaped "a\\x20b"\r\n')
    assert client.read_reply() == Status("OK")
    assert client.command("GET", "escaped") == b"a b"


def test_an_empty_multibulk_is_ignored(client):
    client.send_bytes(b"*0\r\n")
    assert client.command("PING") == Status("PONG")


def test_binary_and_large_values_round_trip(client):
    blob = b"\x00\xff\r\n\x80tail"
    client.command("SET", "blob", blob)
    assert client.command("GET", "blob") == blob
    big = bytes(range(256)) * 400
    client.command("SET", "big", big)
    assert client.command("GET", "big") == big


@pytest.mark.parametrize(
    "payload",
    [
        b"*abc\r\n",
        b"*1\r\n$abc\r\nPING\r\n",
        b"*1\r\n:5\r\n",
        b"*1\r\n$1\r\nAB\r\n",
    ],
)
def test_a_malformed_frame_is_an_error_then_a_close(server, payload):
    with Client(server.host, server.port) as broken:
        broken.send_bytes(payload)
        answer = broken.read_reply()
        assert isinstance(answer, Failure)
        assert answer.message.startswith("ERR Protocol error")
        assert broken.read_raw() == b""


def test_errors_do_not_close_the_connection(client):
    answer = client.command("NOPE")
    assert isinstance(answer, Failure)
    assert "unknown command" in answer.message
    arity = client.command("GET")
    assert isinstance(arity, Failure)
    assert arity.message == "ERR wrong number of arguments for 'get' command"
    assert client.command("PING") == Status("PONG")


def test_set_options(client):
    assert client.command("SET", "k", "v", "EX", "30") == Status("OK")
    assert client.command("TTL", "k") == 30
    for args in (("SET", "k", "v", "EX", "0"), ("SET", "k", "v", "EX", "abc")):
        answer = client.command(*args)
        assert isinstance(answer, Failure)
    assert client.command("SET", "k", "v", "NX") == Failure("ERR syntax error")


def test_keys_and_flush(client):
    for key in ("alpha", "beta", "gamma"):
        client.command("SET", key, "1")
    assert client.command("KEYS", "*") == [b"alpha", b"beta", b"gamma"]
    assert client.command("KEYS", "a*") == [b"alpha"]
    assert client.command("KEYS", "?eta") == [b"beta"]
    assert client.command("DBSIZE") == 3
    assert client.command("FLUSHDB") == Status("OK")
    assert client.command("DBSIZE") == 0


def test_concurrent_increments_are_not_lost(server):
    def hammer():
        with Client(server.host, server.port) as connection:
            for _ in range(20):
                connection.command("INCR", "shared")

    threads = [threading.Thread(target=hammer) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)
    with Client(server.host, server.port) as client:
        assert client.command("GET", "shared") == b"100"


def test_shutdown_releases_a_connected_client():
    server = Server(port=0).start()
    parked = Client(server.host, server.port)
    parked.send_command("PING")
    assert parked.read_reply() == Status("PONG")
    server.shutdown()
    parked.close()


def test_the_store_refuses_to_increment_a_word():
    store = Store()
    store.set(b"word", b"abc")
    with pytest.raises(NotAnInteger):
        store.incr(b"word")


@pytest.mark.parametrize("raw", ["abc", "-1", "70000"])
def test_parse_port_rejects_nonsense(raw):
    with pytest.raises(ValueError):
        parse_port(raw)


def test_the_reader_holds_a_partial_frame():
    reader = CommandReader()
    assert reader.feed(b"*2\r\n$3\r\nGET\r\n$3\r\nab") == []
    assert reader.pending > 0
    assert reader.feed(b"c\r\n") == [[b"GET", b"abc"]]
    assert reader.pending == 0
