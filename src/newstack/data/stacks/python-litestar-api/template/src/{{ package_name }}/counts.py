"""`wc` semantics, computed over the bytes that arrived.

The numbers are defined on bytes, not on a decoded string: a two-byte character
counts once as a character and twice as bytes, and a carriage return is neither
whitespace nor a word boundary unless a newline follows it. Doing this on `str`
gives the answer for most ASCII input and the wrong one for everything else.
"""

from __future__ import annotations

#: byte values `wc` treats as word separators
SEPARATORS = frozenset(b" \t\n\r\x0b\x0c")


def lines(data: bytes) -> int:
    """Newline-terminated lines; a trailing fragment without a newline still counts."""
    if not data:
        return 0
    count = data.count(b"\n")
    return count if data.endswith(b"\n") else count + 1


def words(data: bytes) -> int:
    """Runs of non-separator bytes."""
    total = 0
    inside = False
    for byte in data:
        if byte in SEPARATORS:
            inside = False
        elif not inside:
            inside = True
            total += 1
    return total


def size(data: bytes) -> int:
    """Bytes, which is what the client sent and what `wc -c` reports."""
    return len(data)
