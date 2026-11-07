"""Events in, ledgers out: stream files, seeded generators, snapshots.

A stream file is one ``key n`` pair per line. The generator is
deterministic, the file format skips blank lines and comments, and a
snapshot keeps its seed so a frozen stream replays its events
exactly, in order, forever.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .keys import UNIVERSE, KeysError, ensure_key

DEFAULT_SEED = 20261107


class CorpusError(ValueError):
    """A stream cannot be read, written, or generated."""

    __slots__ = ()


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[tuple[int, int]]:
    """A deterministic event list: keys on the universe, small counts."""
    if count <= 0:
        raise CorpusError(f"no events from {count}")
    rng = random.Random(seed)
    return [(rng.randrange(UNIVERSE), rng.randint(1, 5)) for _ in range(count)]


def load_stream(path: str) -> list[tuple[int, int]]:
    """One ``key n`` per line; blank lines and # comments skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise CorpusError(f"no such stream: {path}") from error
    events: list[tuple[int, int]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) != 2:
            raise CorpusError(f"the stream holds {stripped!r}, not 'key n'")
        try:
            events.append((ensure_key(int(parts[0])), int(parts[1])))
        except (KeysError, ValueError) as failure:
            raise CorpusError(f"the stream holds {stripped!r}, not 'key n'") from failure
        if events[-1][1] <= 0:
            raise CorpusError(f"the stream counts {parts[1]}, not a positive int")
    if not events:
        raise CorpusError(f"the stream {path} holds no events")
    return events


def write_stream(events: list[tuple[int, int]], path: str) -> None:
    """Write the events, one gate-blessed pair per line."""
    Path(path).write_text(
        "".join(f"{ensure_key(key)} {n}\n" for key, n in events), encoding="utf-8"
    )


@dataclass(frozen=True)
class Snapshot:
    """An event list and the seed that made it, replayable as text."""

    events: tuple[tuple[int, int], ...]
    seed: int

    def dumps(self) -> str:
        return json.dumps(
            {"events": [[key, n] for key, n in self.events], "seed": self.seed}
        )

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        try:
            payload = json.loads(text)
            events = tuple(
                (ensure_key(int(key)), int(n)) for key, n in payload["events"]
            )
            seed = int(payload["seed"])
        except (KeyError, TypeError, ValueError, KeysError, json.JSONDecodeError) as err:
            raise CorpusError(f"half a snapshot: {err}") from err
        return cls(events, seed)
