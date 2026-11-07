"""Value corpora in, reports out: the streams the tree is tested on.

A corpus is a list of whole-number values -- the shape a Fenwick tree
is built over. The generator hands out the two shapes every honest
tree must answer: a shuffled corpus whose cells straddle positives and
negatives, and a single rising corpus whose running sum only climbs.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from .values import ValueRejection, ensure_value

DEFAULT_SEED = 7


class StreamError(ValueError):
    """The corpus cannot be read, written, or replayed."""


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[int]:
    """A shuffled corpus of mixed-sign values -- the honest shape."""
    if not isinstance(count, int) or count < 1:
        raise StreamError("a corpus needs at least one value")
    if not isinstance(seed, int):
        raise StreamError("the generator needs a whole-number seed")
    rng = random.Random(seed)
    return [rng.randint(-500, 500) for _ in range(count)]


def rising(count: int, seed: int = DEFAULT_SEED) -> list[int]:
    """A corpus of ascending values -- the running sum only climbs."""
    if not isinstance(count, int) or count < 1:
        raise StreamError("a corpus needs at least one value")
    if not isinstance(seed, int):
        raise StreamError("the generator needs a whole-number seed")
    rng = random.Random(seed)
    return sorted(rng.randint(0, 4096) for _ in range(count))


@dataclass(frozen=True)
class Snapshot:
    """A corpus and the seed that grew it, frozen as one record."""

    values: list[int]
    seed: int

    def dumps(self) -> str:
        import json

        return json.dumps({"values": self.values, "seed": self.seed})

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        import json

        try:
            record = json.loads(text)
            values = [ensure_value(value) for value in record["values"]]
            seed = ensure_value(record["seed"])
        except (KeyError, TypeError, ValueRejection) as error:
            raise StreamError(f"half a snapshot is no snapshot ({error})") from error
        return cls(values, seed)


def load_values(path: str) -> list[int]:
    """Whole-number values, one per line; blanks and # comments skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise StreamError(f"cannot read the value list ({error})") from error
    values: list[int] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            values.append(ensure_value(int(stripped)))
        except (ValueError, ValueRejection) as error:
            raise StreamError(f"a value list holds whole numbers ({error})") from error
    if not values:
        raise StreamError("a value list without values is no list")
    return values


def write_values(values: list[int], path: str) -> None:
    """One value per line, the shape load_values reads back."""
    try:
        Path(path).write_text(
            "".join(f"{value}\n" for value in values), encoding="utf-8"
        )
    except OSError as error:
        raise StreamError(f"cannot write the value list ({error})") from error
