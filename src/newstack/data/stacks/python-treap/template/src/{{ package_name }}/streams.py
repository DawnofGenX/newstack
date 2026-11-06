"""Load the seeded stream and the shape the draws leave behind.

A tree is a stream of pairs pushed once and read in sorted order, so a
snapshot is small: the entries and the seed. Replaying a snapshot
rebuilds the same tree, which is the property the selftest leans on —
the (key, priority) list is the tree, written down.
"""

from __future__ import annotations

import json
from pathlib import Path

from .draws import DEFAULT_SEED

__all__ = ["Snapshot", "StreamError", "load_keys", "synthetic", "write_keys"]

MAX_PAIRS = 20_000


class StreamError(ValueError):
    """The stream or file cannot become a tree."""


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[tuple[int, int]]:
    """`count` distinct integer pairs, deterministic for one seed."""
    from random import Random

    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise StreamError(f"{count!r} is not a tree size")
    if count > MAX_PAIRS:
        raise StreamError(f"{count} exceeds the {MAX_PAIRS}-pair cap")
    rng = Random(seed)
    keys = rng.sample(range(-count * 4, count * 4), count)
    return [(key, index) for index, key in enumerate(keys)]


def load_keys(path: str | Path) -> list[tuple[int, int]]:
    """Read `key value` lines; blanks and # comments are skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise StreamError(f"cannot read {path}: {error}") from error
    pairs: list[tuple[int, int]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            raise StreamError(f"{path}: {line!r} is not two numbers")
        try:
            pairs.append((int(parts[0]), int(parts[1])))
        except ValueError as error:
            raise StreamError(f"{path}: {line!r} holds a non-integer") from error
    if not pairs:
        raise StreamError(f"{path} holds no pairs")
    return pairs


def write_keys(pairs: list[tuple[int, int]], path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for key, value in pairs:
            handle.write(f"{key} {value}\n")


class Snapshot:
    """One tree frozen to text: replay it and the shape answers again."""

    def __init__(self, pairs: list[tuple[int, int]], seed: int) -> None:
        self.pairs = list(pairs)
        self.seed = seed

    def dumps(self) -> str:
        return json.dumps({"seed": self.seed, "pairs": [[k, v] for k, v in self.pairs]})

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        try:
            data = json.loads(text)
            return cls([(int(k), int(v)) for k, v in data["pairs"]], int(data["seed"]))
        except (KeyError, TypeError, ValueError) as error:
            raise StreamError(f"not a snapshot: {error}") from error
