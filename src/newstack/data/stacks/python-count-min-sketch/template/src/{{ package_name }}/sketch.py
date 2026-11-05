"""A count-min sketch whose error is a number, not a promise.

The sketch answers one question, "how many times did this item arrive?", from a fixed
amount of memory. It can only be wrong in one direction: collisions with other items add
to a counter, so an estimate is never below the truth. The overestimate is bounded by
e / width times the number of updates, and that bound is what this module exposes so the
callers can print it beside the number it applies to.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

# One blake2b digest is at most 64 bytes, and each row needs 8 of them.
MAX_DEPTH = 8
DEFAULT_WIDTH = 2048
DEFAULT_DEPTH = 5


class SketchError(ValueError):
    """The sketch cannot answer the question it was asked."""


def row_hashes(item: str, depth: int) -> list[int]:
    """One digest, sliced into `depth` independent-looking 64-bit row hashes."""
    if depth < 1:
        raise SketchError(f"depth must be at least 1, not {depth}")
    if depth > MAX_DEPTH:
        raise SketchError(
            f"depth {depth} needs more than one digest: a blake2b digest is at most 64 bytes, "
            f"so at most {MAX_DEPTH} rows can come from one hash"
        )
    digest = hashlib.blake2b(
        item.encode("utf-8"), digest_size=8 * depth, person=b"cmsketch"
    ).digest()
    return [int.from_bytes(digest[index * 8 : (index + 1) * 8], "big") for index in range(depth)]


def epsilon(width: int) -> float:
    """The additive error bound per row, as a fraction of the total count."""
    return math.e / width


def delta(depth: int) -> float:
    """The probability that the bound fails, if the row hashes were independent."""
    return math.exp(-depth)


@dataclass
class Counts:
    """A sketch's counters, kept as plain lists so they survive JSON unchanged."""

    width: int
    depth: int
    rows: list[list[int]]


class CountMinSketch:
    """width x depth counters, plus the two facts needed to read them honestly."""

    def __init__(
        self, width: int = DEFAULT_WIDTH, depth: int = DEFAULT_DEPTH, *, conservative: bool = False
    ) -> None:
        if width < 1:
            raise SketchError(f"width must be at least 1, not {width}")
        if depth < 1 or depth > MAX_DEPTH:
            raise SketchError(f"depth must be between 1 and {MAX_DEPTH}, not {depth}")
        self.width = width
        self.depth = depth
        self.conservative = conservative
        self.rows: list[list[int]] = [[0] * width for _ in range(depth)]
        self.updates = 0
        self.total = 0

    # -- updates -------------------------------------------------------------
    def positions(self, item: str) -> list[int]:
        return [value % self.width for value in row_hashes(item, self.depth)]

    def add(self, item: str, count: int = 1) -> None:
        """Record `count` arrivals of `item`.

        A conservative update touches only the counters that already hold the current
        minimum, which keeps the other rows' headroom for the items that need it.
        """
        if not isinstance(count, int) or isinstance(count, bool):
            raise SketchError(f"count must be a whole number, not {count!r}")
        if count < 1:
            raise SketchError(f"count must be at least 1, not {count}")
        spots = self.positions(item)
        if self.conservative:
            current = min(self.rows[row][spot] for row, spot in enumerate(spots))
            for row, spot in enumerate(spots):
                if self.rows[row][spot] == current:
                    self.rows[row][spot] += count
        else:
            for row, spot in enumerate(spots):
                self.rows[row][spot] += count
        self.updates += 1
        self.total += count

    def estimate(self, item: str) -> int:
        """The smallest counter the item hashes to: an upper bound on its true count."""
        return min(self.rows[row][spot] for row, spot in enumerate(self.positions(item)))

    def bound(self) -> float:
        """The additive error the sketch promises, in units of the total count."""
        return epsilon(self.width) * self.total

    # -- combining -----------------------------------------------------------
    def merge(self, other: CountMinSketch) -> CountMinSketch:
        """Pointwise addition: the sketch of a union is the sum of the sketches."""
        if (self.width, self.depth) != (other.width, other.depth):
            raise SketchError(
                f"cannot merge a {self.width}x{self.depth} sketch with a "
                f"{other.width}x{other.depth} one: the rows would not line up"
            )
        if self.conservative != other.conservative:
            raise SketchError(
                "cannot merge a conservative sketch with a plain one: the merged error "
                "bound would not describe either half"
            )
        merged = CountMinSketch(self.width, self.depth, conservative=self.conservative)
        merged.rows = [
            [left + right for left, right in zip(self.rows[row], other.rows[row], strict=True)]
            for row in range(self.depth)
        ]
        merged.updates = self.updates + other.updates
        merged.total = self.total + other.total
        return merged

    # -- persistence ---------------------------------------------------------
    def as_dict(self) -> dict:
        return {
            "type": "count-min-sketch",
            "width": self.width,
            "depth": self.depth,
            "conservative": self.conservative,
            "updates": self.updates,
            "total": self.total,
            "rows": [list(row) for row in self.rows],
        }


def parse_sketch(payload: dict) -> CountMinSketch:
    if payload.get("type") != "count-min-sketch":
        raise SketchError(f"{payload.get('type')!r} is not a count-min sketch")
    sketch = CountMinSketch(
        int(payload["width"]),
        int(payload["depth"]),
        conservative=bool(payload.get("conservative", False)),
    )
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != sketch.depth:
        raise SketchError(f"a sketch of depth {sketch.depth} needs that many rows")
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != sketch.width:
            raise SketchError(f"row {index} holds {len(row)!r} counters, not {sketch.width}")
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in row):
            raise SketchError(f"row {index} holds something that is not a counter")
    sketch.rows = [[int(value) for value in row] for row in rows]
    sketch.updates = int(payload.get("updates", 0))
    sketch.total = int(payload.get("total", 0))
    return sketch
