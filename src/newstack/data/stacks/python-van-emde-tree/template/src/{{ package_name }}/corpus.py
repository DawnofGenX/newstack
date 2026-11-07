"""Keys in, trees out: key lists, seeded generators, snapshots.

A key list is one integer of the universe per line. The generator is
deterministic, the file format skips blank lines and comments, and a
snapshot keeps its seed so a frozen list replays its keys exactly,
in order, forever.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .keys import MAX_KEY, KeysError, ensure_key

DEFAULT_SEED = 20261107


class CorpusError(ValueError):
    """A key list cannot be read, written, or generated."""

    __slots__ = ()


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[int]:
    """A deterministic list of distinct seats, spread over the universe."""
    if count <= 0:
        raise CorpusError(f"no keys from {count}")
    if count > MAX_KEY + 1:
        raise CorpusError(f"the universe holds {MAX_KEY + 1} seats, not {count}")
    rng = random.Random(seed)
    return sorted(rng.sample(range(MAX_KEY + 1), count))


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
            raise CorpusError(f"the key list holds {stripped!r}, not a seat") from failure
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
