"""Texts in, tables out: text lists, seeded generators, snapshots.

A text list is one lowercase text per line, letters only. The
generator is deterministic, the file format skips blank lines and
comments, and a snapshot keeps its seed so a frozen list replays its
texts exactly, in order, forever.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .text import TextError, ensure_text

DEFAULT_SEED = 20261107
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


class CorpusError(ValueError):
    """A text list cannot be read, written, or generated."""

    __slots__ = ()


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[str]:
    """A deterministic list of distinct lowercase texts, repeats inside."""
    if count <= 0:
        raise CorpusError(f"no texts from {count}")
    rng = random.Random(seed)
    texts: set[str] = set()
    while len(texts) < count:
        length = rng.randint(2, 24)
        body = "".join(rng.choice(ALPHABET[: rng.randint(2, 8)]) for _ in range(length))
        texts.add(body)
    return sorted(texts)


def load_texts(path: str) -> list[str]:
    """One text per line; blank lines and # comments skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise CorpusError(f"no such text list: {path}") from error
    texts: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            texts.append(ensure_text(stripped))
        except TextError as failure:
            raise CorpusError(f"the text list holds {failure}") from failure
    if not texts:
        raise CorpusError(f"the text list {path} holds no texts")
    return texts


def write_texts(texts: list[str], path: str) -> None:
    """Write the list, one gate-blessed text per line."""
    Path(path).write_text(
        "".join(f"{ensure_text(body)}\n" for body in texts), encoding="utf-8"
    )


@dataclass(frozen=True)
class Snapshot:
    """A text list and the seed that made it, replayable as text."""

    texts: tuple[str, ...]
    seed: int

    def dumps(self) -> str:
        return json.dumps({"texts": list(self.texts), "seed": self.seed})

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        try:
            payload = json.loads(text)
            texts = tuple(ensure_text(body) for body in payload["texts"])
            seed = int(payload["seed"])
        except (KeyError, TypeError, ValueError, TextError, json.JSONDecodeError) as err:
            raise CorpusError(f"half a snapshot: {err}") from err
        return cls(texts, seed)
