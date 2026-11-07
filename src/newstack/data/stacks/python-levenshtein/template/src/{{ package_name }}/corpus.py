"""Corpora in, corpora out: word lists, seeded generators, snapshots.

A corpus is a word list the gate has already blessed. The generator is
deterministic, the file format is one word per line with comments and
blank lines skipped, and a snapshot keeps its seed so a frozen corpus
replays its words exactly.
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .words import WordError, ensure_word

DEFAULT_SEED = 20260107
ALPHABET = "abcdefghijklmnopqrstuvwxyz"


class CorpusError(ValueError):
    """A corpus cannot be read, written, or generated."""

    __slots__ = ()


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[str]:
    """A deterministic corpus of distinct lowercase words."""
    if count <= 0:
        raise CorpusError(f"no corpus of {count} words")
    rng = random.Random(seed)
    words: set[str] = set()
    while len(words) < count:
        length = rng.randint(2, 8)
        words.add("".join(rng.choice(ALPHABET) for _ in range(length)))
    return sorted(words)


def load_words(path: str) -> list[str]:
    """One word per line; blank lines and # comments skipped."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise CorpusError(f"no such word list: {path}") from error
    words: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            words.append(ensure_word(stripped))
        except WordError as error:
            raise CorpusError(f"the word list holds {error}") from error
    if not words:
        raise CorpusError(f"the word list {path} holds no words")
    return words


def write_words(words: Iterable[str], path: str) -> None:
    """Write the corpus, one gate-blessed word per line."""
    Path(path).write_text(
        "".join(f"{ensure_word(word)}\n" for word in words), encoding="utf-8"
    )


@dataclass(frozen=True)
class Snapshot:
    """A corpus and the seed that made it, replayable as text."""

    words: tuple[str, ...]
    seed: int

    def dumps(self) -> str:
        return json.dumps({"words": list(self.words), "seed": self.seed})

    @classmethod
    def loads(cls, text: str) -> Snapshot:
        try:
            payload = json.loads(text)
            words = tuple(ensure_word(word) for word in payload["words"])
            seed = int(payload["seed"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise CorpusError(f"half a snapshot: {error}") from error
        return cls(words, seed)
