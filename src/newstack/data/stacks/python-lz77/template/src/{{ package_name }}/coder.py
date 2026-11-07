"""The sliding-window coder: compress and decompress, exact inverses.

compress(text) answers with a token stream: a Literal writes one
letter, a BackRef quotes `length` letters sitting `offset` places
behind the emitted end — never further than MAX_WINDOW, never
longer than MAX_MATCH, never into letters the window never saw.
decompress replays each quote letter by letter, so a quote may
ride its own tail: the letters it replays are the letters the
window just emitted. The rule is the contract: the sliding window
never quotes a letter it has never emitted. The product is the
loop: decompress(compress(t)) is t on every shipped and seeded
corpus, and every quote names letters the reconstruction actually
holds at that distance.
"""

from __future__ import annotations

from .text import ensure_text
from .tokens import (
    MAX_MATCH,
    MAX_WINDOW,
    BackRef,
    Literal,
    Token,
)

MIN_MATCH = 2


class CoderError(ValueError):
    """A token stream broke on the way in or the way out."""

    __slots__ = ()


def _match_length(source: str, pos: int, offset: int) -> int:
    """How many letters at pos echo the window behind, tail ridden.

    The comparison walks the source: with a short offset the echo
    runs past pos into letters not yet written, and that is legal,
    because the reader replays the quote letter by letter against
    letters it emitted one step earlier.
    """
    length = 0
    while length < MAX_MATCH and pos + length < len(source):
        if source[pos + length] != source[pos - offset + length]:
            break
        length += 1
    return length


def compress(text: str) -> list[Token]:
    """The greedy stream: longest honest quote first, letters alone."""
    source = ensure_text(text)
    tokens: list[Token] = []
    pos = 0
    while pos < len(source):
        best_offset = 0
        best_length = 0
        for offset in range(1, min(pos, MAX_WINDOW) + 1):
            length = _match_length(source, pos, offset)
            if length > best_length:
                best_offset, best_length = offset, length
        if best_length >= MIN_MATCH:
            tokens.append(BackRef(best_offset, best_length))
            pos += best_length
        else:
            tokens.append(Literal(source[pos]))
            pos += 1
    return tokens


def decompress(tokens: list[Token]) -> str:
    """Replay the stream: literals land, quotes replay the window."""
    out: list[str] = []
    for token in tokens:
        if isinstance(token, Literal):
            out.append(token.letter)
        else:
            if not isinstance(token, BackRef):
                raise CoderError(f"{token!r} is no token the coder ships")
            if token.offset > len(out):
                raise CoderError(
                    f"a quote reaches {token.offset} back into {len(out)} emitted"
                )
            for _step in range(token.length):
                out.append(out[len(out) - token.offset])
    return "".join(out)


def audit(tokens: list[Token]) -> list[str]:
    """Walk the stream against its own reconstruction, break by name.

    Returns the named breaks and answers [] when the stream is
    honest: every quote offset inside the window, every quote
    length inside the ceiling, every letter it quotes already
    sitting at that distance in the letters emitted before it.
    """
    breaks: list[str] = []
    emitted: list[str] = []
    for index, token in enumerate(tokens):
        if isinstance(token, Literal):
            if token.letter not in "abcdefghijklmnopqrstuvwxyz":
                breaks.append(f"token {index}: {token.letter!r} is no letter")
            else:
                emitted.append(token.letter)
            continue
        if not isinstance(token, BackRef):
            breaks.append(f"token {index}: {token!r} is no token")
            continue
        if token.offset > MAX_WINDOW:
            breaks.append(f"token {index}: offset {token.offset} beyond the window")
        if token.length > MAX_MATCH:
            breaks.append(f"token {index}: length {token.length} beyond the ceiling")
        if token.offset > len(emitted):
            breaks.append(
                f"token {index}: quotes {token.offset} back into {len(emitted)}"
            )
            continue
        for _step in range(token.length):
            quoted = emitted[len(emitted) - token.offset]
            if quoted not in "abcdefghijklmnopqrstuvwxyz":
                breaks.append(f"token {index}: quotes {quoted!r}, no letter")
            emitted.append(quoted)
    return breaks
