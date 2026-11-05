"""Okapi BM25 over chunks, with the arithmetic written out.

Nothing here is learned, cached, or approximate: the score of a chunk for a query is a
sum over the query's distinct terms, so two runs over the same corpus give the same
ranking, and a report can name the idf of the term that decided it.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from .chunk import Chunk, words

K1 = 1.2
B = 0.75


@dataclass(frozen=True)
class Hit:
    chunk_id: str
    doc_id: str
    score: float
    text: str


class BM25:
    def __init__(self, chunks: list[Chunk], k1: float = K1, b: float = B) -> None:
        if not chunks:
            raise ValueError("an empty corpus cannot be searched")
        self.chunks = list(chunks)
        self.k1 = k1
        self.b = b
        self.term_frequencies = [Counter(words(chunk.text)) for chunk in self.chunks]
        self.lengths = [sum(counter.values()) for counter in self.term_frequencies]
        total = sum(self.lengths)
        self.average_length = total / len(self.chunks)
        document_frequency: Counter[str] = Counter()
        for counter in self.term_frequencies:
            document_frequency.update(counter.keys())
        self.document_frequency = document_frequency

    def idf(self, term: str) -> float:
        """Strictly positive, even for a term every chunk contains.

        The unsmoothed form `log(N/df)` reaches zero at `df == N` and goes negative
        beyond it, so a stop word would actively push chunks down. The `+0.5`
        smoothing keeps the floor at zero and the ranking monotone.
        """
        count = len(self.chunks)
        found = self.document_frequency.get(term, 0)
        return math.log(1 + (count - found + 0.5) / (found + 0.5))

    def score(self, position: int, terms: list[str]) -> float:
        frequencies = self.term_frequencies[position]
        length = self.lengths[position]
        total = 0.0
        for term in terms:
            frequency = frequencies.get(term, 0)
            if frequency == 0:
                continue
            normaliser = self.k1 * (1 - self.b + self.b * length / self.average_length)
            total += self.idf(term) * frequency * (self.k1 + 1) / (frequency + normaliser)
        return total

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """The best `k` chunks, ties broken by chunk id so the order is reproducible.

        Query terms are de-duplicated: BM25 already weights a term by how often it
        appears in the document, and letting a repeated query term multiply that
        weight again is the most common way a hand-rolled BM25 becomes a keyword
        counter.
        """
        if k < 1:
            raise ValueError("k must be at least 1")
        terms = sorted(set(words(query)))
        scored = [
            Hit(chunk.chunk_id, chunk.doc_id, self.score(position, terms), chunk.text)
            for position, chunk in enumerate(self.chunks)
        ]
        scored = [hit for hit in scored if hit.score > 0]
        scored.sort(key=lambda hit: (-hit.score, hit.chunk_id))
        return scored[:k]
