"""Values in, buffers out: value lists, seeded generators, snapshots.

A value list is one signed integer per line. The generator is
deterministic, the file format skips blank lines and comments, and a
snapshot keeps its seed so a frozen list replays its values exactly,
in order, forever.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .values import MAX_VALUE, ValuesError, ensure_value

DEFAULT_SEED = 20261107


class CorpusError(ValueError):
    """A value list cannot be read, written, or generated."""

    __slots__ = ()


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[int]:
    """A deterministic list of distinct signed values, spread wide."""
    if count <= 0:
        raise CorpusError(f"no values from {count}")
    rng = random.Random(seed)
    values: set[int] = set()
    while len(values) < count:
        values.add(rng.randint(-MAX_VALUE, MAX_VALUE))
    return sorted(values)


def load_values(path: str) -> list[int]:
    """One value per line; blank lines and # comments skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise CorpusError(f"no such value list: {path}") from error
    values: list[int] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            values.append(ensure_value(int(stripped)))
        except (ValuesError, ValueError) as failure:
            raise CorpusError(
                f"the value list holds {stripped!r}, not an integer"
            ) from failure
    if not values:
        raise CorpusError(f"the value list {path} holds no values")
    return values


def write_values(values: list[int], path: str) -> None:
    """Write the list, one gate-blessed value per line."""
    Path(path).write_text(
        "".join(f"{ensure_value(value)}\n" for value in values), encoding="utf-8"
    )


@dataclass(frozen=True)
class Snapshot:
    """A value list and the seed that made it, replayable as text."""

    values: tuple[int, ...]
    seed: int

    def dumps(self) -> str:
        return json.dumps({"values": list(self.values), "seed": self.seed})

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        try:
            payload = json.loads(text)
            values = tuple(ensure_value(int(value)) for value in payload["values"])
            seed = int(payload["seed"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as failure:
            raise CorpusError("half a snapshot is no snapshot") from failure
        return cls(values, seed)
