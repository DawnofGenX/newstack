"""Self-checks that run against a real socket, not against the functions.

`--selftest` starts a server on an ephemeral port, talks RESP to it with the
client in `client.py`, and prints one line per check.
"""

from __future__ import annotations

import threading
import time

from .client import Client, Failure, Status
from .server import Server
from .store import Store


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

    def same(self, name: str, got, want) -> None:
        self.that(name, got == want, f"want {want!r}, got {got!r}")


def _is_error(value, prefix: str) -> bool:
    return isinstance(value, Failure) and value.message.startswith(prefix)


def run() -> int:
    check = Checker()
    server = Server(port=0, idle=5.0).start()
    host, port = server.host, server.port
    print(f"serving on {host}:{port}")

    with Client(host, port) as client:
        check.same("PING is a status reply", client.command("PING"), Status("PONG"))
        check.same("PING echoes its argument as a bulk", client.command("PING", "hi"), b"hi")
        check.same("ECHO returns the same bytes", client.command("ECHO", "hello"), b"hello")
        check.same("SET answers OK", client.command("SET", "greeting", "world"), Status("OK"))
        check.same("GET returns the value", client.command("GET", "greeting"), b"world")
        check.same("GET of a missing key is a nil bulk", client.command("GET", "nope"), None)
        check.same("EXISTS counts each named key", client.command("EXISTS", "greeting", "nope"), 1)
        check.same(
            "EXISTS counts duplicates twice", client.command("EXISTS", "greeting", "greeting"), 2
        )
        check.same("TYPE names a string", client.command("TYPE", "greeting"), Status("string"))
        check.same("TYPE names a missing key none", client.command("TYPE", "nope"), Status("none"))
        check.same("TTL of a missing key is -2", client.command("TTL", "nope"), -2)
        check.same("TTL without an expiry is -1", client.command("TTL", "greeting"), -1)
        check.same(
            "SET with EX stores an expiry",
            client.command("SET", "temp", "v", "EX", "10"),
            Status("OK"),
        )
        check.same("TTL rounds up so a fresh key is not 0", client.command("TTL", "temp"), 10)
        check.same("INCR creates a counter at 1", client.command("INCR", "counter"), 1)
        check.same("INCR increments", client.command("INCR", "counter"), 2)
        check.same("DECR increments downwards", client.command("DECR", "counter"), 1)
        check.that(
            "INCR refuses a value that is not an integer",
            _is_error(client.command("INCR", "greeting"), "ERR value is not an integer"),
        )
        check.same("DEL reports how many keys it removed", client.command("DEL", "greeting"), 1)
        check.same("DEL of a missing key removes zero", client.command("DEL", "greeting"), 0)
        check.same(
            "SET of an empty value is legal", client.command("SET", "empty", ""), Status("OK")
        )
        check.same("GET returns an empty bulk, not nil", client.command("GET", "empty"), b"")
        check.that(
            "SET EX 0 is refused",
            _is_error(client.command("SET", "k", "v", "EX", "0"), "ERR invalid expire time"),
        )
        check.that(
            "SET EX without a number is refused",
            _is_error(client.command("SET", "k", "v", "EX", "abc"), "ERR value is not an integer"),
        )
        check.that(
            "SET with an unknown option is a syntax error",
            _is_error(client.command("SET", "k", "v", "KEEPTTL"), "ERR syntax error"),
        )
        check.that(
            "an unknown command is an error, not a crash",
            _is_error(client.command("NOPE"), "ERR unknown command"),
        )
        check.that(
            "GET with no argument reports the arity",
            _is_error(client.command("GET"), "ERR wrong number of arguments for 'get' command"),
        )
        check.same("COMMAND keeps clients quiet", client.command("COMMAND", "DOCS"), [])
        check.same("DBSIZE counts live keys", client.command("DBSIZE") >= 2, True)
        check.same(
            "KEYS * returns every key",
            sorted(client.command("KEYS", "*")),
            sorted([b"counter", b"temp", b"empty"]),
        )
        check.same("KEYS takes a glob", client.command("KEYS", "c*"), [b"counter"])

        # Bytes, not text.
        blob = b"\x00\xff\r\nbinary payload"
        check.same("SET stores binary safely", client.command("SET", "bin", blob), Status("OK"))
        check.same("GET returns exactly those bytes", client.command("GET", "bin"), blob)
        big = bytes(range(256)) * 400
        check.same("a 100 KB value round-trips", client.command("SET", "big", big), Status("OK"))
        check.same("and comes back unchanged", client.command("GET", "big"), big)

        # Framing.
        check.same("an inline command works", client.command("PING"), Status("PONG"))
        client.send_bytes(b"PING\r\n")
        check.same("inline PING is answered", client.read_reply(), Status("PONG"))
        client.send_bytes(b'SET quoted "a b"\r\n')
        check.same("inline arguments can be quoted", client.read_reply(), Status("OK"))
        check.same("the quoted value kept its space", client.command("GET", "quoted"), b"a b")
        client.send_bytes(b"*0\r\n")
        check.same(
            "an empty multibulk is ignored, not answered", client.command("PING"), Status("PONG")
        )

        # Pipelining: two commands, one write, two replies, in order.
        client.send_bytes(b"*1\r\n$4\r\nPING\r\n*2\r\n$4\r\nECHO\r\n$2\r\nok\r\n")
        check.same("pipelined replies keep their order (1)", client.read_reply(), Status("PONG"))
        check.same("pipelined replies keep their order (2)", client.read_reply(), b"ok")

        # One byte at a time: the parser must hold a partial frame.
        for byte in b"*2\r\n$3\r\nGET\r\n$3\r\nbin\r\n":
            client.send_bytes(bytes([byte]))
        check.same(
            "a command split across 22 writes still parses", client.read_reply(), blob
        )

        check.same("FLUSHDB empties the keyspace", client.command("FLUSHDB"), Status("OK"))
        check.same("DBSIZE is 0 after FLUSHDB", client.command("DBSIZE"), 0)

    # Protocol errors close the connection after exactly one error line.
    with Client(host, port) as broken:
        broken.send_bytes(b"*abc\r\n")
        check.that(
            "a non-numeric multibulk length is a protocol error",
            _is_error(broken.read_reply(), "ERR Protocol error"),
        )
        check.same("the server then closes the connection", broken.read_raw(), b"")

    with Client(host, port) as broken:
        broken.send_bytes(b"*1\r\n$abc\r\nPING\r\n")
        check.that(
            "a non-numeric bulk length is a protocol error",
            _is_error(broken.read_reply(), "ERR Protocol error"),
        )

    with Client(host, port) as broken:
        broken.send_bytes(b"*1\r\n:5\r\n")
        check.that(
            "an argument that is not a bulk string is a protocol error",
            _is_error(broken.read_reply(), "ERR Protocol error"),
        )

    with Client(host, port) as broken:
        broken.send_bytes(b"*1\r\n$1\r\nAB\r\n")
        check.that(
            "a body that overruns its length is a protocol error",
            _is_error(broken.read_reply(), "ERR Protocol error"),
        )
        check.same("and that connection is closed too", broken.read_raw(), b"")

    # Concurrency: one counter, four threads, no lost increments.
    def hammer() -> None:
        with Client(host, port) as client:
            for _ in range(25):
                client.command("INCR", "shared")

    workers = [threading.Thread(target=hammer) for _ in range(4)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(timeout=20)
    with Client(host, port) as client:
        check.same(
            "100 concurrent increments are all counted", client.command("GET", "shared"), b"100"
        )

    # Expiry needs a clock the test can move.
    now = [1000.0]

    def clock() -> float:
        return now[0]

    fake = Store(clock=clock)
    fake.set(b"k", b"v", ttl=5.0)
    check.same("a key with a ttl is still there before the deadline", fake.get(b"k"), b"v")
    check.same("ttl reports the remaining seconds", fake.ttl(b"k"), 5)
    now[0] += 6.0
    check.same("a key is gone after its deadline", fake.get(b"k"), None)
    check.same("and ttl says the key does not exist", fake.ttl(b"k"), -2)
    check.same("and dbsize agrees", fake.dbsize(), 0)

    # Shutdown must not hang with an idle client connected.
    parked = Client(host, port)
    parked.send_command("PING")
    check.same("the parked client is answered first", parked.read_reply(), Status("PONG"))
    started = time.monotonic()
    server.shutdown()
    parked.close()
    check.same(
        "shutdown returns quickly with a client attached", time.monotonic() - started < 3.0, True
    )

    print(f"selftest: {check.checks} checks, {check.failures} failed")
    return 1 if check.failures else 0
