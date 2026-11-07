"""Keys in, trees out: key lists, seeded generators, snapshots.

A key list is one signed integer per line. The generator is
deterministic, the file format skips blank lines and comments, and a
snapshot keeps its seed so a frozen list replays its keys exactly,
in order, forever.
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
    """A key list cannot be read, written, or generated."""

    __slots__ = ()


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[int]:
    """A deterministic list of distinct signed keys, spread wide."""
    if count <= 0:
        raise CorpusError(f"no keys from {count}")
    rng = random.Random(seed)
    keys: set[int] = set()
    while len(keys) < count:
        keys.add(rng.randint(-MAX_KEY, MAX_KEY))
    return sorted(keys)


def load_keys(path: str) -> list[int]:
    """One key per line; blank lines and # comments skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise CorpusError(f"no such key list: {path}") from error
    keys: list[int] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            keys.append(ensure_key(int(stripped)))
        except (KeysError, ValueError) as failure:
            raise CorpusError(f"the key list holds {stripped!r}, not an integer") from failure
    if not keys:
        raise CorpusError(f"the key list {path} holds no keys")
    return keys


def write_keys(keys: list[int], path: str) -> None:
    """Write the list, one gate-blessed key per line."""
    Path(path).write_text(
        "".join(f"{ensure_key(key)}\n" for key in keys), encoding="utf-8"
    )


@dataclass(frozen=True)
class Snapshot:
    """A key list and the seed that made it, replayable as text."""

    keys: tuple[int, ...]
    seed: int

    def dumps(self) -> str:
        return json.dumps({"keys": list(self.keys), "seed": self.seed})

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        try:
            payload = json.loads(text)
            keys = tuple(ensure_key(int(key)) for key in payload["keys"])
            seed = int(payload["seed"])
        except (KeyError, TypeError, ValueError, KeysError, json.JSONDecodeError) as err:
            raise CorpusError(f"half a snapshot: {err}") from err
        return cls(keys, seed)
