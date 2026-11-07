"""Patterns in, digests out: pattern lists, seeded generators, snapshots.

A pattern list is one lowercase-letter pattern per line. The
generator is deterministic, the file format skips blank lines and
comments, and a snapshot keeps its seed so a frozen list replays
its patterns exactly, in order, forever.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .pattern import PatternError, ensure_pattern

DEFAULT_SEED = 20261107
LETTERS = "abcdefghijklmnopqrstuvwxyz"


class CorpusError(ValueError):
    """A pattern list cannot be read, written, or generated."""

    __slots__ = ()


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[str]:
    """A deterministic list of distinct short patterns, reuse allowed.

    Repeats are kept on purpose: a rolling window only shows its
    temper when letters come back, and the corpus must feed the
    scanner the tangles it exists for.
    """
    if count <= 0:
        raise CorpusError(f"no patterns from {count}")
    rng = random.Random(seed)
    patterns: set[str] = set()
    while len(patterns) < count:
        size = rng.randint(1, 6)
        patterns.add("".join(rng.choice(LETTERS[:5]) for _ in range(size)))
    return sorted(patterns)


def load_patterns(path: str) -> list[str]:
    """One pattern per line; blank lines and # comments skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise CorpusError(f"no such pattern list: {path}") from error
    patterns: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            patterns.append(ensure_pattern(stripped))
        except PatternError as failure:
            raise CorpusError(f"the pattern list holds {stripped!r}, no pattern") from failure
    if not patterns:
        raise CorpusError(f"the pattern list {path} holds no patterns")
    return patterns


def write_patterns(patterns: list[str], path: str) -> None:
    """Write the list, one gate-blessed pattern per line."""
    Path(path).write_text(
        "".join(f"{ensure_pattern(pattern)}\n" for pattern in patterns),
        encoding="utf-8",
    )


@dataclass(frozen=True)
class Snapshot:
    """A pattern list and the seed that made it, replayable as text."""

    patterns: tuple[str, ...]
    seed: int

    def dumps(self) -> str:
        return json.dumps({"patterns": list(self.patterns), "seed": self.seed})

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        try:
            payload = json.loads(text)
            patterns = tuple(ensure_pattern(pattern) for pattern in payload["patterns"])
            seed = int(payload["seed"])
        except (KeyError, TypeError, ValueError, PatternError, json.JSONDecodeError) as err:
            raise CorpusError(f"half a snapshot: {err}") from err
        return cls(patterns, seed)
