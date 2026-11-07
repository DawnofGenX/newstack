"""Six stories about weights, words, and what a loop owes a text.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .coder import decode, encode
from .corpus import synthetic
from .freq import tally
from .table import audit, code_table
from .tree import (
    build_tree,
    height,
    walk_table_agreement,
)


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the coder makes, each computed fresh."""
    corpus = synthetic(48, seed=9)
    text = "abracadabrabananabracadabra"

    book = code_table(tally(text))
    bits = encode(text, book)
    first = Story(
        "the loop closes: the bits decode to the letters they were sent",
        f"letters={len(text)} bits={len(bits)} equal={decode(bits, book) == text}",
        decode(bits, book) == text,
    )

    breaks = audit(book)
    second = Story(
        "no shipped code is a prefix of another",
        f"words={len(book.codes)} breaks={len(breaks)}",
        not breaks,
    )

    skewed = "aaaaaaaaaabbbbcc"
    paid = code_table(tally(skewed))
    spent = len(encode(skewed, paid))
    third = Story(
        "a skewed text pays strictly under eight bits a letter",
        f"letters={len(skewed)} bits={spent} ceiling={len(skewed) * 8} "
        f"under={spent < len(skewed) * 8}",
        spent < len(skewed) * 8,
    )

    ladder = build_tree(tally(text))
    agree = walk_table_agreement(ladder, book)
    fourth = Story(
        "the tree walk and the table agree, letter for letter",
        f"words={len(book.codes)} agree={agree} heights={height(ladder)}",
        agree,
    )

    twin = code_table(tally(text))
    fifth = Story(
        "the same weights always build the same table",
        f"words={len(book.codes)} identical={twin.codes == book.codes}",
        twin.codes == book.codes,
    )

    checked = all(decode(encode(one), code_table(tally(one))) == one for one in corpus)
    honest = all(audit(code_table(tally(one))) == [] for one in corpus)
    sixth = Story(
        "a seeded corpus survives the loop, text after text",
        f"{len(corpus)} texts loop={checked} audit={honest}",
        checked and honest,
    )
    return [first, second, third, fourth, fifth, sixth]
