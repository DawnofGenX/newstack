"""Texts in, ledgers out: corpora, generators, snapshots.

One text per line; blank lines and # comments are skipped and
every other line must pass the text gate. The generator is
deterministic from its seed, and a snapshot keeps that seed, so a
frozen corpus replays its texts exactly, in order, forever. The
report prices every text in bits against its naive byte price.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path as DiskPath

from .coder import encode, size_report
from .freq import tally
from .table import code_table
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
    """A deterministic list of skewed texts the coder bites on."""
    if count <= 0:
        raise CorpusError(f"no texts from {count}")
    rng = random.Random(seed)
    texts: list[str] = []
    seen: set[str] = set()
    while len(texts) < count:
        pool = LETTERS[: rng.randint(2, 6)]
        weights = [pool[0]] * rng.randint(1, 5) + list(pool)
        text = "".join(rng.choice(weights) for _ in range(rng.randint(6, 40)))
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
    """Price the corpus line by line: letters, bits, the table's verdict."""
    lines: list[str] = []
    for text in texts:
        letters, bits, _ = size_report(text)
        words = len(code_table(tally(text)).codes) if text else 0
        lines.append(
            f"{letters} letters -> {bits} bits over {words} words {text[:20]!r}"
        )
    return lines


def stream_json(text: str) -> str:
    """The coder's wire format: the bits and the table that reads them."""
    bits = encode(text)
    book = code_table(tally(text)) if text else None
    return json.dumps(
        {"bits": bits, "codes": dict(book.codes) if book else {}},
        sort_keys=True,
    )
