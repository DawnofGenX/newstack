"""The command table: names, arities, and replies.

Everything returns already-encoded RESP bytes, so the server only has to write
them; nothing here touches a socket.
"""

from __future__ import annotations

import re

from . import protocol
from .protocol import encode_bulk, encode_error, encode_integer, encode_simple
from .store import NotAnInteger, Store

WRONG_ARITY = "ERR wrong number of arguments for '%s' command"
SYNTAX = "ERR syntax error"

# name -> (minimum argument count, maximum argument count or None). The count
# includes the command name itself, exactly like Redis' own command table.
ARITY: dict[bytes, tuple[int, int | None]] = {
    b"ping": (1, 2),
    b"echo": (2, 2),
    b"set": (3, 5),
    b"get": (2, 2),
    b"del": (2, None),
    b"exists": (2, None),
    b"incr": (2, 2),
    b"decr": (2, 2),
    b"dbsize": (1, 1),
    b"flushdb": (1, 1),
    b"type": (2, 2),
    b"ttl": (2, 2),
    b"keys": (2, 2),
    b"command": (1, None),
}


def _parse_expiry(args: list[bytes]) -> float | None:
    """`SET key value [EX seconds]`: anything else is a syntax error."""
    if len(args) == 3:
        return None
    if len(args) != 5:
        raise ValueError(SYNTAX)
    option = args[3].upper()
    if option != b"EX":
        raise ValueError(SYNTAX)
    try:
        seconds = int(args[4])
    except ValueError as exc:
        raise ValueError("ERR value is not an integer or out of range") from exc
    if seconds <= 0:
        raise ValueError("ERR invalid expire time in 'set' command")
    return float(seconds)


def execute(store: Store, args: list[bytes]) -> bytes:
    """Run one command and return the reply bytes."""
    name = args[0].lower()
    rule = ARITY.get(name)
    if rule is None:
        text = args[0].decode("utf-8", "replace")
        return encode_error(f"ERR unknown command '{text}'")
    low, high = rule
    if len(args) < low or (high is not None and len(args) > high):
        return encode_error(WRONG_ARITY % name.decode("ascii"))

    if name == b"ping":
        if len(args) == 2:
            return encode_bulk(args[1])
        return encode_simple("PONG")
    if name == b"echo":
        return encode_bulk(args[1])
    if name == b"set":
        try:
            ttl = _parse_expiry(args)
        except ValueError as exc:
            return encode_error(str(exc))
        store.set(args[1], args[2], ttl)
        return encode_simple("OK")
    if name == b"get":
        value = store.get(args[1])
        return protocol.NIL_BULK if value is None else encode_bulk(value)
    if name == b"del":
        return encode_integer(store.delete(args[1:]))
    if name == b"exists":
        return encode_integer(store.exists(args[1:]))
    if name in (b"incr", b"decr"):
        delta = 1 if name == b"incr" else -1
        try:
            return encode_integer(store.incr(args[1], delta))
        except NotAnInteger:
            return encode_error("ERR value is not an integer or out of range")
        except OverflowError:
            return encode_error("ERR increment or decrement would overflow")
    if name == b"dbsize":
        return encode_integer(store.dbsize())
    if name == b"flushdb":
        store.flush()
        return encode_simple("OK")
    if name == b"type":
        return encode_simple(store.type_of(args[1]))
    if name == b"ttl":
        return encode_integer(store.ttl(args[1]))
    if name == b"keys":
        pattern = args[1]
        names = store.keys()
        if pattern == b"*":
            return protocol.encode_array([encode_bulk(key) for key in names])
        return protocol.encode_array(
            [encode_bulk(key) for key in names if _glob(pattern, key)]
        )
    if name == b"command":
        # redis-cli asks for the command table when it starts; an empty array
        # keeps it from complaining without pretending to implement it.
        return protocol.EMPTY_ARRAY
    return encode_error(f"ERR unknown command '{name.decode('ascii', 'replace')}'")


def _glob(pattern: bytes, key: bytes) -> bool:
    """Byte-wise `*` / `?` matching, which is all KEYS promises."""
    expression = bytearray()
    for byte in pattern:
        char = bytes([byte])
        if char == b"*":
            expression.extend(b".*")
        elif char == b"?":
            expression.extend(b".")
        else:
            expression.extend(re.escape(char))
    return re.fullmatch(bytes(expression), key) is not None
