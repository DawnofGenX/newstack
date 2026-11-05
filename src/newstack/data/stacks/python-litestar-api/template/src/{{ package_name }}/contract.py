"""The contract as a pure function: (method, raw target, body) -> (status, JSON text).

Nothing here imports Litestar. The framework adapter is four lines of glue, so
every rule below — the status codes, the 404 detail string, the key order of the
stats reply — is testable without a socket, and readable without knowing what a
Litestar handler signature looks like.
"""

from __future__ import annotations

from . import counts
from .jsonread import read_text_member

MISSING_TEXT = '{"error":"missing_text"}'
INVALID_JSON = '{"error":"invalid_json"}'
METHOD_NOT_ALLOWED = '{"error":"method_not_allowed"}'

#: byte values a percent escape may not produce
_HEX = "0123456789abcdefABCDEF"


def quote(text: str) -> str:
    """JSON string contents for `text`, matching what the other stacks emit.

    `json.dumps(..., ensure_ascii=False)` is not used: it leaves U+2028 alone and
    would let a lone surrogate through as an escape the strict parsers reject.
    """
    out: list[str] = ['"']
    for character in text:
        code = ord(character)
        if character == '"':
            out.append('\\"')
        elif character == "\\":
            out.append("\\\\")
        elif code < 0x20:
            out.append(f"\\u{code:04x}")
        else:
            out.append(character)
    out.append('"')
    return "".join(out)


def stats_body(text: str, data: bytes) -> str:
    """The one place the stats reply is formatted, so its key order cannot drift."""
    return (
        '{"text":'
        + quote(text)
        + f',"lines":{counts.lines(data)}'
        + f',"words":{counts.words(data)}'
        + f',"bytes":{counts.size(data)}'
        + "}"
    )


def percent_decode(raw: str) -> bytes | None:
    """`+` is a space, `%XX` is a byte, anything undecodable is `None`."""
    out = bytearray()
    index = 0
    while index < len(raw):
        character = raw[index]
        if character == "+":
            out.append(0x20)
            index += 1
        elif character == "%":
            if index + 2 >= len(raw):
                return None
            high, low = raw[index + 1], raw[index + 2]
            if high not in _HEX or low not in _HEX:
                return None
            out.append(int(high + low, 16))
            index += 3
        elif ord(character) < 0x80:
            out.append(ord(character))
            index += 1
        else:
            return None
    return bytes(out)


def query_text(query: str) -> str | None:
    """First `text=` member wins; a value that will not decode counts as absent."""
    for pair in query.split("&"):
        if not pair:
            continue
        name, _, value = pair.partition("=")
        if name == "text":
            decoded = percent_decode(value)
            return None if decoded is None else decoded.decode("utf-8", "replace")
    return None


def route(method: str, target: str, body: bytes = b"") -> tuple[int, str]:
    """Status and body text for one request. `target` is the raw path plus query."""
    path, _, query = target.partition("?")

    if path == "/health":
        if method != "GET":
            return 405, METHOD_NOT_ALLOWED
        return 200, '{"status":"ok"}'

    if path == "/stats":
        if method == "GET":
            text = query_text(query)
            if text is None:
                return 422, MISSING_TEXT
            return 200, stats_body(text, text.encode("utf-8"))
        if method == "POST":
            outcome, text = read_text_member(body)
            if outcome == "invalid":
                return 422, INVALID_JSON
            if outcome == "missing":
                return 422, MISSING_TEXT
            return 200, stats_body(text, text.encode("utf-8"))
        return 405, METHOD_NOT_ALLOWED

    return 404, '{"error":"not_found","detail":' + quote(f"no route for {method} {target}") + "}"
