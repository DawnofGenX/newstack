"""Protocol conformance suite: real server on port 0, masking client only."""

import json
import threading

import pytest

from {{ package_name }} import frames
from {{ package_name }}.client import WSClient
from {{ package_name }}.handshake import make_accept
from {{ package_name }}.server import make_server


@pytest.fixture(scope="module")
def server():
    srv = make_server("127.0.0.1", 0)
    port = srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    yield port
    srv.shutdown()
    srv.server_close()


@pytest.fixture()
def client(server):
    c = WSClient("127.0.0.1", server)
    yield c
    c.close()


def _reply(c: WSClient, obj) -> dict:
    c.send_text(json.dumps(obj))
    return json.loads(c.recv_text(5))


def _close_code(c: WSClient, send: bytes) -> int:
    c.sock.sendall(send)
    frame = c.receive(5)
    assert frame.opcode == 0x8
    return int.from_bytes(frame.payload[:2], "big")


def masked(fin=True, opcode=0x1, payload=b"", rsv=0):
    key = b"\x09\x08\x07\x06"
    m = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    n = len(payload)
    b0 = (0x80 if fin else 0) | (rsv << 4) | opcode
    if n < 126:
        head = bytes([b0, 0x80 | n])
    elif n < (1 << 16):
        head = bytes([b0, 0xFE]) + n.to_bytes(2, "big")
    else:
        head = bytes([b0, 0xFF]) + n.to_bytes(8, "big")
    return head + key + m


def test_handshake_accept(server):
    # WSClient's constructor asserts on any non-101 or bad accept hash.
    with WSClient("127.0.0.1", server) as c:
        assert c.reader is not None


def _plain_http(port: int, request: str) -> tuple[int, dict[str, str]]:
    """Send a raw request and read only the response head (no upgrade needed)."""
    import socket

    with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
        sock.sendall(request.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = sock.recv(4096)
            assert chunk, "server closed before sending a response head"
            buf += chunk
    head = buf.split(b"\r\n\r\n", 1)[0].decode("latin-1")
    lines = head.split("\r\n")
    status = int(lines[0].split()[1])
    headers = {}
    for line in lines[1:]:
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip()
    return status, headers


def _upgrade_request(path="/ws", version="13", method="GET", upgrade="websocket"):
    return (
        f"{method} {path} HTTP/1.1\r\n"
        "Host: 127.0.0.1\r\n"
        "Upgrade: " + upgrade + "\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
        "Sec-WebSocket-Version: " + version + "\r\n"
        "\r\n"
    )


def test_handshake_version_rejected(server):
    status, headers = _plain_http(server, _upgrade_request(version="8"))
    assert status == 426
    assert headers["sec-websocket-version"] == "13"


def test_handshake_bad_path_404(server):
    status, _ = _plain_http(server, _upgrade_request(path="/nope"))
    assert status == 404


def test_handshake_missing_upgrade_400(server):
    status, _ = _plain_http(server, _upgrade_request(upgrade="h2c"))
    assert status == 400


def test_handshake_wrong_method_405(server):
    status, _ = _plain_http(server, _upgrade_request(method="POST"))
    assert status == 405


def test_stats_ascii(server):
    with WSClient("127.0.0.1", server) as c:
        assert _reply(c, {"type": "stats", "text": "hello world\n"}) == {
            "type": "stats", "lines": 1, "words": 2, "bytes": 12}


def test_stats_utf8(server):
    with WSClient("127.0.0.1", server) as c:
        assert _reply(c, {"type": "stats", "text": "héllo wörld\n"}) == {
            "type": "stats", "lines": 1, "words": 2, "bytes": 14}


def test_stats_separators(server):
    with WSClient("127.0.0.1", server) as c:
        assert _reply(c, {"type": "stats", "text": "a\tb\nc"}) == {
            "type": "stats", "lines": 2, "words": 3, "bytes": 5}


def test_echo(server):
    with WSClient("127.0.0.1", server) as c:
        assert _reply(c, {"type": "echo", "text": "x"}) == {"type": "echo", "text": "x"}


def test_ping_pong_app(server):
    with WSClient("127.0.0.1", server) as c:
        assert _reply(c, {"type": "ping"}) == {"type": "pong"}


def test_invalid_json(server):
    with WSClient("127.0.0.1", server) as c:
        c.send_text("{oops")
        assert json.loads(c.recv_text(5)) == {"type": "error", "error": "invalid_json"}


def test_unknown_type(server):
    with WSClient("127.0.0.1", server) as c:
        assert _reply(c, {"type": "jump"}) == {"type": "error", "error": "unknown_type"}


def test_nonstring_text(server):
    with WSClient("127.0.0.1", server) as c:
        assert _reply(c, {"type": "echo", "text": 3}) == {"type": "error", "error": "invalid_text"}


def test_fragmentation(client):
    client.sock.sendall(masked(fin=False, opcode=0x1, payload=b'{"type":"ech'))
    client.sock.sendall(masked(fin=False, opcode=0x0, payload=b'o","text":"z"}'))
    client.sock.sendall(masked(fin=True, opcode=0x0, payload=b""))
    assert json.loads(client.recv_text(5)) == {"type": "echo", "text": "z"}


def test_unmasked_rejected(client):
    assert _close_code(client, frames.encode(0x1, b"{}", mask=False)) == 1002


def test_rsv_rejected(client):
    assert _close_code(client, masked(opcode=0x1, payload=b"{}", rsv=1)) == 1002


def test_unknown_opcode_rejected(client):
    assert _close_code(client, masked(opcode=0x7, payload=b"x")) == 1002


def test_oversized_control_rejected(client):
    assert _close_code(client, masked(opcode=0x9, payload=b"q" * 126)) == 1002


def test_utf8_rejection(client):
    assert _close_code(client, masked(payload=b"\xc3\x28")) == 1007


def test_binary_rejected(client):
    assert _close_code(client, masked(opcode=0x2, payload=b"\x00")) == 1003


def test_oversized_message_1009(server):
    with WSClient("127.0.0.1", server) as c:
        wrap_len = len(json.dumps({"type": "echo", "text": ""}))
        pad = "z" * (65537 - wrap_len)
        c.sock.sendall(masked(payload=json.dumps({"type": "echo", "text": pad}).encode()))
        frame = c.receive(5)
        assert int.from_bytes(frame.payload[:2], "big") == 1009


def test_ping_payload_echo(client):
    client.send_ping(b"abc123")
    frame = client.receive(5)
    assert frame.opcode == 0xA and frame.payload == b"abc123"


def test_close_echo(client):
    client.send_close(4242)
    frame = client.receive(5)
    assert frame.opcode == 0x8 and int.from_bytes(frame.payload[:2], "big") == 4242


def test_close_bare_defaults_1000(client):
    client.send_frame(True, 0x8, b"")
    frame = client.receive(5)
    assert int.from_bytes(frame.payload[:2], "big") == 1000


def test_close_one_byte_rejected(client):
    assert _close_code(client, masked(opcode=0x8, payload=b"\x01")) == 1002


def test_accept_hash_matches_guid(server):
    key = "x" * 24
    assert make_accept("dGhlIHNhbXBsZSBub25jZQ==") == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
    assert len(make_accept(key)) == 28
