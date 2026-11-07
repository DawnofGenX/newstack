"""The coder: letters in, bits out, and the walk back.

encode(text) tallies, deals the canonical table, and spends each
letter's word: the product is the loop — decode(encode(t), table)
is t on every shipped and seeded corpus. decode walks the bit
string against the table alone; a decoder never asks for the
tree. The tree walk and the table agree letter for letter, and
the audit proves no shipped code prefixes another.
"""

from __future__ import annotations

from .freq import tally
from .table import (
    CodeTable,
    TableError,
    audit,
    code_table,
)
from .text import ensure_text


class CoderError(ValueError):
    """A bit string or a table broke on the way in or the way out."""

    __slots__ = ()


def encode(text: str, table: CodeTable | None = None) -> str:
    """Spend each letter its word: the text as a run of bits."""
    source = ensure_text(text)
    if not source:
        return ""
    book = table if table is not None else code_table(tally(source))
    try:
        return "".join(book.bits_for(letter) for letter in source)
    except TableError as missing:
        raise CoderError(f"the table is missing a letter: {missing}") from missing


def decode(bits: str, table: CodeTable) -> str:
    """Walk the bits against the table alone, word by word."""
    if set(bits) - set("01"):
        raise CoderError("a bit string runs in 0 and 1 only")
    letters: list[str] = []
    current = ""
    for bit in bits:
        current += bit
        word = table.words.get(current)
        if word is not None:
            letters.append(word)
            current = ""
    if current:
        raise CoderError(f"{current!r} is the start of no word: a clipped stream")
    return "".join(letters)


def size_report(text: str) -> tuple[int, int, CodeTable]:
    """Letters in, bits spent out, and the table that paid: the ledger."""
    source = ensure_text(text)
    book = code_table(tally(source))
    return len(source), len(encode(source, book)), book


def honest(text: str) -> bool:
    """The loop closed, the table clean: the coder's whole promise."""
    letters, _bits, book = size_report(text)
    if not letters:
        return audit(book) == [] if book.codes else True
    return decode(encode(text, book), book) == text and audit(book) == []
