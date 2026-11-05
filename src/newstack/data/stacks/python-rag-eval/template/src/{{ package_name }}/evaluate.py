"""Turn a corpus and a set of judgements into numbers you can argue with."""

from __future__ import annotations

from dataclasses import dataclass

from .chunk import DEFAULT_OVERLAP, DEFAULT_SIZE, chunk_corpus
from .index import BM25
from .metrics import (
    mean,
    ndcg_at_k,
    precision_at_k,
    ranked_documents,
    recall_at_k,
    reciprocal_rank,
)


@dataclass(frozen=True)
class QueryScore:
    query: str
    relevant: int
    found: int
    recall: float | None
    precision: float
    reciprocal_rank: float
    ndcg: float
    top: str


@dataclass(frozen=True)
class Report:
    k: int
    size: int
    overlap: int
    chunks: int
    scores: list[QueryScore]

    def macro(self, attribute: str) -> float:
        value, _ = mean([getattr(score, attribute) for score in self.scores])
        return value

    @property
    def judged(self) -> int:
        return sum(1 for score in self.scores if score.relevant > 0)

    @property
    def skipped(self) -> int:
        return sum(1 for score in self.scores if score.relevant == 0)

    @property
    def micro_recall(self) -> float:
        """Pooled recall: every relevant document counts once, whatever query it came from.

        Macro and micro answer different questions. Macro asks "how well does this work
        per query"; micro asks "how much of the judged corpus did we find", and is
        dominated by queries with many relevant documents. Reporting only one of them
        is the usual way a retrieval change looks good and is not.
        """
        relevant = sum(score.relevant for score in self.scores)
        if relevant == 0:
            return 0.0
        return sum(score.found for score in self.scores) / relevant

    def as_dict(self) -> dict[str, object]:
        return {
            "k": self.k,
            "size": self.size,
            "overlap": self.overlap,
            "chunks": self.chunks,
            "queries": len(self.scores),
            "judged": self.judged,
            "skipped": self.skipped,
            "macro_recall": round(self.macro("recall"), 4),
            "micro_recall": round(self.micro_recall, 4),
            "macro_precision": round(self.macro("precision"), 4),
            "mrr": round(self.macro("reciprocal_rank"), 4),
            "ndcg": round(self.macro("ndcg"), 4),
            "per_query": [
                {
                    "query": score.query,
                    "relevant": score.relevant,
                    "found": score.found,
                    "recall": None if score.recall is None else round(score.recall, 4),
                    "ndcg": round(score.ndcg, 4),
                    "reciprocal_rank": round(score.reciprocal_rank, 4),
                    "top": score.top,
                }
                for score in self.scores
            ],
        }


def evaluate(
    corpus: dict[str, str],
    queries: dict[str, dict[str, int]],
    size: int = DEFAULT_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    k: int = 3,
) -> Report:
    """Search every query and score it. No sampling, no shuffling, no model in the loop."""
    if k < 1:
        raise ValueError("k must be at least 1")
    chunks = chunk_corpus(corpus, size=size, overlap=overlap)
    index = BM25(chunks)

    scores: list[QueryScore] = []
    for query in sorted(queries):
        grades = queries[query]
        relevant = {doc_id for doc_id, grade in grades.items() if grade > 0}
        hits = index.search(query, k=k)
        documents = ranked_documents([hit.chunk_id for hit in hits])
        scores.append(
            QueryScore(
                query=query,
                relevant=len(relevant),
                found=len(set(documents[:k]) & relevant),
                recall=recall_at_k(documents, relevant, k),
                precision=precision_at_k(documents, relevant, k),
                reciprocal_rank=reciprocal_rank(documents, relevant),
                ndcg=ndcg_at_k(documents, grades, k),
                top=documents[0] if documents else "-",
            )
        )

    return Report(k=k, size=size, overlap=overlap, chunks=len(chunks), scores=scores)
