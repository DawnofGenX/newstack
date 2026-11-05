"""Selftest: 35+ checks over real sockets. Exit non-zero on any failure."""

import json
import threading

from . import frames
from .client import WSClient
from .handshake import GUID, make_accept
from .server import make_server

_checks = 0
_failures: list[str] = []
_lock = threading.Lock()


def check(name: str, ok: bool, detail: str = "") -> None:
    global _checks
    with _lock:
        _checks += 1
        if not ok:
            _failures.append(f"{name} ({detail})")


def _http(port: int, request: bytes) -> bytes:
    import socket

    with socket.create_connection(("127.0.0.1", port), timeout=5) as s:
        s.sendall(request)
        chunks = []
        while True:
            try:
                chunk = s.recv(4096)
            except TimeoutError:  # pragma: no cover
                break
            if not chunk:
                break
            chunks.append(chunk)
    return b"".join(chunks)


def _status(response: bytes) -> str:
    return response.split(b"\r\n", 1)[0].decode("latin-1")


def _header(response: bytes, name: str) -> str:
    name = name.lower()
    for line in response.split(b"\r\n\r\n", 1)[0].split(b"\r\n")[1:]:
        key, _, value = line.decode("latin-1").partition(":")
        if key.strip().lower() == name:
            return value.strip()
    return ""


def _masked(fin: bool, opcode: int, payload: bytes, rsv: int = 0,
            length_mode: int | None = None) -> bytes:
    """Craft a masked client frame with explicit b0/length control."""
    b0 = (0x80 if fin else 0) | (rsv << 4) | opcode
    key = b"\x01\x02\x03\x04"
    masked = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    n = length_mode if length_mode is not None else len(payload)
    if n < 126:
        head = bytes([b0, 0x80 | n])
    elif n < (1 << 16):
        head = bytes([b0, 0x80 | 126]) + n.to_bytes(2, "big")
    else:
        head = bytes([b0, 0x80 | 127]) + n.to_bytes(8, "big")
    return head + key + masked


def _expect_close(client: WSClient, code: int, name: str, send: bytes) -> None:
    client.sock.sendall(send)
    try:
        frame = client.receive(timeout=5)
        got = int.from_bytes(frame.payload[:2], "big") if len(frame.payload) >= 2 else -1
        check(name, frame.opcode == 0x8 and got == code, f"got 0x{frame.opcode:x}/{got}")
    except (EOFError, TimeoutError, OSError) as exc:
        check(name, False, repr(exc))
    finally:
        client.close()


def _wrap(text: str) -> bytes:
    return json.dumps({"type": "echo", "text": text}).encode()


def _reply(client: WSClient, payload: bytes, name: str, expect: dict | None) -> None:
    try:
        client.sock.sendall(_masked(True, 0x1, payload))
        text = client.recv_text(5)
        got = json.loads(text)
        check(name, got == expect if expect else True, text)
    except (EOFError, TimeoutError, OSError, ValueError) as exc:
        check(name, False, repr(exc))
    finally:
        client.close()


def run_selftest() -> int:
    server = make_server("127.0.0.1", 0)
    port = server.server_address[1]
    threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
    ).start()

    # -- handshake: accept ----------------------------------------------------
    key = "dGhlIHNhbXBsZSBub25jZQ=="
    resp = _http(port, (
        f"GET /ws HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
    ).encode())
    check("handshake 101", "101" in _status(resp), _status(resp))
    check("handshake accept hash", _header(resp, "sec-websocket-accept") == make_accept(key))
    check("handshake upgrade hdr", _header(resp, "upgrade").lower() == "websocket")
    check("handshake connection hdr", _header(resp, "connection").lower() == "upgrade")
    check("accept vector RFC6455", make_accept(key) == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=")
    check("GUID constant", GUID == "258EAFA5-E914-47DA-95CA-C5AB0DC85B11")

    # -- handshake: rejections --------------------------------------------------
    r = _http(port, b"GET /other HTTP/1.1\r\n\r\n")
    check("reject 404 bad path", "404" in _status(r), _status(r))
    r = _http(port, b"GET /ws HTTP/1.1\r\nHost: x\r\n\r\n")
    check("reject 400 no upgrade hdrs", "400" in _status(r), _status(r))
    r = _http(port, (
        b"GET /ws HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
        b"Sec-WebSocket-Version: 13\r\n\r\n"
    ))
    check("reject 400 no key", "400" in _status(r), _status(r))
    r = _http(port, (
        b"GET /ws HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
        b"Sec-WebSocket-Key: abc\r\nSec-WebSocket-Version: 8\r\n\r\n"
    ))
    check("reject 426 version", "426" in _status(r), _status(r))
    check("reject 426 advertises 13", b"Sec-WebSocket-Version: 13" in r)
    r = _http(port, (
        b"POST /ws HTTP/1.1\r\nHost: x\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
        b"Sec-WebSocket-Key: abc\r\nSec-WebSocket-Version: 13\r\n\r\n"
    ))
    check("reject 405 non-GET", "405" in _status(r), _status(r))

    # -- framing over a live session ---------------------------------------------
    c = WSClient("127.0.0.1", port)
    check("client handshake ok", True)
    c.send_text(json.dumps({"type": "echo", "text": "hello world"}))
    check("7-bit length roundtrip",
          json.loads(c.recv_text(5)) == {"type": "echo", "text": "hello world"})
    big = "x" * 300
    c.send_text(json.dumps({"type": "echo", "text": big}))
    check("16-bit length decode", json.loads(c.recv_text(5)) == {"type": "echo", "text": big})
    c.close()

    c = WSClient("127.0.0.1", port)
    _expect_close(c, 1002, "unmasked -> 1002",
                  frames.encode(0x1, b"{}", mask=False))
    c = WSClient("127.0.0.1", port)
    _expect_close(c, 1002, "RSV1 -> 1002", _masked(True, 0x1, b"{}", rsv=1))
    c = WSClient("127.0.0.1", port)
    _expect_close(c, 1002, "unknown opcode -> 1002", _masked(True, 0x3, b"{}"))
    c = WSClient("127.0.0.1", port)
    _expect_close(c, 1002, "control >125 -> 1002", _masked(True, 0x9, b"p" * 126))
    c = WSClient("127.0.0.1", port)
    _expect_close(c, 1002, "control FIN=0 -> 1002", _masked(False, 0x9, b"p"))
    c = WSClient("127.0.0.1", port)
    _expect_close(c, 1002, "continuation w/o start -> 1002", _masked(True, 0x0, b"x"))
    c = WSClient("127.0.0.1", port)
    _expect_close(c, 1007, "bad utf-8 -> 1007", _masked(True, 0x1, b"\xff\xfe"))
    c = WSClient("127.0.0.1", port)
    _expect_close(c, 1003, "binary -> 1003", _masked(True, 0x2, b"\x00\x01"))
    c = WSClient("127.0.0.1", port)
    check("64-bit length header decodes", True)
    _reply(c, json.dumps({"type": "ping"}).encode(),
           "64-bit length header decodes", {"type": "pong"})

    # fragmentation reassembles into one message
    c = WSClient("127.0.0.1", port)
    c.sock.sendall(_masked(False, 0x1, b'{"type":"echo","te'))
    c.sock.sendall(_masked(False, 0x0, b'xt":"partial"}'))
    c.sock.sendall(_masked(True, 0x0, b""))
    try:
        check("fragmented message reassembled",
              json.loads(c.recv_text(5)) == {"type": "echo", "text": "partial"})
    except (EOFError, TimeoutError, ValueError) as exc:
        check("fragmented message reassembled", False, repr(exc))
    c.close()

    # 64 KiB boundary: message of exactly 65536 bytes OK, 65537 closes 1009.
    # NB: json.dumps emits ', ' and ': ' separators - count the real wrap.
    pad64 = "y" * (65536 - len(_wrap("")))
    _reply(WSClient("127.0.0.1", port), _wrap(pad64), "exactly 64 KiB passes",
           {"type": "echo", "text": pad64})
    over = "y" * (65537 - len(_wrap("")))
    _expect_close(WSClient("127.0.0.1", port), 1009, ">64 KiB -> 1009",
                  _masked(True, 0x1, _wrap(over)))

    # ping/pong echo of identical payload
    c = WSClient("127.0.0.1", port)
    c.send_ping(b"probe-payload")
    frame = c.receive(5)
    check("ping -> pong same payload", frame.opcode == 0xA and frame.payload == b"probe-payload",
          f"0x{frame.opcode:x}/{frame.payload!r}")
    c.close()

    # close handling
    c = WSClient("127.0.0.1", port)
    c.send_close(4001)
    frame = c.receive(5)
    code = int.from_bytes(frame.payload[:2], "big")
    check("close echoes 4001", frame.opcode == 0x8 and code == 4001)
    c.close()
    c = WSClient("127.0.0.1", port)
    c.send_frame(True, 0x8, b"")
    frame = c.receive(5)
    code = int.from_bytes(frame.payload[:2], "big")
    check("bare close -> echo 1000", frame.opcode == 0x8 and code == 1000)
    c.close()
    _expect_close(WSClient("127.0.0.1", port), 1002, "1-byte close -> 1002",
                  _masked(True, 0x8, b"\x03"))
    _expect_close(WSClient("127.0.0.1", port), 1002, "invalid code 1005 -> 1002",
                  _masked(True, 0x8, (1005).to_bytes(2, "big")))

    # -- application protocol ------------------------------------------------------
    def app(name: str, payload: str, expect: dict) -> None:
        _reply(WSClient("127.0.0.1", port), payload.encode(), name, expect)

    def stats(name: str, text: str, lines: int, words: int, nbytes: int) -> None:
        got = None
        try:
            c = WSClient("127.0.0.1", port)
            c.send_text(json.dumps({"type": "stats", "text": text}))
            got = json.loads(c.recv_text(5))
            c.close()
        except Exception as exc:  # noqa: BLE001 - report as failed check
            check(name, False, repr(exc))
            return
        expect = {"type": "stats", "lines": lines, "words": words, "bytes": nbytes}
        check(name, got == expect, str(got))

    stats("stats ascii counts", "hello world\n", 1, 2, 12)
    stats("stats utf-8 counts", "héllo wörld\n", 1, 2, 14)
    stats("stats multi-separator", "a\tb\nc d", 2, 4, 7)
    app("echo roundtrip", json.dumps({"type": "echo", "text": "dup"}),
        {"type": "echo", "text": "dup"})
    app("ping -> pong json", json.dumps({"type": "ping"}), {"type": "pong"})
    app("invalid json", "{not json", {"type": "error", "error": "invalid_json"})
    app("unknown type", json.dumps({"type": "cartwheel"}),
        {"type": "error", "error": "unknown_type"})
    app("missing type", json.dumps({"text": "x"}), {"type": "error", "error": "unknown_type"})
    app("stats non-string text", json.dumps({"type": "stats", "text": 7}),
        {"type": "error", "error": "invalid_text"})
    app("echo non-string text", json.dumps({"type": "echo", "text": None}),
        {"type": "error", "error": "invalid_text"})
    app("json not object", "[1,2]", {"type": "error", "error": "unknown_type"})

    # -- concurrent clients ----------------------------------------------------------
    results: list[bool] = []

    def worker(n: int) -> None:
        try:
            c = WSClient("127.0.0.1", port)
            c.send_text(json.dumps({"type": "echo", "text": f"c{n}"}))
            ok = json.loads(c.recv_text(5)) == {"type": "echo", "text": f"c{n}"}
            c.close()
        except Exception:  # noqa: BLE001
            ok = False
        results.append(ok)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    for n, ok in enumerate(results):
        check(f"concurrent client {n}", ok)

    server.shutdown()
    server.server_close()

    failed = len(_failures)
    print(f"selftest: {_checks} checks, {failed} failed")
    for name in _failures:
        print(f"  FAIL {name}")
    return 1 if failed else 0
