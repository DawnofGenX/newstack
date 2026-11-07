"""Texts in, streams out: corpora, generators, snapshots.

One text per line; blank lines and # comments are skipped and
every other line must pass the text gate. The generator is
deterministic from its seed, and a snapshot keeps that seed, so a
frozen corpus replays its texts exactly, in order, forever.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path as DiskPath

from .coder import compress
from .text import LETTERS, TextError, ensure_text

DEFAULT_SEED = 20261107


class CorpusError(ValueError):
    """A corpus cannot be read, written, generated, or replayed."""

    __slots__ = ()


@dataclass(frozen=True)
class Snapshot:
    """A frozen corpus and the seed that owes it."""

    texts: tuple[str, ...]
    seed: int

    def dumps(self) -> str:
        return json.dumps({"seed": self.seed, "texts": list(self.texts)})

    @classmethod
    def loads(cls, payload: str) -> Snapshot:
        try:
            record = json.loads(payload)
            return cls(tuple(record["texts"]), int(record["seed"]))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as failure:
            raise CorpusError(f"half a snapshot: {failure}") from failure


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[str]:
    """A deterministic list of repetitive texts a coder bites on."""
    if count <= 0:
        raise CorpusError(f"no texts from {count}")
    rng = random.Random(seed)
    texts: list[str] = []
    seen: set[str] = set()
    while len(texts) < count:
        stem = "".join(rng.choice(LETTERS[:5]) for _ in range(rng.randint(1, 6)))
        repeats = rng.randint(1, 8)
        text = stem * repeats
        if text in seen:
            continue
        seen.add(text)
        texts.append(text)
    return texts


def load_texts(path: str) -> list[str]:
    """One text per line; blank lines and # comments skipped."""
    try:
        text = DiskPath(path).read_text(encoding="utf-8")
    except OSError as failure:
        raise CorpusError(f"no such corpus: {path}") from failure
    texts: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            texts.append(ensure_text(stripped))
        except TextError as failure:
            raise CorpusError(f"the corpus holds {stripped!r}, no text: {failure}") from failure
    if not texts:
        raise CorpusError(f"{path} names no texts")
    return texts


def write_texts(texts: list[str], path: str) -> None:
    """Write a corpus, one text per line, ended by a newline."""
    try:
        DiskPath(path).write_text("\n".join(texts) + "\n", encoding="utf-8")
    except OSError as failure:
        raise CorpusError(f"cannot write {path}: {failure}") from failure


def report_lines(texts: list[str]) -> list[str]:
    """Compress the corpus and answer line by line, letters vs tokens."""
    lines: list[str] = []
    for text in texts:
        tokens = compress(text)
        lines.append(f"{len(text)} letters -> {len(tokens)} tokens {text[:20]!r}")
    return lines
