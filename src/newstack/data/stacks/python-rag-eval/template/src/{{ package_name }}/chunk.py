"""Split documents into overlapping word windows with stable identifiers.

The identifier is `doc#start`, where `start` is a word offset in the document. It is
not a hash and not a counter: the same document chunked twice produces the same ids,
so a retrieval report can be diffed between runs and a hit can be traced back to the
words it covers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

WORD = re.compile(r"[a-z0-9]+")

DEFAULT_SIZE = 40
DEFAULT_OVERLAP = 10


def words(text: str) -> list[str]:
    """Lowercase alphanumeric words.

    Punctuation is dropped on purpose: `rotate-key.md` becomes `rotate key md`, so a
    query about rotation matches the prose and not only the heading.
    """
    return WORD.findall(text.lower())


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    start: int
    end: int
    text: str

    @property
    def chunk_id(self) -> str:
        return f"{self.doc_id}#{self.start}"

    @property
    def length(self) -> int:
        return self.end - self.start


def chunk_document(
    doc_id: str,
    text: str,
    size: int = DEFAULT_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Word windows of `size`, each starting `size - overlap` words after the last.

    An overlap of zero is allowed and produces disjoint chunks; an overlap equal to
    the size would never advance, and a larger one would run backwards, so both are
    refused instead of looping.
    """
    if size < 1:
        raise ValueError("size must be at least 1 word")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= size:
        raise ValueError("overlap must be smaller than size, or the window never moves")

    tokens = words(text)
    if not tokens:
        return []

    step = size - overlap
    chunks: list[Chunk] = []
    start = 0
    while start < len(tokens):
        end = min(start + size, len(tokens))
        chunks.append(Chunk(doc_id, start, end, " ".join(tokens[start:end])))
        if end == len(tokens):
            break
        start += step
    return chunks


def chunk_corpus(
    documents: dict[str, str],
    size: int = DEFAULT_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Every document, in name order, so the corpus order never depends on the filesystem."""
    chunks: list[Chunk] = []
    for doc_id in sorted(documents):
        chunks.extend(chunk_document(doc_id, documents[doc_id], size, overlap))
    return chunks


def uncovered(doc_id: str, text: str, chunks: list[Chunk]) -> list[int]:
    """Word positions no chunk contains - should always be empty.

    Overlap makes it easy to skip a stretch of a document without noticing: a step
    larger than `size - overlap` leaves a hole, and every metric afterwards is quietly
    measured against an incomplete corpus.
    """
    covered: set[int] = set()
    for chunk in chunks:
        covered.update(range(chunk.start, chunk.end))
    return [position for position in range(len(words(text))) if position not in covered]
