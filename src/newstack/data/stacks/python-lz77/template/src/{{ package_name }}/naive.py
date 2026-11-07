"""The oracles: a coder with no cleverness at all.

The emit oracle writes every letter as its own literal and never
looks back; the read oracle replays tokens one letter at a time
against the text built so far. Every answer the real coder gives
must unfold back to the letters these oracles were handed, and the
naive token count is the ceiling the clever coder must never
cross. The coder cannot grade its own homework from here.
"""

from __future__ import annotations

from .tokens import (
    BackRef,
    Literal,
    Token,
    TokenError,
    tokens_from_json,
    tokens_to_json,
)


def naive_emit(text: str) -> list[Token]:
    """Every letter its own literal: the answer a coder always owes."""
    return [Literal(ch) for ch in text]


def naive_read(tokens: list[Token]) -> str:
    """Unfold tokens in order against the letters emitted so far."""
    out: list[str] = []
    for token in tokens:
        if isinstance(token, Literal):
            out.append(token.letter)
        else:
            assert isinstance(token, BackRef)
            if token.offset > len(out):
                raise TokenError(f"the quote reaches {token.offset} back into {len(out)}")
            for _step in range(token.length):
                out.append(out[len(out) - token.offset])
    return "".join(out)


def naive_roundtrip(text: str) -> bool:
    """The oracle's own loop: emit all-literal, read it back whole."""
    return naive_read(naive_emit(text)) == text


def naive_size(text: str) -> int:
    """The naive coder's price for a text: one token per letter."""
    return len(text)


def naive_json_roundtrip(tokens: list[Token]) -> list[Token]:
    """Tokens through JSON and back must land as the tokens they were."""
    return tokens_from_json(tokens_to_json(tokens))
