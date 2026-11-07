"""Key streams in, snapshots out: the corpora the forest is tested on.

A stream is a list of ``(key, value)`` pairs of whole numbers --
negatives allowed, a forest orders by comparison, not by bits. The
generator hands out the shapes a meldable heap must survive: mixed
pushes, pop-mins, and melds folded between them.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SEED = 7


class StreamError(ValueError):
    """The stream cannot be read, written, or replayed."""


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[tuple[int, object]]:
    """A shuffled corpus of distinct keys -- the mixed shape."""
    if not isinstance(count, int) or count < 1:
        raise StreamError("a corpus needs at least one key")
    if not isinstance(seed, int):
        raise StreamError("the generator needs a whole-number seed")
    rng = random.Random(seed)
    keys = rng.sample(range(-2048, 4096), count)
    return [(key, index) for index, key in enumerate(keys)]


def monotone(count: int, seed: int = DEFAULT_SEED) -> list[tuple[int, object]]:
    """A stream of distinct ascending keys -- the forward-only shape."""
    if not isinstance(count, int) or count < 1:
        raise StreamError("a stream needs at least one key")
    if not isinstance(seed, int):
        raise StreamError("the generator needs a whole-number seed")
    rng = random.Random(seed)
    keys = sorted(rng.sample(range(0, 4096), count))
    return [(key, index) for index, key in enumerate(keys)]


@dataclass(frozen=True)
class Snapshot:
    """A corpus and the seed that grew it, frozen as one record."""

    pairs: list[tuple[int, object]]
    seed: int

    def dumps(self) -> str:
        return json.dumps({"pairs": self.pairs, "seed": self.seed})

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        try:
            record = json.loads(text)
            pairs = [(int(key), value) for key, value in record["pairs"]]
            seed = int(record["seed"])
        except (KeyError, TypeError, ValueError) as error:
            raise StreamError(f"half a snapshot is no snapshot ({error})") from error
        return cls(pairs, seed)


def load_keys(path: str) -> list[tuple[int, object]]:
    """Read ``key value`` lines; blanks and # comments are skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise StreamError(f"cannot read {path} ({error.strerror})") from error
    pairs: list[tuple[int, object]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        words = line.split()
        if not words or words[0].startswith("#"):
            continue
        if len(words) != 2:
            raise StreamError(f"{path}:{number} wants a key and a value")
        try:
            pairs.append((int(words[0]), int(words[1])))
        except ValueError as error:
            raise StreamError(f"{path}:{number} holds a non-integer ({error})") from error
    if not pairs:
        raise StreamError(f"{path} holds no keys")
    return pairs


def write_keys(pairs: list[tuple[int, object]], path: str) -> None:
    """Write a stream back out in the format load_keys reads."""
    body = "\n".join(f"{key} {value}" for key, value in pairs)
    Path(path).write_text(body + "\n", encoding="utf-8")
