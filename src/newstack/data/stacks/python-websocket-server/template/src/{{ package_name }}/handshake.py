"""HTTP upgrade handshake for RFC 6455 (accept + rejection responses)."""

import base64
import hashlib

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
WS_PATH = "/ws"


class HandshakeError(Exception):
    """Raised for requests that must be rejected with a plain HTTP status."""

    def __init__(self, status: int, reason: str, body: str) -> None:
        super().__init__(f"{status} {reason}")
        self.status = status
        self.reason = reason
        self.body = body


def make_accept(key: str) -> str:
    """Sec-WebSocket-Accept per RFC 6455 4.2.2 (base64 of raw SHA-1 digest)."""
    digest = hashlib.sha1((key + GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def _reject(status: int, reason: str, body: str) -> HandshakeError:
    return HandshakeError(status, reason, body)


def parse_request(raw: bytes) -> dict:
    """Parse the upgrade request; raise HandshakeError for rejections."""
    try:
        text = raw.decode("latin-1")
    except UnicodeDecodeError as exc:  # pragma: no cover - latin-1 is total
        raise _reject(400, "Bad Request", "bad request") from exc
    if "\r\n\r\n" not in text:
        raise _reject(400, "Bad Request", "incomplete request")
    head = text.split("\r\n\r\n", 1)[0]
    lines = head.split("\r\n")
    parts = lines[0].split()
    if len(parts) < 2:
        raise _reject(400, "Bad Request", "malformed request line")
    method, path = parts[0], parts[1]

    headers: dict[str, str] = {}
    for line in lines[1:]:
        if ":" not in line:
            continue
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip()

    if not path.startswith(WS_PATH):
        raise _reject(404, "Not Found", "no handler for this path")
    if method.upper() != "GET":
        raise _reject(405, "Method Not Allowed", "use GET to open a websocket")

    upgrade = headers.get("upgrade", "")
    connection = headers.get("connection", "")
    if upgrade.lower() != "websocket" or "upgrade" not in connection.lower():
        raise _reject(400, "Bad Request", "missing or incorrect upgrade headers")

    key = headers.get("sec-websocket-key", "")
    version = headers.get("sec-websocket-version", "")
    if not key or not version:
        raise _reject(400, "Bad Request", "missing key or version header")
    if version != "13":
        err = _reject(426, "Upgrade Required", "this server speaks websocket 13 only")
        err.version_header = version  # type: ignore[attr-defined]
        raise err

    return {"key": key, "path": path, "headers": headers}


def accept_response(key: str) -> bytes:
    return (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {make_accept(key)}\r\n\r\n"
    ).encode("ascii")


def rejection_response(err: HandshakeError) -> bytes:
    extra = ""
    if err.status == 426:
        extra = "Sec-WebSocket-Version: 13\r\n"
    body = err.body.encode("utf-8")
    return (
        f"HTTP/1.1 {err.status} {err.reason}\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"{extra}Connection: close\r\n\r\n"
    ).encode("ascii") + body
