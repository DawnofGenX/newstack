"""Which values an array hands to a tree, and how they render.

A ladder folds whole numbers as they stand, so anything that is not an
integer is refused at the door rather than quietly folded later.
"""

from __future__ import annotations

import random
from pathlib import Path

DEFAULT_SEED = 7


class ArrayValueError(ValueError):
    """The value cannot stand in a window."""


def ensure_value(value: object) -> int:
    """Return the whole number the caller meant, or refuse the stand-in."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ArrayValueError(f"a window folds whole numbers, got {value!r}")
    return value


def describe(value: object) -> str:
    """Render a value the way the ladder would name it."""
    return str(value)


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[int]:
    """A seeded array of whole numbers -- the shape the ladder is tested on."""
    if not isinstance(count, int) or count < 1:
        raise ArrayValueError("an array needs at least one value")
    if not isinstance(seed, int):
        raise ArrayValueError("the generator needs a whole-number seed")
    rng = random.Random(seed)
    return [rng.randrange(-500, 500) for _ in range(count)]


def load_values(path: str) -> list[int]:
    """Read one whole number per line; blanks and # comments are skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise ArrayValueError(f"cannot read {path} ({error.strerror})") from error
    values: list[int] = []
    for number, line in enumerate(text.splitlines(), start=1):
        words = line.split()
        if not words or words[0].startswith("#"):
            continue
        if len(words) != 1:
            raise ArrayValueError(f"{path}:{number} wants exactly one value")
        try:
            values.append(int(words[0]))
        except ValueError as error:
            raise ArrayValueError(
                f"{path}:{number} holds a non-integer ({error})"
            ) from error
    if not values:
        raise ArrayValueError(f"{path} holds no values")
    return values


def write_values(values: list[int], path: str) -> None:
    """Write an array back out in the format load_values reads."""
    body = "\n".join(str(value) for value in values)
    Path(path).write_text(body + "\n", encoding="utf-8")
