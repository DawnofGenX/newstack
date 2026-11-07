"""Corpora in, corpora out: point lists, seeded generators, snapshots.

A corpus is a point list the gate has already blessed. The generator is
deterministic, the file format is one ``x,y`` pair per line with
comments and blank lines skipped, and a snapshot keeps its seed so a
frozen corpus replays its points exactly.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .points import PointError, ensure_point

DEFAULT_SEED = 20261107
DEFAULT_SPAN = 500


class CorpusError(ValueError):
    """A corpus cannot be read, written, or generated."""

    __slots__ = ()


def synthetic(count: int, seed: int = DEFAULT_SEED,
              span: int = DEFAULT_SPAN) -> list[tuple[int, int]]:
    """A deterministic corpus of distinct integer points."""
    if count <= 0:
        raise CorpusError(f"no corpus of {count} points")
    if span <= 0 or span * span < count:
        raise CorpusError(f"no {count} distinct points in a {span} span")
    rng = random.Random(seed)
    points: set[tuple[int, int]] = set()
    while len(points) < count:
        points.add((rng.randint(-span, span), rng.randint(-span, span)))
    return sorted(points)


def parse_point(text: str) -> tuple[int, int]:
    """``x,y`` becomes a pair; anything else is refused by name."""
    parts = text.split(",")
    if len(parts) != 2:
        raise CorpusError(f"not a point: {text!r} is not x,y")
    try:
        pair = (int(parts[0]), int(parts[1]))
    except ValueError as error:
        raise CorpusError(f"not a point: {text!r} holds {error}") from error
    try:
        return ensure_point(pair)
    except PointError as error:
        raise CorpusError(f"the point list holds {error}") from error


def load_points(path: str) -> list[tuple[int, int]]:
    """One ``x,y`` per line; blank lines and # comments skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise CorpusError(f"no such point list: {path}") from error
    points: list[tuple[int, int]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        points.append(parse_point(stripped))
    if not points:
        raise CorpusError(f"the point list {path} holds no points")
    return points


def write_points(points: list[tuple[int, int]], path: str) -> None:
    """Write the corpus, one gate-blessed pair per line."""
    Path(path).write_text(
        "".join(f"{ensure_point(point)[0]},{ensure_point(point)[1]}\n"
                for point in points),
        encoding="utf-8",
    )


@dataclass(frozen=True)
class Snapshot:
    """A corpus and the seed that made it, replayable as text."""

    points: tuple[tuple[int, int], ...]
    seed: int

    def dumps(self) -> str:
        return json.dumps(
            {"points": [list(point) for point in self.points], "seed": self.seed}
        )

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        try:
            payload = json.loads(text)
            points = tuple(ensure_point(tuple(point))
                           for point in payload["points"])
            seed = int(payload["seed"])
        except (KeyError, TypeError, ValueError,
                PointError, json.JSONDecodeError) as error:
            raise CorpusError(f"half a snapshot: {error}") from error
        return cls(points, seed)
