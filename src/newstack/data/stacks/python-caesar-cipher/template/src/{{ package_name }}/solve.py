"""Caesar cipher: shift letters, recover them, try every key.

The rule this cipher keeps, and the marker the detector looks for:
each letter is shifted by the same amount, non-letters stay put,
and a round-trip recovers the original text exactly. Brute force
tries all twenty-six shifts. Mutate the modulus and the alphabet
wraps on the wrong boundary.

Detect phrase: each letter is shifted by the same amount, round-trips recover the text.
"""
from __future__ import annotations

MAX_LENGTH = 100
ALPHABET = 26


class CipherError(ValueError):
    """An input the cipher refuses."""

    __slots__ = ()


def _validate(text, shift=None) -> str:
    if not isinstance(text, str):
        raise CipherError("text must be a string")
    if len(text) > MAX_LENGTH:
        raise CipherError(f"text exceeds the ceiling {MAX_LENGTH}")
    if shift is not None and (isinstance(shift, bool) or not isinstance(shift, int)):
        raise CipherError("shift must be an integer")
    return text


def _shift_char(ch: str, shift: int) -> str:
    if "a" <= ch <= "z":
        base = ord("a")
    elif "A" <= ch <= "Z":
        base = ord("A")
    else:
        return ch
    return chr((ord(ch) - base + shift) % ALPHABET + base)


def encode(text: str, shift: int) -> str:
    text = _validate(text, shift)
    return "".join(_shift_char(ch, shift) for ch in text)


def decode(text: str, shift: int) -> str:
    text = _validate(text, shift)
    return "".join(_shift_char(ch, -shift) for ch in text)


def brute_force(text: str) -> list:
    text = _validate(text)
    return [(s, decode(text, s)) for s in range(ALPHABET)]


def audit(text: str, shift: int) -> list:
    text = _validate(text, shift)
    if decode(encode(text, shift), shift) != text:
        return ["round-trip failed"]
    return []


__all__ = [
    "ALPHABET",
    "MAX_LENGTH",
    "CipherError",
    "audit",
    "brute_force",
    "decode",
    "encode",
]
