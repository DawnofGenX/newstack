"""The token stream: literals, back-references, and their JSON face.

A token is one of two things. A Literal carries a single lowercase
letter; a BackRef names an offset and a length and quotes `length`
letters that sit `offset` places behind the end of the stream
emitted so far, riding its own tail when the quote runs past the
window it points at. Every shipped token quotes only letters the
window has already seen, and the JSON face is a flat list so a
stream can cross a shell boundary and come back token for token.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

MAX_WINDOW = 4096
MAX_MATCH = 32


class TokenError(ValueError):
    """A token, or the JSON standing in for one, is not well formed."""

    __slots__ = ()


@dataclass(frozen=True)
class Literal:
    """One letter, emitted as itself."""

    letter: str

    def __post_init__(self) -> None:
        if self.letter not in "abcdefghijklmnopqrstuvwxyz":
            raise TokenError(f"{self.letter!r} is not a lowercase letter")


@dataclass(frozen=True)
class BackRef:
    """`length` letters sitting `offset` behind the emitted end."""

    offset: int
    length: int

    def __post_init__(self) -> None:
        if self.offset < 1:
            raise TokenError(f"an offset starts at one, not {self.offset}")
        if self.length < 2:
            raise TokenError(f"a back-reference quotes at least two, not {self.length}")
        if self.offset > MAX_WINDOW:
            raise TokenError(f"an offset runs to {MAX_WINDOW}, not {self.offset}")
        if self.length > MAX_MATCH:
            raise TokenError(f"a quote runs to {MAX_MATCH}, not {self.length}")


Token = Literal | BackRef


def tokens_to_letters(tokens: list[Token]) -> str:
    """Fold a token stream: literals land, quotes replay the window."""
    out: list[str] = []
    for token in tokens:
        if isinstance(token, Literal):
            out.append(token.letter)
        else:
            if token.offset > len(out):
                raise TokenError(f"the quote reaches {token.offset} back into {len(out)}")
            for _step in range(token.length):
                out.append(out[len(out) - token.offset])
    return "".join(out)


def tokens_to_json(tokens: list[Token]) -> str:
    """The stream as a flat JSON list: ["a", "r"] or ["b", 4, 9]."""
    rows = []
    for token in tokens:
        if isinstance(token, Literal):
            rows.append(["a", token.letter])
        else:
            rows.append(["b", token.offset, token.length])
    return json.dumps(rows)


def tokens_from_json(text: str) -> list[Token]:
    """Read a stream back from its JSON face, token for token."""
    try:
        rows = json.loads(text)
    except json.JSONDecodeError as failure:
        raise TokenError(f"the stream is not JSON: {failure}") from failure
    if not isinstance(rows, list):
        raise TokenError("a token stream is a list of rows")
    tokens: list[Token] = []
    for row in rows:
        if not isinstance(row, list) or not row:
            raise TokenError(f"{row!r} is not a token row")
        if row[0] == "a" and len(row) == 2 and isinstance(row[1], str):
            tokens.append(Literal(row[1]))
        elif row[0] == "b" and len(row) == 3:
            tokens.append(BackRef(row[1], row[2]))
        else:
            raise TokenError(f"{row!r} is neither a literal nor a quote")
    return tokens
