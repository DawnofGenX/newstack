"""Words in, snapshots out: word lists, seeded generators, frozen pairs.

A word list is one lowercase-letter word per line. The generator is
deterministic, the file format skips blank lines and comments, and
a snapshot keeps its seed so a frozen list replays its words
exactly, in order, forever.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .word import WordError, ensure_word

DEFAULT_SEED = 20261107
LETTERS = "abcdefghijklmnopqrstuvwxyz"


class CorpusError(ValueError):
    """A word list cannot be read, written, or generated."""

    __slots__ = ()


def synthetic(count: int, seed: int = DEFAULT_SEED) -> list[str]:
    """A deterministic list of distinct short words, reuse allowed.

    Repeats are kept on purpose: a prefix only shows itself when a
    letter comes back, and the corpus must feed the array the
    tangles it exists for.
    """
    if count <= 0:
        raise CorpusError(f"no words from {count}")
    rng = random.Random(seed)
    words: set[str] = set()
    while len(words) < count:
        size = rng.randint(1, 8)
        words.add("".join(rng.choice(LETTERS[:5]) for _ in range(size)))
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
        except WordError as failure:
            raise CorpusError(f"the word list holds {stripped!r}, no word") from failure
    if not words:
        raise CorpusError(f"the word list {path} holds no words")
    return words


def write_words(words: list[str], path: str) -> None:
    """Write the list, one gate-blessed word per line."""
    Path(path).write_text(
        "".join(f"{ensure_word(word)}\n" for word in words),
        encoding="utf-8",
    )


@dataclass(frozen=True)
class Snapshot:
    """A word list and the seed that made it, replayable as text."""

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
        except (KeyError, TypeError, ValueError, WordError, json.JSONDecodeError) as err:
            raise CorpusError(f"half a snapshot: {err}") from err
        return cls(words, seed)
