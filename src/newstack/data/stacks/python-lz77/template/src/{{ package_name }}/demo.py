"""Six stories about windows, quotes, and what a loop owes a text.

Every number printed here is computed at run time by the real
modules; a story that stops holding fails the selftest, not the
reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .coder import audit, compress, decompress
from .corpus import synthetic
from .naive import naive_read, naive_size
from .tokens import (
    MAX_MATCH,
    MAX_WINDOW,
    BackRef,
    Literal,
    tokens_to_letters,
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

    tokens = compress(text)
    first = Story(
        "the loop closes: the read hands back the letters it was sent",
        f"letters={len(text)} tokens={len(tokens)} "
        f"equal={decompress(tokens) == text}",
        decompress(tokens) == text,
    )

    quote = BackRef(4, 4)
    stream: list = [Literal("a"), Literal("b"), Literal("r"), Literal("a"),
                    quote]
    audited = audit(stream) == []
    second = Story(
        "every quote names letters the window already emitted",
        f"offset={quote.offset} length={quote.length} audit-clean={audited} "
        f"text={tokens_to_letters(stream)!r}",
        audited and tokens_to_letters(stream) == "abraabra",
    )

    probe = "abracadabra" * 4
    paid = compress(probe)
    third = Story(
        "a repeat pays in tokens, never in letters",
        f"letters={len(probe)} tokens={len(paid)} "
        f"naive={naive_size(probe)} cheaper={len(paid) < len(probe)}",
        len(paid) < len(probe) and len(paid) <= naive_size(probe),
    )

    tangle = "a" * 32
    tail = compress(tangle)
    fourth = Story(
        "a quote may ride its own tail",
        f"letters={len(tangle)} tokens={len(tail)} "
        f"back={decompress(tail) == tangle}",
        decompress(tail) == tangle and len(tail) < 10,
    )

    empty = compress("")
    fifth = Story(
        "the empty text stream is the empty stream",
        f"tokens={len(empty)} back={decompress(empty)!r}",
        decompress(empty) == "" and empty == [] and naive_read([]) == "",
    )

    checked = all(decompress(compress(one)) == one for one in corpus)
    honest = all(audit(compress(one)) == [] for one in corpus)
    sixth = Story(
        "a seeded corpus survives the loop, text after text",
        f"{len(corpus)} texts loop={checked} audit={honest} "
        f"window={MAX_WINDOW} ceiling={MAX_MATCH}",
        checked and honest,
    )
    return [first, second, third, fourth, fifth, sixth]
