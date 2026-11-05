"""Retrieval metrics, each with the assumption it makes written down.

Ranking happens over chunks but every label is attached to a document, so the first
job is to collapse a chunk ranking into a document ranking - once per document, at the
position of its best chunk. Counting chunk hits instead inflates recall for long
documents, which are simply chunked more often.
"""

from __future__ import annotations

import math


def ranked_documents(chunk_ids: list[str]) -> list[str]:
    """Documents in the order their best-ranked chunk appears."""
    seen: set[str] = set()
    order: list[str] = []
    for chunk_id in chunk_ids:
        doc_id = chunk_id.split("#", 1)[0]
        if doc_id not in seen:
            seen.add(doc_id)
            order.append(doc_id)
    return order


def recall_at_k(documents: list[str], relevant: set[str], k: int) -> float | None:
    """Fraction of the relevant documents found in the first `k`.

    Returns None when an author marked a query with no relevant documents: there is
    nothing to recall, and scoring that as 0.0 blames the retriever for a gap in the
    labels. The caller counts and reports these instead.
    """
    if not relevant:
        return None
    if k < 1:
        raise ValueError("k must be at least 1")
    found = set(documents[:k]) & relevant
    return len(found) / len(relevant)


def precision_at_k(documents: list[str], relevant: set[str], k: int) -> float:
    """Share of the `k` slots that hold a relevant document.

    The denominator is `k`, not the number of results returned: a retriever that
    finds three relevant chunks and stops is not more precise than one that finds
    three and returns ten.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    return len(set(documents[:k]) & relevant) / k


def reciprocal_rank(documents: list[str], relevant: set[str]) -> float:
    """1/rank of the first relevant document, or 0.0 when there is none."""
    for position, doc_id in enumerate(documents, start=1):
        if doc_id in relevant:
            return 1.0 / position
    return 0.0


def dcg(grades: list[int]) -> float:
    """Discounted cumulative gain with the exponential gain `2**g - 1`."""
    return sum((2**grade - 1) / math.log2(position + 1) for position, grade in enumerate(grades, 1))


def ndcg_at_k(documents: list[str], grades: dict[str, int], k: int) -> float:
    """Graded gain normalised by the best ordering the labels allow.

    A document the labels do not mention counts as grade 0 rather than being dropped:
    the corpus was searched in full, so an unjudged document that ranks first really
    did occupy a slot.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    actual = [grades.get(doc_id, 0) for doc_id in documents[:k]]
    ideal = sorted(grades.values(), reverse=True)[:k]
    best = dcg(ideal)
    if best == 0:
        return 0.0
    return dcg(actual) / best


def mean(values: list[float | None]) -> tuple[float, int]:
    """Average of the values that exist, plus how many were skipped."""
    kept = [value for value in values if value is not None]
    if not kept:
        return 0.0, len(values)
    return sum(kept) / len(kept), len(values) - len(kept)
