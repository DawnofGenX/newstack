"""The rolling hash: a documented base, a documented modulus, one law.

The hash of a window is the polynomial ``letter * BASE**k`` sum
reduced modulo ``MODULUS``, letters valued 1..26 (never zero, so
``ab`` and ``b`` never share a hash by accident of leading zeros).
The window update — subtract the outgoing letter's weighted term,
multiply the remainder by ``BASE``, add the incoming letter, reduce
— is the product's heart, and it answers to one law: on every
window the update equals recomputing the hash from scratch. That
equality is checked, never assumed, on every shipped corpus.
"""

from __future__ import annotations

BASE = 911  # odd, far from 26; keeps the polynomial injective in practice
MODULUS = 1_000_000_007  # prime, comfortably above BASE * MAX_PATTERN
EMPTY_HASH = 0


class HashError(ValueError):
    """The hash was handed a window it cannot weigh."""


def letter_value(letter: str) -> int:
    """The letter's weight: 1..26, never zero."""
    if len(letter) != 1 or not "a" <= letter <= "z":
        raise HashError(f"no weight for {letter!r}")
    return ord(letter) - 96


def window_hash(window: str) -> int:
    """The polynomial hash of the window, computed from scratch.

    This is the oracle the update answer is graded against: it never
    rolls, it never trusts, it walks the window letter by letter.
    The empty window hashes to ``EMPTY_HASH``.
    """
    digest = 0
    for letter in window:
        digest = (digest * BASE + letter_value(letter)) % MODULUS
    return digest


def leading_power(width: int) -> int:
    """BASE**(width - 1) mod MODULUS: the outgoing letter's weight.

    Width zero owns no power; width one owns ``1``.
    """
    if width < 0:
        raise HashError(f"no power for width {width}")
    if width == 0:
        return 0
    return pow(BASE, width - 1, MODULUS)


def roll(digest: int, outgoing: str, incoming: str, width: int) -> int:
    """Slide a width-wide window one letter right, one multiply spared.

    ``digest`` is the hash of the window that starts one letter
    left of ``outgoing``; the result must equal ``window_hash`` of
    the window that ends one letter right of ``incoming``. The
    outgoing letter's full weighted term leaves, the remainder
    shifts up, the incoming letter joins, one reduction closes it.
    """
    if width <= 0:
        raise HashError(f"no roll for width {width}")
    left = (digest - letter_value(outgoing) * leading_power(width)) % MODULUS
    return (left * BASE + letter_value(incoming)) % MODULUS


def windows(text: str, width: int) -> list[str]:
    """Every width-wide window of the text, left to right.

    A helper for the checks: the law speaks about these strings,
    so they are made here without cleverness.
    """
    if width <= 0:
        raise HashError(f"no windows for width {width}")
    if width > len(text):
        return []
    return [text[start : start + width] for start in range(len(text) - width + 1)]
