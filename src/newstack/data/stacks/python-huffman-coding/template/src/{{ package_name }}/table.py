"""The canonical table: shortest words to the heaviest letters.

code_table(frequencies) builds the ladder, harvests each letter's
depth, ranks letters by (depth, letter) and deals bit strings in
sequence — so reading the table in letter order is reading it in
word order, and a decoder never asks for the tree. The table is
prefix-free by construction: no code it ships is a prefix of
another, and the audit walks the table against itself to prove
it. A lone letter speaks as "0".
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .freq import Frequency
from .tree import (
    Node,
    TreeError,
    build_tree,
    depths,
)


class TableError(ValueError):
    """A table, or a bit string handed to one, is malformed."""

    __slots__ = ()


@dataclass(frozen=True)
class CodeTable:
    """letter -> bit string, plus the mirror the decoder walks."""

    codes: dict[str, str]
    words: dict[str, str] = field(init=False)

    def __post_init__(self) -> None:
        for letter, bits in self.codes.items():
            if not bits or set(bits) - set("01"):
                raise TableError(f"{letter!r} speaks {bits!r}, which is no bit string")
        object.__setattr__(self, "words", {bits: letter for letter, bits in self.codes.items()})

    def bits_for(self, letter: str) -> str:
        try:
            return self.codes[letter]
        except KeyError as missing:
            raise TableError(f"{letter!r} has no word in this table") from missing

    def letter_for(self, bits: str) -> str:
        try:
            return self.words[bits]
        except KeyError as missing:
            raise TableError(f"{bits!r} is no word in this table") from missing


def audit(table: CodeTable) -> list[str]:
    """Walk the table against itself: no shipped code prefixes another.

    Returns the named breaks and answers [] when the table is
    honest: every code is a bit string, every letter is lowercase,
    and every pair of distinct codes differs before either ends.
    """
    breaks: list[str] = []
    for letter, bits in sorted(table.codes.items()):
        if not bits or set(bits) - set("01"):
            breaks.append(f"{letter!r} speaks {bits!r}, which is no bit string")
    words = sorted(table.codes.items(), key=lambda pair: (pair[1], pair[0]))
    for index, (letter, bits) in enumerate(words):
        for other, word in words[index + 1 :]:
            if word.startswith(bits) or bits.startswith(word):
                shorter, longer = (bits, word) if len(bits) <= len(word) else (word, bits)
                breaks.append(f"{shorter!r} prefixes {longer!r}: {letter}/{other} collide")
    return breaks


def code_table(frequencies: Frequency) -> CodeTable:
    """The canonical deal: ladder depths in, sequential bit strings out."""
    return deal(build_tree(frequencies))


def deal(tree: Node) -> CodeTable:
    """Deal the ladder's depths into canonical bit strings, letter by letter."""
    harvest = depths(tree)
    ranked = sorted(harvest.items(), key=lambda pair: (max(pair[1], 1), pair[0]))
    codes: dict[str, str] = {}
    value = 0
    previous = 0
    for letter, depth in ranked:
        length = max(depth, 1)
        value <<= length - previous
        codes[letter] = format(value, "b").rjust(length, "0")
        value += 1
        previous = length
    return CodeTable(codes)


__all__ = [
    "CodeTable",
    "TableError",
    "TreeError",
    "audit",
    "code_table",
    "deal",
]
