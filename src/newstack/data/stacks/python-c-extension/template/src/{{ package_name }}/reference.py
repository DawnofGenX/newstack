"""The pure-Python counter the extension is checked against.

Two implementations is the whole point: a byte counter is easy to get subtly
wrong (``\\v`` and ``\\f`` are separators, ``\\r`` does not end a line, a word
starts only after a separator), and three fixtures cannot tell you that.
"""

from __future__ import annotations

SEPARATORS = frozenset({0x20, 0x09, 0x0A, 0x0D, 0x0B, 0x0C})


def count_bytes(data: bytes) -> tuple[int, int, int]:
    lines = data.count(b"\n")
    words = 0
    inside_word = False
    for byte in data:
        if byte in SEPARATORS:
            inside_word = False
        elif not inside_word:
            inside_word = True
            words += 1
    return lines, words, len(data)


def count_str(text: str) -> tuple[int, int, int]:
    return count_bytes(text.encode("utf-8"))
