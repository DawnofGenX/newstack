"""Items in, heaps out: item lists, seeded generators, snapshots.

An item list is one signed integer per line, the key the heap ranks
by. The generator is deterministic, the file format skips blank lines
and comments, and a snapshot keeps its seed so a frozen list replays
its items exactly, in order, forever.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .keys import KeysError, ensure_key

DEFAULT_SEED = 20261107
MAX_KEY = 2**31 - 1


class CorpusError(ValueError):
    """An item list cannot be read, written, or generated."""

    __slots__ = ()


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[int]:
    """A deterministic list of distinct signed keys, spread wide."""
    if count <= 0:
        raise CorpusError(f"no items from {count}")
    rng = random.Random(seed)
    keys: set[int] = set()
    while len(keys) < count:
        keys.add(rng.randint(-MAX_KEY, MAX_KEY))
    return sorted(keys)


def load_items(path: str) -> list[int]:
    """One key per line; blank lines and # comments skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise CorpusError(f"no such item list: {path}") from error
    keys: list[int] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            keys.append(ensure_key(int(stripped)))
        except (KeysError, ValueError) as error:
            raise CorpusError(f"not an integer: {stripped!r}") from error
    return keys


def write_items(keys: list[int], path: str) -> None:
    """Write the keys one per line, the way load_items reads them back."""
    try:
        Path(path).write_text(
            "\n".join(str(key) for key in keys) + "\n", encoding="utf-8"
        )
    except OSError as error:
        raise CorpusError(f"cannot write item list: {path}") from error


@dataclass(frozen=True)
class Snapshot:
    """A frozen item list and the seed that grew it."""

    keys: tuple[int, ...]
    seed: int

    def dumps(self) -> str:
        return json.dumps({"keys": list(self.keys), "seed": self.seed})

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        try:
            raw = json.loads(text)
            keys = tuple(ensure_key(key) for key in raw["keys"])
        except (json.JSONDecodeError, KeyError, TypeError, KeysError) as error:
            raise CorpusError("half a snapshot is no snapshot") from error
        return cls(keys, int(raw["seed"]))
