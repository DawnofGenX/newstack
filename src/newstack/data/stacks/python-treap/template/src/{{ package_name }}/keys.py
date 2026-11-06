"""The keys this tree accepts, and the one truth about their order.

The tree is total over numbers and strings: every key has a place on
the ordered line, and two equal keys are the same node. Order is the
search half of the promise everything else leans on, so it is decided
here, once, and nowhere else. A key outside numbers or strings is
refused, not guessed at.
"""

from __future__ import annotations

__all__ = ["KeyValueError", "describe", "ensure_key"]


class KeyValueError(ValueError):
    """The value offered cannot live on an ordered line."""


def ensure_key(value: object) -> object:
    """Return the key itself once proven to be orderable here.

    Ints, floats, and strings share one ordered line the way Python
    already orders them (1 and 1.0 land on the same spot). Anything
    else has no honest place in the order, so it is refused.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise KeyValueError(f"{value!r} is neither a number nor a string")
    return value


def describe(key: object) -> str:
    """Render a key the way the command line prints it."""
    if isinstance(key, float) and key.is_integer():
        return str(int(key))
    if isinstance(key, str):
        return key
    return str(key)
